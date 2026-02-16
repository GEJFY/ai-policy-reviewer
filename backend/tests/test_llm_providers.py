"""
LLMプロバイダー接続テスト

マルチクラウドLLMプロバイダー（Azure, AWS Bedrock, GCP Vertex AI, Local/Ollama）の
接続と基本機能をテストする。

使用方法:
    pytest tests/test_llm_providers.py -v
    pytest tests/test_llm_providers.py -v -k azure
    pytest tests/test_llm_providers.py -v -k bedrock
    pytest tests/test_llm_providers.py -v -k vertex
    pytest tests/test_llm_providers.py -v -k ollama
    pytest tests/test_llm_providers.py -v -k tier
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings, LLMProvider, ModelTier, MODEL_TIER_DEFAULTS
from app.services.llm_service import (
    UnifiedLLMService,
    AzureOpenAIClient,
    AWSBedrockClient,
    GCPVertexClient,
    OllamaClient,
    LLMResponse,
)


class TestLLMProviderConfiguration:
    """LLMプロバイダー設定のテスト"""

    def test_llm_provider_enum(self):
        """LLMProviderのenum値をテスト"""
        assert LLMProvider.AZURE.value == "azure"
        assert LLMProvider.AWS_BEDROCK.value == "aws_bedrock"
        assert LLMProvider.GCP_VERTEX.value == "gcp_vertex"
        assert LLMProvider.LOCAL.value == "local"

    def test_settings_default_provider(self):
        """デフォルトプロバイダーの設定をテスト"""
        assert settings.llm_provider == LLMProvider.AZURE

    def test_settings_available_providers(self):
        """利用可能なプロバイダーの取得をテスト"""
        providers = settings.get_available_providers()
        assert isinstance(providers, list)

    def test_is_azure_configured_method(self):
        """is_azure_configuredメソッドのテスト"""
        result = settings.is_azure_configured()
        assert isinstance(result, bool)

    def test_is_bedrock_configured_method(self):
        """is_bedrock_configuredメソッドのテスト"""
        result = settings.is_bedrock_configured()
        assert isinstance(result, bool)

    def test_is_vertex_configured_method(self):
        """is_vertex_configuredメソッドのテスト"""
        result = settings.is_vertex_configured()
        assert isinstance(result, bool)


class TestAzureOpenAIClient:
    """Azure OpenAI クライアントのテスト"""

    def test_client_is_available_method(self):
        """is_available メソッドのテスト"""
        client = AzureOpenAIClient()
        result = client.is_available()
        # 設定によってTrue/Falseが変わる
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_client_generate_mock(self):
        """モックを使用した生成テスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"findings": []}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_openai = MagicMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        # クライアントを作成してモックを設定
        client = AzureOpenAIClient()
        client.client = mock_openai
        client.deployment = "gpt-5-2"

        messages = [{"role": "user", "content": "Hello"}]
        response = await client.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.provider == "azure"
        assert response.content == '{"findings": []}'
        assert response.usage["total_tokens"] == 150


class TestAWSBedrockClient:
    """AWS Bedrock クライアントのテスト"""

    def test_client_is_available_method(self):
        """is_available メソッドのテスト"""
        client = AWSBedrockClient()
        result = client.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_client_generate_mock(self):
        """モックを使用した生成テスト"""
        with patch("boto3.client") as mock_boto:
            # モックレスポンスを設定
            response_body = {
                "content": [{"text": '{"findings": []}'}],
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }
            mock_body = MagicMock()
            mock_body.read.return_value = json.dumps(response_body).encode()
            mock_response = {"body": mock_body}
            mock_boto.return_value.invoke_model.return_value = mock_response

            client = AWSBedrockClient()
            client.client = mock_boto.return_value
            client.model_id = "anthropic.claude-sonnet-4-6"

            messages = [{"role": "user", "content": "Hello"}]
            response = await client.generate(messages)

            assert isinstance(response, LLMResponse)
            assert response.provider == "aws_bedrock"
            assert response.content == '{"findings": []}'
            assert response.usage["total_tokens"] == 150


