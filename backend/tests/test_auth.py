"""
Authentication module tests.

認証モジュール（JWT、ログイン、登録、ロールベースアクセス制御）のテスト。
"""

import pytest
from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_handler import JWTHandler, TokenPayload
from app.core.security.rate_limiter import rate_limiter


client = TestClient(app)


def _reset_rate_limiter():
    """テスト間でレートリミッターの状態をリセット"""
    rate_limiter._states.clear()


# =============================================================================
# JWT Handler Tests
# =============================================================================

class TestJWTHandler:
    """JWTハンドラーのテスト"""

    def setup_method(self):
        self.handler = JWTHandler(secret_key="test-secret-key-12345")

    def test_create_access_token(self):
        """アクセストークンが生成されること"""
        token = self.handler.create_access_token("user123", roles=["admin"])
        assert token
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """リフレッシュトークンが生成されること"""
        token = self.handler.create_refresh_token("user123")
        assert token
        assert isinstance(token, str)

    def test_create_token_pair(self):
        """トークンペアが生成されること"""
        pair = self.handler.create_token_pair("user123", roles=["reviewer"])
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0

    def test_verify_access_token(self):
        """アクセストークンが正しく検証されること"""
        token = self.handler.create_access_token("user123", roles=["admin", "user"])
        payload = self.handler.verify_token(token)
        assert payload is not None
        assert payload.sub == "user123"
        assert payload.type == "access"
        assert "admin" in payload.roles

    def test_verify_refresh_token(self):
        """リフレッシュトークンが正しく検証されること"""
        token = self.handler.create_refresh_token("user123")
        payload = self.handler.verify_token(token, expected_type="refresh")
        assert payload is not None
        assert payload.sub == "user123"
        assert payload.type == "refresh"

    def test_verify_token_wrong_type(self):
        """トークンタイプが一致しない場合Noneを返すこと"""
        token = self.handler.create_access_token("user123")
        payload = self.handler.verify_token(token, expected_type="refresh")
        assert payload is None

    def test_verify_expired_token(self):
        """期限切れトークンはNoneを返すこと"""
        token = self.handler.create_access_token(
            "user123",
            expires_delta=timedelta(seconds=-1),
        )
        payload = self.handler.verify_token(token)
        assert payload is None

    def test_verify_invalid_token(self):
        """不正なトークンはNoneを返すこと"""
        payload = self.handler.verify_token("invalid-token-string")
        assert payload is None

    def test_refresh_access_token(self):
        """リフレッシュトークンから新しいアクセストークンが生成されること"""
        refresh = self.handler.create_refresh_token("user123")
        new_access = self.handler.refresh_access_token(refresh, roles=["user"])
        assert new_access is not None
        payload = self.handler.verify_token(new_access)
        assert payload.sub == "user123"

    def test_refresh_with_invalid_token(self):
        """無効なリフレッシュトークンではNoneを返すこと"""
        result = self.handler.refresh_access_token("invalid-token")
        assert result is None

    def test_refresh_with_access_token_fails(self):
        """アクセストークンではリフレッシュできないこと"""
        access = self.handler.create_access_token("user123")
        result = self.handler.refresh_access_token(access)
        assert result is None

    def test_decode_token_unsafe(self):
        """期限切れでもデコードできること（デバッグ用）"""
        token = self.handler.create_access_token(
            "user123",
            expires_delta=timedelta(seconds=-1),
        )
        data = self.handler.decode_token_unsafe(token)
        assert data is not None
        assert data["sub"] == "user123"

    def test_different_secret_keys(self):
        """異なる秘密鍵では検証に失敗すること"""
        handler2 = JWTHandler(secret_key="different-secret-key")
        token = self.handler.create_access_token("user123")
        payload = handler2.verify_token(token)
        assert payload is None


# =============================================================================
# Auth API Endpoint Tests
# =============================================================================

class TestAuthLoginAPI:
    """ログインAPIのテスト"""

    def setup_method(self):
        _reset_rate_limiter()

    def test_login_success(self):
        """正しい認証情報でログインできること"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_wrong_password(self):
        """誤ったパスワードで401エラーになること"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """存在しないユーザーで401エラーになること"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password",
        })
        assert response.status_code == 401

    def test_login_empty_username(self):
        """空のユーザー名で422エラーになること"""
        response = client.post("/api/v1/auth/login", json={
            "username": "",
            "password": "password",
        })
        assert response.status_code == 422


class TestAuthRegisterAPI:
    """ユーザー登録APIのテスト"""

    def setup_method(self):
        _reset_rate_limiter()

    def test_register_success(self):
        """新規ユーザーを登録できること"""
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser_reg",
            "password": "securepassword123",
            "display_name": "テストユーザー",
            "role": "user",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser_reg"
        assert data["display_name"] == "テストユーザー"
        assert "user" in data["roles"]

    def test_register_duplicate_username(self):
        """重複ユーザー名で409エラーになること"""
        response = client.post("/api/v1/auth/register", json={
            "username": "admin",
            "password": "securepassword123",
            "display_name": "重複テスト",
        })
        assert response.status_code == 409

    def test_register_short_password(self):
        """短いパスワードで422エラーになること"""
        response = client.post("/api/v1/auth/register", json={
            "username": "shortpw",
            "password": "short",
            "display_name": "短いパスワード",
        })
        assert response.status_code == 422

    def test_register_invalid_username(self):
        """不正なユーザー名で422エラーになること"""
        response = client.post("/api/v1/auth/register", json={
            "username": "invalid user!",
            "password": "securepassword123",
            "display_name": "不正テスト",
        })
        assert response.status_code == 422


class TestAuthTokenRefreshAPI:
    """トークンリフレッシュAPIのテスト"""

    def setup_method(self):
        _reset_rate_limiter()

    def test_refresh_success(self):
        """有効なリフレッシュトークンでリフレッシュできること"""
        # まずログイン
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        tokens = login_response.json()

        # リフレッシュ
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self):
        """無効なリフレッシュトークンで401エラーになること"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert response.status_code == 401


class TestAuthMeAPI:
    """現在のユーザー情報APIのテスト"""

    def setup_method(self):
        _reset_rate_limiter()

    def test_me_authenticated(self):
        """認証済みユーザーの情報を取得できること"""
        # ログイン
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        tokens = login_response.json()

        # ユーザー情報取得
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "admin" in data["roles"]

    def test_me_unauthorized(self):
        """認証なしで401エラーになること"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self):
        """無効なトークンで401エラーになること"""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid-token",
        })
        assert response.status_code == 401


class TestAuthLogoutAPI:
    """ログアウトAPIのテスト"""

    def setup_method(self):
        _reset_rate_limiter()

    def test_logout_success(self):
        """認証済みユーザーがログアウトできること"""
        # ログイン
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        tokens = login_response.json()

        # ログアウト
        response = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert response.status_code == 200
        assert "ログアウト" in response.json()["message"]

    def test_logout_unauthorized(self):
        """認証なしでログアウトは401エラーになること"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401
