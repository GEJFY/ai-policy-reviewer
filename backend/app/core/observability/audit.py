"""
Security audit logging for compliance requirements.

コンプライアンス要件のためのセキュリティ監査ログ。
誰が、いつ、何をしたかを記録。
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

from app.core.observability.correlation import CorrelationContext


class AuditEventType(str, Enum):
    """監査イベントタイプ"""

    # 認証イベント
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    TOKEN_REVOKE = "auth.token.revoke"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"

    # 文書イベント
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_ACCESS = "document.access"
    DOCUMENT_DOWNLOAD = "document.download"

    # レビューイベント
    REVIEW_START = "review.start"
    REVIEW_COMPLETE = "review.complete"
    REVIEW_CANCEL = "review.cancel"

    # 指摘事項イベント
    FINDING_APPROVE = "finding.approve"
    FINDING_REJECT = "finding.reject"
    FINDING_DEFER = "finding.defer"
    FINDING_BULK_UPDATE = "finding.bulk_update"

    # マスタデータイベント
    TERM_CREATE = "master.term.create"
    TERM_UPDATE = "master.term.update"
    TERM_DELETE = "master.term.delete"
    CHECK_ITEM_CREATE = "master.check_item.create"
    CHECK_ITEM_UPDATE = "master.check_item.update"
    CHECK_ITEM_DELETE = "master.check_item.delete"
    WRITING_RULE_CREATE = "master.writing_rule.create"
    WRITING_RULE_UPDATE = "master.writing_rule.update"
    WRITING_RULE_DELETE = "master.writing_rule.delete"

    # 管理イベント
    CONFIG_CHANGE = "admin.config.change"
    USER_CREATE = "admin.user.create"
    USER_UPDATE = "admin.user.update"
    USER_DELETE = "admin.user.delete"
    ROLE_ASSIGN = "admin.role.assign"
    ROLE_REVOKE = "admin.role.revoke"

    # データアクセスイベント
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    BULK_UPDATE = "data.bulk_update"

    # システムイベント
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"


class AuditLogger:
    """
    セキュリティ監査ロガー。

    監査イベントをJSON形式で専用ログファイルに記録。
    コンプライアンス要件を満たすための詳細な追跡情報を提供。
    """

    def __init__(
        self, log_dir: str = "logs", max_bytes: int = 50_000_000, backup_count: int = 10
    ):
        """
        監査ロガーを初期化。

        Args:
            log_dir: ログディレクトリ
            max_bytes: ログファイルの最大サイズ（デフォルト50MB）
            backup_count: 保持するバックアップ数
        """
        self.logger = logging.getLogger("security.audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # 親ロガーに伝播しない

        # 既存のハンドラーをクリア
        self.logger.handlers.clear()

        # ログディレクトリ作成
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # ローテーションファイルハンドラー
        handler = RotatingFileHandler(
            log_path / "audit.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def log(
        self,
        event_type: AuditEventType,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        action_result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        監査イベントをログ出力。

        Args:
            event_type: イベントタイプ
            resource_type: リソースタイプ（例: "document", "review"）
            resource_id: リソースID
            action_result: 結果（"success", "failure", "error"）
            details: 追加詳細情報
            user_id: ユーザーID（Noneの場合コンテキストから取得）
            ip_address: IPアドレス（Noneの場合コンテキストから取得）
            user_agent: User-Agent
        """
        # コンテキストから情報を取得（指定がない場合）
        if user_id is None:
            user_id = CorrelationContext.get_user_id()
        if ip_address is None:
            ip_address = CorrelationContext.get_client_ip()

        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "correlation_id": CorrelationContext.get_correlation_id(),
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "action_result": action_result,
            "details": details or {},
        }

        # JSON形式でログ出力
        self.logger.info(json.dumps(audit_record, ensure_ascii=False))

    def log_auth(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        success: bool = True,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """認証関連イベントをログ。"""
        self.log(
            event_type=event_type,
            resource_type="auth",
            action_result="success" if success else "failure",
            details={"reason": reason} if reason else None,
            user_id=user_id,
            ip_address=ip_address,
        )

    def log_document(
        self,
        event_type: AuditEventType,
        document_id: int,
        document_title: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> None:
        """文書関連イベントをログ。"""
        details: Dict[str, Any] = {}
        if document_title:
            details["title"] = document_title
        if file_size:
            details["file_size"] = file_size

        self.log(
            event_type=event_type,
            resource_type="document",
            resource_id=document_id,
            details=details if details else None,
        )

    def log_review(
        self,
        event_type: AuditEventType,
        review_id: int,
        document_id: Optional[int] = None,
        findings_count: Optional[int] = None,
    ) -> None:
        """レビュー関連イベントをログ。"""
        details = {}
        if document_id:
            details["document_id"] = document_id
        if findings_count is not None:
            details["findings_count"] = findings_count

        self.log(
            event_type=event_type,
            resource_type="review",
            resource_id=review_id,
            details=details if details else None,
        )

    def log_finding(
        self,
        event_type: AuditEventType,
        finding_id: int,
        review_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> None:
        """指摘事項関連イベントをログ。"""
        details: Dict[str, Any] = {}
        if review_id:
            details["review_id"] = review_id
        if status:
            details["status"] = status

        self.log(
            event_type=event_type,
            resource_type="finding",
            resource_id=finding_id,
            details=details if details else None,
        )

    def log_master_data(
        self,
        event_type: AuditEventType,
        resource_type: str,
        resource_id: int,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """マスタデータ変更イベントをログ。"""
        self.log(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"changes": changes} if changes else None,
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
    ) -> None:
        """システムエラーをログ。"""
        self.log(
            event_type=AuditEventType.SYSTEM_ERROR,
            resource_type="system",
            action_result="error",
            details={
                "error_type": error_type,
                "error_message": error_message[:500],  # 長すぎるメッセージを切り詰め
                "stack_trace": stack_trace[:2000] if stack_trace else None,
            },
        )


# シングルトンインスタンス
audit_logger = AuditLogger()
