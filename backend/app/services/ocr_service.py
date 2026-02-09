"""
Multi-provider OCR service.

PDFからテキストを抽出するためのマルチプロバイダーOCRサービス。
対応プロバイダー:
    - Azure Document Intelligence (azure_doc_intel)
    - Tesseract OCR (tesseract) — ローカル実行
    - AWS Tesseract (aws_tesseract) — リモートREST API経由
"""

import time
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings, OCRProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Base OCR Service (ABC)
# =============================================================================

class BaseOCRService(ABC):
    """OCRサービスの基底クラス"""

    @abstractmethod
    def is_available(self) -> bool:
        """サービスが利用可能かチェック。"""
        ...

    @abstractmethod
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """PDFファイルからテキストを抽出。"""
        ...

    @abstractmethod
    async def extract_text_from_bytes(self, content: bytes) -> str:
        """PDFバイトデータからテキストを抽出。"""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名を返す。"""
        ...


# =============================================================================
# Azure Document Intelligence OCR
# =============================================================================

class AzureDocIntelOCRService(BaseOCRService):
    """Azure Document Intelligence を使用したOCRサービス。"""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Azure Document Intelligence クライアントを初期化。"""
        if not (settings.azure_doc_intel_endpoint and settings.azure_doc_intel_key):
            logger.warning("AzureDocIntelOCR: credentials not configured")
            return

        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential

            self.client = DocumentIntelligenceClient(
                endpoint=settings.azure_doc_intel_endpoint,
                credential=AzureKeyCredential(settings.azure_doc_intel_key),
            )
            logger.info("AzureDocIntelOCR initialized (Document Intelligence v1.0)")
        except ImportError:
            logger.warning("AzureDocIntelOCR: azure-ai-documentintelligence not installed")
        except Exception as e:
            logger.error(f"AzureDocIntelOCR initialization failed: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def provider_name(self) -> str:
        return "azure_doc_intel"

    async def extract_text_from_pdf(self, file_path: str) -> str:
        if not self.client:
            raise RuntimeError("Azure Document Intelligence not configured")

        logger.info(f"AzureDocIntelOCR: extracting | file={file_path}")
        start = time.time()

        with open(file_path, "rb") as f:
            content = f.read()
        return await self._extract(content, start, f"file={file_path}")

    async def extract_text_from_bytes(self, content: bytes) -> str:
        if not self.client:
            raise RuntimeError("Azure Document Intelligence not configured")

        logger.info(f"AzureDocIntelOCR: extracting | size={len(content)} bytes")
        start = time.time()
        return await self._extract(content, start, f"size={len(content)}")

    async def _extract(self, content: bytes, start: float, log_ctx: str) -> str:
        """共通の抽出処理。"""
        from azure.ai.documentintelligence.models import AnalyzeResult

        try:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=content,
                content_type="application/pdf",
            )
            result: AnalyzeResult = poller.result()

            extracted_text = []
            total_lines = 0
            if result.pages:
                for page in result.pages:
                    page_text = []
                    if page.lines:
                        for line in page.lines:
                            page_text.append(line.content)
                            total_lines += 1
                    extracted_text.append("\n".join(page_text))

            full_text = "\n\n".join(extracted_text)
            duration = time.time() - start
            logger.info(
                f"AzureDocIntelOCR: completed | {log_ctx} | "
                f"pages={len(result.pages) if result.pages else 0} | "
                f"lines={total_lines} | chars={len(full_text)} | {duration:.2f}s"
            )
            return full_text

        except Exception as e:
            duration = time.time() - start
            logger.error(f"AzureDocIntelOCR: failed | {log_ctx} | {duration:.2f}s | {e}")
            raise


# =============================================================================
# Tesseract OCR (Local)
# =============================================================================

class TesseractOCRService(BaseOCRService):
    """ローカルTesseract OCRサービス。pytesseract + pdf2image を使用。"""

    def __init__(self):
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            import pytesseract
            if settings.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
            # バージョン確認でインストール状態をチェック
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info("TesseractOCR: available")
        except Exception as e:
            self._available = False
            logger.warning(f"TesseractOCR: not available | {e}")
        return self._available

    def provider_name(self) -> str:
        return "tesseract"

    async def extract_text_from_pdf(self, file_path: str) -> str:
        logger.info(f"TesseractOCR: extracting | file={file_path}")
        start = time.time()

        with open(file_path, "rb") as f:
            content = f.read()
        return await self._extract(content, start, f"file={file_path}")

    async def extract_text_from_bytes(self, content: bytes) -> str:
        logger.info(f"TesseractOCR: extracting | size={len(content)} bytes")
        start = time.time()
        return await self._extract(content, start, f"size={len(content)}")

    async def _extract(self, content: bytes, start: float, log_ctx: str) -> str:
        """PDF → 画像 → テキスト変換。"""
        import pytesseract
        from pdf2image import convert_from_bytes
        from PIL import Image

        if settings.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path

        try:
            # PDF → 画像変換
            images = convert_from_bytes(content, dpi=300)
            logger.info(f"TesseractOCR: converted to {len(images)} images | {log_ctx}")

            # 各ページをOCR
            page_texts = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(
                    image,
                    lang=settings.tesseract_lang,
                )
                page_texts.append(text.strip())

            full_text = "\n\n".join(page_texts)
            duration = time.time() - start
            logger.info(
                f"TesseractOCR: completed | {log_ctx} | "
                f"pages={len(images)} | chars={len(full_text)} | {duration:.2f}s"
            )
            return full_text

        except Exception as e:
            duration = time.time() - start
            logger.error(f"TesseractOCR: failed | {log_ctx} | {duration:.2f}s | {e}")
            raise


