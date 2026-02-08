"""
Resilience module for fault tolerance and graceful degradation.

耐障害性モジュール：サーキットブレーカー、リトライ、フォールバックを提供。
"""

from app.core.resilience.circuit_breaker import (
    CircuitState,
    CircuitBreaker,
    CircuitBreakerOpenError,
    azure_openai_breaker,
    aws_bedrock_breaker,
    gcp_vertex_breaker,
    azure_doc_intel_breaker,
    get_all_breakers,
)

__all__ = [
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "azure_openai_breaker",
    "aws_bedrock_breaker",
    "gcp_vertex_breaker",
    "azure_doc_intel_breaker",
    "get_all_breakers",
]
