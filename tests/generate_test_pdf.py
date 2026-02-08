"""
テスト用PDF生成スクリプト
AIレビューシステムの検証用に、意図的に問題を含む社内規程サンプルを生成する
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# 日本語フォントの設定（Windows環境）
FONT_PATHS = [
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/msmincho.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
]

def register_japanese_font():
    """日本語フォントを登録"""
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Japanese', font_path))
                return True
            except:
                continue
    return False

def create_styles():
    """スタイルを作成"""
    styles = getSampleStyleSheet()

    # 日本語フォントが使えるか確認
    font_name = 'Japanese' if 'Japanese' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

    styles.add(ParagraphStyle(
        name='JapaneseTitle',
        fontName=font_name,
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name='JapaneseHeading',
        fontName=font_name,
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='JapaneseBody',
        fontName=font_name,
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceBefore=5,
        spaceAfter=5,
        leading=16,
    ))

    styles.add(ParagraphStyle(
        name='JapaneseArticle',
        fontName=font_name,
        fontSize=10,
        spaceBefore=10,
        spaceAfter=5,
        leading=16,
    ))

    return styles


# ============================================================
# テスト用規程文書（意図的に問題を含む）
# ============================================================

# 注釈：以下の文書には以下の問題を意図的に含めています
# 1. 用語不統一: 「従業員」「社員」「スタッフ」の混在
# 2. 曖昧表現: 「等」「など」「原則として」「適宜」「速やかに」
# 3. 責任主体不明確: 「される」「行う」で主語が不明
# 4. 和暦表記: 「令和6年」のみで西暦なし
# 5. 条項番号不統一: 「1条」「第2条」の混在
# 6. 外来語表記: 「Security」「Compliance」の英語表記
# 7. 参照不明確: 「別途定める」で参照先なし

SAMPLE_POLICY_TEXT = """
情報セキュリティ管理規程（サンプル）

制定日：令和6年4月1日
改訂日：令和6年10月1日


第1章　総則

1条（目的）
本規程は、当社における情報資産の保護及び適切な管理を目的とし、社員が遵守すべき事項を定めるものである。
当社のSecurityを確保し、情報漏えい等のリスクを低減することを目指す。

第2条（適用範囲）
本規程は、当社の全てのスタッフに適用される。また、派遣スタッフや業務委託先の者など、当社の業務に従事する者についても適用される。
なお、詳細については別途定める。

3条（用語の定義）
本規程における用語は、以下のとおりとする。
（1）「機密情報」とは、Confidentialに指定された情報をいう。
（2）「情シス」とは、情報システム部門をいう。
（3）「上長」とは、直属の上司をいう。


第2章　情報セキュリティ体制

第4条（管理体制）
情報セキュリティに関する管理体制は、次のとおりとする。
1　情報セキュリティ委員会を設置する。
2　委員会は、原則として四半期ごとに開催される。
3　緊急時には適宜開催することができる。

5条（責任と権限）
情報セキュリティの責任と権限は、以下のとおり定める。
情報セキュリティに関する重要事項が決定される。
必要に応じて、適切な措置が講じられる。
Complianceの観点から、法令遵守状況が確認される。


第3章　情報の取扱い

第六条（情報の分類）
従業員は、取り扱う情報を以下のとおり分類しなければならない。
（一）極秘：経営戦略や個人データ等、漏えい時に重大な影響を及ぼす情報
（二）秘：業務上の機密情報など
（三）社外秘：社外に開示すべきでない情報

7条（情報の保管）
機密情報等は、施錠可能な場所に保管する。
電子データは、速やかに暗号化して保存する。
保管期間については、別途定める要領に従う。

第8条（情報の廃棄）
不要となった機密情報は、適切に廃棄される。
紙文書はシュレッダー処理を行う。
電子媒体は、復元不可能な状態にする。


第4章　セキュリティ対策

第9条（アクセス管理）
1　システムへのアクセス権限は、業務上必要な範囲で付与する。
2　パスワードは、十分な長さと複雑さを持つものとする。
3　アクセス権限の見直しは、随時行われる。

第10条（インシデント対応）
セキュリティインシデントが発生した場合、発見した者は直ちに上司に報告する。
報告を受けた場合、速やかに対応チームが編成される。
対応状況は、関係者に適宜共有される。


第5章　教育・監査

11条（教育訓練）
社員に対し、情報セキュリティに関する教育訓練を実施する。
教育は、年１回以上実施するものとする。
新入社員には、入社時に必ず教育を行う。

第12条（監査）
情報セキュリティの状況について、年1回以上の監査が実施される。
監査結果は、取会に報告される。


第6章　罰則

第13条（罰則）
本規程に違反した従業員は、就業規則の定めにより懲戒処分の対象となる場合がある。
重大な違反については、別途対応が検討される。


附則
本規程は、令和6年4月1日より施行する。
"""


def generate_test_pdf(output_path: str):
    """テスト用PDFを生成"""
    register_japanese_font()
    styles = create_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=25*mm,
        bottomMargin=25*mm,
        leftMargin=25*mm,
        rightMargin=25*mm,
    )

    story = []

    # テキストを行ごとに処理
    lines = SAMPLE_POLICY_TEXT.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 10))
            continue

        # タイトル
        if '情報セキュリティ管理規程' in line:
            story.append(Paragraph(line, styles['JapaneseTitle']))
        # 章見出し
        elif line.startswith('第') and '章' in line:
            story.append(Spacer(1, 15))
            story.append(Paragraph(f'<b>{line}</b>', styles['JapaneseHeading']))
        # 条文
        elif ('条' in line and ('（' in line or '(' in line)) or line.startswith('附則'):
            story.append(Paragraph(f'<b>{line}</b>', styles['JapaneseArticle']))
        # 本文
        else:
            story.append(Paragraph(line, styles['JapaneseBody']))

    doc.build(story)
    print(f"テスト用PDFを生成しました: {output_path}")
    return output_path


if __name__ == "__main__":
    # 出力先
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "sample_security_policy.pdf")

    generate_test_pdf(output_path)

    print("\n" + "=" * 60)
    print("このPDFには以下の問題が意図的に含まれています：")
    print("=" * 60)
    print("""
1. 【用語不統一】
   - 「従業員」「社員」「スタッフ」の混在
   - 「派遣スタッフ」「派遣社員」の混在
   - 「上長」「上司」の使用（→「所属長」が正式）
   - 「情シス」の略称使用（→「情報システム」が正式）

2. 【曖昧表現】
   - 「等」「など」の多用
   - 「原則として」「適宜」「速やかに」の使用
   - 「適切に」「十分な」等の主観的表現

3. 【責任主体不明確】
   - 「決定される」「講じられる」「実施される」等の受動態
   - 誰が行うのか不明確な文が多数

4. 【フォーマット不統一】
   - 和暦のみの表記（「令和6年」）
   - 条番号形式の不統一（「1条」「第2条」「第六条」「7条」）
   - 号の表記不統一（「（1）」「（一）」）

5. 【外来語表記】
   - 「Security」「Compliance」「Confidential」の英語表記

6. 【参照不明確】
   - 「別途定める」のみで参照先が不明
   - 「就業規則の定め」で具体的な条項番号なし

7. 【略称使用】
   - 「取会」（→「取締役会」が正式）
""")
