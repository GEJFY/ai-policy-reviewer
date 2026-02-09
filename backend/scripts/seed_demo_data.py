"""
デモ用ダミーデータ投入スクリプト

規程レビューツールのデモに必要なサンプルデータを投入します。
- 用語辞書: 50件
- チェック項目: 20件
- 記載ルール: 15件

Usage:
    cd backend
    python -m scripts.seed_demo_data
"""

import sys
import os
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.base import Base
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule


# =============================================================================
# 用語辞書データ（50件）
# =============================================================================
TERMS_DATA = [
    # ----- 人事カテゴリ（15件）-----
    {
        "term": "従業員",
        "definition": "当社と雇用契約を締結し、労務を提供する者の総称。正社員、契約社員、パートタイマー、嘱託社員を含む。",
        "category": "人事",
        "aliases": '["社員", "スタッフ", "職員"]',
        "usage_note": "規程内では「従業員」に統一。「社員」は正社員のみを指す場合に使用。"
    },
    {
        "term": "正社員",
        "definition": "当社と期間の定めのない雇用契約を締結した従業員。フルタイム勤務を原則とする。",
        "category": "人事",
        "aliases": '["正規社員", "正規従業員"]',
        "usage_note": "「正規社員」は旧表記のため「正社員」を使用すること。"
    },
    {
        "term": "契約社員",
        "definition": "当社と期間の定めのある雇用契約を締結した従業員。契約期間は原則1年以内とし、更新は最長5年まで。",
        "category": "人事",
        "aliases": '["有期契約社員", "有期雇用社員"]',
        "usage_note": "2024年4月より「有期雇用社員」の表記を廃止。"
    },
    {
        "term": "パートタイマー",
        "definition": "1週間の所定労働時間が正社員より短い従業員。",
        "category": "人事",
        "aliases": '["パート", "短時間労働者", "パート社員"]',
        "usage_note": "法令では「短時間労働者」だが、社内規程では「パートタイマー」を使用。"
    },
    {
        "term": "嘱託社員",
        "definition": "定年退職後に再雇用された従業員。原則として65歳まで雇用を継続する。",
        "category": "人事",
        "aliases": '["嘱託", "再雇用社員", "シニア社員"]',
        "usage_note": "高年齢者雇用安定法に基づく継続雇用制度による雇用形態。"
    },
    {
        "term": "管理監督者",
        "definition": "労働基準法第41条第2号に定める管理監督者に該当する者。部長職以上を原則とする。",
        "category": "人事",
        "aliases": '["管理職", "マネージャー"]',
        "usage_note": "法的定義と異なるため、「管理職」と「管理監督者」は区別して使用すること。"
    },
    {
        "term": "所定労働時間",
        "definition": "就業規則に定められた始業時刻から終業時刻までの時間から休憩時間を除いた時間。1日8時間、1週40時間を上限とする。",
        "category": "人事",
        "aliases": '["所定労働", "契約労働時間"]',
        "usage_note": "「法定労働時間」との混同に注意。"
    },
    {
        "term": "時間外労働",
        "definition": "法定労働時間（1日8時間、1週40時間）を超えて行う労働。36協定の締結が必要。",
        "category": "人事",
        "aliases": '["残業", "超過勤務", "超勤"]',
        "usage_note": "規程では「時間外労働」を使用。「残業」は口語表現。"
    },
    {
        "term": "年次有給休暇",
        "definition": "労働基準法第39条に基づき付与される有給の休暇。入社6ヶ月経過後、出勤率8割以上で10日付与。",
        "category": "人事",
        "aliases": '["有給休暇", "有休", "年休"]',
        "usage_note": "略称「有休」「年休」は口語。規程では「年次有給休暇」を使用。"
    },
    {
        "term": "休職",
        "definition": "従業員としての身分を保持したまま、一定期間就労義務を免除すること。傷病休職、自己都合休職等がある。",
        "category": "人事",
        "aliases": '["休業"]',
        "usage_note": "「休職」と「休業」は異なる。「休業」は会社都合または法定（育児・介護等）を指す。"
    },
    {
        "term": "懲戒処分",
        "definition": "企業秩序違反に対する制裁。譴責、減給、出勤停止、降格、諭旨解雇、懲戒解雇の6種類を設ける。",
        "category": "人事",
        "aliases": '["懲戒", "制裁", "処分"]',
        "usage_note": "具体的な処分を示す場合は種別を明記すること。"
    },
    {
        "term": "解雇",
        "definition": "使用者による一方的な労働契約の解約。普通解雇と懲戒解雇がある。",
        "category": "人事",
        "aliases": '["免職", "罷免"]',
        "usage_note": "「免職」「罷免」は公務員用語。民間企業では「解雇」を使用。"
    },
    {
        "term": "退職",
        "definition": "労働契約の終了。自己都合退職、会社都合退職、定年退職等がある。",
        "category": "人事",
        "aliases": '["離職"]',
        "usage_note": "「離職」は雇用保険上の用語。社内規程では「退職」を使用。"
    },
    {
        "term": "人事考課",
        "definition": "従業員の業績・能力・態度を評価し、処遇に反映させる制度。年2回（上期・下期）実施。",
        "category": "人事",
        "aliases": '["人事評価", "業績評価", "考課"]',
        "usage_note": "「人事評価」との混用注意。当社では「人事考課」を正式名称とする。"
    },
    {
        "term": "賃金",
        "definition": "労働の対償として使用者が労働者に支払うすべてのもの。基本給、諸手当、賞与を含む。",
        "category": "人事",
        "aliases": '["給与", "報酬", "給料"]',
        "usage_note": "労働基準法では「賃金」。社内では「給与」も可だが、規程は「賃金」で統一。"
    },

    # ----- 法務カテゴリ（10件）-----
    {
        "term": "決裁権限",
        "definition": "業務執行について最終的な意思決定を行う権限。職位に応じて決裁権限規程で定める。",
        "category": "法務",
        "aliases": '["決裁権", "承認権限"]',
        "usage_note": "「承認」は中間段階、「決裁」は最終意思決定を指す。"
    },
    {
        "term": "稟議",
        "definition": "意思決定を得るために、関係者の回覧・承認を経て決裁者の承認を得る手続き。",
        "category": "法務",
        "aliases": '["起案", "伺い"]',
        "usage_note": "電子稟議システム導入後も「稟議」の用語は継続使用。"
    },
    {
        "term": "取締役会",
        "definition": "会社法に基づく機関。取締役全員で構成され、業務執行の決定および取締役の職務執行の監督を行う。",
        "category": "法務",
        "aliases": '["役員会", "Board"]',
        "usage_note": "「役員会」は口語。規程では「取締役会」を使用。"
    },
    {
        "term": "代表取締役",
        "definition": "会社を代表する権限を有する取締役。対外的に会社を代表し、業務を執行する。",
        "category": "法務",
        "aliases": '["社長", "CEO"]',
        "usage_note": "「社長」は役職名であり、法的地位ではない。法的文書では「代表取締役」を使用。"
    },
    {
        "term": "利益相反取引",
        "definition": "取締役が自己または第三者のために会社と取引を行うこと。取締役会の承認が必要。",
        "category": "法務",
        "aliases": '["競業取引", "自己取引"]',
        "usage_note": "会社法第356条に基づく。「競業取引」は別概念なので混同しないこと。"
    },
    {
        "term": "コンプライアンス",
        "definition": "法令遵守のみならず、社内規程、企業倫理、社会規範を遵守すること。",
        "category": "法務",
        "aliases": '["法令遵守", "法令順守"]',
        "usage_note": "広義のコンプライアンスは法令遵守だけでなく倫理・社会規範も含む。"
    },
    {
        "term": "内部通報",
        "definition": "法令違反行為等を発見した従業員が、所定の窓口に通報すること。公益通報者保護法に基づく保護対象。",
        "category": "法務",
        "aliases": '["公益通報", "ホットライン", "内部告発"]',
        "usage_note": "「内部告発」はネガティブな印象があるため「内部通報」を使用。"
    },
    {
        "term": "個人情報",
        "definition": "生存する個人に関する情報であって、特定の個人を識別できるもの。個人情報保護法に基づく取扱いが必要。",
        "category": "法務",
        "aliases": '["パーソナルデータ", "個人データ"]',
        "usage_note": "「個人データ」は個人情報保護法上の定義。規程では文脈に応じて使い分け。"
    },
    {
        "term": "契約",
        "definition": "当事者間の意思表示の合致によって成立する法律行為。権利義務関係を発生させる。",
        "category": "法務",
        "aliases": '["合意", "約定"]',
        "usage_note": "「合意」は契約の前段階も含む広い概念。法的拘束力を持つ場合は「契約」を使用。"
    },
    {
        "term": "守秘義務",
        "definition": "業務上知り得た秘密を第三者に開示・漏洩してはならない義務。在職中および退職後も継続。",
        "category": "法務",
        "aliases": '["秘密保持義務", "機密保持義務", "NDA"]',
        "usage_note": "契約書では「秘密保持義務」、就業規則では「守秘義務」を使用することが多い。"
    },

    # ----- 財務カテゴリ（10件）-----
    {
        "term": "予算",
        "definition": "一定期間における収入・支出の計画。年度予算は取締役会で承認される。",
        "category": "財務",
        "aliases": '["バジェット", "Budget"]',
        "usage_note": "英語表記は社内文書では避ける。"
    },
    {
        "term": "決算",
        "definition": "一定期間の経営成績と財政状態を確定する手続き。四半期決算と年度決算がある。",
        "category": "財務",
        "aliases": '["決算処理", "決算業務"]',
        "usage_note": "「決算」は結果と過程の両方を指す。"
    },
    {
        "term": "経費",
        "definition": "事業遂行に必要な費用。旅費交通費、交際費、消耗品費等を含む。",
        "category": "財務",
        "aliases": '["費用", "コスト", "支出"]',
        "usage_note": "「経費」は会計上の費用勘定を指す。日常的な「支出」とは区別。"
    },
    {
        "term": "仮払い",
        "definition": "経費の概算額を事前に支給すること。使途確定後に精算を行う。",
        "category": "財務",
        "aliases": '["仮払金", "概算払い"]',
        "usage_note": "「前払い」とは異なる。前払いは債務の履行、仮払いは概算支給。"
    },
    {
        "term": "精算",
        "definition": "仮払い金や立替金の使途を確定し、過不足を調整すること。",
        "category": "財務",
        "aliases": '["清算"]',
        "usage_note": "「清算」は法人の解散時に使用。経費処理は「精算」。"
    },
    {
        "term": "売掛金",
        "definition": "商品・サービスの販売により発生した未回収の債権。",
        "category": "財務",
        "aliases": '["売上債権", "未収金"]',
        "usage_note": "「未収金」は営業外の債権。営業上の債権は「売掛金」。"
    },
    {
        "term": "買掛金",
        "definition": "商品・サービスの購入により発生した未払いの債務。",
        "category": "財務",
        "aliases": '["仕入債務", "未払金"]',
        "usage_note": "「未払金」は営業外の債務。営業上の債務は「買掛金」。"
    },
    {
        "term": "固定資産",
        "definition": "1年以上使用する資産で、取得価額が10万円以上のもの。土地、建物、機械装置、車両等。",
        "category": "財務",
        "aliases": '["有形固定資産", "設備"]',
        "usage_note": "「設備」は広義。会計上の「固定資産」は取得価額基準がある。"
    },
    {
        "term": "減価償却",
        "definition": "固定資産の取得価額を耐用年数にわたって費用配分する手続き。",
        "category": "財務",
        "aliases": '["償却"]',
        "usage_note": "「償却」は広義。固定資産に対する費用配分は「減価償却」を使用。"
    },
    {
        "term": "税務調査",
        "definition": "税務署による納税申告の正確性を確認するための調査。事前通知が原則。",
        "category": "財務",
        "aliases": '["税務調査", "査察"]',
        "usage_note": "「査察」は国税犯則取締法に基づく強制調査。通常は「税務調査」。"
    },

    # ----- ITカテゴリ（8件）-----
    {
        "term": "情報システム",
        "definition": "業務処理を行うためのコンピュータシステム全般。ハードウェア、ソフトウェア、ネットワークを含む。",
        "category": "IT",
        "aliases": '["システム", "IT基盤"]',
        "usage_note": "単に「システム」と言う場合は文脈で判断。規程では「情報システム」を使用。"
    },
    {
        "term": "情報資産",
        "definition": "情報および情報を管理・処理するための設備・システム等の総称。保護の対象となる。",
        "category": "IT",
        "aliases": '["情報資源", "ITアセット"]',
        "usage_note": "情報セキュリティポリシーでは「情報資産」を使用。"
    },
    {
        "term": "アクセス権限",
        "definition": "情報システムや情報資産へのアクセスを許可される範囲。職務に応じて付与される。",
        "category": "IT",
        "aliases": '["権限", "パーミッション"]',
        "usage_note": "単に「権限」と言う場合は決裁権限と混同の恐れあり。"
    },
    {
        "term": "パスワード",
        "definition": "本人認証に使用する秘密の文字列。8文字以上、英数字記号の組み合わせを必須とする。",
        "category": "IT",
        "aliases": '["暗証番号", "PIN"]',
        "usage_note": "「暗証番号」は数字のみの場合。英数字含む場合は「パスワード」。"
    },
    {
        "term": "ウイルス",
        "definition": "コンピュータに被害を与える不正プログラム。マルウェアの一種。",
        "category": "IT",
        "aliases": '["マルウェア", "不正プログラム"]',
        "usage_note": "「マルウェア」が正式だが、一般向けには「ウイルス」でも可。"
    },
    {
        "term": "バックアップ",
        "definition": "データの複製を作成し、障害時に復旧できるようにすること。日次、週次、月次の頻度で実施。",
        "category": "IT",
        "aliases": '["データ複製", "退避"]',
        "usage_note": "「バックアップ」は外来語だが定着している。規程でも使用可。"
    },
    {
        "term": "インシデント",
        "definition": "情報セキュリティ上の事故・事象。ウイルス感染、不正アクセス、情報漏洩等。",
        "category": "IT",
        "aliases": '["セキュリティインシデント", "事故"]',
        "usage_note": "「事故」は結果が明確な場合。予兆・疑いを含む場合は「インシデント」。"
    },
    {
        "term": "クラウドサービス",
        "definition": "インターネット経由で提供されるコンピュータ資源やソフトウェア。SaaS、PaaS、IaaSを含む。",
        "category": "IT",
        "aliases": '["クラウド", "外部サービス"]',
        "usage_note": "「クラウド」は略称。正式には「クラウドサービス」を使用。"
    },

    # ----- 一般カテゴリ（7件）-----
    {
        "term": "当社",
        "definition": "本規程を制定した会社を指す。株式会社サンプル商事。",
        "category": "一般",
        "aliases": '["弊社", "自社", "会社"]',
        "usage_note": "規程内では「当社」で統一。「弊社」は対外的な謙譲語。"
    },
    {
        "term": "本規程",
        "definition": "現在参照している規程を指す自己参照語。",
        "category": "一般",
        "aliases": '["この規程", "本規定"]',
        "usage_note": "「規定」は条文の内容、「規程」は規則文書全体を指す。"
    },
    {
        "term": "別途定める",
        "definition": "本規程とは別の規程・細則・要領等で詳細を定めることを示す。",
        "category": "一般",
        "aliases": '["別に定める", "細則で定める"]',
        "usage_note": "具体的な規程名がある場合は明記することが望ましい。"
    },
    {
        "term": "遅滞なく",
        "definition": "合理的な期間内にすみやかに行うことを意味する法律用語。具体的な日数は状況による。",
        "category": "一般",
        "aliases": '["速やかに", "直ちに"]',
        "usage_note": "「直ちに」>「速やかに」>「遅滞なく」の順に緊急度が高い。"
    },
    {
        "term": "所属長",
        "definition": "従業員が所属する組織の長。部長、課長、グループリーダー等。",
        "category": "一般",
        "aliases": '["上長", "上司", "直属上司"]',
        "usage_note": "規程では「所属長」を使用。「上司」は口語。"
    },
    {
        "term": "事業年度",
        "definition": "会計期間の単位。4月1日から翌年3月31日までの1年間。",
        "category": "一般",
        "aliases": '["会計年度", "年度"]',
        "usage_note": "「年度」は略称。正式には「事業年度」を使用。"
    },
    {
        "term": "施行",
        "definition": "規程が効力を発生すること。制定・改定後に施行日を定めて実施する。",
        "category": "一般",
        "aliases": '["発効", "適用開始"]',
        "usage_note": "「施行」は法令・規程用語。ソフトウェアの「リリース」とは異なる。"
    },
]


