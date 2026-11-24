"""通用 schema：分页、角色枚举、状态枚举。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)
    sort_by: str = Field(default="updated_at")
    order: str = Field(default="desc")


class PageData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    total_approx: int | None = None
    page: int
    page_size: int
    has_more: bool
