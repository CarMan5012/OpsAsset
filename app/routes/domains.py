import socket
import struct
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models import Domain, Host
from app.schemas import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    DomainListResponse,
    DomainDnsCheckResult,
    DomainHostSimple
)

router = APIRouter(prefix="/api/domains", tags=["域名与公网绑定资产"])

def parse_host_ids(raw_ids: Optional[str], fallback_id: Optional[int] = None) -> List[int]:
    """解析逗号分隔的主机ID列表"""
    ids = []
    if raw_ids:
        for part in raw_ids.split(','):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    if not ids and fallback_id:
        ids.append(fallback_id)
    return list(dict.fromkeys(ids))

def attach_hosts_to_domain(domain: Domain, host_map: Dict[int, Host]) -> DomainResponse:
    """组装包含多台承载主机的 DomainResponse"""
    ids = parse_host_ids(domain.bound_host_ids, domain.bound_host_id)
    hosts_list = []
    for hid in ids:
        if hid in host_map:
            h = host_map[hid]
            hosts_list.append(DomainHostSimple(
                id=h.id,
                hostname=h.hostname,
                private_ip=h.private_ip,
                public_ip=h.public_ip or "",
                env=h.env,
                status=h.status or "online"
            ))
    
    primary_host = hosts_list[0] if hosts_list else None

    resp = DomainResponse(
        id=domain.id,
        domain_name=domain.domain_name,
        public_ip=domain.public_ip or "",
        port=domain.port or "80, 443",
        env=domain.env or "prod",
        bound_host_id=domain.bound_host_id,
        bound_host_ids=ids,
        notes=domain.notes or "",
        resolved_ip=domain.resolved_ip or "",
        resolve_status=domain.resolve_status or "unknown",
        last_checked_at=domain.last_checked_at,
        created_at=domain.created_at or datetime.now(),
        updated_at=domain.updated_at,
        host=primary_host,
        hosts=hosts_list
    )
    return resp

