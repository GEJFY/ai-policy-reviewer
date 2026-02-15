"""サンプルtxtファイルをPDFに変換するスクリプト"""
import os
from fpdf import FPDF

FONT_PATH = "C:/Windows/Fonts/yumin.ttf"


def create_pdf(txt_path: str, pdf_path: str):
    """テキストファイルをPDFに変換"""
    pdf = FPDF()
    pdf.set_margin(10)
    pdf.add_page()
    pdf.add_font("YuMincho", "", FONT_PATH)
    pdf.set_font("YuMincho", size=9)
    pdf.set_auto_page_break(auto=True, margin=10)

    # 有効幅を明示的に計算 (A4=210mm, margin=10mm x 2)
    effective_w = pdf.w - pdf.l_margin - pdf.r_margin

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            # 全角スペース・タブを半角に正規化
            line = line.replace("\u3000", "  ").replace("\t", "    ")
            stripped = line.lstrip()

            if not stripped:
                pdf.ln(3)
                continue

            # x位置を左マージンにリセットしてから描画
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(effective_w, 5, stripped)

    pdf.output(pdf_path)
    print(f"Created: {pdf_path} ({os.path.getsize(pdf_path) // 1024}KB)")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    txt_files = [
        "情報セキュリティポリシー.txt",
        "内部統制規程.txt",
        "就業規則_改定案_v2.txt",
    ]

    for txt_file in txt_files:
        txt_path = os.path.join(script_dir, txt_file)
        if os.path.exists(txt_path):
            pdf_file = txt_file.replace(".txt", ".pdf")
            pdf_path = os.path.join(script_dir, pdf_file)
            create_pdf(txt_path, pdf_path)
        else:
            print(f"Not found: {txt_path}")

    print("\nDone! PDF files created in samples/ directory.")
