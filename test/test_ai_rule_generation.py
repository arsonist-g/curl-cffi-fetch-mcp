"""测试 AI 规则生成和应用

测试流程：
1. 清空该 URL 的现有规则
2. 使用 trafilatura 通用转换（无规则）
3. 使用 AI 规则引擎转换（自动生成规则）
4. 再次使用规则引擎转换（使用已生成的规则）
5. 对比三次转换的结果
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trafilatura import extract
from src.core.fetcher import fetch_url
from src.core.rule_engine import convert as rule_engine_convert
from src.core.rule_store import rule_store
from src.config import settings


TEST_URL = ""
TEST_URL_2 = ""


def html_to_markdown_generic(html: str) -> str:
    """通用 HTML 转 Markdown（用于测试对比）

    使用 trafilatura 进行通用转换
    """
    markdown = extract(
        html,
        output_format="markdown",
        include_comments=False,
        include_tables=True
    )
    return markdown if markdown else ""


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def save_result(filename: str, content: str):
    """保存结果到文件"""
    output_dir = project_root / "test_output"
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"结果已保存到: {filepath}")


def print_stats(content: str, label: str):
    """打印内容统计信息"""
    lines = content.split("\n")
    chars = len(content)
    words = len(content.split())

    print(f"{label} 统计:")
    print(f"  - 总字符数: {chars:,}")
    print(f"  - 总行数: {len(lines):,}")
    print(f"  - 总词数: {words:,}")
    print(f"  - 前 500 字符预览:")
    print("-" * 80)
    print(content[:500])
    print("-" * 80)


async def main():
    """主测试流程"""

    print_section("测试配置")
    print(f"测试 URL: {TEST_URL}")
    print(f"AI API: {settings.AI_API_BASE_URL}")
    print(f"AI Model: {settings.AI_MODEL}")
    print(f"规则数据库: {settings.RULE_DB_PATH}")

    # 检查 AI 配置
    if not settings.AI_API_BASE_URL or not settings.AI_API_KEY:
        print("\n[ERROR] AI API 未配置！")
        print("请在 .env 文件中配置 AI_API_BASE_URL 和 AI_API_KEY")
        return

    # 步骤 1: 清空现有规则
    print_section("步骤 1: 清空现有规则")

    from urllib.parse import urlparse
    parsed = urlparse(TEST_URL)
    host = parsed.netloc

    all_rules = rule_store.list_all()
    host_rules = [r for r in all_rules if r["host"] == host]

    if host_rules:
        print(f"找到 {len(host_rules)} 条 {host} 的规则，正在删除...")
        for rule in host_rules:
            rule_store.delete(rule["host"], rule["path_pattern"])
            print(f"  - 已删除: {rule['host']}{rule['path_pattern']}")
    else:
        print(f"没有找到 {host} 的规则")

    # 步骤 2: 抓取 HTML
    print_section("步骤 2: 抓取网页 HTML")

    try:
        html_content, status_code, response_headers = await fetch_url(
            url=TEST_URL,
            impersonate=settings.DEFAULT_IMPERSONATE,
            timeout=settings.DEFAULT_TIMEOUT
        )

        print(f"HTTP 状态码: {status_code}")
        print(f"HTML 大小: {len(html_content):,} 字符")

        if status_code >= 400:
            print(f"[ERROR] HTTP 请求失败: {status_code}")
            return

    except Exception as e:
        print(f"[ERROR] 抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 3: 通用转换（无规则）
    print_section("步骤 3: 通用 trafilatura 转换（无规则）")

    try:
        generic_markdown = html_to_markdown_generic(html_content)

        print_stats(generic_markdown, "通用转换")
        save_result("1_generic_conversion.md", generic_markdown)

    except Exception as e:
        print(f"[ERROR] 通用转换失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 4: AI 规则引擎转换（首次，自动生成规则）
    print_section("步骤 4: AI 规则引擎转换（首次，自动生成规则）")

    try:
        print("正在调用 AI 生成规则...")
        print("(这可能需要 10-30 秒，请耐心等待)")

        ai_first_markdown = await rule_engine_convert(html_content, TEST_URL)

        print_stats(ai_first_markdown, "AI 首次转换")
        save_result("2_ai_first_conversion.md", ai_first_markdown)

        # 检查是否生成了规则
        rule = rule_store.match(TEST_URL)
        if rule:
            print("\n[OK] 规则已生成:")
            print(f"  - Host: {rule['host']}")
            print(f"  - Path Pattern: {rule['path_pattern']}")
            print(f"  - 压缩级别: {rule.get('compression_level', 'N/A')} ← 生成规则时使用的压缩级别")
            print(f"  - 规则内容:")
            import json
            rule_content = json.loads(rule["rule_content"])
            print(f"    - Title Selector: {rule_content.get('title', 'N/A')}")
            print(f"    - Content Selector: {rule_content.get('content', 'N/A')}")
            print(f"    - Exclude Selectors: {rule_content.get('exclude', [])}")
            print(f"  - 寿命: {rule['lifetime_seconds']} 秒 ({rule['lifetime_seconds'] / 3600:.1f} 小时)")
            print(f"  - 过期时间: {rule['expires_at']}")

            # 说明应用规则时的行为
            compression_level = rule.get('compression_level', 'L0')
            print(f"\n[INFO] 应用规则时的行为:")
            if compression_level == "trafilatura":
                print(f"  - 直接使用 trafilatura 提取，不压缩 HTML")
            else:
                print(f"  - 直接在原始 HTML 上应用规则提取（不压缩）")
                print(f"  - 压缩级别 {compression_level} 仅用于记录生成规则时的压缩情况")
        else:
            print("\n[WARNING] 未找到生成的规则")

    except Exception as e:
        print(f"[ERROR] AI 规则引擎转换失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 5: 再次使用规则引擎转换（使用已生成的规则）
    print_section("步骤 5: 再次使用规则引擎转换（使用已生成的规则）")

    try:
        print("正在使用已生成的规则转换...")

        # 先显示规则信息
        rule = rule_store.match(TEST_URL)
        if rule:
            compression_level = rule.get('compression_level', 'L0')
            print(f"[INFO] 规则的压缩级别: {compression_level}")
            if compression_level == "trafilatura":
                print(f"  → 直接使用 trafilatura 提取")
            else:
                print(f"  → 直接在原始 HTML 上应用规则（不压缩）")

        ai_second_markdown = await rule_engine_convert(html_content, TEST_URL)

        print_stats(ai_second_markdown, "AI 第二次转换")
        save_result("3_ai_second_conversion.md", ai_second_markdown)

        # 检查规则使用计数
        rule = rule_store.match(TEST_URL)
        if rule:
            print(f"\n规则使用计数: {rule['usage_count']}")

    except Exception as e:
        print(f"[ERROR] 第二次转换失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 6: 对比结果
    print_section("步骤 6: 对比结果")

    print("内容长度对比:")
    print(f"  - 通用转换: {len(generic_markdown):,} 字符")
    print(f"  - AI 首次转换: {len(ai_first_markdown):,} 字符")
    print(f"  - AI 第二次转换: {len(ai_second_markdown):,} 字符")

    print("\n内容差异:")
    if ai_first_markdown == ai_second_markdown:
        print("  - AI 首次和第二次转换结果完全相同 ✓")
    else:
        print("  - AI 首次和第二次转换结果不同 ✗")
        print(f"    差异字符数: {abs(len(ai_first_markdown) - len(ai_second_markdown)):,}")

    # 计算内容压缩率
    generic_len = len(generic_markdown)
    ai_len = len(ai_first_markdown)

    if generic_len > 0:
        compression_rate = (1 - ai_len / generic_len) * 100
        print(f"\n内容压缩率: {compression_rate:.1f}%")
        if compression_rate > 0:
            print(f"  - AI 规则提取后内容减少了 {compression_rate:.1f}%")
        else:
            print(f"  - AI 规则提取后内容增加了 {abs(compression_rate):.1f}%")

    # 步骤 7: 总结
    print_section("测试总结")

    print("✓ 测试完成！")
    print("\n生成的文件:")
    print("  1. test_output/1_generic_conversion.md - 通用转换结果")
    print("  2. test_output/2_ai_first_conversion.md - AI 首次转换结果（生成规则）")
    print("  3. test_output/3_ai_second_conversion.md - AI 第二次转换结果（使用规则）")
    print("\n建议:")
    print("  - 对比文件内容，查看 AI 规则提取的效果")
    print("  - 检查是否成功提取了标题和正文内容")
    print("  - 检查是否过滤了导航栏、侧边栏等噪音内容")


async def test_rule_reuse():
    """测试规则复用

    使用 TEST_URL_2 测试是否能复用 TEST_URL 生成的规则
    """

    print_section("测试规则复用")
    print(f"第一个 URL: {TEST_URL}")
    print(f"第二个 URL: {TEST_URL_2}")

    # 检查 AI 配置
    if not settings.AI_API_BASE_URL or not settings.AI_API_KEY:
        print("\n[ERROR] AI API 未配置！")
        return

    # 步骤 1: 确保第一个 URL 已经生成了规则
    print_section("步骤 1: 检查现有规则")

    from urllib.parse import urlparse
    parsed = urlparse(TEST_URL)
    host = parsed.netloc

    all_rules = rule_store.list_all()
    host_rules = [r for r in all_rules if r["host"] == host]

    if not host_rules:
        print(f"[WARNING] 没有找到 {host} 的规则")
        print("请先运行主测试生成规则")
        return

    print(f"找到 {len(host_rules)} 条 {host} 的规则:")
    for rule in host_rules:
        print(f"  - {rule['host']}{rule['path_pattern']}")
        print(f"    使用次数: {rule['usage_count']}")

    # 步骤 2: 抓取第二个 URL
    print_section("步骤 2: 抓取第二个 URL")

    try:
        html_content, status_code, response_headers = await fetch_url(
            url=TEST_URL_2,
            impersonate=settings.DEFAULT_IMPERSONATE,
            timeout=settings.DEFAULT_TIMEOUT
        )

        print(f"HTTP 状态码: {status_code}")
        print(f"HTML 大小: {len(html_content):,} 字符")

        if status_code >= 400:
            print(f"[ERROR] HTTP 请求失败: {status_code}")
            return

    except Exception as e:
        print(f"[ERROR] 抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 3: 使用规则引擎转换（应该复用现有规则）
    print_section("步骤 3: 使用规则引擎转换（测试规则复用）")

    try:
        # 检查是否能匹配到规则
        matched_rule = rule_store.match(TEST_URL_2)
        if matched_rule:
            print(f"[OK] 匹配到规则:")
            print(f"  - Host: {matched_rule['host']}")
            print(f"  - Path Pattern: {matched_rule['path_pattern']}")
            print(f"  - 使用次数（转换前）: {matched_rule['usage_count']}")
        else:
            print("[WARNING] 未匹配到规则，将生成新规则")

        # 执行转换
        print("\n正在转换...")
        markdown = await rule_engine_convert(html_content, TEST_URL_2)

        print_stats(markdown, "规则引擎转换")
        save_result("4_rule_reuse_conversion.md", markdown)

        # 检查规则使用计数是否增加
        matched_rule_after = rule_store.match(TEST_URL_2)
        if matched_rule_after:
            print(f"\n规则使用计数（转换后）: {matched_rule_after['usage_count']}")
            if matched_rule and matched_rule_after['usage_count'] > matched_rule['usage_count']:
                print("[OK] 规则使用计数已增加，说明成功复用了规则 ✓")
            else:
                print("[INFO] 规则使用计数未变化")

    except Exception as e:
        print(f"[ERROR] 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 4: 总结
    print_section("规则复用测试总结")

    print("✓ 测试完成！")
    print("\n生成的文件:")
    print("  - test_output/4_rule_reuse_conversion.md - 规则复用转换结果")
    print("\n验证要点:")
    print("  - 检查是否匹配到了正确的规则")
    print("  - 检查规则使用计数是否增加")
    print("  - 检查转换结果是否正确提取了内容")


if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "reuse":
        # 运行规则复用测试
        try:
            asyncio.run(test_rule_reuse())
        except KeyboardInterrupt:
            print("\n\n测试被用户中断")
        except Exception as e:
            print(f"\n\n[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # 运行主测试
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n测试被用户中断")
        except Exception as e:
            print(f"\n\n[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
