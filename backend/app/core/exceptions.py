"""
カスタム例外クラス
アプリケーション固有のエラーを定義
"""

from typing import Optional, Dict, Any


class PolicyReviewerException(Exception):
    """規程レビューツールの基底例外クラス"""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """例外情報を辞書形式で返す"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================
# 認証・認可関連
# ============================================================
class AuthenticationError(PolicyReviewerException):
    """認証エラー"""

    def __init__(self, message: str = "認証に失敗しました", details: Optional[Dict] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(PolicyReviewerException):
    """認可エラー"""

    def __init__(self, message: str = "この操作を実行する権限がありません", details: Optional[Dict] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


# ============================================================
# リソース関連
# ============================================================
class ResourceNotFoundError(PolicyReviewerException):
    """リソースが見つからないエラー"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        message: Optional[str] = None,
    ):
        msg = message or f"{resource_type}（ID: {resource_id}）が見つかりません"
        super().__init__(
            msg,
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceConflictError(PolicyReviewerException):
    """リソースの競合エラー"""

    def __init__(
        self,
        resource_type: str,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        msg = message or f"{resource_type}が既に存在します"
        super().__init__(msg, "RESOURCE_CONFLICT", details)


# ============================================================
# 文書処理関連
# ============================================================
class DocumentProcessingError(PolicyReviewerException):
    """文書処理エラー"""

    def __init__(self, message: str, document_id: Optional[int] = None, details: Optional[Dict] = None):
        details = details or {}
        if document_id:
            details["document_id"] = document_id
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)


class OCRError(DocumentProcessingError):
    """OCR処理エラー"""

    def __init__(self, message: str = "OCR処理に失敗しました", document_id: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message, document_id, details)
        self.error_code = "OCR_ERROR"


class UnsupportedFileTypeError(DocumentProcessingError):
    """サポートされていないファイル形式"""

    def __init__(self, file_type: str, supported_types: list[str]):
        super().__init__(
            f"ファイル形式 '{file_type}' はサポートされていません。サポート形式: {', '.join(supported_types)}",
            details={"file_type": file_type, "supported_types": supported_types},
        )
        self.error_code = "UNSUPPORTED_FILE_TYPE"


class FileTooLargeError(DocumentProcessingError):
    """ファイルサイズ超過"""

    def __init__(self, file_size: int, max_size: int):
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        super().__init__(
            f"ファイルサイズ（{size_mb:.1f}MB）が制限（{max_mb:.1f}MB）を超えています",
            details={"file_size": file_size, "max_size": max_size},
        )
        self.error_code = "FILE_TOO_LARGE"


# ============================================================
# レビュー処理関連
# ============================================================
class ReviewError(PolicyReviewerException):
    """レビュー処理エラー"""

    def __init__(self, message: str, review_id: Optional[int] = None, details: Optional[Dict] = None):
        details = details or {}
        if review_id:
            details["review_id"] = review_id
        super().__init__(message, "REVIEW_ERROR", details)


class ReviewNotReadyError(ReviewError):
    """レビュー実行準備が整っていない"""

    def __init__(self, reason: str, review_id: Optional[int] = None):
        super().__init__(
            f"レビューを実行できません: {reason}",
            review_id,
            {"reason": reason},
        )
        self.error_code = "REVIEW_NOT_READY"


class ReviewAlreadyCompletedError(ReviewError):
    """レビューが既に完了している"""

    def __init__(self, review_id: int):
        super().__init__(
            "このレビューは既に完了しています",
            review_id,
        )
        self.error_code = "REVIEW_ALREADY_COMPLETED"


# ============================================================
# AI/外部サービス関連
# ============================================================
class ExternalServiceError(PolicyReviewerException):
    """外部サービスエラー"""

    def __init__(self, service_name: str, message: str, details: Optional[Dict] = None):
        details = details or {}
        details["service_name"] = service_name
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class AzureOpenAIError(ExternalServiceError):
    """Azure OpenAI APIエラー"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__("Azure OpenAI", message, details)
        self.error_code = "AZURE_OPENAI_ERROR"


class AzureDocumentIntelligenceError(ExternalServiceError):
    """Azure Document Intelligenceエラー"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__("Azure Document Intelligence", message, details)
        self.error_code = "AZURE_DOC_INTEL_ERROR"


class ServiceUnavailableError(ExternalServiceError):
    """サービス利用不可"""

    def __init__(self, service_name: str, reason: Optional[str] = None):
        msg = f"{service_name}サービスが利用できません"
        if reason:
            msg += f": {reason}"
        super().__init__(service_name, msg)
        self.error_code = "SERVICE_UNAVAILABLE"


class RateLimitExceededError(ExternalServiceError):
    """レート制限超過"""

    def __init__(self, service_name: str, retry_after: Optional[int] = None):
        msg = f"{service_name}のレート制限に達しました"
        details = {}
        if retry_after:
            msg += f"。{retry_after}秒後に再試行してください"
            details["retry_after"] = retry_after
        super().__init__(service_name, msg, details)
        self.error_code = "RATE_LIMIT_EXCEEDED"


# ============================================================
# バリデーション関連
# ============================================================
class ValidationError(PolicyReviewerException):
    """入力値検証エラー"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", details)


class InvalidInputError(ValidationError):
    """不正な入力値"""

    def __init__(self, field: str, message: str, value: Any = None):
        details = {"field": field}
        if value is not None:
            details["value"] = str(value)[:100]  # 値が長すぎる場合は切り詰め
        super().__init__(message, field, details)
        self.error_code = "INVALID_INPUT"


class MissingRequiredFieldError(ValidationError):
    """必須フィールドの欠落"""

    def __init__(self, field: str):
        super().__init__(f"'{field}' は必須項目です", field)
        self.error_code = "MISSING_REQUIRED_FIELD"


# ============================================================
# データベース関連
# ============================================================
class DatabaseError(PolicyReviewerException):
    """データベースエラー"""

    def __init__(self, message: str = "データベースエラーが発生しました", details: Optional[Dict] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class DatabaseConnectionError(DatabaseError):
    """データベース接続エラー"""

    def __init__(self, message: str = "データベースに接続できません"):
        super().__init__(message)
        self.error_code = "DATABASE_CONNECTION_ERROR"


# ============================================================
# 設定関連
# ============================================================
class ConfigurationError(PolicyReviewerException):
    """設定エラー"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)


class MissingConfigurationError(ConfigurationError):
    """必須設定の欠落"""

    def __init__(self, config_key: str):
        super().__init__(f"設定 '{config_key}' が必要です", config_key)
        self.error_code = "MISSING_CONFIGURATION"
