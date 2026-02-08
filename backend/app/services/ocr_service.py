"""
OCR service using Azure Document Intelligence.
PDFからテキストを抽出するためのサービス

azure-ai-documentintelligence v1.0.0 対応版
（旧 azure-ai-formrecognizer からの移行）
"""

import time
import logging
from typing import Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from PDF documents using Azure Document Intelligence."""

    def __init__(self):
        """Initialize the OCR service."""
        self.client: Optional[DocumentIntelligenceClient] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Azure Document Intelligence client if configured."""
        if settings.azure_doc_intel_endpoint and settings.azure_doc_intel_key:
            self.client = DocumentIntelligenceClient(
                endpoint=settings.azure_doc_intel_endpoint,
                credential=AzureKeyCredential(settings.azure_doc_intel_key),
            )
            logger.info("OCRService initialized successfully (Document Intelligence v1.0)")
        else:
            logger.warning("OCRService not configured - missing Azure credentials")

    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self.client is not None

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        if not self.client:
            logger.error("OCR service not configured")
            raise RuntimeError("OCR service not configured")

        logger.info(f"Starting OCR extraction | file_path={file_path}")
        start_time = time.time()

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            # 新しいAPI: analyze_document を使用
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=content,
                content_type="application/pdf",
            )

            result: AnalyzeResult = poller.result()

            # Extract text from all pages
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
            duration_sec = time.time() - start_time

            logger.info(
                f"OCR extraction completed | file_path={file_path} | "
                f"pages={len(result.pages) if result.pages else 0} | lines={total_lines} | "
                f"chars={len(full_text)} | duration_sec={duration_sec:.2f}"
            )

            return full_text

        except Exception as e:
            duration_sec = time.time() - start_time
            logger.error(
                f"OCR extraction failed | file_path={file_path} | "
                f"duration_sec={duration_sec:.2f} | error={str(e)}"
            )
            raise

    async def extract_text_from_bytes(self, content: bytes) -> str:
        """
        Extract text from PDF bytes.

        Args:
            content: PDF file content as bytes

        Returns:
            Extracted text content
        """
        if not self.client:
            logger.error("OCR service not configured")
            raise RuntimeError("OCR service not configured")

        logger.info(f"Starting OCR extraction from bytes | size={len(content)} bytes")
        start_time = time.time()

        try:
            # 新しいAPI: analyze_document を使用
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=content,
                content_type="application/pdf",
            )

            result: AnalyzeResult = poller.result()

            # Extract text from all pages
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
            duration_sec = time.time() - start_time

            logger.info(
                f"OCR extraction completed | input_size={len(content)} bytes | "
                f"pages={len(result.pages) if result.pages else 0} | lines={total_lines} | "
                f"chars={len(full_text)} | duration_sec={duration_sec:.2f}"
            )

            return full_text

        except Exception as e:
            duration_sec = time.time() - start_time
            logger.error(
                f"OCR extraction failed | input_size={len(content)} bytes | "
                f"duration_sec={duration_sec:.2f} | error={str(e)}"
            )
            raise


# Singleton instance
ocr_service = OCRService()
