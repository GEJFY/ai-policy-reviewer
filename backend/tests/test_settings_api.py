"""
Settings API endpoint tests.

設定APIのテスト。シークレットマスク・モデル一覧を検証。
"""

from fastapi.testclient import TestClient


class TestSettingsAPI:
    """設定API テストクラス。"""

    def test_get_settings(self, client: TestClient):
        """設定エンドポイントが正常に動作する。"""
        response = client.get("/api/v1/settings/")

        assert response.status_code == 200
        data = response.json()

        # トップレベルキーの存在確認
        assert "system" in data
        assert "llm" in data
        assert "providers" in data
        assert "embedding" in data
        assert "ocr" in data
        assert "app" in data
        assert "validation" in data

    def test_settings_system_info(self, client: TestClient):
        """システム情報が含まれる。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        system = data["system"]
        assert "version" in system
        assert "debug" in system
        assert "database_url" in system

    def test_settings_llm_info(self, client: TestClient):
        """LLM設定が含まれる。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        llm = data["llm"]
        assert "provider" in llm
        assert "model" in llm
        assert "available_providers" in llm
        assert isinstance(llm["available_providers"], list)

    def test_settings_providers_structure(self, client: TestClient):
        """プロバイダー設定の構造が正しい。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        providers = data["providers"]
        assert "azure" in providers
        assert "aws_bedrock" in providers
        assert "gcp_vertex" in providers
        assert "ollama" in providers

        # 各プロバイダーにconfiguredフラグがある
        for key in ["azure", "aws_bedrock", "gcp_vertex", "ollama"]:
            assert "configured" in providers[key]

    def test_settings_secrets_masked(self, client: TestClient):
        """シークレット値がマスクされている。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        azure = data["providers"]["azure"]
        # APIキーが空文字列またはマスク済み
        api_key = azure["api_key"]
        assert api_key == "" or api_key.startswith("***")

        aws = data["providers"]["aws_bedrock"]
        access_key = aws["access_key_id"]
        assert access_key == "" or access_key.startswith("***")

    def test_settings_validation(self, client: TestClient):
        """バリデーション結果が含まれる。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        validation = data["validation"]
        assert "is_valid" in validation
        assert "missing" in validation
        assert "warnings" in validation
        assert isinstance(validation["missing"], list)
        assert isinstance(validation["warnings"], list)

    def test_settings_app_config(self, client: TestClient):
        """アプリケーション設定が含まれる。"""
        response = client.get("/api/v1/settings/")
        data = response.json()

        app = data["app"]
        assert "upload_dir" in app
        assert "max_file_size_mb" in app
        assert "cors_origins" in app
        assert isinstance(app["cors_origins"], list)

    def test_get_available_models(self, client: TestClient):
        """モデル一覧エンドポイントが正常に動作する。"""
        response = client.get("/api/v1/settings/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data

        models = data["models"]
        # 全プロバイダーのモデルが含まれる
        assert "azure" in models
        assert "aws_bedrock" in models
        assert "gcp_vertex" in models
        assert "local" in models

    def test_models_have_tier_info(self, client: TestClient):
        """モデルにティア情報が含まれる。"""
        response = client.get("/api/v1/settings/models")
        data = response.json()

        # Azureのモデルを確認
        azure_models = data["models"]["azure"]
        assert len(azure_models) > 0

        for model in azure_models:
            assert "tier" in model
            assert "model" in model
            assert model["tier"] in ["precision", "balanced", "cost_effective"]
