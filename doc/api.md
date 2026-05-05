# API 文档

## OneAPI 接口

OneAPI 提供标准的 REST API 接口，所有接口都需要通过 API Key 鉴权。

### 鉴权方式

所有接口支持两种鉴权方式：
- **Header 方式**：`Authorization: Bearer your-api-key`
- **Query 方式**：`?api_key=your-api-key`

### 1. 查询支持的浏览器指纹

获取所有 curl-cffi 支持的浏览器指纹列表（动态从库中提取）。

**请求**：
```bash
curl -X GET "http://localhost:8000/v1/impersonates" \
  -H "Authorization: Bearer your-api-key"
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": "chrome136",
      "name": "Chrome 136",
      "description": "Chrome 136 版本浏览器指纹"
    },
    {
      "id": "safari184",
      "name": "Safari 18.4",
      "description": "Safari 18.4 版本浏览器指纹"
    }
  ],
  "error": null
}
```

### 2. 查询可用代理

获取配置的代理池列表。

**请求**：
```bash
curl -X GET "http://localhost:8000/v1/proxies" \
  -H "Authorization: Bearer your-api-key"
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": "hk",
      "description": "香港代理"
    }
  ],
  "error": null
}
```

### 3. 抓取网页

使用浏览器指纹模拟抓取网页并转换为 Markdown。

**智能规则引擎**：
- 自动匹配已有规则进行精确内容提取
- 无匹配规则时，使用 AI 自动生成提取规则
- 规则自动缓存，提升后续抓取效率

**请求**：
```bash
curl -X POST "http://localhost:8000/v1/fetch" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "impersonate": "chrome136",
    "proxy": "hk",
    "timeout": 30
  }'
```

**请求参数**：
- `url` (必填): 目标网页 URL
- `impersonate` (可选): 浏览器指纹类型，默认 `chrome`
- `proxy` (可选): 代理配置，支持两种模式：
  - **代理标识符**：如 `"hk"`, `"sg"` - 从代理池中查找（需先在 `.env` 中配置 `PROXY_POOL`）
  - **完整代理 URL**：如 `"http://proxy.example.com:8080"`, `"socks5://user:pass@proxy:1080"` - 直接使用该代理
- `headers` (可选): 自定义请求头（JSON 对象）
  - **注意**：基础 headers（User-Agent、Accept 等）会由浏览器指纹自动生成，通常无需手动设置
  - 仅在需要添加特殊 headers（如 Authorization、Referer 等）时使用
- `cookies` (可选): 自定义 Cookies（JSON 对象）
  - **格式**：`{"cookie_name": "cookie_value"}`
  - **用途**：用于需要登录态或特定会话的场景
- `timeout` (可选): 超时时间（秒），默认 30

**带 Cookies 和自定义 Headers 的请求示例**：
```bash
curl -X POST "http://localhost:8000/v1/fetch" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/user/profile",
    "impersonate": "chrome136",
    "headers": {
      "Referer": "https://example.com/login",
      "X-Custom-Header": "custom-value"
    },
    "cookies": {
      "session_id": "abc123xyz",
      "user_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "timeout": 30
  }'
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "status_code": 200,
    "content_type": "text/html",
    "markdown": "# Example Domain\n\nThis domain is for use in...",
    "length": 1256
  },
  "error": null
}
```

## MCP 接口

MCP (Model Context Protocol) 提供标准的 JSON-RPC 2.0 接口，供 AI 客户端调用。

### 鉴权说明

MCP 端点与 OneAPI 端点共享相同的 API Key 鉴权机制，支持 Header 和 Query 两种方式：
- Header 方式：`Authorization: Bearer your-api-key`
- Query 方式：`?api_key=your-api-key`

### 1. 初始化连接

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

### 2. 列出可用工具

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

**可用工具**：
- `list_proxies`: 查询可用的代理列表
- `fetch_url_tool`: 使用浏览器指纹模拟抓取网页并转换为 Markdown
- `get_cached_content`: 分块读取缓存的网页内容（当内容超过 2k tokens 时使用）

### 3. 调用 list_proxies 工具

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "list_proxies",
      "arguments": {}
    }
  }'
```

### 4. 调用 fetch_url_tool 工具

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "fetch_url_tool",
      "arguments": {
        "url": "https://example.com",
        "impersonate": "chrome136",
        "proxy": "hk",
        "timeout": 30
      }
    }
  }'
```

**工具参数**：
- `url` (必填): 目标网页 URL
- `impersonate` (可选): 浏览器指纹类型，默认 `chrome`
- `proxy` (可选): 代理配置，支持两种模式：
  - **代理标识符**：如 `"hk"`, `"sg"` - 从代理池中查找（需先在 `.env` 中配置 `PROXY_POOL`）
  - **完整代理 URL**：如 `"http://proxy.example.com:8080"`, `"socks5://user:pass@proxy:1080"` - 直接使用该代理
