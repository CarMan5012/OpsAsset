from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ----------------- 集群与关联 Schemas -----------------

class ClusterRelationSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cluster_id: int
    cluster_name: str
    cluster_type: str
    port: Optional[str] = ""
    cluster_version: Optional[str] = ""
    version: Optional[str] = ""
    env: Optional[str] = ""
    description: Optional[str] = ""
    role: str

class ClusterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="集群名称")
    cluster_type: str = Field(..., min_length=1, max_length=50, description="集群类型 (K8s, Redis, MySQL 等)")
    port: Optional[str] = Field("", max_length=100, description="服务端口/范围 (如 3306, 6379, 6443, 30000-32767)")
    version: Optional[str] = Field("", max_length=50, description="集群/软件版本 (如 v1.28.3, 7.0.12)")
    env: str = Field("prod", description="所属环境")
    description: Optional[str] = Field("", max_length=255, description="集群描述")

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if not v:
            return "prod"
        v = str(v).strip().lower()
        if v in ["生产", "生产环境", "production"]:
            return "prod"
        if v in ["测试", "测试环境", "testing"]:
            return "test"
        return v

class ClusterCreate(ClusterBase):
    pass

class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    cluster_type: Optional[str] = None
    port: Optional[str] = None
    version: Optional[str] = None
    env: Optional[str] = None
    description: Optional[str] = None

class HostSimpleForCluster(BaseModel):
    host_id: int
    hostname: str
    private_ip: str
    public_ip: Optional[str] = ""
    open_ports: Optional[str] = ""
    cpu_cores: int = 0
    memory_gb: float = 0.0
    disk_gb: float = 0.0
    os: Optional[str] = ""
    arch: Optional[str] = "amd64"
    kernel_version: Optional[str] = ""
    env: str
    status: str
    role: str
    notes: Optional[str] = ""

