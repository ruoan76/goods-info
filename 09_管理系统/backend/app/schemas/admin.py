"""管理后台 schema：用户 / 单位 / 分类模板 / 外部码映射。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class RoleEnum(str):
    VIEWER = "Viewer"
    OPERATOR = "Operator"
    STEWARD = "Steward"


class UserCreate(BaseModel):
    account: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    role: str
    dept: str | None = None
    phone: str | None = None

    @field_validator("role")
    @classmethod
    def role_domain(cls, v: str) -> str:
        if v not in ("Viewer", "Operator", "Steward"):
            raise ValueError("role 仅接受 Viewer/Operator/Steward")
        return v


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    status: str | None = None
    dept: str | None = None
    phone: str | None = None

    @field_validator("role")
    @classmethod
    def role_domain(cls, v: str | None) -> str | None:
        if v is not None and v not in ("Viewer", "Operator", "Steward"):
            raise ValueError("role 仅接受 Viewer/Operator/Steward")
        return v

    @field_validator("status")
    @classmethod
    def status_domain(cls, v: str | None) -> str | None:
        if v is not None and v not in ("ACTIVE", "INACTIVE"):
            raise ValueError("status 仅接受 ACTIVE/INACTIVE")
        return v


class UnitCreate(BaseModel):
    code: str
    name: str
    sort_order: int = 0
    enabled: bool = True


class UnitUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    enabled: bool | None = None


class TemplateWrite(BaseModel):
    template: dict[str, Any]


class ExternalMapWrite(BaseModel):
    mappings: list[dict[str, Any]]
