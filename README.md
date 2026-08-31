# OpsAsset - 现代云原生运维资产与集群管理系统

<p align="center">
  <img src="frontend/public/favicon.svg" width="96" height="96" alt="OpsAsset Logo" />
</p>

<p align="center">
  专为 DevOps 与 SRE 运维团队量身打造的<b>轻量、高颜值、零维护负担、企业级安全</b>的 IT 基础设施与集群拓扑管理平台。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue.js-3.4+-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue3" />
  <img src="https://img.shields.io/badge/Element_Plus-2.6+-409EFF?style=flat-square&logo=elementplus&logoColor=white" alt="Element Plus" />
  <img src="https://img.shields.io/badge/SQLCipher-AES--256-0284C7?style=flat-square&logo=sqlite&logoColor=white" alt="SQLCipher" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 🌟 核心特性

### 1. 🖥️ 基础设施与硬件资产全景管理
- **完整硬件规格**：主机名、内网 IP（唯一标识）、外网 IP、CPU 核数、内存与数据盘容量（自动智能 TB / GB 换算）、CPU 架构（amd64 / arm64）、操作系统、精简内核版本（自动提取 `x.xx.x`）。
- **多公网 IP 智能跨行合并**：多台主机共享出口 IP 时表格与 Excel 导出自动跨行合并展示。
- **端口汇总与一键复制**：聚合主机自身开放端口与关联服务端口，支持一键快捷复制。
- **高密度科技控制台排版**：采用大厂云控制台紧凑数据表格规范，无数据单元格纯空白呈现，告别冗余占位符。

### 2. 🧩 服务与集群拓扑管理
- **多组件全支持**：原生支持 Kubernetes、Redis、MySQL、Nacos、RabbitMQ/RocketMQ、MongoDB、Kafka、Elasticsearch、ClickHouse 等服务集群。
- **双向角色关联**：灵活定义节点角色（Master / Worker / Broker / Follower 等），支持在主机列表直接过滤并展示集群服务徽章（如 `Redis v7.0.12`）。

### 3. 🌐 域名资产与解析追踪
- 集中管理业务域名、公网/内网解析 IP、关联绑定主机、SSL/TLS 证书到期预警与解析健康状态。

### 4. 🎨 专业级高颜值 Excel / CSV 导入导出
- **科技石板深蓝表头**：导出文件内置 `#1E293B` 深邃表头、底边青蓝强调线、首行窗格冻结与全列自动筛选器。
- **拟态彩色胶囊徽章**：状态（在线/维护/下线）与环境（生产/测试/开发）在 Excel 中自动渲染为对应彩色胶囊样式。
- **动态列与范围自定义**：支持按环境范围（全部/生产/测试等）、勾选主机导出，支持自由选择导出列。
- **100% 所见即所得预览**：弹窗与导入导出中心提供与生成文件完全一致的实时表格预览。
- **标准智能导入模板**：下载模板内置 DataValidation 字典下拉选择，支持内网 IP 冲突自动覆盖更新 (Upsert)。

### 5. 🔒 SQLCipher 256-bit AES 数据库全库透明加密
- **整库底层加密**：通过环境变量 `DATABASE_SECRET_KEY` 一键开启 256 位 AES 强加密，即使 `.db` 文件被直接拷贝或下载也无法打开。
- **业务代码零侵入**：模糊搜索（LIKE 检索）、多字段排序、分页与聚合操作 100% 原生支持。
- **存量数据无损自动升级**：首次配置密钥启动时，系统自动安全备份并平滑升级历史明文库为加密密文库。

### 6. ⚙️ 动态字典配置中心
- 支持在控制台灵活自定义环境类型（prod/test/dev/stage）、主机状态、CPU 架构、集群类型与常用操作系统字典。

---

## 🚀 快速开始

### 方式 1：Docker Compose 一键启动 (强烈推荐)

系统内置**多阶段构建 Dockerfile**，自动完成前端 Vite 编译、Nginx 高性能静态分发与 FastAPI 后端守护，单容器即可完整运行。

```bash
# 1. 启动容器 (自动构建与启动)
docker-compose up -d --build

# 2. 访问控制台
# 浏览器打开 http://<服务器IP>:8000
```

#### `docker-compose.yml` 配置示例：
```yaml
services:
  ops-asset:
    build:
      context: .
      dockerfile: Dockerfile
    image: ops-asset:latest
    container_name: ops-asset-app
    restart: always
    ports:
      - "8000:8000"
    volumes:
      # 持久化挂载 SQLite / SQLCipher 数据库目录
      - ./data:/data
    environment:
      - DATABASE_URL=sqlite:////data/asset.db
      # 数据库全库透明加密密钥 (留空表示不加密；生产环境请设置为自己的强随机密钥)
      - DATABASE_SECRET_KEY=your_secure_db_secret_key_here
      - TZ=Asia/Shanghai
```

---

### 方式 2：本地 Python + 前端开发模式

```bash
# 1. 后端安装依赖并启动
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 前端启动开发服务 (可选，进行前端热更新调试)
cd frontend
npm install
npm run dev
```

---

## 📖 导入导出与数据规则说明

| 字段名称 | 规则与格式说明 | 示例 |
| :--- | :--- | :--- |
| **内网 IP** | 资产唯一主键（必填），重复时将自动执行覆盖更新 (Upsert) | `192.168.1.100` |
| **外网 IP** | 选填，支持多 IP（英文逗号/空格分隔），同 IP 主机将自动跨行合并 | `114.114.114.114` |
| **环境** | 支持代码或中文名称（系统字典自动映射） | `prod` 或 `生产环境` |
| **状态** | 支持 `online`（在线）、`offline`（下线）、`maintenance`（维护） | `在线` |
| **所属服务** | 格式为 `集群名:角色`，多个用逗号隔开，导入时将自动创建并关联 | `k8s-prod:Master, redis-order:Worker` |
| **内核版本** | 支持完整版本号输入，系统自动提取前缀 `x.xx.x` 核心主版本号 | `5.15.0-89-generic` ➔ `5.15.0` |

---

## 🔐 数据库安全与密钥管理

- **生成高强度 256 位加密密钥**：
  ```bash
  # Linux / macOS (OpenSSL)
  openssl rand -hex 32

  # Windows (PowerShell)
  powershell -Command "[System.Guid]::NewGuid().ToString('N') + [System.Guid]::NewGuid().ToString('N')"

  # Python (跨平台)
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- **密钥安全与备份**：配置在 `docker-compose.yml` 的 `DATABASE_SECRET_KEY` 中，请妥善保管好主密钥，后续每次启动保持密钥一致即可无感解密。

---

## 🛠️ API 接口在线文档

系统启动后，直接访问交互式 Swagger UI 文档：
- **Swagger API 文档**：`http://<IP>:8000/docs`
- **ReDoc 接口规范**：`http://<IP>:8000/redoc`

