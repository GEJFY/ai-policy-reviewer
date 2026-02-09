"""
Prometheus metrics for application monitoring.

アプリケーション監視用のPrometheusメトリクス。
リクエスト、LLM使用量、レビュー処理などを計測。
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from typing import Tuple

# カスタムレジストリ（デフォルトメトリクスを除外可能）
REGISTRY = CollectorRegistry(auto_describe=True)


# =============================================================================
# HTTPリクエストメトリクス
# =============================================================================

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=REGISTRY,
)


# =============================================================================
# LLMメトリクス
# =============================================================================

LLM_REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "status"],
    registry=REGISTRY,
)

LLM_TOKEN_USAGE = Counter(
    "llm_tokens_total",
    "Total tokens used in LLM requests",
    ["provider", "type"],  # type: prompt/completion
    registry=REGISTRY,
)

LLM_LATENCY = Histogram(
    "llm_request_duration_seconds",
    "LLM request latency in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY,
)

LLM_ERRORS = Counter(
    "llm_errors_total",
    "Total LLM API errors",
    ["provider", "error_type"],
    registry=REGISTRY,
)


# =============================================================================
# レビュー処理メトリクス
# =============================================================================

REVIEW_DURATION = Histogram(
    "review_duration_seconds",
    "Document review duration in seconds",
    ["check_category"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=REGISTRY,
)

ACTIVE_REVIEWS = Gauge(
    "active_reviews",
    "Number of currently processing reviews",
    registry=REGISTRY,
)

REVIEW_FINDINGS = Counter(
    "review_findings_total",
    "Total review findings generated",
    ["severity", "category"],
    registry=REGISTRY,
)

DOCUMENTS_PROCESSED = Counter(
    "documents_processed_total",
    "Total documents processed",
    ["status"],  # success/failed
    registry=REGISTRY,
)


# =============================================================================
# サーキットブレーカーメトリクス
# =============================================================================

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
    registry=REGISTRY,
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
    registry=REGISTRY,
)


# =============================================================================
# データベースメトリクス
# =============================================================================

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],  # select/insert/update/delete
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=REGISTRY,
)

DB_CONNECTIONS = Gauge(
    "db_connections",
    "Number of database connections",
    ["state"],  # active/idle
    registry=REGISTRY,
)


# =============================================================================
# アプリケーション情報
# =============================================================================

APP_INFO = Info(
    "app",
    "Application information",
    registry=REGISTRY,
)


def set_app_info(version: str, environment: str, llm_provider: str) -> None:
    """アプリケーション情報を設定。"""
    APP_INFO.info(
        {
            "version": version,
            "environment": environment,
            "llm_provider": llm_provider,
        }
    )


# =============================================================================
# メトリクス取得
# =============================================================================


def get_metrics() -> Tuple[bytes, str]:
    """
    Prometheusフォーマットでメトリクスを取得。

    Returns:
        Tuple[bytes, str]: (メトリクスデータ, Content-Type)
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


def get_metrics_text() -> str:
    """メトリクスをテキスト形式で取得。"""
    return generate_latest(REGISTRY).decode("utf-8")
