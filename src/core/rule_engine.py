"""规则引擎 - 重构版本

编排规则查询、HTML 压缩、AI 生成、规则应用的全流程
"""

import json
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from trafilatura import extract
from markdownify import markdownify as md
from src.config import settings
from src.core.rule_store import rule_store
from src.core.ai_client import call_ai_for_rule
from src.core.prompts import RULE_GENERATION_PROMPT
from src.core.html_compressor import compress_html_adaptive, apply_compression, count_tokens


def is_expired(rule: Dict) -> bool:
    """判断规则是否过期

    参数:
        rule: 规则字典

    返回:
        是否过期
    """
    return time.time() >= rule["expires_at"]


def apply_rule(html: str, rule: Dict) -> str:
    """使用规则提取内容并转换为 Markdown

    参数:
        html: 原始 HTML 内容（不压缩）
        rule: 规则字典，包含 rule_content 字段

    返回:
        Markdown 格式的内容

    注意:
        应用规则时直接在原始 HTML 上提取，不进行压缩。
        compression_level 字段仅用于记录生成规则时使用的压缩级别，
        不影响应用规则时的行为。
    """
    compression_level = rule.get("compression_level", "L0")

    # 特殊情况：如果规则标记为 trafilatura，直接使用 trafilatura
    if compression_level == "trafilatura":
        markdown = extract(
            html,
            output_format="markdown",
            include_comments=False,
            include_tables=True
        )
        if markdown:
            return markdown
        # trafilatura 失败，继续尝试使用规则

    # 解析规则
    try:
        rule_content = json.loads(rule["rule_content"])
    except json.JSONDecodeError:
        # 规则格式错误，使用 trafilatura 兜底
        markdown = extract(html, output_format="markdown", include_comments=False, include_tables=True)
        return markdown if markdown else html

    # 解析 HTML（使用原始 HTML，不压缩）
    soup = BeautifulSoup(html, "lxml")

    # 提取标题
    title = ""
    title_selector = rule_content.get("title")
    if title_selector:
        title_elem = soup.select_one(title_selector)
        if title_elem:
            title = title_elem.get_text(strip=True)

    # 提取正文内容
    content_html = ""
    content_selector = rule_content.get("content")
    if content_selector:
        content_elem = soup.select_one(content_selector)
        if content_elem:
            # 移除排除的元素
            exclude_selectors = rule_content.get("exclude", [])
            for exclude_selector in exclude_selectors:
                for elem in content_elem.select(exclude_selector):
                    elem.decompose()

            content_html = str(content_elem)

    # 如果提取失败，使用 trafilatura 兜底
    if not content_html:
        markdown = extract(html, output_format="markdown", include_comments=False, include_tables=True)
        return markdown if markdown else html

    # 转换为 Markdown（使用 markdownify，忠实转换，不丢弃内容）
    markdown_content = md(content_html, heading_style="ATX", code_language="")

    if not markdown_content:
        # markdownify 失败，直接返回 HTML
        markdown_content = content_html

    # 组合标题和内容
    if title:
        result = f"# {title}\n\n{markdown_content}"
    else:
        result = markdown_content

    return result


async def generate_rule(html: str, url: str) -> tuple[Dict, str]:
    """调用 AI 生成新规则

    流程：
    1. 自适应压缩 HTML
    2. 如果压缩后仍超过上限，使用 trafilatura HTML 格式
    3. 调用 AI 生成规则

    参数:
        html: HTML 内容
        url: 目标 URL

    返回:
        (规则字典, 压缩级别)
    """
    # 自适应压缩
    compressed_html, compression_level = compress_html_adaptive(
        html,
        token_limit=settings.AI_MAX_TOKENS
    )

    # 如果仍超过上限，使用 trafilatura
    if compression_level == "L3_exceeded":
        trafilatura_html = extract(
            html,
            output_format="html",
            include_comments=False,
            include_tables=True
        )

        if trafilatura_html and count_tokens(trafilatura_html) < settings.AI_MAX_TOKENS:
            compressed_html = trafilatura_html
            compression_level = "trafilatura"
        else:
            # trafilatura 也无法压缩到上限以下，使用 L3 结果
            compression_level = "L3"

    # 调用 AI 生成规则
    rule_json = await call_ai_for_rule(
        RULE_GENERATION_PROMPT,
        compressed_html,
        url=url
    )

    return {"rule_content": rule_json}, compression_level


