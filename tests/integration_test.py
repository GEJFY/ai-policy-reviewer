"""
結合テストスクリプト
APIエンドポイントの動作確認を行う
"""

import os
import sys
import time
import requests
from pathlib import Path

# テスト設定
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# テスト結果
results = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def log_test(name: str, passed: bool, message: str = ""):
    """テスト結果をログ出力"""
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if not passed:
        results["failed"] += 1
        results["errors"].append(f"{name}: {message}")
    else:
        results["passed"] += 1


def test_health_check():
    """ヘルスチェックエンドポイントのテスト"""
    print("\n=== ヘルスチェック ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        log_test("GET /health", response.status_code == 200, f"Status: {response.status_code}")

        data = response.json()
        log_test("レスポンス形式", "status" in data, str(data))
    except Exception as e:
        log_test("ヘルスチェック", False, str(e))


def test_root():
    """ルートエンドポイントのテスト"""
    print("\n=== ルートエンドポイント ===")
    try:
        response = requests.get(BASE_URL, timeout=10)
        log_test("GET /", response.status_code == 200, f"Status: {response.status_code}")

        data = response.json()
        log_test("バージョン情報", "version" in data, str(data))
    except Exception as e:
        log_test("ルート", False, str(e))


def test_terms_api():
    """用語辞書APIのテスト"""
    print("\n=== 用語辞書API ===")
    try:
        # 一覧取得
        response = requests.get(f"{API_URL}/terms", timeout=10)
        log_test("GET /terms", response.status_code == 200, f"Status: {response.status_code}")

        terms = response.json()
        log_test("用語データ取得", len(terms) > 0, f"Count: {len(terms)}")

        # 詳細取得
        if terms:
            term_id = terms[0]["id"]
            response = requests.get(f"{API_URL}/terms/{term_id}", timeout=10)
            log_test(f"GET /terms/{term_id}", response.status_code == 200, f"Status: {response.status_code}")

        # カテゴリフィルタ
        response = requests.get(f"{API_URL}/terms?category=人事", timeout=10)
        log_test("カテゴリフィルタ", response.status_code == 200, f"Status: {response.status_code}")

    except Exception as e:
        log_test("用語辞書API", False, str(e))


def test_check_items_api():
    """チェック項目APIのテスト"""
    print("\n=== チェック項目API ===")
    try:
        # 一覧取得
        response = requests.get(f"{API_URL}/check-items", timeout=10)
        log_test("GET /check-items", response.status_code == 200, f"Status: {response.status_code}")

        items = response.json()
        log_test("チェック項目取得", len(items) > 0, f"Count: {len(items)}")

        # カテゴリ一覧
        response = requests.get(f"{API_URL}/check-items/categories", timeout=10)
        log_test("GET /check-items/categories", response.status_code == 200, f"Status: {response.status_code}")

    except Exception as e:
        log_test("チェック項目API", False, str(e))


def test_writing_rules_api():
    """記載ルールAPIのテスト"""
    print("\n=== 記載ルールAPI ===")
    try:
        # 一覧取得
        response = requests.get(f"{API_URL}/writing-rules", timeout=10)
        log_test("GET /writing-rules", response.status_code == 200, f"Status: {response.status_code}")

        rules = response.json()
        log_test("記載ルール取得", len(rules) > 0, f"Count: {len(rules)}")

    except Exception as e:
        log_test("記載ルールAPI", False, str(e))


def test_documents_api():
    """文書管理APIのテスト"""
    print("\n=== 文書管理API ===")
    try:
        # 一覧取得
        response = requests.get(f"{API_URL}/documents", timeout=10)
        log_test("GET /documents", response.status_code == 200, f"Status: {response.status_code}")

        # PDFアップロード
        test_pdf = Path(__file__).parent / "sample_security_policy.pdf"
        if test_pdf.exists():
            with open(test_pdf, "rb") as f:
                files = {"file": ("test_policy.pdf", f, "application/pdf")}
                response = requests.post(
                    f"{API_URL}/documents/upload",
                    files=files,
                    timeout=120,
                )
            log_test("POST /documents/upload", response.status_code in [200, 201], f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                doc_data = response.json()
                log_test("アップロード成功", "id" in doc_data, str(doc_data))
                return doc_data.get("id")
        else:
            log_test("テストPDF", False, f"ファイルが見つかりません: {test_pdf}")

    except Exception as e:
        log_test("文書管理API", False, str(e))

    return None


def test_reviews_api(document_id: int = None):
    """レビューAPIのテスト"""
    print("\n=== レビューAPI ===")
    try:
        # 一覧取得
        response = requests.get(f"{API_URL}/reviews", timeout=10)
        log_test("GET /reviews", response.status_code == 200, f"Status: {response.status_code}")

        # レビュー作成（文書がある場合）
        if document_id:
            # チェック項目のIDを取得
            check_items_response = requests.get(f"{API_URL}/check-items", timeout=10)
            if check_items_response.status_code == 200:
                check_items = check_items_response.json()
                check_item_ids = [item["id"] for item in check_items[:2]]  # 最初の2つだけ

                print("  レビュー実行中（時間がかかります）...")
                response = requests.post(
                    f"{API_URL}/reviews",
                    json={
                        "document_id": document_id,
                        "check_item_ids": check_item_ids,
                    },
                    timeout=300,  # 5分タイムアウト
                )
                log_test("POST /reviews", response.status_code in [200, 201], f"Status: {response.status_code}")

                if response.status_code in [200, 201]:
                    review_data = response.json()
                    review_id = review_data.get("id")

                    # レビュー詳細取得
                    response = requests.get(f"{API_URL}/reviews/{review_id}", timeout=10)
                    log_test(f"GET /reviews/{review_id}", response.status_code == 200, f"Status: {response.status_code}")

                    # 指摘事項取得
                    response = requests.get(f"{API_URL}/reviews/{review_id}/findings", timeout=10)
                    log_test("GET /reviews/{id}/findings", response.status_code == 200, f"Status: {response.status_code}")

                    findings = response.json()
                    log_test("指摘事項検出", True, f"検出数: {len(findings)}")

                    return review_id, findings

    except requests.exceptions.Timeout:
        log_test("レビューAPI", False, "タイムアウト")
    except Exception as e:
        log_test("レビューAPI", False, str(e))

    return None, []


def test_findings_api(review_id: int, findings: list):
    """指摘事項APIのテスト"""
    print("\n=== 指摘事項API ===")
    try:
        if not findings:
            print("  スキップ: 指摘事項がありません")
            return

        finding_id = findings[0]["id"]

        # 承認
        response = requests.put(f"{API_URL}/findings/{finding_id}/approve", timeout=10)
        log_test(f"PUT /findings/{finding_id}/approve", response.status_code == 200, f"Status: {response.status_code}")

        # ステータス確認
        response = requests.get(f"{API_URL}/reviews/{review_id}/findings", timeout=10)
        updated_findings = response.json()
        approved = next((f for f in updated_findings if f["id"] == finding_id), None)
        log_test("承認状態更新", approved and approved["status"] == "APPROVED", str(approved.get("status") if approved else "None"))

    except Exception as e:
        log_test("指摘事項API", False, str(e))


def print_summary():
    """テスト結果サマリーを出力"""
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"合計: {total}件")
    print(f"成功: {results['passed']}件")
    print(f"失敗: {results['failed']}件")

    if results["errors"]:
        print("\n失敗したテスト:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("=" * 60)

    return results["failed"] == 0


def main():
    """メイン実行"""
    print("=" * 60)
    print("規程レビューツール 結合テスト")
    print("=" * 60)
    print(f"対象URL: {BASE_URL}")

    # サーバー接続確認
    print("\nサーバー接続を確認中...")
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("サーバー接続OK")
                break
        except:
            if i < max_retries - 1:
                print(f"  リトライ中... ({i + 1}/{max_retries})")
                time.sleep(2)
            else:
                print("エラー: サーバーに接続できません")
                print("サーバーを起動してから再実行してください:")
                print("  cd backend && uvicorn app.main:app --reload")
                sys.exit(1)

    # テスト実行
    test_health_check()
    test_root()
    test_terms_api()
    test_check_items_api()
    test_writing_rules_api()

    document_id = test_documents_api()

    if document_id:
        review_id, findings = test_reviews_api(document_id)
        if review_id and findings:
            test_findings_api(review_id, findings)
    else:
        print("\n  スキップ: 文書アップロードに失敗したためレビューテストをスキップ")

    # 結果サマリー
    success = print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