class TestGCPVertexClient:
    """GCP Vertex AI クライアントのテスト"""

    def test_client_is_available_method(self):
        """is_available メソッドのテスト"""
        client = GCPVertexClient()
        result = client.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_client_generate_mock(self):
        """モックを使用した生成テスト"""
        with patch("vertexai.init"):
            with patch(
                "vertexai.generative_models.GenerativeModel"
            ) as mock_model_class:
                with patch("vertexai.generative_models.GenerationConfig"):
                    # モックレスポンスを設定
                    mock_response = MagicMock()
                    mock_response.text = '{"findings": []}'
                    mock_response.usage_metadata = MagicMock()
                    mock_response.usage_metadata.prompt_token_count = 100
                    mock_response.usage_metadata.candidates_token_count = 50
                    mock_model_class.return_value.generate_content.return_value = (
                        mock_response
                    )

                    client = GCPVertexClient()
                    client.model = mock_model_class.return_value
                    client.model_name = "gemini-3.0-flash-preview"

                    messages = [{"role": "user", "content": "Hello"}]
                    response = await client.generate(messages)

                    assert isinstance(response, LLMResponse)
                    assert response.provider == "gcp_vertex"
                    assert response.content == '{"findings": []}'


class TestUnifiedLLMService:
    """統合LLMサービスのテスト"""

    def test_service_initialization(self):
        """サービス初期化のテスト"""
        service = UnifiedLLMService()
        providers = service.get_available_providers()
        assert isinstance(providers, list)

    def test_is_available_method(self):
        """is_availableメソッドのテスト"""
        service = UnifiedLLMService()
        result = service.is_available()
        assert isinstance(result, bool)

    def test_set_provider_available(self):
        """利用可能なプロバイダーへの切り替えテスト"""
        service = UnifiedLLMService()

        if service.get_available_providers():
            provider = service.get_available_providers()[0]
            result = service.set_provider(provider)
            assert result is True
            assert service.active_provider == provider

    def test_set_provider_unavailable(self):
        """利用不可のプロバイダーへの切り替えテスト"""
        service = UnifiedLLMService()

        # クライアントを空にして、切り替え失敗をテスト
        service.clients = {}
        result = service.set_provider(LLMProvider.AZURE)
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_with_mock(self):
        """モックを使用した生成テスト"""
        service = UnifiedLLMService()

        # モッククライアントを作成
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_response = LLMResponse(
            content='{"findings": []}',
            model="test-model",
            provider="azure",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_client.generate = AsyncMock(return_value=mock_response)

        service.clients[LLMProvider.AZURE] = mock_client
        service.active_provider = LLMProvider.AZURE

        messages = [{"role": "user", "content": "Test message"}]
        response = await service.generate(messages)

        assert response.content == '{"findings": []}'
        assert response.provider == "azure"
        assert response.usage["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_generate_no_provider_raises(self):
        """プロバイダーなしでの生成でエラーをテスト"""
        service = UnifiedLLMService()
        service.clients = {}
        service.active_provider = None

        with pytest.raises(RuntimeError):
            await service.generate([{"role": "user", "content": "Test"}])


class TestLLMProviderConnectionIntegration:
    """
    LLMプロバイダー接続の統合テスト

    注意: これらのテストは実際のAPI呼び出しを行うため、
    適切な環境変数が設定されている場合のみ実行される。
    """

    @pytest.mark.skipif(
        not settings.is_azure_configured(), reason="Azure OpenAI not configured"
    )
    @pytest.mark.asyncio
    async def test_azure_connection(self):
        """Azure OpenAI接続テスト"""
        client = AzureOpenAIClient()
        assert client.is_available()

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": 'Say \'connection test successful\' in JSON format: {"status": "..."}',
            },
        ]

        response = await client.generate(messages, max_tokens=100)
        assert response.provider == "azure"
        assert "status" in response.content or "successful" in response.content.lower()
        print(f"Azure response: {response.content}")

    @pytest.mark.skipif(
        not settings.is_bedrock_configured(), reason="AWS Bedrock not configured"
    )
    @pytest.mark.asyncio
    async def test_bedrock_connection(self):
        """AWS Bedrock接続テスト"""
        client = AWSBedrockClient()
        assert client.is_available()

        messages = [
            {
                "role": "user",
                "content": 'Say \'connection test successful\' in JSON format: {"status": "..."}',
            }
        ]

        response = await client.generate(messages, max_tokens=100)
        assert response.provider == "aws_bedrock"
        assert "status" in response.content or "successful" in response.content.lower()
        print(f"Bedrock response: {response.content}")

    @pytest.mark.skipif(
        not settings.is_vertex_configured(), reason="GCP Vertex AI not configured"
    )
    @pytest.mark.asyncio
    async def test_vertex_connection(self):
        """GCP Vertex AI接続テスト"""
        client = GCPVertexClient()
        if not client.is_available():
            pytest.skip("GCP Vertex AI client not available (region/credential issue)")

        messages = [
            {
                "role": "user",
                "content": 'Say \'connection test successful\' in JSON format: {"status": "..."}',
            }
        ]

        response = await client.generate(messages, max_tokens=100)
        assert response.provider == "gcp_vertex"
        assert "status" in response.content or "successful" in response.content.lower()
        print(f"Vertex AI response: {response.content}")


