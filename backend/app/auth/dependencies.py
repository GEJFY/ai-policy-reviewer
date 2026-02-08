"""
FastAPI authentication dependencies.

FastAPI認証用の依存関係。
エンドポイントで認証を要求するために使用。
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import jwt_handler, TokenPayload
from app.core.observability.correlation import CorrelationContext

logger = logging.getLogger(__name__)

# HTTPベアラースキーム
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """現在のユーザー情報"""

    def __init__(
        self,
        user_id: str,
        roles: list[str] = None,
        token_payload: TokenPayload = None,
    ):
        self.user_id = user_id
        self.roles = roles or []
        self.token_payload = token_payload

    def has_role(self, role: str) -> bool:
        """指定されたロールを持っているか"""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """指定されたロールのいずれかを持っているか"""
        return any(r in self.roles for r in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """指定された全てのロールを持っているか"""
        return all(r in self.roles for r in roles)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """
    現在のユーザーを取得（オプショナル）。

    認証されていない場合はNoneを返す。
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = jwt_handler.verify_token(token)

    if not payload:
        return None

    # コンテキストにユーザー情報を設定
    CorrelationContext.set_user_id(payload.sub)

    return CurrentUser(
        user_id=payload.sub,
        roles=payload.roles,
        token_payload=payload,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    現在のユーザーを取得（必須）。

    認証されていない場合は401エラー。
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = jwt_handler.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # コンテキストにユーザー情報を設定
    CorrelationContext.set_user_id(payload.sub)

    logger.debug(f"User authenticated | user_id={payload.sub} | roles={payload.roles}")

    return CurrentUser(
        user_id=payload.sub,
        roles=payload.roles,
        token_payload=payload,
    )


def require_role(role: str):
    """
    特定のロールを要求するデコレータ用の依存関係。

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: CurrentUser = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not user.has_role(role):
            logger.warning(f"Access denied | user_id={user.user_id} | required_role={role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return role_checker


def require_any_role(roles: list[str]):
    """
    複数のロールのいずれかを要求する依存関係。

    Usage:
        @router.get("/management")
        async def management_endpoint(
            user: CurrentUser = Depends(require_any_role(["admin", "manager"]))
        ):
            ...
    """
    async def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not user.has_any_role(roles):
            logger.warning(
                f"Access denied | user_id={user.user_id} | required_roles={roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {roles} required",
            )
        return user

    return role_checker


# 一般的なロール依存関係
require_admin = require_role("admin")
require_reviewer = require_any_role(["admin", "reviewer"])
require_user = require_any_role(["admin", "reviewer", "user"])
