from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import or_, func

from app.database import get_db
from app.models import Host, Cluster, HostClusterRelation
from app.routes.dashboard import invalidate_dashboard_cache
from app.schemas import (
    HostCreate,
    HostUpdate,
    HostResponse,
    ClusterRelationSimple
)

router = APIRouter(prefix="/api/hosts", tags=["主机资产管理"])

def format_host_response(host: Host) -> dict:
    clusters = []
    for rel in host.cluster_relations:
        if rel.cluster:
            clusters.append(ClusterRelationSimple(
                cluster_id=rel.cluster.id,
                cluster_name=rel.cluster.name,
                cluster_type=rel.cluster.cluster_type,
                port=rel.cluster.port or "",
                cluster_version=rel.cluster.version or "",
                version=rel.cluster.version or "",
                env=rel.cluster.env or "",
                description=rel.cluster.description or "",
                role=rel.role
            ))
    return {
        "id": host.id,
        "hostname": host.hostname,
        "private_ip": host.private_ip,
        "public_ip": host.public_ip or "",
        "open_ports": host.open_ports or "",
        "cpu_cores": host.cpu_cores,
        "memory_gb": host.memory_gb,
        "disk_gb": host.disk_gb,
        "os": host.os or "",
        "arch": host.arch or "amd64",
        "kernel_version": host.kernel_version or "",
        "env": host.env,
        "status": host.status,
        "notes": host.notes or "",
        "created_at": host.created_at,
        "updated_at": host.updated_at,
        "clusters": clusters
    }

@router.get("", response_model=dict)
def list_hosts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    env: Optional[str] = Query(None, description="环境 prod/test"),
    status: Optional[str] = Query(None, description="状态 online/offline/maintenance"),
    arch: Optional[str] = Query(None, description="架构 amd64/arm64 等"),
    cluster_id: Optional[int] = Query(None, description="所属集群ID"),
    keyword: Optional[str] = Query(None, description="精准搜索关键词(主机名/IP/端口/集群名)"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: Optional[str] = Query(None, description="排序方向: asc/desc 或 ascending/descending"),
    sort_order: Optional[str] = Query(None, description="兼容前端参数名"),
    db: Session = Depends(get_db)
):
    filters = []

    # 1. 严格精准过滤下拉条件
    if env:
        filters.append(Host.env == env)
    if status:
        filters.append(Host.status == status)
    if arch:
        filters.append(Host.arch == arch)
    if cluster_id:
        filters.append(Host.cluster_relations.any(HostClusterRelation.cluster_id == cluster_id))
    
    # 2. 严格精准过滤搜索关键词
    raw_kw = keyword.strip() if keyword else ""
    if raw_kw:
        filters.append(
            or_(
                Host.hostname.ilike(f"%{raw_kw}%"),
                Host.private_ip.ilike(f"%{raw_kw}%"),
                Host.public_ip.ilike(f"%{raw_kw}%"),
                Host.open_ports.ilike(f"%{raw_kw}%"),
                Host.os.ilike(f"%{raw_kw}%"),
                Host.notes.ilike(f"%{raw_kw}%"),
                Host.cluster_relations.any(
                    HostClusterRelation.cluster.has(
                        or_(
                            Cluster.name.ilike(f"%{raw_kw}%"),
                            Cluster.cluster_type.ilike(f"%{raw_kw}%")
                        )
                    )
                )
            )
        )

    # 3. 极速轻量 Count 查询
    count_query = db.query(func.count(Host.id))
    if filters:
        count_query = count_query.filter(*filters)
    total = count_query.scalar() or 0

    # 4. 动态排序映射与规范化
    real_order = (sort_order or order or "desc").lower().strip()
    is_asc = real_order in ["asc", "ascending"]

    sort_column_map = {
        "id": Host.id,
        "hostname": func.lower(Host.hostname),
        "private_ip": Host.private_ip,
        "public_ip": Host.public_ip,
        "open_ports": Host.open_ports,
        "cpu_cores": func.coalesce(Host.cpu_cores, 0),
        "memory_gb": func.coalesce(Host.memory_gb, 0),
        "disk_gb": func.coalesce(Host.disk_gb, 0),
        "os": func.lower(Host.os),
        "arch": Host.arch,
        "kernel_version": Host.kernel_version,
        "env": Host.env,
        "status": Host.status,
        "notes": Host.notes,
        "created_at": Host.created_at,
        "updated_at": Host.updated_at
    }

    data_query = db.query(Host).options(
        joinedload(Host.cluster_relations).joinedload(HostClusterRelation.cluster)
    )
    if filters:
        data_query = data_query.filter(*filters)

    sort_col = sort_column_map.get(sort_by)
    if sort_col is not None:
        if is_asc:
            data_query = data_query.order_by(sort_col.asc(), Host.id.asc())
        else:
            data_query = data_query.order_by(sort_col.desc(), Host.id.desc())
    else:
        data_query = data_query.order_by(Host.id.desc())

    hosts = data_query.offset((page - 1) * size).limit(size).all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [format_host_response(h) for h in hosts]
    }

