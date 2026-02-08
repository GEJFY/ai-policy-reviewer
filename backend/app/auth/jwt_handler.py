"""
JWT token handling for authentication.

認証用JWTトークン管理。
アクセストークン、リフレッシュトークンの生成・検証を行う。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


# トークン設定
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """トークンペイロード"""
    sub: str  # ユーザーID
    exp: datetime  # 有効期限
    iat: datetime  # 発行時刻
    type: str  # access/refresh
    roles: list[str] = []  # ユーザーロール


class TokenPair(BaseModel):
    """アクセストークンとリフレッシュトークンのペア"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class JWTHandler:
    """
    JWT トークン管理クラス。

    アクセストークン（短期）とリフレッシュトークン（長期）の
    生成・検証を行う。
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        JWTハンドラを初期化。

        Args:
            secret_key: 署名用秘密鍵（Noneの場合設定から取得）
        """
        self.secret_key = secret_key or settings.secret_key
        if not self.secret_key or self.secret_key == "your-secret-key-change-in-production":
            logger.warning("Using default secret key - CHANGE IN PRODUCTION!")

    def create_access_token(
        self,
        user_id: str,
        roles: list[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        アクセストークンを生成。

        Args:
            user_id: ユーザーID
            roles: ユーザーロールのリスト
            expires_delta: 有効期限（Noneの場合デフォルト使用）

        Returns:
            str: JWTアクセストークン
        """
        now = datetime.now(timezone.utc)
        expires = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = now + expires

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "access",
            "roles": roles or [],
        }

        token = jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)
        logger.debug(f"Access token created | user_id={user_id} | expires={expire.isoformat()}")
        return token

    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        リフレッシュトークンを生成。

        Args:
            user_id: ユーザーID
            expires_delta: 有効期限（Noneの場合デフォルト使用）

        Returns:
            str: JWTリフレッシュトークン
        """
        now = datetime.now(timezone.utc)
        expires = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        expire = now + expires

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)
        logger.debug(f"Refresh token created | user_id={user_id} | expires={expire.isoformat()}")
        return token

    def create_token_pair(
        self,
        user_id: str,
        roles: list[str] = None,
    ) -> TokenPair:
        """
        アクセストークンとリフレッシュトークンのペアを生成。

        Args:
            user_id: ユーザーID
            roles: ユーザーロールのリスト

        Returns:
            TokenPair: トークンペア
        """
        access_token = self.create_access_token(user_id, roles)
        refresh_token = self.create_refresh_token(user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[TokenPayload]:
        """
        トークンを検証。

        Args:
            token: 検証するJWTトークン
            expected_type: 期待するトークンタイプ（access/refresh）

        Returns:
            TokenPayload: 検証成功時はペイロード、失敗時はNone
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])

            # トークンタイプを検証
            token_type = payload.get("type")
            if token_type != expected_type:
                logger.warning(f"Token type mismatch | expected={expected_type} | got={token_type}")
                return None

            return TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                type=token_type,
                roles=payload.get("roles", []),
            )

        except ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except JWTError as e:
            logger.warning(f"Token verification failed | error={str(e)}")
            return None

    def refresh_access_token(self, refresh_token: str, roles: list[str] = None) -> Optional[str]:
        """
        リフレッシュトークンを使用して新しいアクセストークンを生成。

        Args:
            refresh_token: リフレッシュトークン
            roles: 新しいトークンに含めるロール

        Returns:
            str: 新しいアクセストークン、失敗時はNone
        """
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return None

        return self.create_access_token(payload.sub, roles)

    def decode_token_unsafe(self, token: str) -> Optional[dict]:
        """
        トークンを検証なしでデコード（デバッグ用）。

        Args:
            token: JWTトークン

        Returns:
            dict: デコードされたペイロード
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[ALGORITHM], options={"verify_exp": False})
        except JWTError:
            return None


# シングルトンインスタンス
jwt_handler = JWTHandler()
