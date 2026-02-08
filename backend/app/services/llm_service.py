"""
Unified LLM Service for multi-cloud support.

マルチクラウドLLMプロバイダーを統合するサービス。
Azure Foundry, AWS Bedrock, GCP Vertex AIに対応。

対応モデル:
    Azure Foundry:
        - GPT-5.2, GPT-5-nano
        - Claude Sonnet 4, Claude Opus 4
    AWS Bedrock:
        - Claude Sonnet 4.6, Claude Opus 4
    GCP Vertex AI:
        - Gemini 3.0 Flash Preview
        - Gemini 3.0 Pro Preview
"""

import json
import time
import random
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from app.config import settings, LLMProvider
from app.core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    azure_openai_breaker,
    aws_bedrock_breaker,
    gcp_vertex_breaker,
)
from app.core.observability.metrics import LLM_TOKEN_USAGE, LLM_REQUEST_COUNT, LLM_LATENCY, LLM_ERRORS

logger = logging.getLogger(__name__)


# リトライ設定
MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 30.0
JITTER_FACTOR = 0.1


@dataclass
class LLMResponse:
    """LLMレスポンスの標準化されたデータクラス"""
    content: str
    model: str
    provider: str
    usage: dict
    raw_response: Any = None


class BaseLLMClient(ABC):
    """LLMクライアントの抽象基底クラス"""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        json_mode: bool = True,
    ) -> LLMResponse:
        """メッセージを送信してレスポンスを取得"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """クライアントが利用可能かチェック"""
        pass


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI / Foundry クライアント"""

    def __init__(self):
        self.client = None
        self.deployment = settings.azure_openai_deployment
        self._initialize()

    def _initialize(self):
        """Azure OpenAIクライアントを初期化"""
        if not settings.is_azure_configured():
            logger.warning("Azure OpenAI not configured")
            return

        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version="2024-10-21",
            )
            logger.info(f"Azure OpenAI client initialized | deployment={self.deployment}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI | error={e}")

    def is_available(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        json_mode: bool = True,
    ) -> LLMResponse:
        if not self.client:
            raise RuntimeError("Azure OpenAI client not initialized")

        response_format = {"type": "json_object"} if json_mode else None

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.deployment,
            provider="azure",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response,
        )


class AWSBedrockClient(BaseLLMClient):
    """AWS Bedrock クライアント (Claude Sonnet 4.6, Opus)"""

    def __init__(self):
        self.client = None
        self.model_id = settings.aws_bedrock_model_id
        self._initialize()

    def _initialize(self):
        """AWS Bedrockクライアントを初期化"""
        if not settings.is_bedrock_configured():
            logger.warning("AWS Bedrock not configured")
            return

        try:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info(f"AWS Bedrock client initialized | model={self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock | error={e}")

    def is_available(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        json_mode: bool = True,
    ) -> LLMResponse:
        if not self.client:
            raise RuntimeError("AWS Bedrock client not initialized")

        # Claude用のメッセージフォーマット変換
        # システムメッセージを分離
        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}]
                })

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }

        if system_message:
            body["system"] = system_message

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]

        return LLMResponse(
            content=content,
            model=self.model_id,
            provider="aws_bedrock",
            usage={
                "prompt_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_body.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    response_body.get("usage", {}).get("input_tokens", 0) +
                    response_body.get("usage", {}).get("output_tokens", 0)
                ),
            },
            raw_response=response_body,
        )