async def convert(html: str, url: str) -> str:
    """主入口：根据 URL 匹配规则并转换 HTML

    流程：
    1. 匹配规则
    2. 有规则且未过期 → 应用规则
    3. 有规则但已过期 → 延长寿命并应用
    4. 无规则 → 生成规则并应用

    参数:
        html: HTML 内容
        url: 目标 URL

    返回:
        Markdown 格式的内容
    """
    # 匹配规则
    rule = rule_store.match(url)

    # 情况 1: 有规则且未过期
    if rule and not is_expired(rule):
        rule_store.increment_usage(rule["host"], rule["path_pattern"])
        return apply_rule(html, rule)

    # 情况 2: 有规则但已过期 - 延长寿命并继续使用
    if rule and is_expired(rule):
        rule_store.extend_lifetime(rule["host"], rule["path_pattern"])
        rule_store.increment_usage(rule["host"], rule["path_pattern"])
        return apply_rule(html, rule)

    # 情况 3: 无规则 - 尝试生成新规则
    # 检查是否配置了 AI
    if not settings.AI_API_BASE_URL or not settings.AI_API_KEY:
        # 未配置 AI，直接使用 trafilatura 兜底
        print("未配置 AI，使用 trafilatura 兜底")
        markdown = extract(html, output_format="markdown", include_comments=False, include_tables=True)
        return markdown if markdown else html

    try:
        # AI 生成新规则
        new_rule, compression_level = await generate_rule(html, url)

        # 解析 URL 获取 host
        parsed = urlparse(url)
        host = parsed.netloc

        # 从 AI 生成的规则中提取 path_pattern
        try:
            rule_content = json.loads(new_rule["rule_content"])
            path_pattern = rule_content.get("path_pattern")

            # 如果 AI 没有生成 path_pattern，使用完整路径作为回退
            if not path_pattern:
                path = parsed.path or "/"
                path_pattern = path if path != "/" else "/*"
                print(f"警告: AI 未生成 path_pattern，使用完整路径: {path_pattern}")
            else:
                print(f"AI 生成的 path_pattern: {path_pattern}")

            # 从 rule_content 中移除 path_pattern（它不应该存储在 rule_content 中）
            if "path_pattern" in rule_content:
                del rule_content["path_pattern"]
                new_rule["rule_content"] = json.dumps(rule_content, ensure_ascii=False)

        except (json.JSONDecodeError, KeyError) as e:
            # JSON 解析失败，使用完整路径作为回退
            path = parsed.path or "/"
            path_pattern = path if path != "/" else "/*"
            print(f"警告: 解析规则失败 ({e})，使用完整路径: {path_pattern}")

        # 存储规则
        rule_store.upsert(
            host=host,
            path_pattern=path_pattern,
            rule_content=new_rule["rule_content"],
            compression_level=compression_level,
            source="curl-cffi-fetch"
        )

        print(f"规则已生成并存储: {host}{path_pattern} (压缩级别: {compression_level})")

        # 应用新规则
        new_rule["compression_level"] = compression_level
        return apply_rule(html, new_rule)

    except Exception as e:
        # AI 生成失败，使用 trafilatura 兜底
        print(f"规则生成失败: {e}，使用 trafilatura 兜底")
        markdown = extract(html, output_format="markdown", include_comments=False, include_tables=True)
        return markdown if markdown else html
