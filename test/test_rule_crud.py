"""测试 Rules CRUD 接口

测试规则的增删改查功能
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试配置
BASE_URL = "http://localhost:8000"
API_KEY = "sk-test-key-12345"  # 从 .env 读取的 API_KEY

# 请求头
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def print_section(title: str):
    """打印测试章节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(test_name: str, success: bool, data: Any = None, error: str = None):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{test_name}: {status}")
    if data:
        print(f"  Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    if error:
        print(f"  Error: {error}")
    print()


def test_create_rule() -> Dict[str, Any]:
    """测试创建规则"""
    print_section("测试 1: 创建规则 (POST /v1/rules)")

    # 测试数据
    rule_data = {
        "host": "test.example.com",
        "path_pattern": "/article/*",
        "rule_content": {
            "title": {"selector": "h1.title", "type": "text"},
            "content": {"selector": "div.content", "type": "html"}
        },
        "lifetime_seconds": 3600,
        "source": "test-suite"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/v1/rules",
            headers=HEADERS,
            json=rule_data
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            print_result("创建规则", True, result.get("data"))
            return result.get("data")
        else:
            print_result("创建规则", False, error=result.get("error"))
            return None

    except Exception as e:
        print_result("创建规则", False, error=str(e))
        return None


def test_list_all_rules():
    """测试查询所有规则"""
    print_section("测试 2: 查询所有规则 (GET /v1/rules)")

    try:
        response = requests.get(
            f"{BASE_URL}/v1/rules",
            headers=HEADERS
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            rules = result.get("data", [])
            print_result("查询所有规则", True, {"规则数量": len(rules), "规则列表": rules})
        else:
            print_result("查询所有规则", False, error=result.get("error"))

    except Exception as e:
        print_result("查询所有规则", False, error=str(e))


def test_get_rules_by_host(host: str):
    """测试按 host 查询规则"""
    print_section(f"测试 3: 按 host 查询规则 (GET /v1/rules/{host})")

    try:
        response = requests.get(
            f"{BASE_URL}/v1/rules/{host}",
            headers=HEADERS
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            rules = result.get("data", [])
            print_result(f"查询 {host} 的规则", True, {"规则数量": len(rules), "规则列表": rules})
        else:
            print_result(f"查询 {host} 的规则", False, error=result.get("error"))

    except Exception as e:
        print_result(f"查询 {host} 的规则", False, error=str(e))


def test_get_rules_by_host_and_path(host: str, path_pattern: str):
    """测试按 host 和 path_pattern 查询规则"""
    print_section(f"测试 4: 按 host 和 path_pattern 查询规则 (GET /v1/rules/{host}?path_pattern={path_pattern})")

    try:
        response = requests.get(
            f"{BASE_URL}/v1/rules/{host}",
            headers=HEADERS,
            params={"path_pattern": path_pattern}
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            rules = result.get("data", [])
            print_result(f"查询 {host}{path_pattern} 的规则", True, {"规则数量": len(rules), "规则列表": rules})
        else:
            print_result(f"查询 {host}{path_pattern} 的规则", False, error=result.get("error"))

    except Exception as e:
        print_result(f"查询 {host}{path_pattern} 的规则", False, error=str(e))


def test_update_rule(host: str, path_pattern: str):
    """测试更新规则"""
    print_section(f"测试 5: 更新规则 (PUT /v1/rules/{host}?path_pattern={path_pattern})")

    # 更新数据
    update_data = {
        "rule_content": {
            "title": {"selector": "h1.new-title", "type": "text"},
            "content": {"selector": "div.new-content", "type": "html"},
            "author": {"selector": "span.author", "type": "text"}
        },
        "lifetime_seconds": 7200
    }

    try:
        response = requests.put(
            f"{BASE_URL}/v1/rules/{host}",
            headers=HEADERS,
            params={"path_pattern": path_pattern},
            json=update_data
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            print_result("更新规则", True, result.get("data"))
        else:
            print_result("更新规则", False, error=result.get("error"))

    except Exception as e:
        print_result("更新规则", False, error=str(e))


def test_create_multiple_rules():
    """测试创建多个规则"""
    print_section("测试 6: 创建多个规则")

    rules = [
        {
            "host": "test.example.com",
            "path_pattern": "/news/*",
            "rule_content": {
                "title": {"selector": "h1", "type": "text"}
            },
            "source": "test-suite"
        },
        {
            "host": "another.example.com",
            "path_pattern": "/*",
            "rule_content": {
                "content": {"selector": "body", "type": "html"}
            },
            "source": "test-suite"
        }
    ]

    for i, rule_data in enumerate(rules, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/v1/rules",
                headers=HEADERS,
                json=rule_data
            )

            result = response.json()

            if response.status_code == 200 and result.get("success"):
                print_result(f"创建规则 {i}", True, result.get("data"))
            else:
                print_result(f"创建规则 {i}", False, error=result.get("error"))

        except Exception as e:
            print_result(f"创建规则 {i}", False, error=str(e))


def test_delete_rule(host: str, path_pattern: str):
    """测试删除单个规则"""
    print_section(f"测试 7: 删除单个规则 (DELETE /v1/rules/{host}?path_pattern={path_pattern})")

    try:
        response = requests.delete(
            f"{BASE_URL}/v1/rules/{host}",
            headers=HEADERS,
            params={"path_pattern": path_pattern}
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            print_result("删除规则", True, result.get("data"))
        else:
            print_result("删除规则", False, error=result.get("error"))

    except Exception as e:
        print_result("删除规则", False, error=str(e))


def test_delete_all_rules_by_host(host: str):
    """测试删除某个 host 的所有规则"""
    print_section(f"测试 8: 删除 host 的所有规则 (DELETE /v1/rules/{host})")

    try:
        response = requests.delete(
            f"{BASE_URL}/v1/rules/{host}",
            headers=HEADERS
        )

        result = response.json()

        if response.status_code == 200 and result.get("success"):
            print_result(f"删除 {host} 的所有规则", True, result.get("data"))
        else:
            print_result(f"删除 {host} 的所有规则", False, error=result.get("error"))

    except Exception as e:
        print_result(f"删除 {host} 的所有规则", False, error=str(e))


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  Rules CRUD 接口测试")
    print("=" * 60)
    print(f"  服务地址: {BASE_URL}")
    print(f"  API Key: {API_KEY[:10]}...")
    print("=" * 60)

    # 1. 创建规则
    created_rule = test_create_rule()

    if not created_rule:
        print("\n创建规则失败，终止测试")
        return

    host = created_rule.get("host")
    path_pattern = created_rule.get("path_pattern")

    # 2. 查询所有规则
    test_list_all_rules()

    # 3. 按 host 查询规则
    test_get_rules_by_host(host)

    # 4. 按 host 和 path_pattern 查询规则
    test_get_rules_by_host_and_path(host, path_pattern)

    # 5. 更新规则
    test_update_rule(host, path_pattern)

    # 6. 创建多个规则
    test_create_multiple_rules()

    # 7. 再次查询所有规则
    test_list_all_rules()

    # 8. 删除单个规则
    test_delete_rule(host, "/news/*")

    # 9. 删除 host 的所有规则
    test_delete_all_rules_by_host(host)
    test_delete_all_rules_by_host("another.example.com")

    # 10. 最后查询所有规则
    test_list_all_rules()

    print_section("测试完成")


if __name__ == "__main__":
    main()
