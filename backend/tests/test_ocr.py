"""
OCRマルチプロバイダーテスト

OCRサービス（Azure Document Intelligence, Tesseract, AWS Tesseract）の
ファクトリ・基本機能をテストする。

使用方法:
    pytest tests/test_ocr.py -v
    pytest tests/test_ocr.py -v -k tesseract
    pytest tests/test_ocr.py -v -k azure
    pytest tests/test_ocr.py -v -k factory
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings, OCRProvider
from app.services.ocr_service import (
    BaseOCRService,
    AzureDocIntelOCRService,
    TesseractOCRService,
    AWSTesseractOCRService,
    OCRServiceFactory,
    ocr_service,
)


# =============================================================================
# OCR Provider Enum Tests
# =============================================================================

class TestOCRProviderEnum:
    """OCRProviderのenum値テスト"""

    def test_azure_doc_intel_value(self):
        assert OCRProvider.AZURE_DOC_INTEL.value == "azure_doc_intel"

    def test_tesseract_value(self):
        assert OCRProvider.TESSERACT.value == "tesseract"

    def test_aws_tesseract_value(self):
        assert OCRProvider.AWS_TESSERACT.value == "aws_tesseract"

    def test_all_providers_exist(self):
        """3つのプロバイダーが定義されていること"""
        assert len(OCRProvider) == 3


# =============================================================================
# OCR Service Factory Tests
# =============================================================================

class TestOCRServiceFactory:
    """OCRServiceFactoryのテスト"""

    def test_create_azure_doc_intel(self):
        """Azure Document Intelligenceサービスが生成されること"""
        service = OCRServiceFactory.create(OCRProvider.AZURE_DOC_INTEL)
        assert isinstance(service, AzureDocIntelOCRService)
        assert service.provider_name() == "azure_doc_intel"

    def test_create_tesseract(self):
        """Tesseractサービスが生成されること"""
        service = OCRServiceFactory.create(OCRProvider.TESSERACT)
        assert isinstance(service, TesseractOCRService)
        assert service.provider_name() == "tesseract"

    def test_create_aws_tesseract(self):
        """AWS Tesseractサービスが生成されること"""
        service = OCRServiceFactory.create(OCRProvider.AWS_TESSERACT)
        assert isinstance(service, AWSTesseractOCRService)
        assert service.provider_name() == "aws_tesseract"

    def test_create_default_from_settings(self):
        """設定からデフォルトプロバイダーが選択されること"""
        service = OCRServiceFactory.create()
        assert isinstance(service, BaseOCRService)

    def test_get_available_providers(self):
        """利用可能なプロバイダーリストが取得できること"""
        providers = OCRServiceFactory.get_available_providers()
        assert isinstance(providers, list)
        for p in providers:
            assert isinstance(p, OCRProvider)

    def test_singleton_ocr_service_exists(self):
        """シングルトンインスタンスが存在すること"""
        assert ocr_service is not None
        assert isinstance(ocr_service, BaseOCRService)


# =============================================================================
# Azure Document Intelligence OCR Tests
# =============================================================================

class TestAzureDocIntelOCRService:
    """Azure Document Intelligence OCRのテスト"""

    def test_is_available_without_credentials(self):
        """認証情報なしではis_availableがFalseまたはTrueを返すこと"""
        service = AzureDocIntelOCRService()
        result = service.is_available()
        assert isinstance(result, bool)

    def test_provider_name(self):
        """プロバイダー名が正しいこと"""
        service = AzureDocIntelOCRService()
        assert service.provider_name() == "azure_doc_intel"


# =============================================================================
# Tesseract OCR Tests
# =============================================================================

class TestTesseractOCRService:
    """Tesseract OCRのテスト"""

    def test_provider_name(self):
        """プロバイダー名が正しいこと"""
        service = TesseractOCRService()
        assert service.provider_name() == "tesseract"

    def test_is_available_returns_bool(self):
        """is_availableがboolを返すこと"""
        service = TesseractOCRService()
        result = service.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_extract_with_mock(self):
        """モックを使用したテキスト抽出テスト"""
        service = TesseractOCRService()
        service._available = True

        mock_images = [MagicMock(), MagicMock()]

        with patch('pytesseract.image_to_string') as mock_img_to_str, \
             patch('pytesseract.pytesseract'), \
             patch('pdf2image.convert_from_bytes') as mock_convert:

            mock_convert.return_value = mock_images
            mock_img_to_str.side_effect = ["ページ1のテキスト", "ページ2のテキスト"]

            result = await service.extract_text_from_bytes(b"fake-pdf-content")

            assert "ページ1のテキスト" in result
            assert "ページ2のテキスト" in result
            assert mock_img_to_str.call_count == 2


# =============================================================================
# AWS Tesseract OCR Tests
# =============================================================================

class TestAWSTesseractOCRService:
    """AWS Tesseract OCRのテスト"""

    def test_provider_name(self):
        """プロバイダー名が正しいこと"""
        service = AWSTesseractOCRService()
        assert service.provider_name() == "aws_tesseract"

    def test_is_available_without_endpoint(self):
        """エンドポイントなしではis_availableがFalseを返すこと"""
        service = AWSTesseractOCRService()
        service.endpoint = ""
        assert service.is_available() is False

    def test_is_available_with_endpoint(self):
        """エンドポイントありではis_availableがTrueを返すこと"""
        service = AWSTesseractOCRService()
        service.endpoint = "https://example.com/api"
        assert service.is_available() is True

    @pytest.mark.asyncio
    async def test_extract_with_mock(self):
        """モックを使用したテキスト抽出テスト"""
        service = AWSTesseractOCRService()
        service.endpoint = "https://example.com/api"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "OCR抽出テキスト",
            "pages": 1,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await service.extract_text_from_bytes(b"fake-pdf-content")

            assert result == "OCR抽出テキスト"
            mock_client.post.assert_called_once()


# =============================================================================
# OCR Integration Tests (Tesseract)
# =============================================================================

class TestTesseractIntegration:
    """
    Tesseract OCR統合テスト

    Tesseractがインストール済みの場合のみ実行。
    """

    _TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
    ]

    def _is_tesseract_available(self):
        try:
            import pytesseract
            if settings.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
            else:
                import os
                for path in self._TESSERACT_PATHS:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def test_tesseract_version(self):
        """Tesseractのバージョン取得テスト"""
        if not self._is_tesseract_available():
            pytest.skip("Tesseract not installed")

        import pytesseract
        version = pytesseract.get_tesseract_version()
        assert version is not None
        print(f"Tesseract version: {version}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
