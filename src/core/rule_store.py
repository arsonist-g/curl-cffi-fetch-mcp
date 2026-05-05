"""规则存储层

使用 SQLite 存储 HTML 提取规则，支持 host + path_pattern 匹配
"""

import sqlite3
import time
import fnmatch
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse
from src.config import settings, PROJECT_ROOT


class RuleStore:
    """规则存储管理器"""

    def __init__(self, db_path: str = None):
        """初始化规则存储

        参数:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        if db_path is None:
            db_path = settings.RULE_DB_PATH

        # 确保路径是绝对路径
        if not Path(db_path).is_absolute():
            db_path = str(PROJECT_ROOT / db_path)

        self.db_path = db_path

        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                path_pattern TEXT NOT NULL DEFAULT '/*',
                rule_content TEXT NOT NULL,
                compression_level TEXT NOT NULL DEFAULT 'L0',
                lifetime_seconds INTEGER NOT NULL DEFAULT 86400,
                expires_at REAL NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'curl-cffi-fetch',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(host, path_pattern)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_host ON rules(host)
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_rules_pattern
            ON rules(host, path_pattern)
        """)

        # 检查是否需要添加 compression_level 列（兼容旧数据库）
        cursor.execute("PRAGMA table_info(rules)")
        columns = [col[1] for col in cursor.fetchall()]
        if "compression_level" not in columns:
            cursor.execute("""
                ALTER TABLE rules ADD COLUMN compression_level TEXT NOT NULL DEFAULT 'L0'
            """)

        conn.commit()
        conn.close()

    @staticmethod
    def parse_pattern(pattern_str: str) -> Tuple[str, str]:
        """解析模式字符串为 host 和 path_pattern

        参数:
            pattern_str: 模式字符串，如 "news.example.com/article/*"

        返回:
            (host, path_pattern) 元组
        """
        # 如果包含 ://，先去掉协议部分
        if "://" in pattern_str:
            pattern_str = pattern_str.split("://", 1)[1]

        # 分割 host 和 path
        if "/" in pattern_str:
            host, path_pattern = pattern_str.split("/", 1)
            path_pattern = "/" + path_pattern
        else:
            host = pattern_str
            path_pattern = "/*"

        return host, path_pattern

    @staticmethod
    def url_matches(url_host: str, url_path: str, host: str, path_pattern: str) -> bool:
        """判断 URL 是否匹配规则

        参数:
            url_host: URL 的 host 部分
            url_path: URL 的 path 部分
            host: 规则的 host
            path_pattern: 规则的 path_pattern（支持 fnmatch 通配符）

        返回:
            是否匹配
        """
        if url_host != host:
            return False

        return fnmatch.fnmatch(url_path, path_pattern)

    def match(self, url: str) -> Optional[Dict]:
        """根据 URL 匹配最佳规则

        参数:
            url: 完整的 URL

        返回:
            匹配的规则字典，如果没有匹配则返回 None
        """
        # 解析 URL
        parsed = urlparse(url)
        url_host = parsed.netloc
        url_path = parsed.path or "/"

        # 查询该 host 的所有规则
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM rules WHERE host = ?
        """, (url_host,))

        candidates = cursor.fetchall()
        conn.close()

        if not candidates:
            return None

        # 过滤匹配的规则
        matched = []
        for row in candidates:
            if self.url_matches(url_host, url_path, row["host"], row["path_pattern"]):
                matched.append(dict(row))

        if not matched:
            return None

        # 选择 path_pattern 最长（最具体）的规则
        best_match = max(matched, key=lambda r: len(r["path_pattern"]))

        return best_match

    def list_all(self) -> List[Dict]:
        """列出所有规则

        返回:
            规则列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rules ORDER BY host, path_pattern")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def upsert(
        self,
        host: str,
        path_pattern: str,
        rule_content: str,
        compression_level: str = "L0",
        lifetime_seconds: int = None,
        source: str = "curl-cffi-fetch"
    ) -> Dict:
        """插入或更新规则

        参数:
            host: 域名
            path_pattern: 路径模式
            rule_content: 规则内容（JSON 字符串）
            compression_level: 压缩级别 (L0/L1/L2/L3/trafilatura)
            lifetime_seconds: 规则寿命（秒），默认使用配置值
            source: 规则来源

        返回:
            更新后的规则字典
        """
        if lifetime_seconds is None:
            lifetime_seconds = settings.RULE_DEFAULT_LIFETIME_SECONDS

        now = time.time()
        expires_at = now + lifetime_seconds

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 尝试插入或更新
        cursor.execute("""
            INSERT INTO rules (
                host, path_pattern, rule_content, compression_level, lifetime_seconds,
                expires_at, usage_count, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(host, path_pattern) DO UPDATE SET
                rule_content = excluded.rule_content,
                compression_level = excluded.compression_level,
                lifetime_seconds = excluded.lifetime_seconds,
                expires_at = excluded.expires_at,
                source = excluded.source,
                updated_at = excluded.updated_at
        """, (host, path_pattern, rule_content, compression_level, lifetime_seconds,
              expires_at, source, now, now))

        conn.commit()

        # 读取更新后的规则
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM rules WHERE host = ? AND path_pattern = ?
        """, (host, path_pattern))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def delete(self, host: str, path_pattern: str) -> bool:
        """删除规则

        参数:
            host: 域名
            path_pattern: 路径模式

        返回:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM rules WHERE host = ? AND path_pattern = ?
        """, (host, path_pattern))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def extend_lifetime(self, host: str, path_pattern: str) -> Optional[Dict]:
        """延长规则寿命

        参数:
            host: 域名
            path_pattern: 路径模式

        返回:
            更新后的规则字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 读取当前规则
        cursor.execute("""
            SELECT lifetime_seconds FROM rules
            WHERE host = ? AND path_pattern = ?
        """, (host, path_pattern))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        lifetime_seconds = row[0]
        now = time.time()
        new_expires_at = now + lifetime_seconds

        # 更新过期时间
        cursor.execute("""
            UPDATE rules
            SET expires_at = ?, updated_at = ?
            WHERE host = ? AND path_pattern = ?
        """, (new_expires_at, now, host, path_pattern))

        conn.commit()

        # 读取更新后的规则
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM rules WHERE host = ? AND path_pattern = ?
        """, (host, path_pattern))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def increment_usage(self, host: str, path_pattern: str):
        """增加规则使用计数

        参数:
            host: 域名
            path_pattern: 路径模式
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rules
            SET usage_count = usage_count + 1
            WHERE host = ? AND path_pattern = ?
        """, (host, path_pattern))

        conn.commit()
        conn.close()


# 全局规则存储实例
rule_store = RuleStore()
