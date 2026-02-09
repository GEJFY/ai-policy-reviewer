"""Prompt builder service for constructing review prompts."""

from typing import Optional
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.prompts.check_templates import CHECK_TEMPLATES, DEFAULT_TEMPLATE
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule


class PromptBuilder:
    """Service for building prompts for AI review."""

    def __init__(self):
        """Initialize the prompt builder."""
        self.system_prompt = SYSTEM_PROMPT
        self.templates = CHECK_TEMPLATES

    def build_prompt(
        self,
        check_item: CheckItem,
        document_chunks: list[str],
        terms: Optional[list[Term]] = None,
        writing_rules: Optional[list[WritingRule]] = None,
        related_docs: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Build a complete prompt for AI review.

        Args:
            check_item: The check item being evaluated
            document_chunks: Document content chunks
            terms: Relevant terms from the dictionary
            writing_rules: Applicable writing rules
            related_docs: Related document content for consistency checks

        Returns:
            List of message dicts for the chat API
        """
        # Get template for this category
        template = self._get_template(check_item)

        # Build context strings
        terms_context = self._format_terms(terms) if terms else "（用語辞書なし）"
        rules_context = (
            self._format_rules(writing_rules) if writing_rules else "（記載ルールなし）"
        )
        related_context = (
            self._format_related_docs(related_docs)
            if related_docs
            else "（関連規程なし）"
        )
        doc_content = "\n\n---\n\n".join(document_chunks)

        # Fill template
        user_prompt = template.format(
            terms_context=terms_context,
            writing_rules_context=rules_context,
            related_documents_context=related_context,
            document_content=doc_content,
            check_item_description=check_item.description,
        )

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _get_template(self, check_item: CheckItem) -> str:
        """Get the appropriate template for the check item."""
        # Use custom template if available
        if check_item.prompt_template:
            return check_item.prompt_template

        # Use category-specific template
        category = check_item.category
        if category in self.templates:
            return self.templates[category]

        # Fallback to default
        return DEFAULT_TEMPLATE

    def _format_terms(self, terms: list[Term]) -> str:
        """Format terms list as markdown table."""
        if not terms:
            return "（用語辞書なし）"

        lines = ["| 正式用語 | 別名 | 定義 |", "|---|---|---|"]
        for term in terms:
            aliases = (
                term.aliases
                if isinstance(term.aliases, str)
                else ", ".join(term.aliases or [])
            )
            if not aliases:
                aliases = "-"
            # Truncate long definitions
            definition = (
                term.definition[:100] + "..."
                if len(term.definition) > 100
                else term.definition
            )
            lines.append(f"| {term.term} | {aliases} | {definition} |")

        return "\n".join(lines)

    def _format_rules(self, rules: list[WritingRule]) -> str:
        """Format writing rules as list."""
        if not rules:
            return "（記載ルールなし）"

        lines = []
        for rule in rules:
            lines.append(f"- **{rule.name}** ({rule.rule_type})")
            lines.append(f"  - 正しい形式: {rule.correct_form}")
            if rule.example_bad:
                lines.append(f"  - NG例: {rule.example_bad}")
            if rule.example_good:
                lines.append(f"  - OK例: {rule.example_good}")

        return "\n".join(lines)

    def _format_related_docs(self, docs: list[str]) -> str:
        """Format related documents."""
        if not docs:
            return "（関連規程なし）"

        return "\n\n---\n\n".join(docs)

    def build_suggestion_prompt(
        self,
        original_text: str,
        finding_description: str,
        issue_type: str,
        severity: str,
    ) -> list[dict]:
        """
        Build a prompt for generating improvement suggestions.

        Args:
            original_text: Original problematic text
            finding_description: Description of the issue
            issue_type: Type of the issue
            severity: Severity level

        Returns:
            List of message dicts
        """
        system = """あなたは規程文書の改善提案を行う専門家です。
指摘内容を踏まえ、改善後の文章を生成してください。

## 制約
1. 元の文章の意図を保持すること
2. 過度な変更を避け、最小限の修正にとどめること
3. 規程文書としての格調を維持すること

## 出力形式
```json
{
  "original": "元の文章",
  "revised": "改善後の文章",
  "change_summary": "変更内容の要約",
  "confidence": "HIGH|MEDIUM|LOW"
}
```
"""

        user = f"""## 元の文章
{original_text}

## 指摘内容
{finding_description}

## 問題種別
{issue_type}

## 重要度
{severity}

上記の指摘を反映した改善案を生成してください。"""

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]


# Singleton instance
prompt_builder = PromptBuilder()