# =============================================================================
# チェック項目データ（20件）
# =============================================================================
CHECK_ITEMS_DATA = [
    # ----- 用語統一（TERMINOLOGY）-----
    {
        "name": "社内用語の統一性チェック",
        "category": "TERMINOLOGY",
        "description": "規程内で使用される用語が、社内用語辞書に登録された正式名称と一致しているか確認します。同義語や略称が混在している場合は指摘します。",
        "severity": "HIGH",
        "prompt_template": "以下の文書を分析し、社内用語辞書と照合してください。用語の不統一（例：「従業員」と「社員」の混在）があれば指摘してください。",
        "is_active": True
    },
    {
        "name": "定義との整合性チェック",
        "category": "TERMINOLOGY",
        "description": "規程内で定義された用語が、その定義に沿った意味で一貫して使用されているか確認します。",
        "severity": "HIGH",
        "prompt_template": "文書内で定義されている用語を特定し、その用語がすべての箇所で定義通りに使用されているか確認してください。",
        "is_active": True
    },
    {
        "name": "曖昧な表現の検出",
        "category": "TERMINOLOGY",
        "description": "「など」「等」「その他」「適宜」「必要に応じて」などの曖昧な表現を検出し、明確化が必要な箇所を指摘します。",
        "severity": "MEDIUM",
        "prompt_template": "曖昧な表現（など、等、その他、適宜、必要に応じて、原則として）を検出し、明確化が望ましい箇所を指摘してください。",
        "is_active": True
    },

    # ----- 文法・文体（GRAMMAR）-----
    {
        "name": "文体統一チェック（である体）",
        "category": "GRAMMAR",
        "description": "規程文書は「である体」で統一されているべきです。「です・ます体」が混在している場合は指摘します。",
        "severity": "MEDIUM",
        "prompt_template": "文書全体を確認し、「である体」と「です・ます体」の混在がないか確認してください。",
        "is_active": True
    },
    {
        "name": "受動態の過剰使用チェック",
        "category": "GRAMMAR",
        "description": "主語と責任の所在が不明確になる受動態の過剰使用を検出します。能動態への書き換えを推奨します。",
        "severity": "LOW",
        "prompt_template": "受動態で書かれた文を特定し、主語・責任者が不明確になっている箇所を指摘してください。",
        "is_active": True
    },
    {
        "name": "一文の長さチェック",
        "category": "GRAMMAR",
        "description": "一文が長すぎる（80文字以上）場合、可読性が低下します。適切な文の分割を推奨します。",
        "severity": "LOW",
        "prompt_template": "80文字以上の長い文を特定し、分割を推奨してください。",
        "is_active": True
    },

    # ----- 構造・形式（STRUCTURE）-----
    {
        "name": "条番号の連続性チェック",
        "category": "STRUCTURE",
        "description": "条文番号（第1条、第2条...）が連続しており、欠番や重複がないことを確認します。",
        "severity": "HIGH",
        "prompt_template": "条文番号を抽出し、連続性を確認してください。欠番や重複があれば指摘してください。",
        "is_active": True
    },
    {
        "name": "項・号の形式チェック",
        "category": "STRUCTURE",
        "description": "項（1、2、3...）と号（(1)、(2)...）の形式が統一されているか確認します。",
        "severity": "MEDIUM",
        "prompt_template": "項と号の番号形式を確認し、形式の不統一があれば指摘してください。",
        "is_active": True
    },
    {
        "name": "章・節構成の妥当性チェック",
        "category": "STRUCTURE",
        "description": "章・節の構成が論理的であり、適切な粒度で分類されているか確認します。",
        "severity": "LOW",
        "prompt_template": "章・節の構成を分析し、構成上の改善点があれば指摘してください。",
        "is_active": True
    },

    # ----- 法的要件（COMPLIANCE）-----
    {
        "name": "労働基準法対応チェック",
        "category": "COMPLIANCE",
        "description": "就業規則が労働基準法の必須記載事項を満たしているか確認します。",
        "severity": "HIGH",
        "prompt_template": "労働基準法第89条で定められた就業規則の必須記載事項（労働時間、賃金、退職等）が含まれているか確認してください。",
        "is_active": True
    },
    {
        "name": "個人情報保護法対応チェック",
        "category": "COMPLIANCE",
        "description": "個人情報の取扱いに関する規程が個人情報保護法の要件を満たしているか確認します。",
        "severity": "HIGH",
        "prompt_template": "個人情報の取得、利用目的、第三者提供、安全管理措置について、法的要件を満たしているか確認してください。",
        "is_active": True
    },
    {
        "name": "ハラスメント防止義務チェック",
        "category": "COMPLIANCE",
        "description": "パワハラ防止法（労働施策総合推進法）で義務付けられた措置が規程に含まれているか確認します。",
        "severity": "HIGH",
        "prompt_template": "ハラスメントの定義、相談窓口、対応手順が明記されているか確認してください。",
        "is_active": True
    },

    # ----- 整合性（CONSISTENCY）-----
    {
        "name": "他規程との整合性チェック",
        "category": "CONSISTENCY",
        "description": "参照している他の規程との内容の整合性を確認します。矛盾や齟齬があれば指摘します。",
        "severity": "HIGH",
        "prompt_template": "文書内で参照されている他の規程名を特定し、内容の整合性について確認が必要な箇所を指摘してください。",
        "is_active": True
    },
    {
        "name": "日付・期間の整合性チェック",
        "category": "CONSISTENCY",
        "description": "規程内の日付表記（和暦/西暦）の統一と、期間の矛盾がないか確認します。",
        "severity": "MEDIUM",
        "prompt_template": "日付表記の形式を確認し、不統一や矛盾する期間がないか確認してください。",
        "is_active": True
    },
    {
        "name": "金額・数値の整合性チェック",
        "category": "CONSISTENCY",
        "description": "規程内の金額や数値が一貫しており、計算上の矛盾がないか確認します。",
        "severity": "MEDIUM",
        "prompt_template": "金額や数値を抽出し、整合性を確認してください。矛盾があれば指摘してください。",
        "is_active": True
    },

    # ----- セキュリティ（SECURITY）-----
    {
        "name": "機密情報取扱いチェック",
        "category": "SECURITY",
        "description": "機密情報の分類、取扱い方法、廃棄手順が明確に定められているか確認します。",
        "severity": "HIGH",
        "prompt_template": "機密情報の分類基準、取扱いルール、廃棄方法が明確に規定されているか確認してください。",
        "is_active": True
    },
    {
        "name": "アクセス制御ルールチェック",
        "category": "SECURITY",
        "description": "情報システムへのアクセス制御（認証、認可、ログ）が適切に規定されているか確認します。",
        "severity": "HIGH",
        "prompt_template": "アクセス制御に関するルール（認証方式、権限付与、監査ログ）が明確か確認してください。",
        "is_active": True
    },

    # ----- 運用（OPERATIONAL）-----
    {
        "name": "責任者・担当部署の明確化チェック",
        "category": "OPERATIONAL",
        "description": "各業務プロセスの責任者や担当部署が明確に定められているか確認します。",
        "severity": "MEDIUM",
        "prompt_template": "業務プロセスごとに責任者・担当部署が明記されているか確認してください。",
        "is_active": True
    },
    {
        "name": "手続き・フローの明確化チェック",
        "category": "OPERATIONAL",
        "description": "申請・承認などの手続きの流れが明確に記載されているか確認します。",
        "severity": "MEDIUM",
        "prompt_template": "手続きの流れ（誰が、いつ、何を、どのように）が明確に記載されているか確認してください。",
        "is_active": True
    },
    {
        "name": "例外処理・エスカレーションルールチェック",
        "category": "OPERATIONAL",
        "description": "通常の手続きで対応できない場合の例外処理やエスカレーション先が定められているか確認します。",
        "severity": "LOW",
        "prompt_template": "例外時の対応方法やエスカレーション先が明記されているか確認してください。",
        "is_active": True
    },
]