class ClusterResponse(ClusterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    node_count: int = 0
    nodes: List[HostSimpleForCluster] = []

class ClusterBindItem(BaseModel):
    host_id: int
    role: str = Field("Worker", description="节点角色 (Master/Worker 等)")

class ClusterBindRequest(BaseModel):
    nodes: List[ClusterBindItem]


# ----------------- 主机 Schemas -----------------

class HostBase(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    hostname: str = Field(..., min_length=1, max_length=100, description="主机名")
    private_ip: str = Field(..., description="内网IP (唯一)")
    public_ip: Optional[str] = Field("", description="外网IP")
    cpu_cores: int = Field(0, ge=0, description="CPU核数")
    memory_gb: float = Field(0.0, ge=0.0, description="内存(GB)")
    disk_gb: float = Field(0.0, ge=0.0, description="磁盘(GB)")
    os: Optional[str] = Field("", description="操作系统")
    arch: Optional[str] = Field("amd64", description="CPU架构 (amd64 / arm64 等)")
    kernel_version: Optional[str] = Field("", description="内核版本")
    open_ports: Optional[str] = Field("", description="开放端口/端口范围 (如 22, 80, 443, 30000-32767)")
    env: str = Field("test", description="环境 (prod/test)")
    status: str = Field("online", description="状态 (online/offline/maintenance)")
    notes: Optional[str] = Field("", description="备注")

    @field_validator("arch", mode="before")
    @classmethod
    def validate_arch(cls, v: Any) -> str:
        if not v:
            return "amd64"
        s = str(v).strip().lower()
        if "amd" in s or "x86" in s or "intel" in s or "x64" in s:
            return "amd64"
        if "arm" in s or "aarch" in s:
            return "arm64"
        if "loong" in s:
            return "loongarch64"
        if "mips" in s:
            return "mips64el"
        if "sw" in s or "申威" in s:
            return "sw64"
        return s or "amd64"

    @field_validator("cpu_cores", mode="before")
    @classmethod
    def convert_cpu(cls, v: Any) -> int:
        if v is None or v == "":
            return 0
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0

    @field_validator("memory_gb", "disk_gb", mode="before")
    @classmethod
    def convert_float(cls, v: Any) -> float:
        if v is None or v == "":
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if not v:
            return "prod"
        v = str(v).strip().lower()
        if v in ["生产", "生产环境", "production"]:
            return "prod"
        if v in ["测试", "测试环境", "testing"]:
            return "test"
        if v in ["开发", "开发环境", "development"]:
            return "dev"
        if v in ["预发", "预发布", "staging", "uat"]:
            return "stage"
        if v in ["灾备", "容灾"]:
            return "dr"
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not v:
            return "online"
        v = str(v).strip().lower()
        if v in ["在线", "正常", "online", "running"]:
            return "online"
        if v in ["离线", "停止", "offline", "stopped"]:
            return "offline"
        if v in ["维护", "维护中", "maintenance", "warning"]:
            return "maintenance"
        return v

class HostCreate(HostBase):
    id: Optional[int] = None
    clusters: Optional[List[Any]] = None

class HostUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    hostname: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    os: Optional[str] = None
    arch: Optional[str] = None
    kernel_version: Optional[str] = None
    open_ports: Optional[str] = None
    env: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    cluster_ids_with_roles: Optional[List[dict]] = None

class HostResponse(HostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    clusters: List[ClusterRelationSimple] = []


# ----------------- 看板 Schemas -----------------

class EnvResourceStats(BaseModel):
    host_count: int = 0
    online_count: int = 0
    offline_count: int = 0
    maintenance_count: int = 0
    public_ip_count: int = 0
    total_cpu_cores: int = 0
    total_memory_gb: float = 0.0
    total_disk_gb: float = 0.0

class ClusterTypeCount(BaseModel):
    cluster_type: str
    count: int

class PublicIpDetail(BaseModel):
    ip: str
    hostname: str
    env: str
    is_ipv6: bool = False

class DomainSummaryItem(BaseModel):
    id: int
    domain_name: str
    public_ip: str
    resolved_ip: str
    resolve_status: str
    env: str
    hosts: List[str] = []

class DashboardOverview(BaseModel):
    total_hosts: int
    total_public_ips: int = 0
    total_cpu_cores: int
    total_memory_gb: float
    total_disk_gb: float
    total_clusters: int
    total_domains: int = 0
    matched_domains: int = 0
    mismatched_domains: int = 0
    failed_domains: int = 0
    public_ip_details: List[PublicIpDetail] = []
    domains_summary: List[DomainSummaryItem] = []
    prod: Optional[EnvResourceStats] = None
    test: Optional[EnvResourceStats] = None
    envs: dict[str, EnvResourceStats] = {}
    cluster_types: List[ClusterTypeCount]

class ClusterDistributionItem(BaseModel):
    cluster_id: int
    name: str
    cluster_type: str
    version: Optional[str] = ""
    env: str
    node_count: int
    master_count: int
    worker_count: int
    other_count: int
    public_ips: List[str] = []

# ----------------- 域名 Schemas -----------------

class DomainHostSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hostname: str
    private_ip: str
    public_ip: Optional[str] = ""
    env: str
    status: Optional[str] = "online"

class DomainBase(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    domain_name: str = Field(..., min_length=1, max_length=150, description="域名")
    public_ip: Optional[str] = Field("", description="期望绑定的公网IP (支持多IPv4/IPv6，逗号或空格隔开)")
    port: Optional[str] = Field("80, 443", description="服务端口")
    env: str = Field("prod", description="环境 (prod/test)")
    bound_host_id: Optional[int] = Field(None, description="主承载主机ID")
    bound_host_ids: Optional[List[int]] = Field(default_factory=list, description="关联的多台承载主机ID列表")
    notes: Optional[str] = Field("", description="备注")

    @field_validator("domain_name")
    @classmethod
    def clean_domain_name(cls, v: str) -> str:
        if not v:
            raise ValueError("域名不能为空")
        s = v.strip().lower()
        # 去除协议头与路径
        s = s.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        return s

class DomainCreate(DomainBase):
    pass

class DomainUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    domain_name: Optional[str] = None
    public_ip: Optional[str] = None
    port: Optional[str] = None
    env: Optional[str] = None
    bound_host_id: Optional[int] = None
    bound_host_ids: Optional[List[int]] = None
    notes: Optional[str] = None

class DomainResponse(DomainBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resolved_ip: Optional[str] = ""
    resolve_status: Optional[str] = "unknown"
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    host: Optional[DomainHostSimple] = None
    hosts: List[DomainHostSimple] = []

class DomainListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    size: int
    items: List[DomainResponse]

class DomainDnsCheckResult(BaseModel):
    id: int
    domain_name: str
    public_ip: str
    resolved_ip: str
    resolved_ips_v4: List[str] = []
    resolved_ips_v6: List[str] = []
    resolve_status: str  # matched / mismatched / failed
    is_matched: bool
    message: str

# ----------------- 导入响应 Schemas -----------------

class ImportErrorItem(BaseModel):
    row: int
    ip: str
    reason: str

class ImportResultResponse(BaseModel):
    total_rows: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    errors: List[ImportErrorItem] = []
