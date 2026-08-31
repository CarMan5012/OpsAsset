from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload, joinedload

from app.database import get_db
from app.models import Cluster, Host, HostClusterRelation
from app.routes.dashboard import invalidate_dashboard_cache
from app.schemas import (
    ClusterCreate,
    ClusterUpdate,
    ClusterResponse,
    HostSimpleForCluster,
    ClusterBindRequest
)

router = APIRouter(prefix="/api/clusters", tags=["集群与服务管理"])

def format_cluster_response(cluster: Cluster) -> dict:
    nodes = []
    for rel in cluster.host_relations:
        if rel.host:
            nodes.append(HostSimpleForCluster(
                host_id=rel.host.id,
                hostname=rel.host.hostname,
                private_ip=rel.host.private_ip,
                public_ip=rel.host.public_ip or "",
                open_ports=rel.host.open_ports or "",
                cpu_cores=rel.host.cpu_cores,
                memory_gb=rel.host.memory_gb,
                disk_gb=rel.host.disk_gb,
                os=rel.host.os or "",
                arch=rel.host.arch or "amd64",
                kernel_version=rel.host.kernel_version or "",
                env=rel.host.env,
                status=rel.host.status,
                role=rel.role,
                notes=rel.host.notes or ""
            ))
    return {
        "id": cluster.id,
        "name": cluster.name,
        "cluster_type": cluster.cluster_type,
        "port": cluster.port or "",
        "version": cluster.version or "",
        "env": cluster.env,
        "description": cluster.description or "",
        "created_at": cluster.created_at,
        "updated_at": cluster.updated_at or cluster.created_at,
        "node_count": len(nodes),
        "nodes": nodes
    }

@router.get("", response_model=List[ClusterResponse])
def list_clusters(
    env: Optional[str] = Query(None, description="环境 prod/test"),
    cluster_type: Optional[str] = Query(None, description="集群类型"),
    db: Session = Depends(get_db)
):
    query = db.query(Cluster).options(
        selectinload(Cluster.host_relations).joinedload(HostClusterRelation.host)
    )
    if env:
        query = query.filter(Cluster.env == env)
    if cluster_type:
        query = query.filter(Cluster.cluster_type == cluster_type)

    clusters = query.order_by(Cluster.id.desc()).all()
    return [format_cluster_response(c) for c in clusters]

@router.post("", response_model=ClusterResponse)
def create_cluster(cluster_in: ClusterCreate, db: Session = Depends(get_db)):
    exist = db.query(Cluster).filter(Cluster.name == cluster_in.name).first()
    if exist:
        raise HTTPException(status_code=400, detail=f"集群名称 {cluster_in.name} 已存在")

    cluster = Cluster(
        name=cluster_in.name,
        cluster_type=cluster_in.cluster_type,
        port=cluster_in.port or "",
        version=cluster_in.version or "",
        env=cluster_in.env,
        description=cluster_in.description or ""
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    invalidate_dashboard_cache()
    return format_cluster_response(cluster)


@router.get("/{cluster_id}", response_model=ClusterResponse)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).options(
        joinedload(Cluster.host_relations).joinedload(HostClusterRelation.host)
    ).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")
    return format_cluster_response(cluster)

@router.put("/{cluster_id}", response_model=ClusterResponse)
def update_cluster(cluster_id: int, cluster_in: ClusterUpdate, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    update_data = cluster_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != cluster.name:
        exist = db.query(Cluster).filter(Cluster.name == update_data["name"]).first()
        if exist:
            raise HTTPException(status_code=400, detail=f"集群名称 {update_data['name']} 已存在")

    for field, val in update_data.items():
        setattr(cluster, field, val)

    cluster.updated_at = datetime.now()
    db.commit()
    db.refresh(cluster)
    invalidate_dashboard_cache()
    return format_cluster_response(cluster)

@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")
    db.delete(cluster)
    db.commit()
    invalidate_dashboard_cache()
    return {"message": "集群删除成功", "cluster_id": cluster_id}

@router.post("/{cluster_id}/bind-hosts", response_model=ClusterResponse)
def bind_hosts_to_cluster(cluster_id: int, req: ClusterBindRequest, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    incoming_map = {item.host_id: (item.role.strip() if item.role else "") for item in req.nodes}

    # 1. 清除当前集群中不再保留的主机关联
    current_rels = db.query(HostClusterRelation).filter(HostClusterRelation.cluster_id == cluster_id).all()
    for rel in current_rels:
        if rel.host_id not in incoming_map:
            db.delete(rel)

    # 2. 新增或更新关联及角色
    for host_id, role in incoming_map.items():
        host = db.query(Host).filter(Host.id == host_id).first()
        if not host:
            continue
        rel = db.query(HostClusterRelation).filter(
            HostClusterRelation.host_id == host_id,
            HostClusterRelation.cluster_id == cluster_id
        ).first()

        if rel:
            rel.role = role
        else:
            rel = HostClusterRelation(
                host_id=host_id,
                cluster_id=cluster_id,
                role=role
            )
            db.add(rel)

    db.commit()
    db.refresh(cluster)
    invalidate_dashboard_cache()
    return format_cluster_response(cluster)

@router.delete("/{cluster_id}/unbind-host/{host_id}")
def unbind_host_from_cluster(cluster_id: int, host_id: int, db: Session = Depends(get_db)):
    rel = db.query(HostClusterRelation).filter(
        HostClusterRelation.host_id == host_id,
        HostClusterRelation.cluster_id == cluster_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="关联关系不存在")
    db.delete(rel)
    db.commit()
    invalidate_dashboard_cache()
    return {"message": "解绑成功"}
