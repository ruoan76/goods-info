"""商品域 schema：建档 / 查重 / PATCH / 状态 / 属性。"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


from ..services.ironrules import PATCHABLE_FIELDS


class GoodsCreate(BaseModel):
    barcode: str = Field(min_length=8, max_length=13)
    goods_name: str = Field(min_length=1, max_length=500)
    category_id: str | None = None
    unit_id: str | None = None
    inprice: Decimal | None = Field(default=None, ge=0)
    outprice: Decimal | None = Field(default=None, ge=0)
    quality_grade: str = Field(default="C")
    attrs: dict[str, Any] | None = None

    @field_validator("barcode")
    @classmethod
    def barcode_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("条码必须为纯数字")
        return v

    @field_validator("quality_grade")
    @classmethod
    def grade_domain(cls, v: str) -> str:
        if v not in ("A", "B", "C", "D"):
            raise ValueError("等级必须为 A/B/C/D")
        return v


class GoodsCheckBody(BaseModel):
    barcode: str
    goods_name: str


class PatchBody(BaseModel):
    field: str = Field(description="可即点即改的字段白名单（不含 barcode）")
    new_value: str
    version: int = Field(ge=1)
    reason: str | None = None

    @field_validator("field")
    @classmethod
    def field_whitelist(cls, v: str) -> str:
        if v not in PATCHABLE_FIELDS:
            raise ValueError(f"字段不可通过此端点更新: {v}")
        return v


class CategoryChangeBody(BaseModel):
    category_id: str
    reason: str | None = None


class StatusChangeBody(BaseModel):
    to_status: str
    reason: str

    @field_validator("to_status")
    @classmethod
    def status_domain(cls, v: str) -> str:
        if v not in ("ACTIVE", "INACTIVE", "VOIDED"):
            raise ValueError("状态非法")
        return v


class AttrsWriteBody(BaseModel):
    attrs: dict[str, Any]
