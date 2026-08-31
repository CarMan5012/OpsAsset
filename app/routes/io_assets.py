import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models import Host, Cluster, HostClusterRelation
from app.schemas import ImportResultResponse
from app.services.excel_service import (
    generate_excel_template,
    parse_and_import,
    export_hosts_data
)

router = APIRouter(prefix="/api/assets", tags=["资产导入导出"])
io_alias_router = APIRouter(prefix="/api/io", tags=["资产导入导出别名"])

def handle_download_template():
    """下载标准主机资产导入模板 (Excel .xlsx)"""
    file_stream = generate_excel_template()
    filename = "主机资产导入模板.xlsx"
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/template")
def download_template():
    return handle_download_template()

@io_alias_router.get("/template")
def io_download_template():
    return handle_download_template()

async def handle_import_assets(
    file: UploadFile,
    overwrite: bool,
    db: Session
):
    """上传 Excel 或 CSV 文件批量导入资产"""
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx, .xls 或 .csv 格式的文件")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="上传的文件内容为空")

    try:
        result = parse_and_import(
            file_bytes=contents,
            filename=file.filename,
            db=db,
            overwrite=overwrite
        )
        from app.routes.dashboard import invalidate_dashboard_cache
        invalidate_dashboard_cache()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入解析失败: {str(e)}")

@router.post("/import", response_model=ImportResultResponse)
async def import_assets(
    file: UploadFile = File(...),
    overwrite: bool = Query(True, description="遇到已存在的内网IP时是否覆盖更新"),
    db: Session = Depends(get_db)
):
    return await handle_import_assets(file, overwrite, db)

@io_alias_router.post("/import", response_model=ImportResultResponse)
async def io_import_assets(
    file: UploadFile = File(...),
    overwrite: bool = Query(True, description="遇到已存在的内网IP时是否覆盖更新"),
    db: Session = Depends(get_db)
):
    return await handle_import_assets(file, overwrite, db)

def handle_export_assets(
    format: str,
    env: Optional[str],
    status: Optional[str],
    arch: Optional[str],
    cluster_id: Optional[int],
    keyword: Optional[str],
    columns: Optional[str],
    ids: Optional[str],
    sort_by: Optional[str],
    sort_order: Optional[str],
    order: Optional[str],
    db: Session
):
    """导出主机资产清单为 Excel 或 CSV 文件 (支持精准多维过滤、自定义列选择与多维动态排序)"""
    from sqlalchemy.orm import selectinload
    from sqlalchemy import func
    from app.routes.config import get_config_from_db

    query = db.query(Host).options(
        selectinload(Host.cluster_relations).joinedload(HostClusterRelation.cluster)
    )

    # 1. 指定 ID 优先过滤 (用于在表格中勾选导出选中的主机)
    if ids and ids.strip():
        try:
            id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
            if id_list:
                query = query.filter(Host.id.in_(id_list))
        except ValueError:
            pass
    else:
        if env:
            query = query.filter(Host.env == env)
        if status:
            query = query.filter(Host.status == status)
        if arch:
            query = query.filter(Host.arch == arch)
        if cluster_id:
            query = query.filter(Host.cluster_relations.any(HostClusterRelation.cluster_id == cluster_id))
        
        raw_kw = keyword.strip() if keyword else ""
        if raw_kw:
            query = query.filter(
                or_(
                    Host.hostname.ilike(f"%{raw_kw}%"),
                    Host.private_ip.ilike(f"%{raw_kw}%"),
                    Host.public_ip.ilike(f"%{raw_kw}%"),
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

    # 2. 动态排序 (默认 id desc，保证与主机资产列表完全一致的最新数据展示顺序)
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

    sort_col = sort_column_map.get(sort_by or "id")
    if sort_col is not None:
        if is_asc:
            query = query.order_by(sort_col.asc(), Host.id.asc())
        else:
            query = query.order_by(sort_col.desc(), Host.id.desc())
    else:
        query = query.order_by(Host.id.desc())

    hosts = query.all()

    # 解析选定列
    selected_cols = None
    if columns and columns.strip():
        selected_cols = [c.strip() for c in columns.split(",") if c.strip()]

    # 获取系统元数据字典
    meta_config = get_config_from_db(db)

    file_stream, content_type, extension = export_hosts_data(
        hosts,
        file_format=format,
        selected_columns=selected_cols,
        meta_config=meta_config
    )
    filename = f"服务器资产清单_{env or 'all'}.{extension}"
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        file_stream,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/export")
def export_assets(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$", description="导出格式: xlsx 或 csv"),
    env: Optional[str] = Query(None, description="按环境过滤 prod/test"),
    status: Optional[str] = Query(None, description="按状态过滤 online/offline/maintenance"),
    arch: Optional[str] = Query(None, description="按架构过滤 amd64/arm64 等"),
    cluster_id: Optional[int] = Query(None, description="按所属集群ID过滤"),
    keyword: Optional[str] = Query(None, description="精准搜索关键词(主机名/IP/集群名)"),
    columns: Optional[str] = Query(None, description="自定义导出列(逗号分隔，如: hostname,private_ip,env,status)"),
    ids: Optional[str] = Query(None, description="按指定主机ID列表导出(逗号分隔)"),
    sort_by: Optional[str] = Query("id", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
    order: Optional[str] = Query(None, description="排序方向兼容参数"),
    db: Session = Depends(get_db)
):
    return handle_export_assets(format, env, status, arch, cluster_id, keyword, columns, ids, sort_by, sort_order, order, db)

@io_alias_router.get("/export")
def io_export_assets(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$", description="导出格式: xlsx 或 csv"),
    env: Optional[str] = Query(None, description="按环境过滤 prod/test"),
    status: Optional[str] = Query(None, description="按状态过滤 online/offline/maintenance"),
    arch: Optional[str] = Query(None, description="按架构过滤 amd64/arm64 等"),
    cluster_id: Optional[int] = Query(None, description="按所属集群ID过滤"),
    keyword: Optional[str] = Query(None, description="精准搜索关键词(主机名/IP/集群名)"),
    columns: Optional[str] = Query(None, description="自定义导出列(逗号分隔，如: hostname,private_ip,env,status)"),
    ids: Optional[str] = Query(None, description="按指定主机ID列表导出(逗号分隔)"),
    sort_by: Optional[str] = Query("id", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
    order: Optional[str] = Query(None, description="排序方向兼容参数"),
    db: Session = Depends(get_db)
):
    return handle_export_assets(format, env, status, arch, cluster_id, keyword, columns, ids, sort_by, sort_order, order, db)
