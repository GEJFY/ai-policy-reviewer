"""
Circuit breaker pattern for external service protection.

外部サービス保護のためのサーキットブレーカーパターン。
障害の連鎖を防ぎ、システムの安定性を維持。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

from app.core.observability.metrics import (
    CIRCUIT_BREAKER_STATE,
    CIRCUIT_BREAKER_FAILURES,
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """サーキットブレーカーの状態"""

    CLOSED = "closed"  # 正常動作中
    OPEN = "open"  # 障害検出、リクエスト拒否
    HALF_OPEN = "half_open"  # 回復テスト中


class CircuitBreakerOpenError(Exception):
    """サーキットブレーカーが開いている場合のエラー"""

    def __init__(self, name: str, retry_after: int):
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{name}' is open. Retry after {retry_after} seconds."
        )


@dataclass
class CircuitBreakerConfig:
    """サーキットブレーカーの設定"""

    failure_threshold: int = 5  # 障害しきい値
    success_threshold: int = 3  # 回復に必要な成功回数
    recovery_timeout: int = 60  # 回復待機時間（秒）
    half_open_max_calls: int = 3  # HALF_OPEN状態での最大呼び出し数


@dataclass
class CircuitBreakerStats:
    """サーキットブレーカーの統計情報"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    サーキットブレーカー実装。

    状態遷移:
    - CLOSED: 正常動作。障害がfailure_threshold回連続で発生するとOPENへ
    - OPEN: リクエスト拒否。recovery_timeout後にHALF_OPENへ
    - HALF_OPEN: 回復テスト。success_threshold回成功でCLOSED、失敗でOPEN
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        サーキットブレーカーを初期化。

        Args:
            name: ブレーカー名（ログ・メトリクス用）
            config: 設定（Noneの場合デフォルト使用）
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[datetime] = None

        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

        # メトリクス初期化
        self._update_metrics()

    @property
    def state(self) -> CircuitState:
        """現在の状態を取得。"""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """統計情報を取得。"""
        return self._stats

    def _update_metrics(self) -> None:
        """Prometheusメトリクスを更新。"""
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2,
        }
        CIRCUIT_BREAKER_STATE.labels(service=self.name).set(state_value[self._state])

    def _should_attempt_reset(self) -> bool:
        """回復を試みるべきか判定。"""
        if self._last_failure_time is None:
            return True

        elapsed = datetime.now() - self._last_failure_time
        return elapsed >= timedelta(seconds=self.config.recovery_timeout)

    def _time_until_retry(self) -> int:
        """リトライまでの残り秒数を計算。"""
        if self._last_failure_time is None:
            return 0

        elapsed = datetime.now() - self._last_failure_time
        remaining = self.config.recovery_timeout - elapsed.total_seconds()
        return max(0, int(remaining))

    async def _transition_to(self, new_state: CircuitState) -> None:
        """状態を遷移。"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats.state_changes += 1
            self._update_metrics()

            logger.info(
                f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}"
            )

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        サーキットブレーカーを通して関数を呼び出す。

        Args:
            func: 呼び出す関数（async関数）
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            関数の戻り値

        Raises:
            CircuitBreakerOpenError: ブレーカーがOPEN状態
        """
        async with self._lock:
            self._stats.total_calls += 1

            # OPEN状態のチェック
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    await self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
                    self._success_count = 0
                else:
                    self._stats.rejected_calls += 1
                    raise CircuitBreakerOpenError(self.name, self._time_until_retry())

            # HALF_OPEN状態での呼び出し制限
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._stats.rejected_calls += 1
                    raise CircuitBreakerOpenError(self.name, self._time_until_retry())
                self._half_open_calls += 1

        # 関数を実行
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self) -> None:
        """成功時の処理。"""
        async with self._lock:
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0
                    self._success_count = 0
            else:
                # CLOSED状態での成功は失敗カウントをリセット
                self._failure_count = 0

    async def _on_failure(self, error: Exception) -> None:
        """失敗時の処理。"""
        async with self._lock:
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.now()
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            CIRCUIT_BREAKER_FAILURES.labels(service=self.name).inc()

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure "
                f"({self._failure_count}/{self.config.failure_threshold}): {str(error)[:100]}"
            )

            if self._state == CircuitState.HALF_OPEN:
                # HALF_OPEN中の失敗は即座にOPENへ
                await self._transition_to(CircuitState.OPEN)
            elif self._failure_count >= self.config.failure_threshold:
                # しきい値超過でOPENへ
                await self._transition_to(CircuitState.OPEN)

    async def reset(self) -> None:
        """ブレーカーを手動でリセット。"""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_status(self) -> Dict[str, Any]:
        """ステータス情報を取得。"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "recovery_timeout": self.config.recovery_timeout,
            },
            "stats": {
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "rejected_calls": self._stats.rejected_calls,
                "state_changes": self._stats.state_changes,
            },
            "time_until_retry": (
                self._time_until_retry() if self._state == CircuitState.OPEN else 0
            ),
        }


# =============================================================================
# 各サービス用のサーキットブレーカーインスタンス
# =============================================================================

azure_openai_breaker = CircuitBreaker(
    "azure_openai",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        recovery_timeout=60,
    ),
)

aws_bedrock_breaker = CircuitBreaker(
    "aws_bedrock",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        recovery_timeout=60,
    ),
)

gcp_vertex_breaker = CircuitBreaker(
    "gcp_vertex",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        recovery_timeout=60,
    ),
)

azure_doc_intel_breaker = CircuitBreaker(
    "azure_doc_intel",
    CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        recovery_timeout=30,
    ),
)

ollama_breaker = CircuitBreaker(
    "ollama",
    CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        recovery_timeout=15,  # ローカルなので短い回復タイムアウト
    ),
)

tesseract_breaker = CircuitBreaker(
    "tesseract",
    CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        recovery_timeout=10,
    ),
)


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    """全てのサーキットブレーカーを取得。"""
    return {
        "azure_openai": azure_openai_breaker,
        "aws_bedrock": aws_bedrock_breaker,
        "gcp_vertex": gcp_vertex_breaker,
        "azure_doc_intel": azure_doc_intel_breaker,
        "ollama": ollama_breaker,
        "tesseract": tesseract_breaker,
    }
