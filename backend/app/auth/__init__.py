"""
Authentication module for enterprise-grade security.

エンタープライズレベルのセキュリティ認証モジュール。
JWT認証、ロールベースアクセス制御を提供。
"""

from app.auth.jwt_handler import (
    JWTHandler,
    jwt_handler,
    TokenPayload,
    TokenPair,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_current_user_optional,
    require_role,
    require_any_role,
    require_admin,
    require_reviewer,
    require_user,
)

__all__ = [
    # JWT Handler
    "JWTHandler",
    "jwt_handler",
    "TokenPayload",
    "TokenPair",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    # Dependencies
    "CurrentUser",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_any_role",
    "require_admin",
    "require_reviewer",
    "require_user",
]
