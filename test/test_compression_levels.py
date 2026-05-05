"""测试不同 HTML 压缩级别对 HTML 结构的影响

保存 L0/L1/L2/L3 四个压缩级别的 HTML 文件，用于对比分析
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.fetcher import fetch_url
from src.core.html_compressor import (
    compress_level_1,
    compress_level_2,
    compress_level_3,
    count_tokens
)
from src.config import settings


TEST_URL = ""


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def save_html(filename: str, html_content: str):
    """保存 HTML 到文件"""
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML 已保存到: {filepath}")


def print_html_stats(html_content: str, label: str):
    """打印 HTML 统计信息"""
    chars = len(html_content)
    tokens = count_tokens(html_content)
    lines = html_content.count('\n') + 1

    print(f"{label}:")
    print(f"  - 字符数: {chars:,}")
    print(f"  - Token 数: {tokens:,}")
    print(f"  - 行数: {lines:,}")


async def main():
    """主测试流程"""

    print_section("测试配置")
    print(f"测试 URL: {TEST_URL}")

    # 步骤 1: 抓取 HTML
    print_section("步骤 1: 抓取原始 HTML")

    try:
        html_content, status_code, response_headers = await fetch_url(
            url=TEST_URL,
            impersonate=settings.DEFAULT_IMPERSONATE,
            timeout=settings.DEFAULT_TIMEOUT
        )

        print(f"HTTP 状态码: {status_code}")
        print_html_stats(html_content, "原始 HTML")

        if status_code >= 400:
            print(f"[ERROR] HTTP 请求失败: {status_code}")
            return

    except Exception as e:
        print(f"[ERROR] 抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 2: 保存 L0（原始 HTML）
    print_section("步骤 2: L0 级别（原始 HTML，无压缩）")
    save_html("compression_L0.html", html_content)

    # 步骤 3: 保存 L1
    print_section("步骤 3: L1 级别（移除 script/style/svg/注释）")

    try:
        compressed_html = compress_level_1(html_content)
        print_html_stats(compressed_html, "L1 压缩后")

        reduction = (1 - len(compressed_html) / len(html_content)) * 100
        print(f"  - 压缩率: {reduction:.1f}%")

        save_html("compression_L1.html", compressed_html)

    except Exception as e:
        print(f"[ERROR] L1 压缩失败: {e}")
        import traceback
        traceback.print_exc()

    # 步骤 4: 保存 L2
    print_section("步骤 4: L2 级别（L1 + 属性简化）")

    try:
        compressed_html = compress_level_2(html_content)
        print_html_stats(compressed_html, "L2 压缩后")

        reduction = (1 - len(compressed_html) / len(html_content)) * 100
        print(f"  - 压缩率: {reduction:.1f}%")

        save_html("compression_L2.html", compressed_html)

    except Exception as e:
        print(f"[ERROR] L2 压缩失败: {e}")
        import traceback
        traceback.print_exc()

    # 步骤 5: 保存 L3
    print_section("步骤 5: L3 级别（L2 + 重复元素折叠）")

    try:
        compressed_html = compress_level_3(html_content, max_repeat=5)
        print_html_stats(compressed_html, "L3 压缩后")

        reduction = (1 - len(compressed_html) / len(html_content)) * 100
        print(f"  - 压缩率: {reduction:.1f}%")

        save_html("compression_L3.html", compressed_html)

    except Exception as e:
        print(f"[ERROR] L3 压缩失败: {e}")
        import traceback
        traceback.print_exc()

    # 步骤 6: 总结
    print_section("测试总结")

    print("测试完成！")
    print("\n生成的文件:")
    print("  1. test_output/compression_L0.html - 原始 HTML")
    print("  2. test_output/compression_L1.html - L1 压缩后的 HTML")
    print("  3. test_output/compression_L2.html - L2 压缩后的 HTML")
    print("  4. test_output/compression_L3.html - L3 压缩后的 HTML")
    print("\n分析建议:")
    print("  - 在浏览器中打开这些 HTML 文件，查看渲染效果")
    print("  - 对比各级别的 HTML 结构差异")
    print("  - 检查 div#content_views 容器在各级别中的变化")
    print("  - 查看是否有内容被意外删除或破坏")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
