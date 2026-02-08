"""
Enterprise feature tests.

サーキットブレーカー、メトリクス、セキュリティヘッダー、
相関ID、レート制限のテスト。
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.core.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerOpenError
from app.core.observability.correlation import CorrelationContext
from app.core.observability.metrics import get_metrics_text, REGISTRY
from app.core.security.rate_limiter import RateLimiter, RateLimitConfig


client = TestClient(app)


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

class TestCircuitBreaker:
    """サーキットブレーカーのテスト"""

    def _make_breaker(self, name, failure_threshold=5, recovery_timeout=60):
        """テスト用サーキットブレーカーを作成"""
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        return CircuitBreaker(name, config=config)

    def test_initial_state_is_closed(self):
        """初期状態がCLOSEDであること"""
        cb = self._make_breaker("test_init", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_successful_call(self):
        """成功した呼び出しでCLOSEDのままであること"""
        cb = self._make_breaker("test_success_cb", failure_threshold=3)

        async def success_func():
            return "ok"

        result = asyncio.get_event_loop().run_until_complete(cb.call(success_func))
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_failure_increments_count(self):
        """失敗がカウントされること"""
        cb = self._make_breaker("test_fail_cb", failure_threshold=3)

        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            asyncio.get_event_loop().run_until_complete(cb.call(fail_func))

        status = cb.get_status()
        assert status["failure_count"] == 1
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        """失敗が閾値に達するとOPENになること"""
        cb = self._make_breaker("test_open_cb", failure_threshold=2, recovery_timeout=60)

        async def fail_func():
            raise ValueError("test error")

        for _ in range(2):
            with pytest.raises(ValueError):
                asyncio.get_event_loop().run_until_complete(cb.call(fail_func))

        assert cb.state == CircuitState.OPEN

    def test_open_rejects_calls(self):
        """OPEN状態で呼び出しが拒否されること"""
        cb = self._make_breaker("test_reject_cb", failure_threshold=1, recovery_timeout=60)

        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            asyncio.get_event_loop().run_until_complete(cb.call(fail_func))

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            asyncio.get_event_loop().run_until_complete(cb.call(fail_func))

    def test_get_status(self):
        """ステータスが正しく取得できること"""
        cb = self._make_breaker("test_status_cb", failure_threshold=5)
        status = cb.get_status()
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert "stats" in status
        assert status["stats"]["total_calls"] == 0

    def test_manual_reset(self):
        """手動リセットが動作すること"""
        cb = self._make_breaker("test_reset_cb", failure_threshold=1, recovery_timeout=60)

        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            asyncio.get_event_loop().run_until_complete(cb.call(fail_func))

        assert cb.state == CircuitState.OPEN
        asyncio.get_event_loop().run_until_complete(cb.reset())
        assert cb.state == CircuitState.CLOSED


# =============================================================================
# Correlation ID Tests
# =============================================================================

class TestCorrelationContext:
    """相関IDコンテキストのテスト"""

    def test_generate_id(self):
        """IDが生成されること"""
        cid = CorrelationContext.generate_id()
        assert cid
        assert len(cid) == 36  # UUID format

    def test_get_correlation_id_auto_generates(self):
        """未設定時に自動生成されること"""
        CorrelationContext.clear()
        cid = CorrelationContext.get_correlation_id()
        assert cid
        assert len(cid) == 36

    def test_set_and_get_correlation_id(self):
        """設定と取得が正しく動作すること"""
        CorrelationContext.set_correlation_id("test-123")
        assert CorrelationContext.get_correlation_id() == "test-123"
        CorrelationContext.clear()

    def test_set_from_request(self):
        """リクエスト情報から設定できること"""
        CorrelationContext.set_from_request(
            request_id="req-456",
            user="user1",
            session="sess-789",
            ip="192.168.1.1",
        )
        assert CorrelationContext.get_correlation_id() == "req-456"
        assert CorrelationContext.get_user_id() == "user1"
        assert CorrelationContext.get_session_id() == "sess-789"
        assert CorrelationContext.get_client_ip() == "192.168.1.1"
        CorrelationContext.clear()

    def test_clear(self):
        """クリアが正しく動作すること"""
        CorrelationContext.set_from_request("req-1", "user1", "sess1", "1.1.1.1")
        CorrelationContext.clear()
        assert CorrelationContext.get_user_id() is None
        assert CorrelationContext.get_session_id() is None
        assert CorrelationContext.get_client_ip() is None

    def test_get_context_dict(self):
        """辞書形式で取得できること"""
        CorrelationContext.set_from_request("req-dict", "user-dict")
        ctx = CorrelationContext.get_context_dict()
        assert ctx["correlation_id"] == "req-dict"
        assert ctx["user_id"] == "user-dict"
        CorrelationContext.clear()

    def test_short_id(self):
        """短縮IDが8文字であること"""
        CorrelationContext.set_correlation_id("12345678-long-id-here")
        assert CorrelationContext.get_short_id() == "12345678"
        CorrelationContext.clear()


# =============================================================================
# Rate Limiter Tests
# =============================================================================

class TestRateLimiter:
    """レート制限のテスト"""

    def test_rate_limit_config(self):
        """レート制限設定が正しいこと"""
        config = RateLimitConfig(requests=10, window_seconds=60)
        assert config.requests == 10
        assert config.window_seconds == 60
        assert config.burst == 10  # デフォルトはrequestsと同じ

    def test_rate_limit_config_with_burst(self):
        """バースト設定が反映されること"""
        config = RateLimitConfig(requests=10, window_seconds=60, burst=20)
        assert config.burst == 20

    def test_rate_limiter_stats(self):
        """統計情報が取得できること"""
        limiter = RateLimiter()
        stats = limiter.get_stats()
        assert "total_keys" in stats
        assert "configs" in stats


# =============================================================================
# Health Check Endpoint Tests
# =============================================================================

class TestHealthEndpoints:
    """ヘルスチェックエンドポイントのテスト"""

    def test_liveness_probe(self):
        """/health/liveが200を返すこと"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_probe(self):
        """/health/readyが200を返すこと"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data

    def test_detailed_health(self):
        """/health/detailedが詳細情報を返すこと"""
        response = client.get("/health/detailed")
        # LLM未設定時はunhealthyで503になる可能性がある
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "circuit_breakers" in data
        assert "configuration" in data
        assert "version" in data

    def test_system_info(self):
        """/api/v1/system/infoがシステム情報を返すこと"""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "規程レビューツール"
        assert "llm_provider" in data


# =============================================================================
# Metrics Endpoint Tests
# =============================================================================

class TestMetricsEndpoint:
    """メトリクスエンドポイントのテスト"""

    def test_metrics_endpoint(self):
        """/metricsがPrometheus形式で返すこと"""
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Prometheus形式のメトリクスが含まれていること
        assert "app_info" in content or "HELP" in content


# =============================================================================
# Security Headers Tests
# =============================================================================

class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""

    def test_xss_protection_header(self):
        """X-XSS-Protectionヘッダーが設定されていること"""
        response = client.get("/health")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    def test_content_type_options_header(self):
        """X-Content-Type-Optionsヘッダーが設定されていること"""
        response = client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_frame_options_header(self):
        """X-Frame-Optionsヘッダーが設定されていること"""
        response = client.get("/health")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy_header(self):
        """Referrer-Policyヘッダーが設定されていること"""
        response = client.get("/health")
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# =============================================================================
# Correlation ID Middleware Tests
# =============================================================================

class TestCorrelationMiddleware:
    """相関IDミドルウェアのテスト"""

    def test_correlation_id_in_response(self):
        """レスポンスにX-Correlation-IDが含まれること"""
        response = client.get("/health")
        assert "x-correlation-id" in response.headers

    def test_custom_request_id_propagated(self):
        """X-Request-IDが伝搬されること"""
        response = client.get("/health", headers={
            "X-Request-ID": "custom-request-123",
        })
        assert response.headers.get("x-correlation-id") == "custom-request-123"

    def test_custom_correlation_id_propagated(self):
        """X-Correlation-IDが伝搬されること"""
        response = client.get("/health", headers={
            "X-Correlation-ID": "custom-corr-456",
        })
        assert response.headers.get("x-correlation-id") == "custom-corr-456"