# =============================================================================
# 記載ルールデータ（15件）
# =============================================================================
WRITING_RULES_DATA = [
    # ----- 文体（STYLE）-----
    {
        "name": "である体の使用",
        "rule_type": "STYLE",
        "pattern": r"(です|ます|でした|ました|ください)(?=[。、]|$)",
        "correct_form": "である体を使用する",
        "example_bad": "従業員は上長に報告してください。",
        "example_good": "従業員は所属長に報告しなければならない。",
        "is_active": True
    },
    {
        "name": "能動態の優先使用",
        "rule_type": "STYLE",
        "pattern": r"(される|された|されている|されていた)(?=[。、]|$)",
        "correct_form": "受動態を避け、主語を明確にした能動態を使用する",
        "example_bad": "申請書は所属長により承認される。",
        "example_good": "所属長は申請書を承認する。",
        "is_active": True
    },
    {
        "name": "二重否定の回避",
        "rule_type": "STYLE",
        "pattern": r"(ない|なく)(こと|もの|わけ|場合)(は|が|も)(ない|なく)",
        "correct_form": "二重否定を避け、肯定形で記述する",
        "example_bad": "届出なく欠勤することはできない。",
        "example_good": "欠勤する場合は事前に届け出なければならない。",
        "is_active": True
    },
    {
        "name": "一文一意の原則",
        "rule_type": "STYLE",
        "pattern": None,
        "correct_form": "一つの文には一つの意味のみを含める。複数の内容は文を分ける",
        "example_bad": "従業員は始業時刻までに出社し、業務開始前に健康状態を確認し、異常がある場合は所属長に報告しなければならない。",
        "example_good": "従業員は始業時刻までに出社しなければならない。\\n2 従業員は業務開始前に健康状態を確認しなければならない。\\n3 健康状態に異常がある場合は、所属長に報告しなければならない。",
        "is_active": True
    },

    # ----- 表記（FORMAT）-----
    {
        "name": "数字の半角統一",
        "rule_type": "FORMAT",
        "pattern": r"[０-９]",
        "correct_form": "数字は半角アラビア数字を使用する",
        "example_bad": "第１条、１０日以内",
        "example_good": "第1条、10日以内",
        "is_active": True
    },
    {
        "name": "日付表記の統一（西暦）",
        "rule_type": "FORMAT",
        "pattern": r"(令和|平成|昭和)\d+年",
        "correct_form": "日付は西暦表記を原則とする。和暦を使用する場合は（）内に西暦を併記",
        "example_bad": "令和6年4月1日から施行する。",
        "example_good": "2024年4月1日から施行する。（または「令和6年（2024年）4月1日」）",
        "is_active": True
    },
    {
        "name": "金額表記の統一",
        "rule_type": "FORMAT",
        "pattern": r"¥|￥|円(?!\)|）)",
        "correct_form": "金額は「○○円」と表記し、3桁区切りのカンマを使用する",
        "example_bad": "¥10000、1万円",
        "example_good": "10,000円、1万円（10,000円）",
        "is_active": True
    },
    {
        "name": "条文参照の表記",
        "rule_type": "FORMAT",
        "pattern": None,
        "correct_form": "条文参照は「第○条」「第○条第○項」「第○条第○項第○号」の形式で表記する",
        "example_bad": "1条2項、第三条(1)",
        "example_good": "第1条第2項、第3条第1項第1号",
        "is_active": True
    },

    # ----- 用語（TERMINOLOGY）-----
    {
        "name": "社内用語辞書との整合",
        "rule_type": "TERMINOLOGY",
        "pattern": None,
        "correct_form": "社内用語辞書に登録された正式名称を使用する",
        "example_bad": "社員は速やかに上司に報告すること。",
        "example_good": "従業員は遅滞なく所属長に報告しなければならない。",
        "is_active": True
    },
    {
        "name": "「等」の使用制限",
        "rule_type": "TERMINOLOGY",
        "pattern": r"等(?=[。、]|$)",
        "correct_form": "「等」は最小限にとどめ、可能な限り具体的に列挙する",
        "example_bad": "書類等を提出しなければならない。",
        "example_good": "申請書、添付書類およびその他必要書類を提出しなければならない。",
        "is_active": True
    },
    {
        "name": "外来語の使用",
        "rule_type": "TERMINOLOGY",
        "pattern": r"(コンプライアンス|ガバナンス|マネジメント|リスク)",
        "correct_form": "外来語は初出時に日本語訳を（）内に併記する",
        "example_bad": "コンプライアンスを遵守する。",
        "example_good": "コンプライアンス（法令遵守）を徹底する。（2回目以降は「コンプライアンス」のみ可）",
        "is_active": True
    },

    # ----- 構成（STRUCTURE）-----
    {
        "name": "目的条項の配置",
        "rule_type": "STRUCTURE",
        "pattern": None,
        "correct_form": "第1条は目的条項とし、規程の目的を明記する",
        "example_bad": "（目的条項なし）",
        "example_good": "第1条（目的）この規程は、○○について必要な事項を定め、△△を図ることを目的とする。",
        "is_active": True
    },
    {
        "name": "定義条項の配置",
        "rule_type": "STRUCTURE",
        "pattern": None,
        "correct_form": "第2条は定義条項とし、規程内で使用する用語を定義する",
        "example_bad": "（定義なく用語を使用）",
        "example_good": "第2条（定義）この規程において、次の各号に掲げる用語の意義は、当該各号に定めるところによる。",
        "is_active": True
    },
    {
        "name": "適用範囲の明記",
        "rule_type": "STRUCTURE",
        "pattern": None,
        "correct_form": "適用範囲条項を設け、規程が適用される対象者・対象範囲を明確にする",
        "example_bad": "（適用範囲が不明確）",
        "example_good": "第3条（適用範囲）この規程は、当社に勤務するすべての従業員（正社員、契約社員、パートタイマー）に適用する。",
        "is_active": True
    },
    {
        "name": "附則の記載",
        "rule_type": "STRUCTURE",
        "pattern": None,
        "correct_form": "附則に施行日、経過措置、改廃手続きを記載する",
        "example_bad": "（附則なし）",
        "example_good": "附則\\nこの規程は、2024年4月1日から施行する。\\n2 この規程の施行前に生じた事項については、なお従前の例による。",
        "is_active": True
    },
]