class GCPVertexClient(BaseLLMClient):
    """GCP Vertex AI クライアント (Gemini 3.0 Flash/Pro Preview)"""

    def __init__(self):
        self.model = None
        self.model_name = settings.gcp_vertex_model
        self._initialize()

    def _initialize(self):
        """GCP Vertex AIクライアントを初期化"""
        if not settings.is_vertex_configured():
            logger.warning("GCP Vertex AI not configured")
            return

        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            # 認証設定
            if settings.gcp_credentials_path:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_credentials_path

            vertexai.init(
                project=settings.gcp_project_id,
                location=settings.gcp_location,
            )

            self.model = GenerativeModel(self.model_name)
            logger.info(f"GCP Vertex AI client initialized | model={self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCP Vertex AI | error={e}")

    def is_available(self) -> bool:
        return self.model is not None

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        json_mode: bool = True,
    ) -> LLMResponse:
        if not self.model:
            raise RuntimeError("GCP Vertex AI client not initialized")

        from vertexai.generative_models import GenerationConfig

        # メッセージをGemini形式に変換
        # システムメッセージとユーザーメッセージを結合
        combined_prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                combined_prompt += f"System: {content}\n\n"
            elif role == "user":
                combined_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                combined_prompt += f"Assistant: {content}\n\n"

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if json_mode:
            generation_config.response_mime_type = "application/json"

        response = self.model.generate_content(
            combined_prompt,
            generation_config=generation_config,
        )

        # トークン使用量を取得
        usage_metadata = getattr(response, 'usage_metadata', None)
        prompt_tokens = getattr(usage_metadata, 'prompt_token_count', 0) if usage_metadata else 0
        completion_tokens = getattr(usage_metadata, 'candidates_token_count', 0) if usage_metadata else 0

        return LLMResponse(
            content=response.text,
            model=self.model_name,
            provider="gcp_vertex",
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            raw_response=response,
        )


