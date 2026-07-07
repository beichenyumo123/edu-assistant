"""
认证相关 Pydantic Schema
"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., max_length=100, description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码(6-50位)")
    grade: str | None = Field(None, max_length=20, description="部门（兼容旧字段 grade）")
    major: str | None = Field(None, max_length=100, description="岗位（兼容旧字段 major）")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    grade: str | None
    major: str | None
    avatar_url: str | None
