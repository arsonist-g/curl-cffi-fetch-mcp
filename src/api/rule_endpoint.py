"""规则管理 REST API 端点

提供规则的 CRUD 操作接口
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field
from src.auth import verify_api_key
from src.core.rule_store import rule_store
from src.models.response import OneAPIResponse


# 路由器
router = APIRouter(prefix="/v1", tags=["Rules"])


# 请求模型
class RuleCreateRequest(BaseModel):
    """创建规则请求"""
    host: str = Field(..., description="域名")
    path_pattern: str = Field(default="/*", description="路径模式（支持 fnmatch 通配符）")
    rule_content: dict = Field(..., description="规则内容（JSON 对象）")
    compression_level: str = Field(default="L0", description="压缩级别 (L0/L1/L2/L3/trafilatura)")
    lifetime_seconds: Optional[int] = Field(None, description="规则寿命（秒），默认使用配置值")
    source: str = Field(default="curl-cffi-fetch", description="规则来源")


class RuleUpdateRequest(BaseModel):
    """更新规则请求"""
    rule_content: dict = Field(..., description="规则内容（JSON 对象）")
    compression_level: Optional[str] = Field(None, description="压缩级别 (L0/L1/L2/L3/trafilatura)")
    lifetime_seconds: Optional[int] = Field(None, description="规则寿命（秒）")


# 响应模型
class RuleInfo(BaseModel):
    """规则信息"""
    id: int
    host: str
    path_pattern: str
    rule_content: dict
    compression_level: str
    lifetime_seconds: int
    expires_at: float
    usage_count: int
    source: str
    created_at: float
    updated_at: float


@router.get("/rules", response_model=OneAPIResponse)
async def list_rules(request: Request):
    """查询所有规则

    返回所有存储的规则列表
    """
    # 验证 API Key
    await verify_api_key(request)

    try:
        rules = rule_store.list_all()

        # 解析 rule_content 为 JSON 对象
        for rule in rules:
            try:
                rule["rule_content"] = json.loads(rule["rule_content"])
            except json.JSONDecodeError:
                rule["rule_content"] = {}

        return OneAPIResponse(
            success=True,
            data=rules,
            error=None
        )

    except Exception as e:
        return OneAPIResponse(
            success=False,
            data=None,
            error={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


@router.get("/rules/{host}", response_model=OneAPIResponse)
async def get_rules_by_host(
    host: str,
    request: Request,
    path_pattern: Optional[str] = Query(None, description="精确匹配的路径模式")
):
    """查询指定 host 的规则

    参数:
        host: 域名
        path_pattern: 可选，精确匹配的路径模式

    返回:
        匹配的规则列表或单个规则
    """
    # 验证 API Key
    await verify_api_key(request)

    try:
        all_rules = rule_store.list_all()

        # 过滤指定 host 的规则
        filtered = [r for r in all_rules if r["host"] == host]

        # 如果指定了 path_pattern，进一步过滤
        if path_pattern:
            filtered = [r for r in filtered if r["path_pattern"] == path_pattern]

        # 解析 rule_content 为 JSON 对象
        for rule in filtered:
            try:
                rule["rule_content"] = json.loads(rule["rule_content"])
            except json.JSONDecodeError:
                rule["rule_content"] = {}

        return OneAPIResponse(
            success=True,
            data=filtered,
            error=None
        )

    except Exception as e:
        return OneAPIResponse(
            success=False,
            data=None,
            error={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


@router.post("/rules", response_model=OneAPIResponse)
async def create_rule(rule_request: RuleCreateRequest, request: Request):
    """创建新规则

    参数:
        rule_request: 规则创建请求

    返回:
        创建的规则信息
    """
    # 验证 API Key
    await verify_api_key(request)

    try:
        # 将 rule_content 转换为 JSON 字符串
        rule_content_str = json.dumps(rule_request.rule_content, ensure_ascii=False)

        # 创建规则
        rule = rule_store.upsert(
            host=rule_request.host,
            path_pattern=rule_request.path_pattern,
            rule_content=rule_content_str,
            compression_level=rule_request.compression_level,
            lifetime_seconds=rule_request.lifetime_seconds,
            source=rule_request.source
        )

        if not rule:
            raise Exception("规则创建失败")

        # 解析 rule_content 为 JSON 对象
        rule["rule_content"] = json.loads(rule["rule_content"])

        return OneAPIResponse(
            success=True,
            data=rule,
            error=None
        )

    except Exception as e:
        return OneAPIResponse(
            success=False,
            data=None,
            error={
                "code": "CREATE_ERROR",
                "message": f"创建规则失败: {str(e)}"
            }
        )


@router.put("/rules/{host}", response_model=OneAPIResponse)
async def update_rule(
    host: str,
    rule_request: RuleUpdateRequest,
    request: Request,
    path_pattern: str = Query(..., description="要更新的路径模式")
):
    """更新规则

    参数:
        host: 域名
        path_pattern: 路径模式
        rule_request: 规则更新请求

    返回:
        更新后的规则信息
    """
    # 验证 API Key
    await verify_api_key(request)

    try:
        # 将 rule_content 转换为 JSON 字符串
        rule_content_str = json.dumps(rule_request.rule_content, ensure_ascii=False)

        # 更新规则（upsert 会自动处理）
        rule = rule_store.upsert(
            host=host,
            path_pattern=path_pattern,
            rule_content=rule_content_str,
            compression_level=rule_request.compression_level or "L0",
            lifetime_seconds=rule_request.lifetime_seconds,
            source="curl-cffi-fetch"  # 更新时保持来源
        )

        if not rule:
            raise Exception("规则更新失败")

        # 解析 rule_content 为 JSON 对象
        rule["rule_content"] = json.loads(rule["rule_content"])

        return OneAPIResponse(
            success=True,
            data=rule,
            error=None
        )

    except Exception as e:
        return OneAPIResponse(
            success=False,
            data=None,
            error={
                "code": "UPDATE_ERROR",
                "message": f"更新规则失败: {str(e)}"
            }
        )


@router.delete("/rules/{host}", response_model=OneAPIResponse)
async def delete_rule(
    host: str,
    request: Request,
    path_pattern: Optional[str] = Query(None, description="要删除的路径模式，不指定则删除该 host 的所有规则")
):
    """删除规则

    参数:
        host: 域名
        path_pattern: 可选，路径模式。如果不指定，删除该 host 的所有规则

    返回:
        删除结果
    """
    # 验证 API Key
    await verify_api_key(request)

    try:
        if path_pattern:
            # 删除指定规则
            deleted = rule_store.delete(host, path_pattern)
            message = f"已删除规则: {host}{path_pattern}" if deleted else "规则不存在"
        else:
            # 删除该 host 的所有规则
            all_rules = rule_store.list_all()
            host_rules = [r for r in all_rules if r["host"] == host]

            deleted_count = 0
            for rule in host_rules:
                if rule_store.delete(rule["host"], rule["path_pattern"]):
                    deleted_count += 1

            message = f"已删除 {deleted_count} 条规则"

        return OneAPIResponse(
            success=True,
            data={"message": message},
            error=None
        )

    except Exception as e:
        return OneAPIResponse(
            success=False,
            data=None,
            error={
                "code": "DELETE_ERROR",
                "message": f"删除规则失败: {str(e)}"
            }
        )
