"""HTML 智能压缩器

逐级压缩 HTML，保留结构但减少 token 数量，用于 AI 规则生成
"""

import re
import tiktoken
from bs4 import BeautifulSoup, Comment
from typing import Tuple


def count_tokens(text: str) -> int:
    """计算文本的 token 数量

    参数:
        text: 文本内容

    返回:
        token 数量
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def remove_blank_lines(html: str) -> str:
    """移除空行和多余空白

    参数:
        html: HTML 内容

    返回:
        移除空行后的 HTML
    """
    lines = html.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def compress_level_1(html: str) -> str:
    """压缩级别 1：移除 script/style/svg/noscript/注释

    移除内容：
    - <script> 标签及内容
    - <style> 标签及内容
    - <svg> 标签及内容
    - <noscript> 标签及内容
    - HTML 注释

    参数:
        html: 原始 HTML

    返回:
        压缩后的 HTML
    """
    soup = BeautifulSoup(html, "lxml")

    # 移除 script, style, svg, noscript
    for tag in soup.find_all(["script", "style", "svg", "noscript"]):
        tag.decompose()

    # 移除注释
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    result = str(soup)
    result = remove_blank_lines(result)

    return result


def compress_level_2(html: str) -> str:
    """压缩级别 2：L1 + 属性简化

    在 L1 基础上：
    - 只保留 class 和 id 属性
    - 移除 style, onclick, data-* 等其他属性

    参数:
        html: 原始 HTML

    返回:
        压缩后的 HTML
    """
    soup = BeautifulSoup(html, "lxml")

    # L1 的移除操作
    for tag in soup.find_all(["script", "style", "svg", "noscript"]):
        tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 简化属性：只保留 class 和 id
    for tag in soup.find_all(True):
        keep_attrs = ["class", "id"]
        attrs_to_remove = [attr for attr in tag.attrs if attr not in keep_attrs]
        for attr in attrs_to_remove:
            del tag[attr]

    result = str(soup)
    result = remove_blank_lines(result)

    return result


def compress_level_3(html: str, max_repeat: int = 5) -> str:
    """压缩级别 3：L2 + 重复元素折叠

    在 L2 基础上：
    - 重复的同级元素只保留前 max_repeat 个（默认 5）
    - 添加注释标记被折叠的数量

    参数:
        html: 原始 HTML
        max_repeat: 保留的重复元素数量（默认 5）

    返回:
        压缩后的 HTML
    """
    soup = BeautifulSoup(html, "lxml")

    # L1 的移除操作
    for tag in soup.find_all(["script", "style", "svg", "noscript"]):
        tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # L2 的属性简化
    for tag in soup.find_all(True):
        keep_attrs = ["class", "id"]
        attrs_to_remove = [attr for attr in tag.attrs if attr not in keep_attrs]
        for attr in attrs_to_remove:
            del tag[attr]

    # L3 的重复元素折叠
    for parent in soup.find_all(True):
        children = list(parent.children)
        if len(children) <= max_repeat:
            continue

        # 按标签名分组
        tag_groups = {}
        for child in children:
            if hasattr(child, "name") and child.name:
                tag_name = child.name
                if tag_name not in tag_groups:
                    tag_groups[tag_name] = []
                tag_groups[tag_name].append(child)

        # 折叠每组
        for tag_name, tags in tag_groups.items():
            if len(tags) > max_repeat:
                # 保留前 max_repeat 个
                for i in range(max_repeat, len(tags)):
                    tags[i].decompose()

                # 添加注释标记
                if tags and max_repeat > 0:
                    comment_text = f" ... {len(tags) - max_repeat} more {tag_name} elements ... "
                    comment_node = soup.new_string(comment_text)
                    tags[max_repeat - 1].insert_after(comment_node)

    result = str(soup)
    result = remove_blank_lines(result)

    return result


def compress_html_adaptive(html: str, token_limit: int = 4096, max_repeat: int = 5) -> Tuple[str, str]:
    """自适应压缩：逐级压缩直到低于 token 上限

    压缩策略：
    1. 原始 HTML < token_limit → 不压缩
    2. L1 压缩 < token_limit → 使用 L1
    3. L2 压缩 < token_limit → 使用 L2
    4. L3 压缩 < token_limit → 使用 L3
    5. L3 仍超过 → 返回 L3 结果，标记需要 trafilatura

    参数:
        html: 原始 HTML
        token_limit: token 上限（默认 4096）
        max_repeat: 重复元素保留数量（默认 5）

    返回:
        (压缩后的 HTML, 压缩级别标识)
        压缩级别: "L0" | "L1" | "L2" | "L3" | "L3_exceeded"
    """
    original_tokens = count_tokens(html)

    # 如果原始 HTML 已经低于上限，直接返回
    if original_tokens <= token_limit:
        return html, "L0"

    # 尝试 L1
    compressed = compress_level_1(html)
    if count_tokens(compressed) <= token_limit:
        return compressed, "L1"

    # 尝试 L2
    compressed = compress_level_2(html)
    if count_tokens(compressed) <= token_limit:
        return compressed, "L2"

    # 尝试 L3
    compressed = compress_level_3(html, max_repeat=max_repeat)
    if count_tokens(compressed) <= token_limit:
        return compressed, "L3"

    # L3 仍超过上限，返回 L3 结果并标记
    return compressed, "L3_exceeded"


def apply_compression(html: str, level: str, max_repeat: int = 5) -> str:
    """应用指定级别的压缩

    用于规则应用时，使用与规则生成时相同的压缩级别

    参数:
        html: 原始 HTML
        level: 压缩级别 ("L0" | "L1" | "L2" | "L3" | "trafilatura")
        max_repeat: 重复元素保留数量（默认 5）

    返回:
        压缩后的 HTML
    """
    if level == "L0":
        return html
    elif level == "L1":
        return compress_level_1(html)
    elif level == "L2":
        return compress_level_2(html)
    elif level == "L3":
        return compress_level_3(html, max_repeat=max_repeat)
    elif level == "trafilatura":
        # trafilatura 压缩在 rule_engine 中处理
        return html
    else:
        # 未知级别，不压缩
        return html