def seed_terms(db: Session) -> int:
    """用語辞書データを投入する。"""
    count = 0
    for term_data in TERMS_DATA:
        existing = db.query(Term).filter(Term.term == term_data["term"]).first()
        if not existing:
            term = Term(**term_data)
            db.add(term)
            count += 1
    db.commit()
    return count


def seed_check_items(db: Session) -> int:
    """チェック項目データを投入する。"""
    count = 0
    for item_data in CHECK_ITEMS_DATA:
        existing = db.query(CheckItem).filter(CheckItem.name == item_data["name"]).first()
        if not existing:
            item = CheckItem(**item_data)
            db.add(item)
            count += 1
    db.commit()
    return count


def seed_writing_rules(db: Session) -> int:
    """記載ルールデータを投入する。"""
    count = 0
    for rule_data in WRITING_RULES_DATA:
        existing = db.query(WritingRule).filter(WritingRule.name == rule_data["name"]).first()
        if not existing:
            rule = WritingRule(**rule_data)
            db.add(rule)
            count += 1
    db.commit()
    return count


def main():
    """メイン実行関数。"""
    print("=" * 60)
    print("  規程レビューツール - デモデータ投入")
    print("=" * 60)
    print()

    # データベース接続
    db = SessionLocal()

    try:
        # テーブル作成（存在しない場合）
        Base.metadata.create_all(bind=engine)
        print("✓ データベーステーブル確認完了")

        # 用語辞書の投入
        print("\n[1/3] 用語辞書データを投入中...")
        term_count = seed_terms(db)
        print(f"  → {term_count}件の用語を追加しました（全{len(TERMS_DATA)}件）")

        # チェック項目の投入
        print("\n[2/3] チェック項目データを投入中...")
        check_count = seed_check_items(db)
        print(f"  → {check_count}件のチェック項目を追加しました（全{len(CHECK_ITEMS_DATA)}件）")

        # 記載ルールの投入
        print("\n[3/3] 記載ルールデータを投入中...")
        rule_count = seed_writing_rules(db)
        print(f"  → {rule_count}件の記載ルールを追加しました（全{len(WRITING_RULES_DATA)}件）")

        print("\n" + "=" * 60)
        print("  デモデータ投入完了")
        print("=" * 60)
        print(f"""
投入データ:
  - 用語辞書:     {len(TERMS_DATA)}件
  - チェック項目: {len(CHECK_ITEMS_DATA)}件
  - 記載ルール:   {len(WRITING_RULES_DATA)}件

次のステップ:
  1. デモ用PDFを生成: python -m scripts.generate_demo_pdfs
  2. サーバーを起動: start_all.bat（または uvicorn app.main:app --reload --port 8080）
  3. フロントエンド: http://localhost:3030
  4. API Docs: http://localhost:8080/docs
  5. samples/ フォルダのPDFをアップロードしてレビューを実行
""")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
