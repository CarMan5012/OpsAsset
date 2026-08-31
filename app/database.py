import os
import shutil
import logging
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("app.database")

# 1. 优先读取环境变量
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_SECRET_KEY = os.getenv("DATABASE_SECRET_KEY", "").strip()

raw_db_path = None
if not DATABASE_URL:
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_db_path = (data_dir / "asset.db").resolve()
    DATABASE_URL = f"sqlite:///{raw_db_path}"
elif DATABASE_URL.startswith("sqlite:///"):
    path_str = DATABASE_URL.replace("sqlite:///", "")
    raw_db_path = Path(path_str).resolve()
    if raw_db_path.parent and not raw_db_path.parent.exists():
        raw_db_path.parent.mkdir(parents=True, exist_ok=True)


def auto_migrate_plain_to_cipher_if_needed(db_file: Path, secret_key: str):
    """
    当配置了 DATABASE_SECRET_KEY 时，自动检测磁盘上的数据库是否为历史明文库。
    若是历史明文库，先备份为 .bak_plain，并平滑转为 256-bit AES 加密库。
    """
    if not db_file or not db_file.exists() or db_file.stat().st_size == 0 or not secret_key:
        return

    try:
        # 读取 SQLite 文件魔数头 (前 16 字节)
        with open(db_file, "rb") as f:
            header = f.read(16)
        
        # 如果以 'SQLite format 3\x00' 开头，说明是普通未加密的明文库
        if header.startswith(b"SQLite format 3"):
            logger.info("检测到历史明文 SQLite 数据库，正在自动平滑升级为 SQLCipher 密文库...")
            backup_file = db_file.with_name(f"{db_file.name}.bak_plain")
            if not backup_file.exists():
                shutil.copy2(db_file, backup_file)
                logger.info(f"已安全备份旧明文数据库至: {backup_file}")
            
            # 使用 sqlcipher 尝试将明文库转换为密文库
            try:
                import sqlcipher3
                temp_encrypted = db_file.with_name(f"{db_file.name}.tmp_enc")
                if temp_encrypted.exists():
                    temp_encrypted.unlink()
                
                # 连接明文库并通过 sqlcipher_export 导出为加密库
                conn = sqlcipher3.connect(str(db_file))
                cur = conn.cursor()
                safe_key = secret_key.replace("'", "''")
                cur.execute(f"ATTACH DATABASE '{temp_encrypted}' AS encrypted KEY '{safe_key}';")
                cur.execute("SELECT sqlcipher_export('encrypted');")
                cur.execute("DETACH DATABASE encrypted;")
                conn.close()
                
                # 替换原文件
                if temp_encrypted.exists() and temp_encrypted.stat().st_size > 0:
                    shutil.move(str(temp_encrypted), str(db_file))
                    logger.info("数据库已成功平滑升级并转换为 SQLCipher 强加密模式！")
            except Exception as e:
                logger.warning(f"自动转密执行遇到异常 (将尝试直接以加密模式挂载): {e}")
    except Exception as ex:
        logger.warning(f"检查数据库文件头异常: {ex}")


# 如果启用了密钥且是 SQLite 路径，先检测并执行平滑转换
if DATABASE_URL.startswith("sqlite") and DATABASE_SECRET_KEY and raw_db_path:
    auto_migrate_plain_to_cipher_if_needed(raw_db_path, DATABASE_SECRET_KEY)

# 2. SQLite 特殊连接参数与驱动适配
connect_args = {"check_same_thread": False, "timeout": 15} if DATABASE_URL.startswith("sqlite") else {}

engine_kwargs = {
    "connect_args": connect_args,
    "echo": False
}

if DATABASE_URL.startswith("sqlite") and DATABASE_SECRET_KEY:
    try:
        import sqlcipher3
        engine_kwargs["module"] = sqlcipher3
        logger.info("已成功加载 sqlcipher3 模块作为数据库底层加解密驱动")
    except ImportError:
        logger.warning("未检测到 sqlcipher3 模块，将使用标准 sqlite 驱动配合 PRAGMA key")

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)

# 3. 开启 SQLite 工业级高并发 WAL 模式与 SQLCipher 密钥注入
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if DATABASE_SECRET_KEY:
            safe_key = DATABASE_SECRET_KEY.replace("'", "''")
            cursor.execute(f"PRAGMA key = '{safe_key}'")
            cursor.execute("PRAGMA cipher_compatibility = 4")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app import models  # 确保所有模型注册
    Base.metadata.create_all(bind=engine)

    # 兼容已有数据库自动补充 version 与 arch 字段
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            # 检查 clusters 表
            result = conn.execute(text("PRAGMA table_info(clusters)")).fetchall()
            col_names = [r[1] for r in result]
            if col_names and "version" not in col_names:
                conn.execute(text("ALTER TABLE clusters ADD COLUMN version VARCHAR(50) DEFAULT ''"))
                conn.commit()
            if col_names and "port" not in col_names:
                conn.execute(text("ALTER TABLE clusters ADD COLUMN port VARCHAR(100) DEFAULT ''"))
                conn.commit()
            if col_names and "updated_at" not in col_names:
                conn.execute(text("ALTER TABLE clusters ADD COLUMN updated_at DATETIME"))
                conn.commit()

            # 检查 hosts 表中是否有 arch 字段与 open_ports 字段
            host_result = conn.execute(text("PRAGMA table_info(hosts)")).fetchall()
            host_col_names = [r[1] for r in host_result]
            if host_col_names and "arch" not in host_col_names:
                conn.execute(text("ALTER TABLE hosts ADD COLUMN arch VARCHAR(30) DEFAULT 'amd64'"))
                conn.commit()
            if host_col_names and "open_ports" not in host_col_names:
                conn.execute(text("ALTER TABLE hosts ADD COLUMN open_ports VARCHAR(255) DEFAULT ''"))
                conn.commit()
            
            # 将旧的 x86_64 历史数据统一更新为小写 amd64
            conn.execute(text("UPDATE hosts SET arch = 'amd64' WHERE arch = 'x86_64' OR arch = 'X86_64' OR arch IS NULL OR arch = ''"))
            conn.commit()

            # 检查 domains 表中是否有 bound_host_ids 字段
            domain_result = conn.execute(text("PRAGMA table_info(domains)")).fetchall()
            domain_col_names = [r[1] for r in domain_result]
            if domain_col_names and "bound_host_ids" not in domain_col_names:
                conn.execute(text("ALTER TABLE domains ADD COLUMN bound_host_ids VARCHAR(255) DEFAULT ''"))
                conn.commit()
    except Exception:
        pass

    # 初始化 system_configs 默认字典数据
    try:
        db = SessionLocal()
        from app.routes.config import get_config_from_db
        get_config_from_db(db)
        db.close()
    except Exception:
        pass
