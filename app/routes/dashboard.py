import re
import time
from collections import defaultdict
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import Host, Cluster, HostClusterRelation, Domain
from app.schemas import (
    DashboardOverview,
    EnvResourceStats,
    ClusterTypeCount,
    ClusterDistributionItem
)

router = APIRouter(prefix="/api/dashboard", tags=["资产看板与统计"])

# 极速内存缓存 (10秒自动刷新，数据变动可秒级感知)
_CACHE = {
    "overview": None,
    "overview_ts": 0,
    "dist": None,
    "dist_ts": 0,
    "ttl": 10  # 缓存 10 秒
}

def parse_public_ips(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [x.strip() for x in re.split(r"[,，\s\n]+", str(raw)) if x.strip()]

def invalidate_dashboard_cache():
    """写操作时可调用清空缓存"""
    _CACHE["overview"] = None
    _CACHE["overview_ts"] = 0
    _CACHE["dist"] = None
    _CACHE["dist_ts"] = 0

def calc_env_stats(hosts: List[Host]) -> EnvResourceStats:
    stats = EnvResourceStats()
    stats.host_count = len(hosts)
    env_pub_ips = set()

    for h in hosts:
        st = (h.status or "").lower()
        if st in ("online", "running"):
            stats.online_count += 1
        elif st in ("offline", "stopped"):
            stats.offline_count += 1
        elif st in ("maintenance", "warning"):
            stats.maintenance_count += 1

        stats.total_cpu_cores += (h.cpu_cores or 0)
        stats.total_memory_gb += (h.memory_gb or 0.0)
        stats.total_disk_gb += (h.disk_gb or 0.0)

        if h.public_ip:
            for ip in parse_public_ips(h.public_ip):
                env_pub_ips.add(ip)

    stats.public_ip_count = len(env_pub_ips)
    stats.total_memory_gb = round(stats.total_memory_gb, 2)
    stats.total_disk_gb = round(stats.total_disk_gb, 2)
    return stats

@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(db: Session = Depends(get_db)):
    now = time.time()
    if _CACHE["overview"] is not None and (now - _CACHE["overview_ts"]) < _CACHE["ttl"]:
        return _CACHE["overview"]

    # 1. 批量查询所有主机与集群基本信息
    all_hosts = db.query(Host).all()
    total_clusters = db.query(func.count(Cluster.id)).scalar() or 0
    all_domains = db.query(Domain).all()

    # 提取所有公网 IP 明细
    all_pub_ips = set()
    pub_ip_details = []
    seen_ips = set()
    for h in all_hosts:
        if h.public_ip:
            for ip in parse_public_ips(h.public_ip):
                all_pub_ips.add(ip)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pub_ip_details.append({
                        "ip": ip,
                        "hostname": h.hostname,
                        "env": h.env,
                        "is_ipv6": ":" in ip
                    })

    # 统计域名数据
    total_domains = len(all_domains)
    matched_domains = sum(1 for d in all_domains if d.resolve_status == "matched")
    mismatched_domains = sum(1 for d in all_domains if d.resolve_status == "mismatched")
    failed_domains = sum(1 for d in all_domains if d.resolve_status == "failed")

    # 收集域名关联主机名
    host_map = {h.id: h.hostname for h in all_hosts}
    domains_summary = []
    for d in all_domains:
        h_names = []
        if d.bound_host_ids:
            for hid_str in d.bound_host_ids.split(','):
                if hid_str.strip().isdigit():
                    hid = int(hid_str.strip())
                    if hid in host_map:
                        h_names.append(host_map[hid])
        elif d.bound_host_id and d.bound_host_id in host_map:
            h_names.append(host_map[d.bound_host_id])

        domains_summary.append({
            "id": d.id,
            "domain_name": d.domain_name,
            "public_ip": d.public_ip or "",
            "resolved_ip": d.resolved_ip or "",
            "resolve_status": d.resolve_status or "unknown",
            "env": d.env,
            "hosts": h_names
        })

    # 动态分组计算各环境资源指标
    hosts_by_env = defaultdict(list)
    for h in all_hosts:
        env_key = h.env or "other"
        hosts_by_env[env_key].append(h)

    env_stats_map = {
        env_k: calc_env_stats(h_list)
        for env_k, h_list in hosts_by_env.items()
    }

    prod_stats = env_stats_map.get("prod", EnvResourceStats())
    test_stats = env_stats_map.get("test", EnvResourceStats())

    total_cpu = sum(s.total_cpu_cores for s in env_stats_map.values())
    total_mem = round(sum(s.total_memory_gb for s in env_stats_map.values()), 2)
    total_disk = round(sum(s.total_disk_gb for s in env_stats_map.values()), 2)

    # 2. 统计各集群类型数量
    type_counts = db.query(
        Cluster.cluster_type,
        func.count(Cluster.id)
    ).group_by(Cluster.cluster_type).all()

    cluster_types = [
        ClusterTypeCount(cluster_type=t[0], count=t[1])
        for t in type_counts
    ]

    res = DashboardOverview(
        total_hosts=len(all_hosts),
        total_public_ips=len(all_pub_ips),
        total_cpu_cores=total_cpu,
        total_memory_gb=total_mem,
        total_disk_gb=total_disk,
        total_clusters=total_clusters,
        total_domains=total_domains,
        matched_domains=matched_domains,
        mismatched_domains=mismatched_domains,
        failed_domains=failed_domains,
        public_ip_details=pub_ip_details,
        domains_summary=domains_summary,
        prod=prod_stats,
        test=test_stats,
        envs=env_stats_map,
        cluster_types=cluster_types
    )
    _CACHE["overview"] = res
    _CACHE["overview_ts"] = now
    return res

@router.get("/cluster-distribution", response_model=List[ClusterDistributionItem])
def get_cluster_distribution(db: Session = Depends(get_db)):
    now = time.time()
    if _CACHE["dist"] is not None and (now - _CACHE["dist_ts"]) < _CACHE["ttl"]:
        return _CACHE["dist"]

    clusters = db.query(Cluster).all()
    if not clusters:
        return []

    # 批量一次性查询所有节点关联关系与主机信息，消除 N+1 性能瓶颈
    all_rels = db.query(HostClusterRelation).options(joinedload(HostClusterRelation.host)).all()
    rels_by_cluster = defaultdict(list)
    for r in all_rels:
        rels_by_cluster[r.cluster_id].append(r)

    result = []
    for c in clusters:
        rels = rels_by_cluster.get(c.id, [])
        master_count = sum(1 for r in rels if any(k in (r.role or "").lower() for k in ["master", "leader", "primary", "主"]))
        worker_count = sum(1 for r in rels if any(k in (r.role or "").lower() for k in ["worker", "slave", "follower", "broker", "node", "从", "工作"]))
        other_count = len(rels) - master_count - worker_count

        pub_ips = set()
        for r in rels:
            if r.host and r.host.public_ip:
                for ip in parse_public_ips(r.host.public_ip):
                    pub_ips.add(ip)

        result.append(ClusterDistributionItem(
            cluster_id=c.id,
            name=c.name,
            cluster_type=c.cluster_type,
            version=c.version or "",
            env=c.env,
            node_count=len(rels),
            master_count=master_count,
            worker_count=worker_count,
            other_count=other_count,
            public_ips=sorted(list(pub_ips))
        ))

    sorted_res = sorted(result, key=lambda x: x.node_count, reverse=True)
    _CACHE["dist"] = sorted_res
    _CACHE["dist_ts"] = now
    return sorted_res
