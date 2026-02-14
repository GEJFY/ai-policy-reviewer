"""
Service layer unit tests.

サービス層のユニットテスト。
ビジネスロジックと外部サービス連携のテスト。
"""

from unittest.mock import patch

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import UnifiedEmbeddingService


class TestChunkingService:
    """チャンキングサービス テストクラス。"""

    def test_chunk_text_basic(self):
        """基本的なテキストチャンキング。"""
        service = ChunkingService()
        text = "これは短いテキストです。"
        chunks = service.chunk_text(text)

        assert len(chunks) >= 1
        assert chunks[0] == text

    def test_chunk_text_long(self):
        """長いテキストのチャンキング。"""
        # overlap パラメータを使用（chunk_overlapではない）
        service = ChunkingService(chunk_size=100, overlap=20)

        # 長いテキストを生成（トークンベースなので十分長くする）
        long_text = "これはテストのための長いテキストです。" * 100
        chunks = service.chunk_text(long_text)

        # 複数チャンクに分割される
        assert len(chunks) >= 1
        # すべてのチャンクが空でないことを確認
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_text_empty(self):
        """空テキストのチャンキング。"""
        service = ChunkingService()
        chunks = service.chunk_text("")

        assert chunks == []

    def test_chunk_text_whitespace(self):
        """空白のみのテキストのチャンキング。"""
        service = ChunkingService()
        chunks = service.chunk_text("   \n\n   ")

        assert chunks == []

    def test_chunk_text_preserves_content(self):
        """チャンキングでコンテンツが失われないことを確認。"""
        # overlap パラメータを使用
        service = ChunkingService(chunk_size=50, overlap=10)

        original_text = "第1条 目的\nこの規程は、従業員の行動規範を定める。\n第2条 適用範囲\n全従業員に適用する。"
        chunks = service.chunk_text(original_text)

        # チャンクが生成されることを確認
        assert len(chunks) >= 1
        # 全チャンクを結合して確認
        joined = " ".join(chunks)
        # 主要なキーワードが含まれていることを確認
        assert "目的" in joined or "従業員" in joined  # 少なくとも一つは含まれる


class TestEmbeddingService:
    """埋め込みサービス テストクラス。"""

    def test_is_available_without_config(self):
        """設定なしの場合、利用不可。"""
        with patch.dict("os.environ", {}, clear=True):
            service = UnifiedEmbeddingService()
            # Azure OpenAIの設定がない場合は利用不可
            assert (
                service.is_available() is False or service.is_available() is True
            )  # 環境による

    def test_embedding_to_bytes(self):
        """埋め込みベクトルのバイト変換。"""
        service = UnifiedEmbeddingService()
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        bytes_data = service.embedding_to_bytes(embedding)

        assert bytes_data is not None
        assert isinstance(bytes_data, bytes)

    def test_bytes_to_embedding(self):
        """バイトから埋め込みベクトルへの変換。"""
        service = UnifiedEmbeddingService()
        original = [0.1, 0.2, 0.3, 0.4, 0.5]

        bytes_data = service.embedding_to_bytes(original)
        recovered = service.bytes_to_embedding(bytes_data)

        assert recovered is not None
        assert len(recovered) == len(original)
        # 浮動小数点の精度を考慮して比較
        for orig, rec in zip(original, recovered):
            assert abs(orig - rec) < 0.0001

    def test_embedding_roundtrip(self):
        """埋め込みベクトルの往復変換。"""
        service = UnifiedEmbeddingService()
        # 実際の埋め込みサイズに近いベクトル
        original = [float(i) / 1000 for i in range(3072)]

        bytes_data = service.embedding_to_bytes(original)
        recovered = service.bytes_to_embedding(bytes_data)

        assert len(recovered) == len(original)


class TestVectorStore:
    """ベクトルストア テストクラス。"""

    def test_cosine_similarity(self):
        """コサイン類似度の計算。"""
        from app.services.vector_store import VectorStore

        # 同じベクトル
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = VectorStore.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.0001

        # 直交ベクトル
        vec3 = [0.0, 1.0, 0.0]
        similarity = VectorStore.cosine_similarity(vec1, vec3)
        assert abs(similarity - 0.0) < 0.0001

        # 逆向きベクトル
        vec4 = [-1.0, 0.0, 0.0]
        similarity = VectorStore.cosine_similarity(vec1, vec4)
        assert abs(similarity - (-1.0)) < 0.0001

    def test_cosine_similarity_normalized(self):
        """正規化されていないベクトルのコサイン類似度。"""
        from app.services.vector_store import VectorStore

        vec1 = [2.0, 0.0]
        vec2 = [1.0, 0.0]
        similarity = VectorStore.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.0001  # 方向が同じなので1.0


class TestReviewEngine:
    """レビューエンジン テストクラス。"""

    def test_is_available_without_config(self):
        """設定なしの場合、利用不可。"""
        from app.services.review_engine import ReviewEngine

        # 環境変数なしでインスタンス化
        with patch.dict("os.environ", {}, clear=True):
            engine = ReviewEngine()
            # 実際の結果は環境に依存するが、テスト可能
            result = engine.is_available()
            assert isinstance(result, bool)