- `headers` (可选): 自定义请求头（JSON 对象）
  - 基础 headers 由浏览器指纹自动生成，仅在需要特殊 headers 时使用
- `cookies` (可选): 自定义 Cookies（JSON 对象，格式：`{"name": "value"}`）
  - 用于需要登录态或特定会话的场景
- `timeout` (可选): 超时时间（秒），默认 30

**带 Cookies 的调用示例**：
```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "fetch_url_tool",
      "arguments": {
        "url": "https://example.com/user/profile",
        "impersonate": "chrome136",
        "cookies": {
          "session_id": "abc123xyz",
          "user_token": "token_value_here"
        },
        "timeout": 30
      }
    }
  }'
```

## 缓存机制

当网页内容超过 2000(默认) tokens 时，`fetch_url_tool` 会自动缓存内容并返回元信息，避免 token 溢出。

### 工作原理

1. **自动检测**：抓取网页后，使用 tiktoken（cl100k_base 编码器）计算 token 数
2. **智能缓存**：
   - 内容 < 2k tokens：直接返回完整 Markdown
   - 内容 ≥ 2k tokens：缓存内容，返回元信息（UUID + token 数）
3. **分块读取**：使用 `get_cached_content` 工具按 token 区间读取
4. **自动清理**：
   - 完全读取后 5 分钟自动删除（防止调取错误重试）
   - 未读完的缓存 30 分钟后过期删除（防止内存泄漏）

### 使用示例

#### 1. 抓取大型网页

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "fetch_url_tool",
      "arguments": {
        "url": "https://large-page.com"
      }
    }
  }'
```

**响应（大内容）**：
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"type\": \"cached\", \"uuid\": \"550e8400-e29b-41d4-a716-446655440000\", \"url\": \"https://large-page.com\", \"total_tokens\": 5000, \"message\": \"内容已缓存，请使用 get_cached_content 工具分块读取\"}"
      }
    ]
  }
}
```

#### 2. 分块读取缓存内容

```bash
# 读取前 2000 tokens
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "get_cached_content",
      "arguments": {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "start_token": 0,
        "end_token": 2000
      }
    }
  }'
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"uuid\": \"550e8400-...\", \"chunk\": \"# 页面标题\\n\\n实际的 Markdown 内容...\", \"start_token\": 0, \"end_token\": 2000, \"total_tokens\": 5000, \"is_fully_read\": false, \"progress\": \"40% (2000/5000 tokens)\"}"
      }
    ]
  }
}
```

```bash
# 读取剩余内容（自动使用默认 chunk_size）
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "tools/call",
    "params": {
      "name": "get_cached_content",
      "arguments": {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "start_token": 2000
      }
    }
  }'
```

### 缓存配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CACHE_REDIS_URL` | 配置 Redis URL 后使用 Redis 缓存，否则使用内存缓存 | - |
| `CACHE_TOKEN_THRESHOLD` | Token 阈值（超过此值启用缓存） | `2000` |
| `CACHE_DEFAULT_CHUNK_SIZE` | 默认分块大小（tokens） | `2000` |
| `CACHE_DELETE_DELAY_SECONDS` | 完全读取后延迟删除时间（秒） | `300` |
| `CACHE_TTL_SECONDS` | 未读完缓存的 TTL（秒） | `1800` |
| `CACHE_CLEANUP_INTERVAL` | 后台清理任务间隔（秒） | `300` |

### 缓存后端

**内存缓存（默认）**：
- 无需额外依赖
- 适合单机部署
- 服务重启后缓存丢失

**Redis 缓存（可选）**：
```env
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379/0
```
- 支持持久化
- 支持多实例部署
- 需要安装 `redis[asyncio]` 依赖

### 注意事项

1. **Token 计数**：使用 OpenAI 的 cl100k_base 编码器（GPT-4/3.5-turbo 标准）
2. **精确切分**：按 token 边界切分，不会在单词或句子中间截断
3. **自动清理**：完全读取后 5 分钟内仍可重新访问，之后自动删除
4. **内存占用**：单个缓存约 100-200KB，100 个并发缓存约 12-20MB

## 智能规则系统

服务内置智能规则引擎，自动优化网页内容提取质量。

### 工作原理

1. **规则匹配**：根据 URL 的 host + path_pattern 匹配已有规则
2. **AI 生成**：无匹配规则时，使用 AI 分析网页结构并生成提取规则
3. **规则应用**：使用规则精确提取标题、正文等核心内容
4. **自动缓存**：生成的规则自动存储，默认有效期 72 小时