class UnifiedLLMService:
    """
    統合LLMサービス

    複数のLLMプロバイダーを透過的に切り替えて使用できる。
    設定に基づいてアクティブなプロバイダーを自動選択。
    サーキットブレーカーパターンで障害を分離。
    """

    def __init__(self):
        self.clients: dict[LLMProvider, BaseLLMClient] = {}
        self.circuit_breakers: dict[LLMProvider, CircuitBreaker] = {}
        self.active_provider: Optional[LLMProvider] = None
        self._initialize_clients()

    def _initialize_clients(self):
        """全プロバイダーのクライアントを初期化"""
        # Azure
        azure_client = AzureOpenAIClient()
        if azure_client.is_available():
            self.clients[LLMProvider.AZURE] = azure_client
            self.circuit_breakers[LLMProvider.AZURE] = azure_openai_breaker

        # AWS Bedrock
        bedrock_client = AWSBedrockClient()
        if bedrock_client.is_available():
            self.clients[LLMProvider.AWS_BEDROCK] = bedrock_client
            self.circuit_breakers[LLMProvider.AWS_BEDROCK] = aws_bedrock_breaker

        # GCP Vertex AI
        vertex_client = GCPVertexClient()
        if vertex_client.is_available():
            self.clients[LLMProvider.GCP_VERTEX] = vertex_client
            self.circuit_breakers[LLMProvider.GCP_VERTEX] = gcp_vertex_breaker

        # アクティブプロバイダーを設定
        if settings.llm_provider in self.clients:
            self.active_provider = settings.llm_provider
        elif self.clients:
            # 設定されたプロバイダーが利用不可の場合、最初に利用可能なものを使用
            self.active_provider = list(self.clients.keys())[0]
            logger.warning(
                f"Configured provider {settings.llm_provider} not available, "
                f"using {self.active_provider}"
            )

        if self.active_provider:
            logger.info(f"UnifiedLLMService initialized | active_provider={self.active_provider.value}")
        else:
            logger.warning("UnifiedLLMService: No LLM providers available")

    def is_available(self) -> bool:
        """サービスが利用可能かチェック"""
        return self.active_provider is not None

    def get_available_providers(self) -> list[LLMProvider]:
        """利用可能なプロバイダーのリストを返す"""
        return list(self.clients.keys())

    def set_provider(self, provider: LLMProvider) -> bool:
        """アクティブなプロバイダーを切り替え"""
        if provider in self.clients:
            self.active_provider = provider
            logger.info(f"LLM provider switched to {provider.value}")
            return True
        logger.warning(f"Provider {provider.value} not available")
        return False

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        json_mode: bool = True,
        provider: Optional[LLMProvider] = None,
    ) -> LLMResponse:
        """
        LLMを呼び出してレスポンスを取得

        サーキットブレーカーパターンで障害を分離。
        障害が続く場合は自動的にリクエストを拒否。

        Args:
            messages: メッセージリスト
            temperature: 生成温度
            max_tokens: 最大トークン数
            json_mode: JSONモード有効化
            provider: 使用するプロバイダー（Noneの場合アクティブプロバイダー使用）

        Returns:
            LLMResponse: 標準化されたレスポンス

        Raises:
            CircuitBreakerOpenError: サーキットブレーカーが開いている場合
            RuntimeError: プロバイダーが利用不可の場合
        """
        target_provider = provider or self.active_provider
        if not target_provider or target_provider not in self.clients:
            raise RuntimeError(f"LLM provider not available: {target_provider}")

        client = self.clients[target_provider]
        circuit_breaker = self.circuit_breakers.get(target_provider)

        start_time = time.time()

        # サーキットブレーカーを通してLLMを呼び出す
        if circuit_breaker:
            try:
                response = await circuit_breaker.call(
                    self._call_with_retry,
                    client,
                    messages,
                    temperature,
                    max_tokens,
                    json_mode,
                )
            except CircuitBreakerOpenError as e:
                logger.warning(
                    f"Circuit breaker open | provider={target_provider.value} | "
                    f"retry_after={e.retry_after}s"
                )
                # メトリクス記録
                LLM_REQUEST_COUNT.labels(
                    provider=target_provider.value,
                    model="unknown",
                    status="circuit_open",
                ).inc()
                raise
        else:
            response = await self._call_with_retry(
                client, messages, temperature, max_tokens, json_mode
            )

        duration_sec = time.time() - start_time

        # メトリクス記録
        self._record_metrics(target_provider, response, duration_sec)

        return response

    def _record_metrics(
        self,
        provider: LLMProvider,
        response: LLMResponse,
        duration_sec: float = 0.0,
    ) -> None:
        """LLM呼び出しのメトリクスを記録"""
        provider_name = provider.value
        model_name = response.model

        # トークン使用量
        usage = response.usage
        if usage.get("prompt_tokens"):
            LLM_TOKEN_USAGE.labels(provider=provider_name, type="prompt").inc(
                usage["prompt_tokens"]
            )
        if usage.get("completion_tokens"):
            LLM_TOKEN_USAGE.labels(provider=provider_name, type="completion").inc(
                usage["completion_tokens"]
            )

        # リクエストカウント
        LLM_REQUEST_COUNT.labels(
            provider=provider_name,
            model=model_name,
            status="success",
        ).inc()

        # レイテンシ
        if duration_sec > 0:
            LLM_LATENCY.labels(provider=provider_name, model=model_name).observe(duration_sec)

    async def _call_with_retry(
        self,
        client: BaseLLMClient,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> LLMResponse:
        """リトライロジック付きでLLMを呼び出す"""
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            start_time = time.time()

            try:
                response = await client.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )

                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"LLM call completed | provider={response.provider} | "
                    f"model={response.model} | attempt={attempt + 1} | "
                    f"duration_ms={duration_ms:.2f} | tokens={response.usage.get('total_tokens', 0)}"
                )

                return response

            except Exception as e:
                last_error = e
                duration_ms = (time.time() - start_time) * 1000

                # リトライ可能なエラーかチェック
                if self._is_retryable_error(e) and attempt < MAX_RETRIES:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        f"LLM call failed (retrying) | attempt={attempt + 1}/{MAX_RETRIES + 1} | "
                        f"delay_sec={delay:.2f} | error={str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"LLM call failed | duration_ms={duration_ms:.2f} | error={str(e)}"
                    )
                    if attempt >= MAX_RETRIES:
                        raise

        if last_error:
            raise last_error

    def _is_retryable_error(self, error: Exception) -> bool:
        """リトライ可能なエラーかチェック"""
        error_type = type(error).__name__

        # 一般的なリトライ可能エラー
        retryable_errors = [
            "RateLimitError",
            "APIConnectionError",
            "ServiceUnavailableError",
            "InternalServerError",
            "ThrottlingException",  # AWS
            "ResourceExhausted",  # GCP
        ]

        if error_type in retryable_errors:
            return True

        # ステータスコードベースのチェック
        status_code = getattr(error, "status_code", None)
        if status_code and status_code >= 500:
            return True

        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """リトライ待機時間を計算"""
        delay = BASE_DELAY * (2 ** attempt)
        delay = min(delay, MAX_DELAY)
        jitter = delay * JITTER_FACTOR * (2 * random.random() - 1)
        return max(0.1, delay + jitter)


# シングルトンインスタンス
llm_service = UnifiedLLMService()
