import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routes.hosts import router as hosts_router
from app.routes.clusters import router as clusters_router
from app.routes.dashboard import router as dashboard_router
from app.routes.io_assets import router as io_assets_router, io_alias_router
from app.routes.config import router as config_router
from app.routes.domains import router as domains_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时自动建表与初始化
    init_db()
    yield

app = FastAPI(
    title="OpsAsset 极简运维资产与集群管理系统",
    description="轻量级服务器硬件资产盘点、集群分布管理与批量导入导出系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(config_router)
app.include_router(dashboard_router)
app.include_router(hosts_router)
app.include_router(clusters_router)
app.include_router(domains_router)
app.include_router(io_assets_router)
app.include_router(io_alias_router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "OpsAsset 服务正常运行"}

# 静态资源挂载与前端单页路由支持 (官方原生 StaticFiles，绝对稳定、零死锁、毫秒级响应)
static_dir = Path(__file__).resolve().parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)

assets_dir = static_dir / "assets"
if not assets_dir.exists():
    assets_dir.mkdir(parents=True, exist_ok=True)

app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "OpsAsset API 服务已就绪，请在 static 目录下放置 index.html 或访问 /docs 查看接口文档"}