### 规则格式

规则使用 JSON 格式定义内容提取逻辑：

```json
{
  "title": "h1.article-title",
  "content": "div.article-content",
  "exclude": [
    "header.navbar",
    "aside.sidebar",
    "div.ads",
    "footer"
  ]
}
```

**字段说明**：
- `title`: 标题的 CSS 选择器
- `content`: 正文内容的 CSS 选择器
- `exclude`: 需要排除的元素选择器列表（可选）

### 规则管理接口

#### 1. 查询所有规则

```bash
curl -X GET "http://localhost:8000/v1/rules" \
  -H "Authorization: Bearer your-api-key"
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "host": "blog.example.com",
      "path_pattern": "/article/*",
      "rule_content": {
        "title": "h1.title",
        "content": "div.content"
      },
      "lifetime_seconds": 259200,
      "expires_at": 1778238014.033,
      "usage_count": 5,
      "source": "curl-cffi-fetch",
      "created_at": 1777978814.033,
      "updated_at": 1777978814.033
    }
  ],
  "error": null
}
```

#### 2. 查询指定 host 的规则

```bash
# 查询 host 的所有规则
curl -X GET "http://localhost:8000/v1/rules/blog.example.com" \
  -H "Authorization: Bearer your-api-key"

# 精确匹配 host + path_pattern
curl -X GET "http://localhost:8000/v1/rules/blog.example.com?path_pattern=/article/*" \
  -H "Authorization: Bearer your-api-key"
```

#### 3. 创建规则

```bash
curl -X POST "http://localhost:8000/v1/rules" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "blog.example.com",
    "path_pattern": "/article/*",
    "rule_content": {
      "title": "h1.article-title",
      "content": "div.article-body",
      "exclude": ["aside.sidebar", "div.ads"]
    },
    "lifetime_seconds": 259200,
    "source": "manual"
  }'
```

**请求参数**：
- `host` (必填): 域名
- `path_pattern` (可选): 路径模式，支持 fnmatch 通配符，默认 `/*`
- `rule_content` (必填): 规则内容（JSON 对象）
- `lifetime_seconds` (可选): 规则寿命（秒），默认 259200（72小时）
- `source` (可选): 规则来源标识，默认 `curl-cffi-fetch`

#### 4. 更新规则

```bash
curl -X PUT "http://localhost:8000/v1/rules/blog.example.com?path_pattern=/article/*" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_content": {
      "title": "h1.new-title",
      "content": "div.new-content"
    },
    "lifetime_seconds": 86400
  }'
```

**请求参数**：
- `rule_content` (必填): 新的规则内容
- `lifetime_seconds` (可选): 新的规则寿命

#### 5. 删除规则

```bash
# 删除单个规则
curl -X DELETE "http://localhost:8000/v1/rules/blog.example.com?path_pattern=/article/*" \
  -H "Authorization: Bearer your-api-key"

# 删除 host 的所有规则
curl -X DELETE "http://localhost:8000/v1/rules/blog.example.com" \
  -H "Authorization: Bearer your-api-key"
```

### 规则匹配逻辑

1. **精确匹配**：优先匹配 host + path_pattern 完全相同的规则
2. **通配符匹配**：支持 fnmatch 风格的通配符
   - `*` 匹配任意字符
   - `?` 匹配单个字符
   - `[abc]` 匹配字符集
3. **最长匹配**：多个规则匹配时，选择 path_pattern 最长（最具体）的规则

**匹配示例**：
- URL: `https://blog.example.com/article/123`
- 规则 1: `blog.example.com` + `/*` → 匹配
- 规则 2: `blog.example.com` + `/article/*` → 匹配（优先使用，更具体）
- 规则 3: `blog.example.com` + `/news/*` → 不匹配

### AI 规则生成配置

规则自动生成需要配置 AI API（支持 OpenAI 兼容接口）：

```env
AI_API_BASE_URL=https://api.openai.com/v1
AI_API_KEY=your-openai-api-key
AI_MODEL=gpt-4o-mini
AI_MAX_TOKENS=4096
```

**配置说明**：
- `AI_API_BASE_URL`: OpenAI 兼容 API 地址
- `AI_API_KEY`: API 密钥
- `AI_MODEL`: 使用的模型（推荐 gpt-4o-mini 或 gpt-4o）
- `AI_MAX_TOKENS`: 最大输出 tokens，同时作为 HTML token 阈值

**未配置 AI 时**：
- 规则匹配正常工作
- 无匹配规则时回退到通用 HTML 转换
- 不影响基础抓取功能

