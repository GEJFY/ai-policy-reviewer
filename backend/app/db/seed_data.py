"""
初期データ投入スクリプト
規程レビューツールの初期マスタデータを投入する
"""

import json
import asyncio
import struct
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.base import Base
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule
from app.services.embedding_service import embedding_service


# ============================================================
# 用語辞書データ
# ============================================================
TERMS_DATA = [
    # 人事関連
    {
        "term": "従業員",
        "aliases": ["社員", "スタッフ", "職員"],
        "definition": "当社と雇用契約を締結し、業務に従事する者をいう。正社員、契約社員、パートタイマー等の雇用形態を問わない。",
        "category": "人事",
        "usage_note": "「社員」ではなく「従業員」を正式用語として使用すること。"
    },
    {
        "term": "管理職",
        "aliases": ["マネージャー", "管理者"],
        "definition": "課長以上の職位にある者で、部下の指揮監督を行う権限を有する者をいう。",
        "category": "人事",
        "usage_note": "「マネージャー」は外来語のため、正式文書では「管理職」を使用。"
    },
    {
        "term": "派遣社員",
        "aliases": ["派遣スタッフ", "派遣労働者"],
        "definition": "労働者派遣契約に基づき、派遣元から当社に派遣され業務に従事する者をいう。",
        "category": "人事",
        "usage_note": None
    },
    {
        "term": "所属長",
        "aliases": ["上長", "上司", "直属の上司"],
        "definition": "従業員が所属する部門の責任者をいう。原則として課長職以上の者を指す。",
        "category": "人事",
        "usage_note": "「上長」「上司」は曖昧なため、「所属長」を使用すること。"
    },
    # IT関連
    {
        "term": "情報システム",
        "aliases": ["システム", "IT", "情シス"],
        "definition": "当社の業務遂行に使用するコンピュータシステム、ネットワーク、ソフトウェア等の総称をいう。",
        "category": "IT",
        "usage_note": "略称「IT」は使用可能だが、初出時は正式名称を記載。"
    },
    {
        "term": "個人情報",
        "aliases": ["パーソナルデータ", "個人データ"],
        "definition": "生存する個人に関する情報であって、当該情報に含まれる氏名、生年月日その他の記述等により特定の個人を識別できるものをいう。",
        "category": "IT",
        "usage_note": "個人情報保護法の定義に準拠。"
    },
    {
        "term": "機密情報",
        "aliases": ["秘密情報", "Confidential"],
        "definition": "当社の事業活動に関する情報のうち、開示範囲を制限し保護すべきものとして指定された情報をいう。",
        "category": "IT",
        "usage_note": "機密区分（極秘・秘・社外秘）を明記すること。"
    },
    # 法務関連
    {
        "term": "取締役会",
        "aliases": ["取会", "Board"],
        "definition": "会社法に基づき設置される当社の業務執行の意思決定機関をいう。",
        "category": "法務",
        "usage_note": "略称の使用は不可。"
    },
    {
        "term": "コンプライアンス",
        "aliases": ["法令遵守", "法令順守"],
        "definition": "法令、社内規程、社会規範等を遵守し、企業活動を行うことをいう。",
        "category": "法務",
        "usage_note": "「法令遵守」との併記も可。"
    },
    {
        "term": "稟議",
        "aliases": ["りんぎ", "決裁"],
        "definition": "業務執行に係る事項について、所定の権限者の承認を得るための手続きをいう。",
        "category": "法務",
        "usage_note": "「決裁」は承認行為を指し、「稟議」は申請から承認までの一連のプロセスを指す。"
    },
    # 財務関連
    {
        "term": "経費",
        "aliases": ["費用", "コスト"],
        "definition": "業務遂行のために支出する費用をいう。旅費交通費、接待交際費、消耗品費等を含む。",
        "category": "財務",
        "usage_note": None
    },
    {
        "term": "予算",
        "aliases": ["Budget"],
        "definition": "事業年度における収入および支出の計画をいう。",
        "category": "財務",
        "usage_note": None
    },
    # 一般
    {
        "term": "営業日",
        "aliases": ["稼働日", "業務日"],
        "definition": "当社が通常の業務を行う日をいう。土曜日、日曜日、祝日および会社が定める休業日を除く。",
        "category": "一般",
        "usage_note": "「稼働日」ではなく「営業日」を使用すること。"
    },
    {
        "term": "別途定める",
        "aliases": ["別に定める", "別途規定する"],
        "definition": "本規程以外の規程、細則、要領等で詳細を定めることを示す。",
        "category": "一般",
        "usage_note": "参照先を明記することが望ましい。"
    },
]