# =============================================================================
# AWS Tesseract OCR (Remote REST API)
# =============================================================================

class AWSTesseractOCRService(BaseOCRService):
    """
    AWS上のTesseract REST APIを使用したOCRサービス。

    API仕様:
        POST /ocr
        Body: {"document": "<base64-encoded-pdf>", "language": "jpn+eng", "format": "pdf"}
        Response: {"text": "...", "pages": N}
    """

    def __init__(self):
        self.endpoint = settings.aws_tesseract_endpoint

    def is_available(self) -> bool:
        return bool(self.endpoint)

    def provider_name(self) -> str:
        return "aws_tesseract"

    async def extract_text_from_pdf(self, file_path: str) -> str:
        logger.info(f"AWSTesseractOCR: extracting | file={file_path}")
        start = time.time()

        with open(file_path, "rb") as f:
            content = f.read()
        return await self._extract(content, start, f"file={file_path}")

    async def extract_text_from_bytes(self, content: bytes) -> str:
        logger.info(f"AWSTesseractOCR: extracting | size={len(content)} bytes")
        start = time.time()
        return await self._extract(content, start, f"size={len(content)}")

    async def _extract(self, content: bytes, start: float, log_ctx: str) -> str:
        """REST API経由でTesseract OCRを実行。"""
        import base64
        import httpx

        if not self.endpoint:
            raise RuntimeError("AWS Tesseract endpoint not configured")

        try:
            encoded = base64.b64encode(content).decode("utf-8")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.endpoint.rstrip('/')}/ocr",
                    json={
                        "document": encoded,
                        "language": settings.tesseract_lang,
                        "format": "pdf",
                    },
                )
                response.raise_for_status()

            result = response.json()
            full_text = result.get("text", "")
            pages = result.get("pages", 0)
            duration = time.time() - start

            logger.info(
                f"AWSTesseractOCR: completed | {log_ctx} | "
                f"pages={pages} | chars={len(full_text)} | {duration:.2f}s"
            )
            return full_text

        except Exception as e:
            duration = time.time() - start
            logger.error(f"AWSTesseractOCR: failed | {log_ctx} | {duration:.2f}s | {e}")
            raise


# =============================================================================
# OCR Service Factory
# =============================================================================

class OCRServiceFactory:
    """OCRサービスのファクトリ。設定に応じた適切なプロバイダーを返す。"""

    @staticmethod
    def create(provider: Optional[OCRProvider] = None) -> BaseOCRService:
        """
        OCRサービスインスタンスを生成。

        Args:
            provider: 使用するプロバイダー（Noneの場合はsettingsから取得）

        Returns:
            BaseOCRService: OCRサービスインスタンス
        """
        target = provider or settings.ocr_provider

        if target == OCRProvider.AZURE_DOC_INTEL:
            return AzureDocIntelOCRService()
        elif target == OCRProvider.TESSERACT:
            return TesseractOCRService()
        elif target == OCRProvider.AWS_TESSERACT:
            return AWSTesseractOCRService()
        else:
            logger.warning(f"Unknown OCR provider '{target}', falling back to Azure")
            return AzureDocIntelOCRService()

    @staticmethod
    def get_available_providers() -> list[OCRProvider]:
        """利用可能なOCRプロバイダーのリストを返す。"""
        available = []

        # Azure Document Intelligence
        azure = AzureDocIntelOCRService()
        if azure.is_available():
            available.append(OCRProvider.AZURE_DOC_INTEL)

        # Tesseract (Local)
        tesseract = TesseractOCRService()
        if tesseract.is_available():
            available.append(OCRProvider.TESSERACT)

        # AWS Tesseract
        aws = AWSTesseractOCRService()
        if aws.is_available():
            available.append(OCRProvider.AWS_TESSERACT)

        return available


# シングルトンインスタンス（後方互換性）
ocr_service = OCRServiceFactory.create()
