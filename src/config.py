"""配置管理模块

配置优先级：
1. 代码默认值
2. 环境变量
3. 请求参数
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录（src 的父目录）
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """应用配置类"""

    # 服务配置
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    DEBUG: bool = False

    # 鉴权配置
    API_KEY: str = ""  # 必填，从 .env 读取

    # 允许的域名列表（用逗号分隔，默认允许所有域名）
    # 环境变量格式：ALLOWED_HOSTS=* 或 ALLOWED_HOSTS=domain1.com,domain2.com
    # 注意：使用 str 类型接收环境变量，通过 validator 转换为 List[str]
    ALLOWED_HOSTS: str = "*"

    # curl-cffi 默认配置
    DEFAULT_IMPERSONATE: str = "chrome"  # 默认浏览器类型
    DEFAULT_TIMEOUT: int = 30  # 默认超时（秒）
    DEFAULT_PROXY: str = ""  # 默认代理标识符（如 "sg", "cn"）

    # 代理池配置（从 .env 读取 JSON 字符串）
    # 格式：{"标识符": {"url": "代理URL", "description": "描述"}}
    PROXY_POOL: Dict[str, Dict[str, str]] | None = None

    # html2text 配置
    HTML2TEXT_BODY_WIDTH: int = 0  # 0 表示不换行
    HTML2TEXT_IGNORE_LINKS: bool = False
    HTML2TEXT_IGNORE_IMAGES: bool = False

    # 缓存配置（强制启用）
    CACHE_REDIS_URL: str = ""  # Redis URL（配置后使用 Redis，否则使用内存缓存）

    # 缓存行为配置
    CACHE_TOKEN_THRESHOLD: int = 2000
    CACHE_DEFAULT_CHUNK_SIZE: int = 2000

    # 缓存清理配置
    CACHE_DELETE_DELAY_SECONDS: int = 300  # 完全读取后延迟删除（5 分钟）
    CACHE_TTL_SECONDS: int = 1800  # 未读完缓存的 TTL（30 分钟）
    CACHE_CLEANUP_INTERVAL: int = 300  # 后台清理间隔（5 分钟）

    @field_validator("PROXY_POOL", mode="before")
    @classmethod
    def parse_proxy_pool(cls, v: Any) -> Dict[str, Dict[str, str]]:
        """解析环境变量中的 JSON 字符串为 dict

        支持格式：
        1. JSON 字符串（推荐用单引号包裹）：'{"sg": {"url": "http://...", "description": "..."}}'
        2. 空字符串或 {} 表示无代理
        3. 已解析的 dict 对象
        """
        if v is None or v == "":
            return {}
        if isinstance(v, str):
            # 去除首尾空白
            v = v.strip()
            if not v or v == "{}":
                return {}
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, dict):
                    print(f"警告: PROXY_POOL 解析结果不是字典类型: {type(parsed)}")
                    return {}
                return parsed
            except json.JSONDecodeError as e:
                print(f"警告: PROXY_POOL JSON 解析失败: {e}")
                print(f"原始值: {v[:100]}...")
                return {}
        return v if isinstance(v, dict) else {}

    @field_validator("ALLOWED_HOSTS", mode="after")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> List[str]:
        """解析允许的域名列表

        支持格式：
        - "*" -> ["*"] (允许所有域名)
        - "domain1.com,domain2.com" -> ["domain1.com", "domain2.com"]
        - ["domain1.com", "domain2.com"] -> ["domain1.com", "domain2.com"]
        """
        if v is None or v == "":
            return ["*"]
        if v == "*":
            return ["*"]
        if isinstance(v, str):
            # 逗号分隔的字符串
            hosts = [host.strip() for host in v.split(",") if host.strip()]
            return hosts if hosts else ["*"]
        if isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,  # 环境变量名大小写敏感
        extra="ignore"  # 忽略额外的环境变量
    )


# 全局配置实例
settings = Settings()
