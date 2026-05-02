# 部署文档

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少需要设置 `API_KEY`：

```env
API_KEY=your-secret-api-key-here
```

### 3. 运行服务

```bash
# 开发模式
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python src/main.py
```

### 4. 访问文档

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 服务信息：http://localhost:8000/

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SERVICE_HOST` | 服务监听地址 | `0.0.0.0` |
| `SERVICE_PORT` | 服务监听端口 | `8000` |
| `DEBUG` | 调试模式 | `false` |
| `API_KEY` | API 鉴权密钥（必填） | - |
| `ALLOWED_HOSTS` | 允许的域名列表（逗号分隔，用于反向代理）| `*` |
| `DEFAULT_IMPERSONATE` | 默认浏览器类型 | `chrome` |
| `DEFAULT_TIMEOUT` | 默认超时时间（秒） | `30` |
| `DEFAULT_PROXY` | 默认代理配置（支持标识符或完整 URL） | - |
| `PROXY_POOL_FILE` | 代理池配置文件路径（相对于项目根目录） | - |
| `PROXY_POOL` | 代理池配置（JSON） | `{}` |
| `HTML2TEXT_BODY_WIDTH` | Markdown 文本宽度 | `0` |
| `HTML2TEXT_IGNORE_LINKS` | 忽略链接 | `false` |
| `HTML2TEXT_IGNORE_IMAGES` | 忽略图片 | `false` |
| `CACHE_REDIS_URL` | 配置 Redis URL 后使用 Redis 缓存，否则使用内存缓存 | - |
| `CACHE_TOKEN_THRESHOLD` | Token 阈值 | `2000` |
| `CACHE_DEFAULT_CHUNK_SIZE` | 默认分块大小（tokens） | `2000` |
| `CACHE_DELETE_DELAY_SECONDS` | 完全读取后延迟删除（秒） | `300` |
| `CACHE_TTL_SECONDS` | 未读完缓存的 TTL（秒） | `1800` |
| `CACHE_CLEANUP_INTERVAL` | 后台清理间隔（秒） | `300` |

### 反向代理配置

当服务部署在反向代理（Nginx、Caddy、Apache）后面时，需要配置 `ALLOWED_HOSTS` 环境变量以允许特定域名访问。

**配置示例**：

```env
# 允许所有域名（默认，适用于开发环境）
ALLOWED_HOSTS=*

# 允许单个域名
ALLOWED_HOSTS=web-fetch.test.com

# 允许多个域名（逗号分隔）
ALLOWED_HOSTS=web-fetch.test.com,api.example.com,localhost
```

**注意事项**：
- 生产环境建议明确指定允许的域名，而不是使用 `*`

### 代理池配置

服务支持两种代理配置方式和两种代理使用方式：

#### 配置方式

**方式 1: 使用 JSON 文件（推荐，支持多行，方便编辑维护）**

1. 复制示例文件：
```bash
cp proxies.json.example proxies.json
```

2. 编辑 `proxies.json`，添加你的代理配置：
```json
{
  "hk": {
    "url": "http://127.0.0.1:17890",
    "description": "香港代理"
  },
  "sg": {
    "url": "http://user:pass@sg-proxy.example.com:8080",
    "description": "新加坡代理"
  },
  "us": {
    "url": "socks5://us-proxy.example.com:1080",
    "description": "美国代理"
  }
}
```

3. 在 `.env` 中配置文件路径：
```env
PROXY_POOL_FILE=proxies.json
```

**方式 2: 使用环境变量（单行 JSON，适合少量代理）**

在 `.env` 中直接配置（注意：整个 JSON 需要用单引号包裹）：

**基本代理配置**：
```env
PROXY_POOL='{"hk": {"url": "http://127.0.0.1:17890", "description": "香港代理"}}'
```

**带鉴权的代理配置**：
```env
# HTTP 代理带用户名密码
PROXY_POOL='{"auth_proxy": {"url": "http://username:password@proxy.example.com:8080", "description": "带鉴权的 HTTP 代理"}}'

