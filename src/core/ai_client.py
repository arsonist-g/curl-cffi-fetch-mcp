"""AI 请求客户端

使用 curl_cffi 发送 OpenAI 兼容 API 请求
"""

import json
import re
import random
import string
from typing import Dict, Any
from curl_cffi.requests import AsyncSession
from src.config import settings


def generate_random_tag() -> str:
    """生成随机 6 位字母标签

    返回:
        随机字符串，如 "ABCDEF"
    """
    return ''.join(random.choices(string.ascii_uppercase, k=6))


async def call_ai_for_rule(prompt_template: str, html: str, **kwargs) -> str:
    """调用 AI 生成或验证规则

    参数:
        prompt_template: 提示词模板
        html: HTML 内容
        **kwargs: 其他模板参数（如 url, existing_rule）

    返回:
        提取的规则 JSON 字符串

    异常:
        ValueError: 如果 AI API 未配置或响应解析失败
        Exception: 如果 API 请求失败
    """
    # 检查配置
    if not settings.AI_API_BASE_URL or not settings.AI_API_KEY:
        raise ValueError("AI API 未配置，请设置 AI_API_BASE_URL 和 AI_API_KEY")

    # 生成随机标签
    tag = generate_random_tag()

    # 填充提示词模板
    prompt = prompt_template.format(
        html=html,
        tag=tag,
        **kwargs
    )

    # 构建请求
    url = f"{settings.AI_API_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AI_API_KEY}"
    }

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": settings.AI_MAX_TOKENS,
        "temperature": 0.3  # 降低随机性，提高稳定性
    }

    # 发送请求
    async with AsyncSession() as session:
        response = await session.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(
                f"AI API 请求失败: HTTP {response.status_code} - {response.text}"
            )

        # 解析响应
        try:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"AI API 响应解析失败: {e}")

    # 提取标签内容
    pattern = f"<rule-{tag}>(.*?)</rule-{tag}>"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        raise ValueError(
            f"AI 响应中未找到规则标签 <rule-{tag}>，响应内容: {content[:500]}"
        )

    rule_json = match.group(1).strip()

    # 验证 JSON 格式
    try:
        json.loads(rule_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回的规则不是有效的 JSON: {e}")

    return rule_json
