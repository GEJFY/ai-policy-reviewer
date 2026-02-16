"""
ChunkingService tests.

階層的チャンキングのテスト。
"""

from app.services.chunking_service import ChunkingService, ChunkResult


class TestChunkingService:
    """ChunkingService テストクラス。"""

    def _make_service(
        self, chunk_size: int = 100, overlap: int = 20
    ) -> ChunkingService:
        return ChunkingService(chunk_size=chunk_size, overlap=overlap)

    def test_chunk_text_empty(self):
        """空テキストは空リストを返す。"""
        svc = self._make_service()
        assert svc.chunk_text("") == []
        assert svc.chunk_text("   ") == []

    def test_chunk_text_short(self):
        """短いテキストは1チャンクを返す。"""
        svc = self._make_service(chunk_size=1000)
        result = svc.chunk_text("Hello world")
        assert len(result) == 1
        assert "Hello world" in result[0]

    def test_chunk_text_with_overlap(self):
        """オーバーラップ付きチャンキング。"""
        svc = self._make_service(chunk_size=50, overlap=10)
        text = "あ" * 200  # Roughly >50 tokens
        result = svc.chunk_text(text)
        assert len(result) > 1

    def test_hierarchical_empty(self):
        """空テキストの階層チャンキング。"""
        svc = self._make_service()
        assert svc.chunk_text_hierarchical("") == []

    def test_hierarchical_no_sections(self):
        """セクションなしのテキストはフラットチャンキング。"""
        svc = self._make_service(chunk_size=1000)
        text = "This is a simple document without any section headers."
        result = svc.chunk_text_hierarchical(text)
        assert len(result) >= 1
        assert isinstance(result[0], ChunkResult)

    def test_hierarchical_with_articles(self):
        """条文パターンで階層チャンキング。"""
        svc = self._make_service(chunk_size=1000)
        text = """前文テキスト。

第1条 この規程は目的を定める。
本条の内容は以下の通り。

第2条 この規程は範囲を定める。
適用範囲について。

第3条 この規程の定義。
用語の定義は以下の通り。"""

        result = svc.chunk_text_hierarchical(text)
        assert len(result) >= 3  # preamble + 3 articles

        # Check section titles
        titles = [r.section_title for r in result if r.section_title]
        assert any("前文" in t for t in titles)
        assert any("第1条" in t for t in titles)
        assert any("第2条" in t for t in titles)

    def test_hierarchical_with_kanji_articles(self):
        """漢数字条文パターン。"""
        svc = self._make_service(chunk_size=1000)
        text = """第一条 目的
内容A。

第二条 範囲
内容B。"""

        result = svc.chunk_text_hierarchical(text)
        assert len(result) >= 2
        titles = [r.section_title for r in result]
        assert any("第一条" in (t or "") for t in titles)

    def test_hierarchical_large_section_sub_chunks(self):
        """大きなセクションはサブチャンクに分割される。"""
        svc = self._make_service(chunk_size=50, overlap=10)
        text = (
            """第1条 この規程は目的を定める。
"""
            + "あ" * 1000
            + """

第2条 この規程は範囲を定める。
短いテキスト。"""
        )

        result = svc.chunk_text_hierarchical(text)
        # 第1条は大きいのでサブチャンク化
        section1_chunks = [
            r for r in result if r.section_title and "第1条" in r.section_title
        ]
        assert len(section1_chunks) > 1
        # サブチャンクにはインデックスが付く
        assert any("1/" in (r.section_title or "") for r in section1_chunks)

    def test_detect_sections_chapter_pattern(self):
        """章パターンの検出。"""
        svc = self._make_service()
        text = """第一章 総則
内容A。

第二章 組織
内容B。"""

        sections = svc._detect_sections(text)
        assert len(sections) >= 2
        assert any("第一章" in s["section"] for s in sections)

    def test_detect_sections_numbered(self):
        """番号付きセクションの検出。"""
        svc = self._make_service()
        text = """1. はじめに
内容A。

2. 目的
内容B。

3. 範囲
内容C。"""

        sections = svc._detect_sections(text)
        assert len(sections) >= 3

    def test_chunk_by_sections_legacy(self):
        """レガシーAPI chunk_by_sections の動作確認。"""
        svc = self._make_service()
        text = """第1条 目的
内容A。

第2条 範囲
内容B。"""

        result = svc.chunk_by_sections(text)
        assert len(result) >= 2
        assert "section" in result[0]
        assert "content" in result[0]

    def test_chunk_result_attributes(self):
        """ChunkResultの属性。"""
        cr = ChunkResult(content="test", section_title="第1条")
        assert cr.content == "test"
        assert cr.section_title == "第1条"

    def test_chunk_result_no_section(self):
        """セクションなしChunkResult。"""
        cr = ChunkResult(content="test")
        assert cr.content == "test"
        assert cr.section_title is None