# SOCKS5 代理带用户名密码
PROXY_POOL='{"socks_proxy": {"url": "socks5://username:password@proxy.example.com:1080", "description": "带鉴权的 SOCKS5 代理"}}'
```

**多代理配置**：
```env
PROXY_POOL='{"hk": {"url": "http://hk-proxy:8080", "description": "香港代理"}, "sg": {"url": "http://user:pass@sg-proxy:8080", "description": "新加坡代理"}, "us": {"url": "socks5://us-proxy:1080", "description": "美国代理"}}'
```

**配置优先级**：`PROXY_POOL_FILE` > `PROXY_POOL`

**注意事项**：
- `proxies.json` 文件已添加到 `.gitignore`，不会被提交到 Git
- Docker 部署时，如果使用 `PROXY_POOL_FILE`，需要将文件挂载到容器中
- 推荐使用 JSON 文件方式，特别是代理数量较多时

#### 使用方式

**方式 1: 代理池映射（推荐用于常用代理）**

在配置文件或环境变量中配置代理池，请求时使用标识符（如 `"hk"`, `"sg"`）。

**方式 2: 直接传入代理 URL（适用于临时或动态代理）**

无需在配置中预先定义，直接在请求中传入完整的代理 URL。

**支持的代理协议**：
- HTTP: `http://proxy.example.com:8080`
- HTTPS: `https://proxy.example.com:8080`
- SOCKS5: `socks5://proxy.example.com:1080`
- 带鉴权: `http://user:pass@proxy.example.com:8080`

**代理模式自动识别**：
- 如果 `proxy` 参数以 `http://`, `https://`, `socks5://` 开头，则直接使用该 URL
- 否则，从代理池中查找对应的标识符

### 浏览器指纹配置

curl-cffi 支持 37+ 种浏览器指纹，包括：

**推荐使用**（最新版本）：
- `chrome136` - Chrome 136（推荐）
- `safari184` - Safari 18.4（推荐）
- `safari184_ios` - Safari 18.4 iOS（推荐）
- `firefox135` - Firefox 135

**通用别名**（自动使用最新版本）：
- `chrome` - 自动使用最新 Chrome
- `safari` - 自动使用最新 Safari
- `safari_ios` - 自动使用最新 Safari iOS
- `firefox` - 自动使用最新 Firefox

**完整列表**：
通过 `GET /v1/impersonates` 接口查询所有支持的浏览器指纹。

## Docker 部署

### 使用 Docker Compose（推荐）

最简单的部署方式，自动配置 Redis 缓存。

#### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，至少设置 API_KEY
```

#### 2. 启动服务

```bash
# 启动所有服务（应用 + Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

#### 3. 访问服务

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 使用 Docker（仅应用）

如果只需要运行应用容器，不使用 Redis 缓存。

#### 1. 构建镜像

```bash
docker build -t curl-cffi-fetch-mcp .
```

#### 2. 运行容器

```bash
docker run -d \
  --name curl-cffi-fetch-mcp \
  -p 8000:8000 \
  -e API_KEY=your-secret-api-key \
  -e DEBUG=false \
  curl-cffi-fetch-mcp
```

#### 3. 使用环境变量文件

```bash
docker run -d \
  --name curl-cffi-fetch-mcp \
  -p 8000:8000 \
  --env-file .env \
  curl-cffi-fetch-mcp
```

### Docker 配置说明

#### 端口映射

默认映射 `8000:8000`，可通过环境变量修改：

```bash
# .env 中配置
SERVICE_PORT=8000           # 容器内服务监听端口
DOCKER_HOST_PORT=9000       # 宿主机映射端口

# docker-compose.yml 会自动使用这些配置
# 映射关系：宿主机 9000 -> 容器 8000
```

#### Redis 缓存

Docker Compose 默认启用 Redis 缓存：
- Redis 数据持久化到 Docker 卷 `redis-data`
- 容器间通过 `app-network` 网络通信
- 应用自动连接到 `redis://redis:6379/0`

如不需要 Redis，可以：

```bash
# 仅启动应用服务
docker-compose up -d app

# 或修改 docker-compose.yml，移除 depends_on 和 CACHE_REDIS_URL
```

#### 健康检查

容器内置健康检查，每 30 秒检查一次 `/health` 端点：

```bash
# 查看容器健康状态
docker ps
docker inspect curl-cffi-fetch-mcp | grep -A 10 Health
```

### 生产环境建议

1. **使用 Redis 缓存**：支持多实例部署和持久化
2. **配置资源限制**：

```yaml
# docker-compose.yml 中添加
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

3. **使用反向代理**：通过 Nginx/Traefik 提供 HTTPS
4. **日志管理**：配置日志驱动和轮转

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 传统部署

### 使用 uvicorn

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 使用 gunicorn + uvicorn worker

```bash
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 安全考虑

- API Key 必须通过 HTTPS 传输（生产环境）
- 支持 Header 和 Query 两种鉴权方式
- URL 格式验证，防止 SSRF 攻击
- 限制可访问的协议（仅 http/https）
