# curl-cffi Fetch MCP

一个基于 curl-cffi 的网页抓取服务，同时提供 MCP (Model Context Protocol) 和 OneAPI 兼容的 REST API 接口。

## 核心特性

- **双协议支持**：MCP Streamable HTTP + OneAPI REST API
- **浏览器指纹模拟**：使用 curl-cffi 的 `impersonate` 特性绕过反爬虫检测
- **HTML 转 Markdown**：自动将网页内容转换为 Markdown 格式
- **智能缓存机制**：Token 感知的分块读取，避免大内容导致 token 溢出
- **灵活配置**：三层配置优先级（代码默认 < .env < 请求参数）
- **代理池管理**：支持为不同网站配置专用代理
- **统一鉴权**：两个端点共享鉴权逻辑

## 文档导航

- **[部署文档](doc/deployment.md)** - 安装、配置、Docker 部署、生产环境部署
- **[API 文档](doc/api.md)** - OneAPI 接口、MCP 接口、缓存机制

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，至少设置 API_KEY
```

### 3. 运行服务

```bash
# 开发模式
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python src/main.py
```

### 4. 访问服务

- API 文档：http://localhost:8000/docs
- 服务信息：http://localhost:8000/

详细的部署说明请参考 [部署文档](doc/deployment.md)。

## API 使用示例

### OneAPI 接口

```bash
# 抓取网页
curl -X POST "http://localhost:8000/v1/fetch" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "impersonate": "chrome136",
    "proxy": "hk"
  }'
```

### MCP 接口

```bash
# 调用 fetch_url_tool 工具
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "fetch_url_tool",
      "arguments": {
        "url": "https://example.com",
        "impersonate": "chrome136"
      }
    }
  }'
```

完整的 API 文档请参考 [API 文档](doc/api.md)。

## 项目结构

```
curl-cffi-fetch-mcp/
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置管理
│   ├── auth.py                  # 鉴权中间件
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fetcher.py           # 核心抓取逻辑
│   │   ├── converter.py         # HTML → Markdown 转换
│   │   ├── cache.py             # Token 感知的智能缓存管理
│   │   └── headers_generator.py # 浏览器指纹信息（动态获取）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── mcp_endpoint.py      # MCP 端点
│   │   └── oneapi_endpoint.py   # OneAPI 端点
│   └── models/
│       ├── __init__.py
│       ├── request.py           # 请求数据模型
│       └── response.py          # 响应数据模型
├── doc/
│   ├── deployment.md            # 部署文档
│   └── api.md                   # API 文档
├── .env                         # 环境配置
├── .env.example                 # 配置示例
├── proxies.json                 # 代理配置文件（不提交到 Git）
├── proxies.json.example         # 代理配置示例
├── requirements.txt             # Python 依赖
└── README.md                    # 项目文档
```

## 技术栈

- **FastAPI 0.135.1**：高性能异步 Web 框架
- **curl-cffi 0.14.0**：支持浏览器指纹模拟的 HTTP 客户端（37+ 种浏览器指纹）
- **html2text 2025.4.15**：HTML 到 Markdown 转换
- **pydantic 2.12.5**：数据验证和序列化
- **pydantic-settings 2.13.1**：类型安全的配置管理
- **mcp 1.26.0**：MCP 协议 Python SDK
- **uvicorn 0.42.0**：ASGI 服务器
- **tiktoken 0.8.0**：Token 计数（OpenAI cl100k_base 编码器）
- **redis[asyncio] 5.0.0**：Redis 异步客户端（可选，用于分布式缓存）

## 许可证

MIT License