# ============================================================
# チェック項目データ
# ============================================================
CHECK_ITEMS_DATA = [
    {
        "name": "用語統一チェック",
        "category": "TERMINOLOGY",
        "description": "社内用語辞書に登録された正式用語との不一致、表記ゆれを検出する。同一文書内での用語の統一性を確認する。",
        "severity": "MEDIUM",
        "is_active": True,
        "prompt_template": None  # デフォルトテンプレートを使用
    },
    {
        "name": "曖昧表現チェック",
        "category": "GRAMMAR",
        "description": "「等」「など」「原則として」「適宜」「速やかに」等の曖昧な表現を検出し、具体的な表現への変更を提案する。",
        "severity": "MEDIUM",
        "is_active": True,
        "prompt_template": None
    },
    {
        "name": "責任主体明確化チェック",
        "category": "STRUCTURE",
        "description": "各条項において、誰が（Who）、いつ（When）、何を（What）行うかが明確に定義されているかを確認する。",
        "severity": "HIGH",
        "is_active": True,
        "prompt_template": None
    },
    {
        "name": "法令参照チェック",
        "category": "COMPLIANCE",
        "description": "参照されている法令名、条文番号の正確性を確認する。法改正により内容が変更されていないかを確認する。",
        "severity": "HIGH",
        "is_active": True,
        "prompt_template": None
    },
    {
        "name": "他規程参照チェック",
        "category": "CONSISTENCY",
        "description": "他の社内規程を参照している箇所について、参照先との整合性を確認する。用語の定義、手続きの内容に矛盾がないかを検証する。",
        "severity": "MEDIUM",
        "is_active": True,
        "prompt_template": None
    },
    {
        "name": "セキュリティ要件チェック",
        "category": "SECURITY",
        "description": "情報セキュリティの観点から、機密分類、アクセス制御、保管・廃棄ルール等が適切に定義されているかを確認する。",
        "severity": "HIGH",
        "is_active": True,
        "prompt_template": None
    },
    {
        "name": "実務適合性チェック",
        "category": "OPERATIONAL",
        "description": "規程の内容が実務上実行可能かを確認する。承認フローの妥当性、期限の現実性、必要リソースの合理性を検証する。",
        "severity": "MEDIUM",
        "is_active": True,
        "prompt_template": None
    },
]


# ============================================================
# 記載ルールデータ
# ============================================================
WRITING_RULES_DATA = [
    {
        "name": "敬体統一（です・ます調）",
        "rule_type": "STYLE",
        "pattern": "文末表現",
        "correct_form": "文末は「です」「ます」「である」のいずれかで統一する。規程類は「である」調を標準とする。",
        "example_bad": "申請する。承認されます。",
        "example_good": "申請する。承認される。",
        "is_active": True
    },
    {
        "name": "西暦表記",
        "rule_type": "FORMAT",
        "pattern": "年号・日付表記",
        "correct_form": "日付は西暦4桁で表記する。和暦を併記する場合は西暦を主とする。",
        "example_bad": "令和6年4月1日",
        "example_good": "2024年4月1日（令和6年）",
        "is_active": True
    },
    {
        "name": "句読点の統一",
        "rule_type": "FORMAT",
        "pattern": "句読点",
        "correct_form": "句点は「。」、読点は「、」を使用する。「，」「．」は使用しない。",
        "example_bad": "申請書を提出し，承認を得る．",
        "example_good": "申請書を提出し、承認を得る。",
        "is_active": True
    },
    {
        "name": "条項番号形式",
        "rule_type": "FORMAT",
        "pattern": "条・項・号の表記",
        "correct_form": "条は「第○条」、項は「第○項」または数字のみ、号は「（○）」形式で表記する。",
        "example_bad": "1条 1項 1号",
        "example_good": "第1条 第1項 （1）",
        "is_active": True
    },
    {
        "name": "数字表記の統一",
        "rule_type": "FORMAT",
        "pattern": "数字表記",
        "correct_form": "数量・金額は算用数字（1, 2, 3）、固有名詞・慣用句は漢数字を使用する。",
        "example_bad": "三日以内に１回",
        "example_good": "3日以内に1回",
        "is_active": True
    },
    {
        "name": "外来語のカタカナ表記",
        "rule_type": "TERMINOLOGY",
        "pattern": "外来語表記",
        "correct_form": "IT用語等の外来語はカタカナで表記する。初出時は原語を（）内に併記してもよい。",
        "example_bad": "Compliance、Security",
        "example_good": "コンプライアンス、セキュリティ",
        "is_active": True
    },
    {
        "name": "受動態の回避",
        "rule_type": "STYLE",
        "pattern": "受動態表現",
        "correct_form": "主体を明確にするため、可能な限り能動態で記述する。受動態を使用する場合は主体を明記する。",
        "example_bad": "申請書が提出される。",
        "example_good": "申請者は申請書を提出する。",
        "is_active": True
    },
    {
        "name": "参照形式の統一",
        "rule_type": "FORMAT",
        "pattern": "規程・法令の参照",
        "correct_form": "規程は「○○規程第○条」、法令は「○○法第○条第○項」の形式で参照する。",
        "example_bad": "就業規則を参照",
        "example_good": "就業規則第10条第2項を参照",
        "is_active": True
    },
]


