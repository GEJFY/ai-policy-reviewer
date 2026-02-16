"""
ログ設定モジュール
本番運用レベルの構造化ログを提供する
"""

import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

# ============================================================
# ログディレクトリの設定
# ============================================================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


# ============================================================
# カスタムフォーマッター
# ============================================================
class JsonFormatter(logging.Formatter):
    """JSON形式のログフォーマッター（本番環境用）"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 例外情報があれば追加
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 追加のコンテキスト情報
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """カラー出力フォーマッター（開発環境用）"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # カラーコードを追加
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


# ============================================================
# ログ設定関数
# ============================================================
def setup_logging(
    level: str = "INFO",
    log_file: Optional[str | Path] = None,
    json_format: bool = False,
) -> None:
    """
    アプリケーション全体のログ設定を行う

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: ログファイルのパス（Noneの場合は自動生成）
        json_format: JSON形式でログを出力するかどうか
    """
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 既存のハンドラーをクリア
    root_logger.handlers.clear()

    # フォーマット設定
    formatter: logging.Formatter
    console_formatter: logging.Formatter
    if json_format:
        formatter = JsonFormatter()
        console_formatter = formatter
    else:
        # 開発環境用のカラーフォーマット
        console_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        console_formatter = ColoredFormatter(
            console_format, datefmt="%Y-%m-%d %H:%M:%S"
        )
        formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    # ファイルハンドラー（ローテーション付き）
    if log_file is None:
        log_file = LOG_DIR / "app.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # エラー専用ログファイル
    error_log_file = LOG_DIR / "error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # SQLAlchemyのログレベルを調整（詳細すぎるため）
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # httpxのログを抑制
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを取得

    Args:
        name: ロガー名（通常は __name__ を使用）

    Returns:
        logging.Logger: 設定済みのロガー
    """
    return logging.getLogger(name)


# ============================================================
# コンテキスト付きログ出力ヘルパー
# ============================================================
class LogContext:
    """
    追加コンテキスト情報を含むログ出力を行うためのヘルパークラス

    使用例:
        log = LogContext(logger, request_id="abc123", user="admin")
        log.info("Processing request", document_id=1)
    """

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context

    def _log(self, level: int, message: str, **extra) -> None:
        """コンテキスト情報を含めてログを出力"""
        combined = {**self.context, **extra}
        extra_str = " | ".join(f"{k}={v}" for k, v in combined.items())
        full_message = f"{message} | {extra_str}" if extra_str else message

        # extraデータをレコードに追加
        record_extra = {"extra_data": combined}
        self.logger.log(level, full_message, extra=record_extra)

    def debug(self, message: str, **extra) -> None:
        self._log(logging.DEBUG, message, **extra)

    def info(self, message: str, **extra) -> None:
        self._log(logging.INFO, message, **extra)

    def warning(self, message: str, **extra) -> None:
        self._log(logging.WARNING, message, **extra)

    def error(self, message: str, **extra) -> None:
        self._log(logging.ERROR, message, **extra)

    def critical(self, message: str, **extra) -> None:
        self._log(logging.CRITICAL, message, **extra)


# ============================================================
# APIコールロガー
# ============================================================
class AzureAPILogger:
    """Azure APIコールのログを記録するクラス"""

    def __init__(self):
        self.logger = get_logger("azure_api")

    def log_request(
        self,
        service: str,
        operation: str,
        request_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        APIリクエストをログに記録

        Args:
            service: サービス名（openai, doc_intelligence等）
            operation: 操作名（chat, embedding, analyze等）
            request_data: リクエストデータ（機密情報は含めない）

        Returns:
            str: リクエストID
        """
        import uuid

        request_id = str(uuid.uuid4())[:8]

        self.logger.info(
            f"API Request | service={service} | operation={operation} | "
            f"request_id={request_id}"
        )

        if request_data:
            # トークン数やサイズのみログに記録（内容は含めない）
            safe_data = {}
            if "messages" in request_data:
                safe_data["message_count"] = len(request_data["messages"])
            if "text" in request_data:
                safe_data["text_length"] = len(request_data["text"])
            if safe_data:
                self.logger.debug(f"Request details | {safe_data}")

        return request_id

    def log_response(
        self,
        request_id: str,
        service: str,
        status: str,
        duration_ms: float,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        APIレスポンスをログに記録

        Args:
            request_id: リクエストID
            service: サービス名
            status: ステータス（success, error）
            duration_ms: 処理時間（ミリ秒）
            response_data: レスポンスデータ（機密情報は含めない）
            error: エラーメッセージ
        """
        if status == "success":
            self.logger.info(
                f"API Response | service={service} | request_id={request_id} | "
                f"status={status} | duration_ms={duration_ms:.2f}"
            )
            if response_data:
                safe_data = {}
                if "usage" in response_data:
                    safe_data["usage"] = response_data["usage"]
                if safe_data:
                    self.logger.debug(f"Response details | {safe_data}")
        else:
            self.logger.error(
                f"API Error | service={service} | request_id={request_id} | "
                f"status={status} | duration_ms={duration_ms:.2f} | error={error}"
            )


# グローバルインスタンス
azure_api_logger = AzureAPILogger()


# ============================================================
# レビュー処理専用ロガー
# ============================================================
class ReviewLogger:
    """レビュー処理の進行状況をログに記録するクラス"""

    def __init__(self, review_id: int, document_id: int):
        self.logger = get_logger("review")
        self.review_id = review_id
        self.document_id = document_id
        self.start_time = datetime.now()

    def _prefix(self) -> str:
        return f"review_id={self.review_id} | document_id={self.document_id}"

    def start(self, check_items_count: int) -> None:
        """レビュー開始をログに記録"""
        self.logger.info(
            f"Review started | {self._prefix()} | check_items={check_items_count}"
        )

    def chunk_processing(self, chunk_index: int, total_chunks: int) -> None:
        """チャンク処理の進行をログに記録"""
        self.logger.debug(
            f"Processing chunk | {self._prefix()} | chunk={chunk_index + 1}/{total_chunks}"
        )

    def check_item_processing(self, check_item_name: str) -> None:
        """チェック項目処理をログに記録"""
        self.logger.debug(
            f"Processing check item | {self._prefix()} | check_item={check_item_name}"
        )

    def findings_detected(self, count: int, high: int, medium: int, low: int) -> None:
        """指摘事項検出をログに記録"""
        self.logger.info(
            f"Findings detected | {self._prefix()} | total={count} | "
            f"high={high} | medium={medium} | low={low}"
        )

    def complete(self, total_findings: int) -> None:
        """レビュー完了をログに記録"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(
            f"Review completed | {self._prefix()} | "
            f"findings={total_findings} | duration_sec={duration:.2f}"
        )

    def error(self, error_message: str) -> None:
        """エラーをログに記録"""
        self.logger.error(f"Review error | {self._prefix()} | error={error_message}")


# ============================================================
# 初期化
# ============================================================
def init_logging() -> None:
    """アプリケーション起動時にログ設定を初期化"""
    is_debug = settings.DEBUG if hasattr(settings, "DEBUG") else False
    level = "DEBUG" if is_debug else "INFO"
    json_format = not is_debug  # 本番環境ではJSON形式

    setup_logging(level=level, json_format=json_format)

    logger = get_logger(__name__)
    logger.info(f"Logging initialized | level={level} | json_format={json_format}")