@router.post("", response_model=HostResponse)
def create_host(host_in: HostCreate, db: Session = Depends(get_db)):
    # 检查 IP 唯一性
    exist = db.query(Host).filter(Host.private_ip == host_in.private_ip).first()
    if exist:
        raise HTTPException(status_code=400, detail=f"内网IP {host_in.private_ip} 已存在")

    host = Host(
        hostname=host_in.hostname,
        private_ip=host_in.private_ip,
        public_ip=host_in.public_ip or "",
        cpu_cores=host_in.cpu_cores,
        memory_gb=host_in.memory_gb,
        disk_gb=host_in.disk_gb,
        os=host_in.os or "",
        arch=host_in.arch or "amd64",
        kernel_version=host_in.kernel_version or "",
        open_ports=host_in.open_ports or "",
        env=host_in.env,
        status=host_in.status,
        notes=host_in.notes or ""
    )
    db.add(host)
    db.flush()

    # 处理关联集群
    if host_in.clusters:
        for item in host_in.clusters:
            cluster = db.query(Cluster).filter(Cluster.id == item.host_id).first()
            # 注意：此处item结构复用，item.host_id 传入的是 cluster_id
            # 兼容处理
            target_cluster_id = getattr(item, 'cluster_id', getattr(item, 'host_id', None))
            if target_cluster_id:
                rel = HostClusterRelation(
                    host_id=host.id,
                    cluster_id=target_cluster_id,
                    role=item.role or "Worker"
                )
                db.add(rel)

    db.commit()
    db.refresh(host)
    invalidate_dashboard_cache()
    return format_host_response(host)

@router.get("/{host_id}", response_model=HostResponse)
def get_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).options(
        joinedload(Host.cluster_relations).joinedload(HostClusterRelation.cluster)
    ).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    return format_host_response(host)

@router.put("/{host_id}", response_model=HostResponse)
def update_host(host_id: int, host_in: HostUpdate, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")

    update_data = host_in.model_dump(exclude_unset=True)

    if "private_ip" in update_data and update_data["private_ip"] != host.private_ip:
        exist = db.query(Host).filter(Host.private_ip == update_data["private_ip"]).first()
        if exist:
            raise HTTPException(status_code=400, detail=f"内网IP {update_data['private_ip']} 已被占用")

    # 处理集群关联更新
    if "cluster_ids_with_roles" in update_data:
        cluster_list = update_data.pop("cluster_ids_with_roles")
        # 清除现有关系
        db.query(HostClusterRelation).filter(HostClusterRelation.host_id == host.id).delete()
        if cluster_list:
            for c in cluster_list:
                rel = HostClusterRelation(
                    host_id=host.id,
                    cluster_id=c.get("cluster_id"),
                    role=c.get("role", "Worker")
                )
                db.add(rel)

    for field, val in update_data.items():
        setattr(host, field, val)

    host.updated_at = datetime.now()
    db.commit()
    db.refresh(host)
    invalidate_dashboard_cache()
    return format_host_response(host)

@router.delete("/{host_id}")
def delete_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    db.delete(host)
    db.commit()
    invalidate_dashboard_cache()
    return {"message": "主机删除成功", "host_id": host_id}

@router.post("/batch-delete")
def batch_delete_hosts(host_ids: List[int], db: Session = Depends(get_db)):
    if not host_ids:
        return {"deleted_count": 0}
    count = db.query(Host).filter(Host.id.in_(host_ids)).delete(synchronize_session=False)
    db.commit()
    invalidate_dashboard_cache()
    return {"message": f"成功批量删除 {count} 台主机", "deleted_count": count}
