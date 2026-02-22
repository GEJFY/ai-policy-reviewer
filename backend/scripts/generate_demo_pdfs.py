"""
デモ用PDF生成スクリプト

samples/ ディレクトリのテキストファイルからデモ用PDFを生成します。
ReportLab を使用して日本語対応のPDFを作成します。

Usage:
    cd backend
    python -m scripts.generate_demo_pdfs

生成されるファイル:
    samples/就業規則_改定案_v2.pdf
    samples/情報セキュリティポリシー.pdf
    samples/内部統制規程.pdf
"""

import os
import sys
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Frame, PageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor


# ===========================================================================
# フォント設定
# ===========================================================================

# Windows 日本語フォント候補（優先順）
FONT_PATHS = [
    ("C:/Windows/Fonts/YuGothM.ttc", "YuGothic"),
    ("C:/Windows/Fonts/meiryo.ttc", "Meiryo"),
    ("C:/Windows/Fonts/msgothic.ttc", "MSGothic"),
    ("C:/Windows/Fonts/msmincho.ttc", "MSMincho"),
]

JAPANESE_FONT = None


def register_japanese_font():
    """日本語フォントを登録し、使用可能なフォント名を返す"""
    global JAPANESE_FONT

    for font_path, font_name in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                JAPANESE_FONT = font_name
                return font_name
            except Exception:
                continue

    print("警告: 日本語フォントが見つかりません。デフォルトフォントを使用します。")
    JAPANESE_FONT = "Helvetica"
    return "Helvetica"


def create_styles(font_name: str) -> dict:
    """PDF用スタイルを作成"""
    styles = getSampleStyleSheet()

    # タイトル（規程名）
    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName=font_name,
        fontSize=20,
        alignment=TA_CENTER,
        spaceBefore=30,
        spaceAfter=10,
        leading=28,
    ))

    # サブタイトル（会社名）
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontName=font_name,
        fontSize=12,
        alignment=TA_CENTER,
        spaceBefore=5,
        spaceAfter=5,
        leading=18,
        textColor=HexColor("#444444"),
    ))

    # 制定・改定日
    styles.add(ParagraphStyle(
        name="DocDate",
        fontName=font_name,
        fontSize=9,
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=20,
        leading=14,
        textColor=HexColor("#666666"),
    ))

    # 章見出し
    styles.add(ParagraphStyle(
        name="ChapterHeading",
        fontName=font_name,
        fontSize=14,
        spaceBefore=20,
        spaceAfter=12,
        leading=20,
        borderWidth=0,
        borderPadding=0,
    ))

    # 条文見出し
    styles.add(ParagraphStyle(
        name="ArticleHeading",
        fontName=font_name,
        fontSize=10.5,
        spaceBefore=12,
        spaceAfter=4,
        leading=16,
    ))

    # 本文
    styles.add(ParagraphStyle(
        name="BodyText_JP",
        fontName=font_name,
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=2,
        leading=16,
        firstLineIndent=0,
    ))

    # 号（インデント付き）
    styles.add(ParagraphStyle(
        name="ItemText",
        fontName=font_name,
        fontSize=10,
        alignment=TA_LEFT,
        spaceBefore=1,
        spaceAfter=1,
        leading=15,
        leftIndent=15,
    ))

    # 附則
    styles.add(ParagraphStyle(
        name="SupplementHeading",
        fontName=font_name,
        fontSize=12,
        spaceBefore=20,
        spaceAfter=10,
        leading=18,
    ))

    # ページフッター用
    styles.add(ParagraphStyle(
        name="Footer",
        fontName=font_name,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=HexColor("#888888"),
    ))

    return styles


# ===========================================================================
# テキスト解析・PDF変換
# ===========================================================================

def parse_policy_text(text: str) -> list:
    """
    規程テキストを構造化された要素リストに変換する。

    Returns:
        list of tuples: (element_type, content)
        element_type: "title", "subtitle", "date", "chapter", "article",
                      "body", "item", "supplement", "spacer", "end"
    """
    elements = []
    lines = text.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            elements.append(("spacer", ""))
            i += 1
            continue

        # タイトル行（最初の非空行で、「規程」「規則」「ポリシー」を含む）
        if i < 3 and any(kw in line for kw in ["規程", "規則", "ポリシー"]):
            elements.append(("title", line))
            i += 1
            continue

        # 会社名
        if "株式会社" in line:
            elements.append(("subtitle", line))
            i += 1
            continue

        # 制定・改定日
        if line.startswith("制定") or line.startswith("改定"):
            elements.append(("date", line))
            i += 1
            continue

        # 章見出し
        if re.match(r"^第\d+章", line):
            elements.append(("chapter", line))
            i += 1
            continue

        # 条文見出し
        if re.match(r"^第\d+条", line):
            elements.append(("article", line))
            i += 1
            continue

        # 附則
        if line == "附則":
            elements.append(("supplement", line))
            i += 1
            continue

        # 「以上」
        if line == "以上":
            elements.append(("end", line))
            i += 1
            continue

        # 号（(1), (2)... または 1, 2...で始まるインデント行）
        if re.match(r"^\s*[\(（]\d+[\)）]", line) or re.match(r"^\s*\d+[\.、．]?\s", line):
            elements.append(("item", line))
            i += 1
            continue

        # インデントされた例示
        if line.startswith("  ") or line.startswith("　"):
            elements.append(("item", line))
            i += 1
            continue

        # その他は本文
        elements.append(("body", line))
        i += 1

    return elements