def query_direct_dns(domain: str, qtype: int = 1, dns_server: str = "223.5.5.5") -> List[str]:
    """直接向公共 DNS 发送 UDP 请求查询 A (1) 或 AAAA (28) 记录"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        header = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
        qname = b"".join(bytes([len(p)]) + p.encode() for p in domain.split(".")) + b"\x00"
        question = qname + struct.pack("!HH", qtype, 1)
        sock.sendto(header + question, (dns_server, 53))
        data, _ = sock.recvfrom(2048)
        sock.close()
        
        ancount = struct.unpack("!H", data[6:8])[0]
        offset = 12 + len(question)
        ips = []
        for _ in range(ancount):
            if offset >= len(data):
                break
            if (data[offset] & 0xC0) == 0xC0:
                offset += 2
            else:
                while offset < len(data) and data[offset] != 0:
                    offset += 1 + data[offset]
                offset += 1
            if offset + 10 > len(data):
                break
            rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset+10])
            offset += 10
            rdata = data[offset:offset+rdlength]
            offset += rdlength
            if rtype == 1 and rdlength == 4:
                ips.append(socket.inet_ntoa(rdata))
            elif rtype == 28 and rdlength == 16:
                ips.append(socket.inet_ntop(socket.AF_INET6, rdata))
        return ips
    except Exception:
        return []

def do_resolve_and_compare(domain: Domain) -> DomainDnsCheckResult:
    """执行 DNS 实际解析 (同时支持 IPv4 + IPv6 全部地址) 并与绑定的公网 IP 比对"""
    clean_name = domain.domain_name.strip().split(":")[0]
    expected_raw = (domain.public_ip or "").strip()
    expected_ips = [ip.strip() for ip in re.split(r"[,，;\s\n]+", expected_raw) if ip.strip()]
    
    resolved_v4 = []
    resolved_v6 = []
    all_resolved = []
    resolve_status = "failed"
    is_matched = False
    message = ""

    # 1. 尝试系统 socket.getaddrinfo (查询所有 IPv4 + IPv6)
    try:
        socket.setdefaulttimeout(3.0)
        addr_infos = socket.getaddrinfo(clean_name, None)
        for info in addr_infos:
            family, _, _, _, sockaddr = info
            ip = sockaddr[0]
            if ip not in all_resolved:
                all_resolved.append(ip)
                if family == socket.AF_INET and ip not in resolved_v4:
                    resolved_v4.append(ip)
                elif family == socket.AF_INET6 and ip not in resolved_v6:
                    resolved_v6.append(ip)
    except Exception:
        pass

    # 2. 显式尝试查询系统 IPv6 (AF_INET6)
    try:
        for info in socket.getaddrinfo(clean_name, None, socket.AF_INET6):
            ip = info[4][0]
            if ip not in all_resolved:
                all_resolved.append(ip)
            if ip not in resolved_v6:
                resolved_v6.append(ip)
    except Exception:
        pass

    # 3. 补充公共 DNS (223.5.5.5 / 119.29.29.29) AAAA (IPv6) 和 A (IPv4) 查询
    for srv in ["223.5.5.5", "119.29.29.29"]:
        if not resolved_v6:
            for ip in query_direct_dns(clean_name, 28, srv):
                if ip not in all_resolved:
                    all_resolved.append(ip)
                if ip not in resolved_v6:
                    resolved_v6.append(ip)
        if not resolved_v4:
            for ip in query_direct_dns(clean_name, 1, srv):
                if ip not in all_resolved:
                    all_resolved.append(ip)
                if ip not in resolved_v4:
                    resolved_v4.append(ip)

    resolved_str = ", ".join(all_resolved)
    
    if not all_resolved:
        resolve_status = "failed"
        message = "DNS 查询未返回任何 IPv4 或 IPv6 记录"
    elif expected_ips:
        # 智能比对：检查配置的绑定 IP 是否在解析到的集合中
        matched_count = sum(1 for exp in expected_ips if exp in all_resolved)
        if matched_count == len(expected_ips):
            resolve_status = "matched"
            is_matched = True
            v4_str = f"IPv4: {', '.join(resolved_v4)}" if resolved_v4 else ""
            v6_str = f"IPv6: {', '.join(resolved_v6)}" if resolved_v6 else ""
            details = " | ".join(filter(None, [v4_str, v6_str]))
            message = f"解析正常：绑定 IP 与 DNS 全部记录一致 ({details})"
        elif matched_count > 0:
            resolve_status = "matched"
            is_matched = True
            message = f"部分一致：{matched_count}/{len(expected_ips)} 个绑定 IP 已成功解析"
        else:
            resolve_status = "mismatched"
            is_matched = False
            message = f"解析不一致：实际解析为 [{resolved_str}]，与配置绑定 IP [{expected_raw}] 不匹配"
    else:
        resolve_status = "matched"
        is_matched = True
        v4_str = f"IPv4: {', '.join(resolved_v4)}" if resolved_v4 else ""
        v6_str = f"IPv6: {', '.join(resolved_v6)}" if resolved_v6 else ""
        message = f"解析成功 (未配置绑定公网IP)：{' | '.join(filter(None, [v4_str, v6_str]))}"

    domain.resolved_ip = resolved_str
    domain.resolve_status = resolve_status
    domain.last_checked_at = datetime.now()

    return DomainDnsCheckResult(
        id=domain.id,
        domain_name=domain.domain_name,
        public_ip=expected_raw,
        resolved_ip=resolved_str,
        resolved_ips_v4=resolved_v4,
        resolved_ips_v6=resolved_v6,
        resolve_status=resolve_status,
        is_matched=is_matched,
        message=message
    )

@router.get("", response_model=DomainListResponse)
def list_domains(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    keyword: Optional[str] = Query(None, description="搜索域名/公网IP/备注"),
    env: Optional[str] = Query(None, description="环境过滤 prod/test"),
    resolve_status: Optional[str] = Query(None, description="解析一致性过滤 matched/mismatched/failed"),
    db: Session = Depends(get_db)
):
    query = db.query(Domain)

    if env:
        query = query.filter(Domain.env == env)
    if resolve_status:
        query = query.filter(Domain.resolve_status == resolve_status)

    raw_kw = (keyword or "").strip()
    if raw_kw:
        query = query.filter(
            or_(
                Domain.domain_name.ilike(f"%{raw_kw}%"),
                Domain.public_ip.ilike(f"%{raw_kw}%"),
                Domain.resolved_ip.ilike(f"%{raw_kw}%"),
                Domain.notes.ilike(f"%{raw_kw}%")
            )
        )

    total = query.count()
    domains = query.order_by(Domain.id.desc()).offset((page - 1) * size).limit(size).all()

    # 收集所有相关的 Host ID 批量查询，避免 N+1
    all_host_ids = set()
    for d in domains:
        ids = parse_host_ids(d.bound_host_ids, d.bound_host_id)
        all_host_ids.update(ids)
    
    host_map = {}
    if all_host_ids:
        hosts = db.query(Host).filter(Host.id.in_(list(all_host_ids))).all()
        host_map = {h.id: h for h in hosts}

    items = [attach_hosts_to_domain(d, host_map) for d in domains]

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

@router.post("", response_model=DomainResponse)
def create_domain(domain_in: DomainCreate, db: Session = Depends(get_db)):
    exist = db.query(Domain).filter(Domain.domain_name == domain_in.domain_name).first()
    if exist:
        raise HTTPException(status_code=400, detail=f"域名 {domain_in.domain_name} 已存在")

    host_ids = domain_in.bound_host_ids or []
    if not host_ids and domain_in.bound_host_id:
        host_ids = [domain_in.bound_host_id]
    
    primary_host_id = host_ids[0] if host_ids else None
    bound_host_ids_str = ",".join(str(i) for i in host_ids)

    if host_ids:
        found_hosts = db.query(Host).filter(Host.id.in_(host_ids)).all()
        found_ids = {h.id for h in found_hosts}
        missing = [i for i in host_ids if i not in found_ids]
        if missing:
            raise HTTPException(status_code=400, detail=f"关联的主机 ID {missing} 不存在")

    domain = Domain(
        domain_name=domain_in.domain_name,
        public_ip=domain_in.public_ip or "",
        port=domain_in.port or "80, 443",
        env=domain_in.env or "prod",
        bound_host_id=primary_host_id,
        bound_host_ids=bound_host_ids_str,
        notes=domain_in.notes or ""
    )

    try:
        do_resolve_and_compare(domain)
    except Exception:
        pass

    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    from app.routes.dashboard import invalidate_dashboard_cache
    invalidate_dashboard_cache()

    hosts = db.query(Host).filter(Host.id.in_(host_ids)).all() if host_ids else []
    host_map = {h.id: h for h in hosts}
    return attach_hosts_to_domain(domain, host_map)

@router.get("/{domain_id}", response_model=DomainResponse)
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名资产不存在")
    
    ids = parse_host_ids(domain.bound_host_ids, domain.bound_host_id)
    hosts = db.query(Host).filter(Host.id.in_(ids)).all() if ids else []
    host_map = {h.id: h for h in hosts}
    return attach_hosts_to_domain(domain, host_map)

@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(domain_id: int, domain_in: DomainUpdate, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名资产不存在")

    update_data = domain_in.model_dump(exclude_unset=True)

    if "domain_name" in update_data and update_data["domain_name"] != domain.domain_name:
        exist = db.query(Domain).filter(Domain.domain_name == update_data["domain_name"]).first()
        if exist:
            raise HTTPException(status_code=400, detail=f"域名 {update_data['domain_name']} 已存在")

    if "bound_host_ids" in update_data and update_data["bound_host_ids"] is not None:
        host_ids = update_data["bound_host_ids"]
        domain.bound_host_ids = ",".join(str(i) for i in host_ids)
        domain.bound_host_id = host_ids[0] if host_ids else None
    elif "bound_host_id" in update_data:
        hid = update_data["bound_host_id"]
        domain.bound_host_id = hid
        domain.bound_host_ids = str(hid) if hid else ""

    for key in ["domain_name", "public_ip", "port", "env", "notes"]:
        if key in update_data:
            setattr(domain, key, update_data[key])

    if "public_ip" in update_data or "domain_name" in update_data:
        try:
            do_resolve_and_compare(domain)
        except Exception:
            pass

    domain.updated_at = datetime.now()
    db.commit()
    db.refresh(domain)

    from app.routes.dashboard import invalidate_dashboard_cache
    invalidate_dashboard_cache()

    ids = parse_host_ids(domain.bound_host_ids, domain.bound_host_id)
    hosts = db.query(Host).filter(Host.id.in_(ids)).all() if ids else []
    host_map = {h.id: h for h in hosts}
    return attach_hosts_to_domain(domain, host_map)

@router.delete("/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名资产不存在")
    db.delete(domain)
    db.commit()

    from app.routes.dashboard import invalidate_dashboard_cache
    invalidate_dashboard_cache()

    return {"message": "域名已删除", "id": domain_id}

@router.post("/{domain_id}/check-dns", response_model=DomainDnsCheckResult)
def check_single_domain_dns(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名资产不存在")
    res = do_resolve_and_compare(domain)
    db.commit()
    return res

@router.post("/check-all-dns", response_model=List[DomainDnsCheckResult])
def check_all_domains_dns(db: Session = Depends(get_db)):
    domains = db.query(Domain).all()
    results = []
    for d in domains:
        res = do_resolve_and_compare(d)
        results.append(res)
    db.commit()
    return results
