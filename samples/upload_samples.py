"""サンプルPDFをAPIにアップロードするスクリプト"""
import os
import requests

API_URL = "http://localhost:8004/api/v1/documents/upload"


def upload_pdf(pdf_path: str):
    """PDFファイルをAPIにアップロード"""
    filename = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        resp = requests.post(API_URL, files=files)

    if resp.status_code == 200:
        data = resp.json()
        print(f"OK: {data['title']} (id={data['id']}, ocr={data['ocr_status']})")
    else:
        print(f"NG: {filename} -> {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    pdf_files = [
        "情報セキュリティポリシー.pdf",
        "内部統制規程.pdf",
        "就業規則_改定案_v2.pdf",
    ]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(script_dir, pdf_file)
        if os.path.exists(pdf_path):
            upload_pdf(pdf_path)
        else:
            print(f"Not found: {pdf_path}")

    print("\nDone!")
