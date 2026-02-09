"""
Health API endpoint tests.

ヘルスチェックAPIのテスト。
"""

from fastapi.testclient import TestClient


class TestHealthAPI:
    """ヘルスチェックAPI テストクラス。"""

    def test_health_check(self, client: TestClient):
        """ヘルスチェックエンドポイントのテスト。"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_redirect_or_response(self, client: TestClient):
        """ルートエンドポイントのテスト。"""
        response = client.get("/")

        # ルートはリダイレクトまたはウェルカムメッセージ
        assert response.status_code in [200, 307]

    def test_api_docs_available(self, client: TestClient):
        """APIドキュメント（Swagger UI）が利用可能。"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "text/html" in response.headers.get("content-type", "")

    def test_openapi_schema_available(self, client: TestClient):
        """OpenAPIスキーマが利用可能。"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
