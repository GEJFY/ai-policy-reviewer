"""
Authentication API endpoints.

認証APIエンドポイント。
ユーザー登録、ログイン、トークンリフレッシュを提供。
"""

import logging

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.auth.jwt_handler import jwt_handler
from app.auth.dependencies import get_current_user, CurrentUser
from app.core.observability.audit import audit_logger, AuditEventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# =============================================================================
# Request / Response Models
# =============================================================================

class LoginRequest(BaseModel):
    """ログインリクエスト"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """ユーザー登録リクエスト"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user", pattern=r"^(admin|reviewer|user)$")


class RefreshRequest(BaseModel):
    """トークンリフレッシュリクエスト"""
    refresh_token: str


class TokenResponse(BaseModel):
    """トークンレスポンス"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    user_id: str
    username: str
    display_name: str
    roles: list[str]


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    message: str


# =============================================================================
# In-memory User Store（本番ではDB/LDAPに置き換え）
# =============================================================================

# デモ/開発用のインメモリユーザーストア
# 初回起動時にパスワードハッシュを生成
def _init_users() -> dict[str, dict]:
    """デモユーザーを初期化"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    default_hash = pwd_context.hash("admin123")
    return {
        "admin": {
            "user_id": "usr_admin_001",
            "username": "admin",
            "display_name": "管理者",
            "password_hash": default_hash,
            "roles": ["admin", "reviewer", "user"],
        },
        "reviewer": {
            "user_id": "usr_reviewer_001",
            "username": "reviewer",
            "display_name": "レビュアー",
            "password_hash": default_hash,
            "roles": ["reviewer", "user"],
        },
    }

_users: dict[str, dict] = _init_users()

_next_user_id = 100


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def _hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    ユーザーログイン。

    認証成功時にアクセストークンとリフレッシュトークンを返す。
    """
    user = _users.get(request.username)

    if not user or not _verify_password(request.password, user["password_hash"]):
        # 監査ログ: ログイン失敗
        audit_logger.log(
            event_type=AuditEventType.LOGIN_FAILURE,
            resource_type="auth",
            resource_id=request.username,
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # トークンペア生成
    token_pair = jwt_handler.create_token_pair(
        user_id=user["user_id"],
        roles=user["roles"],
    )

    # 監査ログ: ログイン成功
    audit_logger.log(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user["user_id"],
        resource_type="auth",
        resource_id=request.username,
    )

    logger.info(f"User logged in | user_id={user['user_id']} | username={request.username}")

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    新規ユーザー登録。

    ユーザー名の重複チェックを行い、新しいユーザーを作成する。
    """
    global _next_user_id

    # 重複チェック
    if request.username in _users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ユーザー名 '{request.username}' は既に使用されています",
        )

    # ユーザー作成
    user_id = f"usr_{_next_user_id:06d}"
    _next_user_id += 1

    _users[request.username] = {
        "user_id": user_id,
        "username": request.username,
        "display_name": request.display_name,
        "password_hash": _hash_password(request.password),
        "roles": [request.role],
    }

    # 監査ログ: ユーザー作成
    audit_logger.log(
        event_type=AuditEventType.USER_CREATE,
        user_id=user_id,
        resource_type="user",
        resource_id=user_id,
        details={"username": request.username, "role": request.role},
    )

    logger.info(f"User registered | user_id={user_id} | username={request.username}")

    return UserResponse(
        user_id=user_id,
        username=request.username,
        display_name=request.display_name,
        roles=[request.role],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    アクセストークンをリフレッシュ。

    有効なリフレッシュトークンを使用して新しいアクセストークンを取得する。
    """
    # リフレッシュトークンを検証
    payload = jwt_handler.verify_token(request.refresh_token, expected_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンが無効または期限切れです",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ユーザーのロール情報を取得（ストアから再取得して最新のロールを反映）
    user = None
    for u in _users.values():
        if u["user_id"] == payload.sub:
            user = u
            break

    roles = user["roles"] if user else []

    # 新しいトークンペアを生成
    token_pair = jwt_handler.create_token_pair(
        user_id=payload.sub,
        roles=roles,
    )

    logger.debug(f"Token refreshed | user_id={payload.sub}")

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: CurrentUser = Depends(get_current_user)):
    """
    現在のユーザー情報を取得。

    有効なアクセストークンが必要。
    """
    # ユーザー情報をストアから取得
    for u in _users.values():
        if u["user_id"] == user.user_id:
            return UserResponse(
                user_id=u["user_id"],
                username=u["username"],
                display_name=u["display_name"],
                roles=u["roles"],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="ユーザーが見つかりません",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(user: CurrentUser = Depends(get_current_user)):
    """
    ログアウト。

    サーバーサイドではトークン無効化（将来のブラックリスト実装用）。
    クライアント側でトークンを破棄する。
    """
    # 監査ログ: ログアウト
    audit_logger.log(
        event_type=AuditEventType.LOGOUT,
        user_id=user.user_id,
        resource_type="auth",
    )

    logger.info(f"User logged out | user_id={user.user_id}")

    return MessageResponse(message="ログアウトしました")