def build_pdf_story(elements: list, styles) -> list:
    """構造化された要素リストからReportLabのstoryを構築する"""
    story = []
    prev_type = None

    for elem_type, content in elements:
        if elem_type == "spacer":
            if prev_type not in ("spacer", "title", "subtitle", "date"):
                story.append(Spacer(1, 6))

        elif elem_type == "title":
            story.append(Spacer(1, 40))
            story.append(Paragraph(content, styles["DocTitle"]))

        elif elem_type == "subtitle":
            story.append(Paragraph(content, styles["DocSubtitle"]))

        elif elem_type == "date":
            story.append(Paragraph(content, styles["DocDate"]))

        elif elem_type == "chapter":
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>{content}</b>", styles["ChapterHeading"]))

        elif elem_type == "article":
            story.append(Paragraph(f"<b>{content}</b>", styles["ArticleHeading"]))

        elif elem_type == "item":
            story.append(Paragraph(content, styles["ItemText"]))

        elif elem_type == "supplement":
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>{content}</b>", styles["SupplementHeading"]))

        elif elem_type == "end":
            story.append(Spacer(1, 20))
            story.append(Paragraph(content, styles["BodyText_JP"]))

        elif elem_type == "body":
            story.append(Paragraph(content, styles["BodyText_JP"]))

        prev_type = elem_type

    return story


def add_page_number(canvas, doc):
    """ページ番号のフッターを追加"""
    canvas.saveState()
    font_name = JAPANESE_FONT or "Helvetica"
    canvas.setFont(font_name, 8)
    canvas.setFillColor(HexColor("#888888"))
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0] / 2, 15 * mm, f"- {page_num} -")
    canvas.restoreState()


def generate_pdf(input_path: str, output_path: str, styles) -> str:
    """テキストファイルからPDFを生成する"""
    # テキスト読み込み
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 構造解析
    elements = parse_policy_text(text)

    # PDF story構築
    story = build_pdf_story(elements, styles)

    # PDF生成
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        title=os.path.splitext(os.path.basename(input_path))[0],
        author="株式会社サンプル商事",
    )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return output_path


# ===========================================================================
# メイン
# ===========================================================================

# 生成対象ファイル一覧
SAMPLE_FILES = [
    "就業規則_改定案_v2.txt",
    "情報セキュリティポリシー.txt",
    "内部統制規程.txt",
    "給与規程.txt",
    "親会社_就業規則.txt",
    "子会社_就業規則.txt",
    "個人情報保護規程.txt",
]


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("  規程レビューツール - デモ用PDF生成")
    print("=" * 60)
    print()

    # プロジェクトルート特定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_dir)
    samples_dir = os.path.join(project_root, "samples")

    if not os.path.exists(samples_dir):
        print(f"エラー: samples/ ディレクトリが見つかりません: {samples_dir}")
        sys.exit(1)

    # フォント登録
    print("[1/2] フォント設定中...")
    font_name = register_japanese_font()
    print(f"  → 使用フォント: {font_name}")

    # スタイル作成
    styles = create_styles(font_name)

    # PDF生成
    print(f"\n[2/2] PDF生成中...")
    generated = []

    for txt_file in SAMPLE_FILES:
        input_path = os.path.join(samples_dir, txt_file)
        if not os.path.exists(input_path):
            print(f"  ⚠ スキップ: {txt_file} が見つかりません")
            continue

        pdf_file = txt_file.replace(".txt", ".pdf")
        output_path = os.path.join(samples_dir, pdf_file)

        try:
            generate_pdf(input_path, output_path, styles)
            # ページ数を概算（ファイルサイズから）
            file_size_kb = os.path.getsize(output_path) / 1024
            print(f"  ✓ {pdf_file} ({file_size_kb:.0f}KB)")
            generated.append(pdf_file)
        except Exception as e:
            print(f"  ✗ {pdf_file}: {e}")

    # サマリー
    print(f"\n{'=' * 60}")
    print(f"  PDF生成完了: {len(generated)}/{len(SAMPLE_FILES)} ファイル")
    print(f"{'=' * 60}")
    print(f"\n生成場所: {samples_dir}")
    for f in generated:
        print(f"  - {f}")

    print(f"""
次のステップ:
  1. デモデータを投入: python -m scripts.seed_demo_data
  2. サーバーを起動: start_all.bat
  3. ブラウザで http://localhost:3030 にアクセス
  4. 生成されたPDFをアップロードしてレビューを実行
""")


if __name__ == "__main__":
    main()