async def seed_terms(db: Session) -> int:
    """用語辞書データを投入"""
    count = 0
    for term_data in TERMS_DATA:
        # 既存チェック
        existing = db.query(Term).filter(Term.term == term_data["term"]).first()
        if existing:
            continue

        # Embedding生成
        embedding_bytes = None
        if embedding_service.is_available():
            try:
                embed_text = f"{term_data['term']}: {term_data['definition']}"
                embedding = await embedding_service.get_embedding(embed_text)
                embedding_bytes = embedding_service.embedding_to_bytes(embedding)
            except Exception as e:
                print(f"  Warning: Failed to generate embedding for '{term_data['term']}': {e}")

        term = Term(
            term=term_data["term"],
            aliases=json.dumps(term_data["aliases"], ensure_ascii=False) if term_data["aliases"] else None,
            definition=term_data["definition"],
            category=term_data["category"],
            usage_note=term_data["usage_note"],
            embedding=embedding_bytes,
        )
        db.add(term)
        count += 1

    db.commit()
    return count


def seed_check_items(db: Session) -> int:
    """チェック項目データを投入"""
    count = 0
    for item_data in CHECK_ITEMS_DATA:
        # 既存チェック
        existing = db.query(CheckItem).filter(CheckItem.name == item_data["name"]).first()
        if existing:
            continue

        item = CheckItem(
            name=item_data["name"],
            category=item_data["category"],
            description=item_data["description"],
            severity=item_data["severity"],
            prompt_template=item_data["prompt_template"],
            is_active=item_data["is_active"],
        )
        db.add(item)
        count += 1

    db.commit()
    return count


def seed_writing_rules(db: Session) -> int:
    """記載ルールデータを投入"""
    count = 0
    for rule_data in WRITING_RULES_DATA:
        # 既存チェック
        existing = db.query(WritingRule).filter(WritingRule.name == rule_data["name"]).first()
        if existing:
            continue

        rule = WritingRule(
            name=rule_data["name"],
            rule_type=rule_data["rule_type"],
            pattern=rule_data["pattern"],
            correct_form=rule_data["correct_form"],
            example_bad=rule_data["example_bad"],
            example_good=rule_data["example_good"],
            is_active=rule_data["is_active"],
        )
        db.add(rule)
        count += 1

    db.commit()
    return count


async def seed_all():
    """全データを投入"""
    print("=" * 60)
    print("初期データ投入を開始します")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 用語辞書
        print("\n[1/3] 用語辞書データを投入中...")
        terms_count = await seed_terms(db)
        print(f"  -> {terms_count}件の用語を追加しました")

        # チェック項目
        print("\n[2/3] チェック項目データを投入中...")
        items_count = seed_check_items(db)
        print(f"  -> {items_count}件のチェック項目を追加しました")

        # 記載ルール
        print("\n[3/3] 記載ルールデータを投入中...")
        rules_count = seed_writing_rules(db)
        print(f"  -> {rules_count}件の記載ルールを追加しました")

        print("\n" + "=" * 60)
        print("初期データ投入が完了しました")
        print(f"  用語辞書: {terms_count}件")
        print(f"  チェック項目: {items_count}件")
        print(f"  記載ルール: {rules_count}件")
        print("=" * 60)

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed_all())
