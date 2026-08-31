from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hostname = Column(String(100), nullable=False)
    private_ip = Column(String(45), nullable=False, unique=True, index=True)
    public_ip = Column(String(45), default="", nullable=True)
    cpu_cores = Column(Integer, nullable=False, default=0)
    memory_gb = Column(Float, nullable=False, default=0.0)
    disk_gb = Column(Float, nullable=False, default=0.0)
    os = Column(String(100), default="", nullable=True)
    arch = Column(String(30), default="amd64", nullable=False, index=True)  # amd64 / arm64 / loongarch64 / etc.
    kernel_version = Column(String(100), default="", nullable=True)
    open_ports = Column(String(255), default="", nullable=True)  # 开放端口/范围，如 22, 80, 443, 30000-32767
    env = Column(String(20), nullable=False, default="test", index=True)  # prod / test
    status = Column(String(20), nullable=False, default="online", index=True)  # online / offline / maintenance
    notes = Column(Text, default="", nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)

    # 关联集群
    cluster_relations = relationship(
        "HostClusterRelation",
        back_populates="host",
        cascade="all, delete-orphan"
    )

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    cluster_type = Column(String(50), nullable=False)  # K8s, Redis, MySQL, Nacos, MQ, MongoDB, Custom
    port = Column(String(100), default="", nullable=True)  # 服务端口/端口范围，如 3306, 6379, 6443, 30000-32767
    version = Column(String(50), default="", nullable=True)  # 集群/软件版本，如 v1.28.3, 7.0.12, 8.0.32
    env = Column(String(20), nullable=False, default="test", index=True)  # prod / test
    description = Column(String(255), default="", nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)

    # 关联主机
    host_relations = relationship(
        "HostClusterRelation",
        back_populates="cluster",
        cascade="all, delete-orphan"
    )

class HostClusterRelation(Base):
    __tablename__ = "host_cluster_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="")  # 如: 主节点 (Master), 工作节点 (Worker) 等，无角色时为空
    notes = Column(String(255), default="", nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    host = relationship("Host", back_populates="cluster_relations")
    cluster = relationship("Cluster", back_populates="host_relations")
    __table_args__ = (
        UniqueConstraint("host_id", "cluster_id", name="uq_host_cluster"),
    )

class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), nullable=False, unique=True, index=True)  # 如: meta_config
    config_value = Column(Text, nullable=False)  # JSON 序列化配置内容
    description = Column(String(255), default="", nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain_name = Column(String(150), nullable=False, unique=True, index=True)  # 如: api.example.com
    public_ip = Column(String(255), default="", nullable=True)                  # 期望绑定的公网IP (支持多IPv4/IPv6)
    resolved_ip = Column(String(255), default="", nullable=True)                # 实际DNS解析出的IP (支持多IPv4/IPv6)
    resolve_status = Column(String(20), default="unknown", nullable=True)       # matched(一致) / mismatched(不一致) / failed(解析失败) / unknown(未检测)
    port = Column(String(100), default="80, 443", nullable=True)               # 映射/服务端口
    env = Column(String(20), nullable=False, default="prod", index=True)        # prod / test
    bound_host_id = Column(Integer, ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True, index=True)  # 主承载主机(兼容单选)
    bound_host_ids = Column(String(255), default="", nullable=True)             # 关联多台承载主机ID列表 (逗号分隔，如 "1,2")
    notes = Column(Text, default="", nullable=True)
    last_checked_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)

    # 关联主机
    host = relationship("Host", foreign_keys=[bound_host_id])