class TestLLMResponse:
    """LLMResponseデータクラスのテスト"""

    def test_llm_response_creation(self):
        """LLMResponseの作成をテスト"""
        response = LLMResponse(
            content='{"test": true}',
            model="gpt-5.2",
            provider="azure",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

        assert response.content == '{"test": true}'
        assert response.model == "gpt-5.2"
        assert response.provider == "azure"
        assert response.usage["total_tokens"] == 15

    def test_llm_response_with_raw(self):
        """raw_response付きLLMResponseのテスト"""
        raw = {"raw": "data"}
        response = LLMResponse(
            content="test",
            model="test-model",
            provider="test",
            usage={},
            raw_response=raw,
        )

        assert response.raw_response == raw

    def test_llm_response_default_raw(self):
        """デフォルトraw_responseのテスト"""
        response = LLMResponse(
            content="test", model="test-model", provider="test", usage={}
        )

        assert response.raw_response is None


class TestRetryLogic:
    """リトライロジックのテスト"""

    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """正常なLLM呼び出しのテスト"""
        service = UnifiedLLMService()

        mock_response = LLMResponse(
            content='{"result": "success"}',
            model="test",
            provider="azure",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.generate = AsyncMock(return_value=mock_response)

        service.clients[LLMProvider.AZURE] = mock_client
        service.active_provider = LLMProvider.AZURE

        response = await service.generate([{"role": "user", "content": "test"}])
        assert response.content == '{"result": "success"}'
        assert response.usage["total_tokens"] == 15


class TestOllamaClient:
    """Ollama (Local LLM) クライアントのテスト"""

    def test_client_is_available_method(self):
        """is_available メソッドのテスト"""
        client = OllamaClient()
        result = client.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_client_generate_mock(self):
        """モックを使用した生成テスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"findings": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80
        mock_response.model = "qwen2.5:3b"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OllamaClient()
        client.client = mock_openai
        client.model_name = "qwen2.5:3b"

        messages = [{"role": "user", "content": "Hello"}]
        response = await client.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.provider == "local"
        assert response.content == '{"findings": []}'
        assert response.usage["total_tokens"] == 80

    @pytest.mark.asyncio
    async def test_client_generate_no_usage(self):
        """usage情報がないモデルのレスポンステスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Ollama"
        mock_response.usage = None
        mock_response.model = "gemma-2-2b-jpn-it"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OllamaClient()
        client.client = mock_openai
        client.model_name = "gemma-2-2b-jpn-it"

        messages = [{"role": "user", "content": "Hello"}]
        response = await client.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.provider == "local"
        assert response.usage["total_tokens"] == 0


class TestModelTierSelection:
    """モデルティア選択のテスト"""

    def test_model_tier_enum(self):
        """ModelTierのenum値をテスト"""
        assert ModelTier.PRECISION.value == "precision"
        assert ModelTier.BALANCED.value == "balanced"
        assert ModelTier.COST_EFFECTIVE.value == "cost_effective"

    def test_model_tier_defaults_structure(self):
        """MODEL_TIER_DEFAULTSの構造をテスト"""
        # 全プロバイダーが含まれること
        assert LLMProvider.AZURE in MODEL_TIER_DEFAULTS
        assert LLMProvider.AWS_BEDROCK in MODEL_TIER_DEFAULTS
        assert LLMProvider.GCP_VERTEX in MODEL_TIER_DEFAULTS
        assert LLMProvider.LOCAL in MODEL_TIER_DEFAULTS

        # 各プロバイダーが全ティアを持つこと
        for provider in LLMProvider:
            tier_map = MODEL_TIER_DEFAULTS[provider]
            assert ModelTier.PRECISION in tier_map
            assert ModelTier.BALANCED in tier_map
            assert ModelTier.COST_EFFECTIVE in tier_map

    def test_model_tier_defaults_values(self):
        """各プロバイダーのデフォルトモデル値をテスト"""
        # Azure
        assert MODEL_TIER_DEFAULTS[LLMProvider.AZURE][ModelTier.PRECISION] == "gpt-5.2"

        # AWS Bedrock
        assert (
            "claude-opus"
            in MODEL_TIER_DEFAULTS[LLMProvider.AWS_BEDROCK][ModelTier.PRECISION]
        )

        # GCP Vertex
        assert (
            "gemini-3"
            in MODEL_TIER_DEFAULTS[LLMProvider.GCP_VERTEX][ModelTier.PRECISION]
        )

        # Local
        assert "qwen" in MODEL_TIER_DEFAULTS[LLMProvider.LOCAL][ModelTier.BALANCED]

    def test_get_effective_model_without_tier(self):
        """ティア未指定時はプロバイダー固有の設定値が返ること"""
        result = settings.get_effective_model()
        # ティア未設定ならプロバイダー固有の設定値
        if settings.llm_tier is None:
            assert result == settings.get_effective_model(settings.llm_provider)

    def test_get_effective_model_per_provider(self):
        """各プロバイダーのget_effective_modelが正しいモデルを返すこと"""
        # ティア未設定時: プロバイダー固有設定値
        if settings.llm_tier is None:
            assert (
                settings.get_effective_model(LLMProvider.AZURE)
                == settings.azure_openai_deployment
            )
            assert (
                settings.get_effective_model(LLMProvider.AWS_BEDROCK)
                == settings.aws_bedrock_model_id
            )
            assert (
                settings.get_effective_model(LLMProvider.GCP_VERTEX)
                == settings.gcp_vertex_model
            )
            assert (
                settings.get_effective_model(LLMProvider.LOCAL) == settings.ollama_model
            )

    def test_is_ollama_configured(self):
        """Ollama設定チェックのテスト"""
        result = settings.is_ollama_configured()
        assert isinstance(result, bool)
        # デフォルトでollama_base_urlが設定されているのでTrue
        assert result is True


class TestOllamaConnectionIntegration:
    """
    Ollama接続の統合テスト

    注意: Ollamaが起動中でモデルがpull済みの場合のみ実行。
    """

    @pytest.mark.skipif(
        not settings.is_ollama_configured(), reason="Ollama not configured"
    )
    @pytest.mark.asyncio
    async def test_ollama_connection(self):
        """Ollama接続テスト（qwen2.5:3bを使用）"""
        client = OllamaClient()
        # テスト用にpull済みのモデルを明示指定
        client.model_name = "qwen2.5:3b"

        if not client.is_available():
            pytest.skip("Ollama server not running")

        messages = [
            {
                "role": "user",
                "content": "Say 'hello' in Japanese. Reply with only the word.",
            }
        ]

        try:
            response = await client.generate(messages, max_tokens=50)
        except Exception as e:
            err_msg = str(e).lower()
            if any(
                kw in err_msg
                for kw in ["not found", "connection", "memory", "500"]
            ):
                pytest.skip(f"Ollama not available: {e}")
            raise

        assert response.provider == "local"
        assert len(response.content) > 0
        print(f"Ollama response: {response.content}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
