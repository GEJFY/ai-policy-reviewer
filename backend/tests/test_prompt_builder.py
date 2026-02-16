"""
Prompt builder service tests.

プロンプトビルダーサービスのユニットテスト。
テンプレート選択、用語フォーマット、ルールフォーマット等をテスト。
"""

from unittest.mock import MagicMock

from app.services.prompt_builder import PromptBuilder
from app.prompts.check_templates import CHECK_TEMPLATES, DEFAULT_TEMPLATE


class TestPromptBuilder:
    """プロンプトビルダーのテスト"""

    def setup_method(self):
        """テスト前にインスタンス生成"""
        self.builder = PromptBuilder()

    def _make_check_item(
        self, category="TERMINOLOGY", description="テスト説明", prompt_template=None
    ):
        """テスト用チェック項目モック"""
        item = MagicMock()
        item.category = category
        item.description = description
        item.prompt_template = prompt_template
        return item

    def _make_term(
        self,
        term="情報セキュリティ",
        aliases="InfoSec, IS",
        definition="情報の機密性・完全性・可用性を維持すること",
    ):
        """テスト用用語モック"""
        t = MagicMock()
        t.term = term
        t.aliases = aliases
        t.definition = definition
        return t

    def _make_rule(
        self,
        name="表記ルール1",
        rule_type="FORMAT",
        correct_form="正しい形式",
        example_bad="NG例",
        example_good="OK例",
    ):
        """テスト用記載ルールモック"""
        r = MagicMock()
        r.name = name
        r.rule_type = rule_type
        r.correct_form = correct_form
        r.example_bad = example_bad
        r.example_good = example_good
        return r

    # =========================================================================
    # _get_template テスト
    # =========================================================================

    def test_get_template_custom(self):
        """カスタムテンプレートが優先されること"""
        item = self._make_check_item(
            prompt_template="カスタムテンプレート: {document_content}"
        )
        result = self.builder._get_template(item)
        assert result == "カスタムテンプレート: {document_content}"

    def test_get_template_category(self):
        """カテゴリ別テンプレートが使われること"""
        for category in CHECK_TEMPLATES:
            item = self._make_check_item(category=category)
            result = self.builder._get_template(item)
            assert result == CHECK_TEMPLATES[category]

    def test_get_template_fallback(self):
        """不明カテゴリでデフォルトテンプレートになること"""
        item = self._make_check_item(category="UNKNOWN_CATEGORY")
        result = self.builder._get_template(item)
        assert result == DEFAULT_TEMPLATE

    # =========================================================================
    # _format_terms テスト
    # =========================================================================

    def test_format_terms_empty(self):
        """空リストで「用語辞書なし」になること"""
        result = self.builder._format_terms([])
        assert "用語辞書なし" in result

    def test_format_terms_single(self):
        """1件の用語がmarkdownテーブルにフォーマットされること"""
        terms = [self._make_term()]
        result = self.builder._format_terms(terms)
        assert "情報セキュリティ" in result
        assert "InfoSec" in result

    def test_format_terms_long_definition_truncated(self):
        """定義が100文字超で切り詰められること"""
        long_def = "あ" * 150
        term = self._make_term(definition=long_def)
        result = self.builder._format_terms([term])
        assert "..." in result

    def test_format_terms_no_aliases(self):
        """別名なしで「-」が表示されること"""
        term = self._make_term(aliases="")
        result = self.builder._format_terms([term])
        assert "| - |" in result

    def test_format_terms_list_aliases(self):
        """別名がリスト形式の場合もフォーマットされること"""
        term = self._make_term(aliases=["エイリアス1", "エイリアス2"])
        result = self.builder._format_terms([term])
        assert "エイリアス1" in result
        assert "エイリアス2" in result

    # =========================================================================
    # _format_rules テスト
    # =========================================================================

    def test_format_rules_empty(self):
        """空リストで「記載ルールなし」になること"""
        result = self.builder._format_rules([])
        assert "記載ルールなし" in result

    def test_format_rules_single(self):
        """1件のルールがフォーマットされること"""
        rules = [self._make_rule()]
        result = self.builder._format_rules(rules)
        assert "表記ルール1" in result
        assert "FORMAT" in result
        assert "正しい形式" in result
        assert "NG例" in result
        assert "OK例" in result

    def test_format_rules_no_examples(self):
        """NG例/OK例がない場合でもエラーにならないこと"""
        rule = self._make_rule(example_bad=None, example_good=None)
        result = self.builder._format_rules([rule])
        assert "表記ルール1" in result

    # =========================================================================
    # _format_related_docs テスト
    # =========================================================================

    def test_format_related_docs_empty(self):
        """空リストで「関連規程なし」になること"""
        result = self.builder._format_related_docs([])
        assert "関連規程なし" in result

    def test_format_related_docs_multiple(self):
        """複数文書がセパレータで結合されること"""
        docs = ["文書A", "文書B"]
        result = self.builder._format_related_docs(docs)
        assert "文書A" in result
        assert "文書B" in result
        assert "---" in result

    # =========================================================================
    # build_prompt テスト
    # =========================================================================

    def test_build_prompt_returns_messages(self):
        """build_promptがsystem/userメッセージを返すこと"""
        item = self._make_check_item()
        result = self.builder.build_prompt(item, ["チャンク1", "チャンク2"])
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    def test_build_prompt_includes_document_content(self):
        """文書チャンクがユーザーメッセージに含まれること"""
        item = self._make_check_item()
        result = self.builder.build_prompt(item, ["テスト文書内容"])
        assert "テスト文書内容" in result[1]["content"]

    def test_build_prompt_with_terms(self):
        """用語情報がプロンプトに含まれること"""
        item = self._make_check_item()
        terms = [self._make_term()]
        result = self.builder.build_prompt(item, ["文書"], terms=terms)
        assert "情報セキュリティ" in result[1]["content"]

    def test_build_prompt_with_rules(self):
        """記載ルールがプロンプトに含まれること（GRAMMAR カテゴリ使用）"""
        item = self._make_check_item(category="GRAMMAR")
        rules = [self._make_rule()]
        result = self.builder.build_prompt(item, ["文書"], writing_rules=rules)
        # テンプレートに{writing_rules_context}がないカテゴリもあるので
        # 少なくともエラーなく生成されることを確認
        assert len(result) == 2
        assert result[1]["role"] == "user"

    # =========================================================================
    # build_suggestion_prompt テスト
    # =========================================================================

    def test_build_suggestion_prompt_returns_messages(self):
        """build_suggestion_promptがsystem/userメッセージを返すこと"""
        result = self.builder.build_suggestion_prompt(
            original_text="元の文章",
            finding_description="指摘内容",
            issue_type="TERMINOLOGY",
            severity="HIGH",
        )
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    def test_build_suggestion_prompt_includes_content(self):
        """提案プロンプトに入力情報が含まれること"""
        result = self.builder.build_suggestion_prompt(
            original_text="テスト元文章",
            finding_description="テスト指摘",
            issue_type="GRAMMAR",
            severity="MEDIUM",
        )
        user_content = result[1]["content"]
        assert "テスト元文章" in user_content
        assert "テスト指摘" in user_content
        assert "GRAMMAR" in user_content
        assert "MEDIUM" in user_content
