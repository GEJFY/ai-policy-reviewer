"""
APIテストスクリプト（Azure不要部分のみ）
マスタデータAPI、基本エンドポイントの動作確認
"""

import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

results = {"passed": 0, "failed": 0, "errors": []}


def log_test(name: str, passed: bool, message: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if not passed:
        results["failed"] += 1
        results["errors"].append(f"{name}: {message}")
    else:
        results["passed"] += 1


def test_basic_endpoints():
    """基本エンドポイントテスト"""
    print("\n=== 基本エンドポイント ===")

    # ルート
    response = requests.get(BASE_URL, timeout=10)
    log_test("GET /", response.status_code == 200)

    # ヘルスチェック
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    log_test("GET /health", response.status_code == 200)
    data = response.json()
    log_test("ヘルスチェック形式", "status" in data and data["status"] == "healthy")


def test_terms_api():
    """用語辞書APIテスト"""
    print("\n=== 用語辞書API ===")

    # 一覧取得
    response = requests.get(f"{API_URL}/terms", timeout=10)
    log_test("GET /terms", response.status_code == 200)
    terms = response.json()
    log_test("用語データ存在", len(terms) > 0, f"Count: {len(terms)}")

    # 詳細取得
    if terms:
        term_id = terms[0]["id"]
        response = requests.get(f"{API_URL}/terms/{term_id}", timeout=10)
        log_test(f"GET /terms/{term_id}", response.status_code == 200)
        term = response.json()
        log_test("用語詳細", "term" in term and "definition" in term)

    # カテゴリフィルタ
    response = requests.get(f"{API_URL}/terms?category=人事", timeout=10)
    log_test("カテゴリフィルタ", response.status_code == 200)

    # 存在しないID
    response = requests.get(f"{API_URL}/terms/99999", timeout=10)
    log_test("存在しないID", response.status_code == 404)


def test_check_items_api():
    """チェック項目APIテスト"""
    print("\n=== チェック項目API ===")

    # 一覧取得
    response = requests.get(f"{API_URL}/check-items", timeout=10)
    log_test("GET /check-items", response.status_code == 200)
    items = response.json()
    log_test("チェック項目存在", len(items) > 0, f"Count: {len(items)}")

    # 詳細取得
    if items:
        item_id = items[0]["id"]
        response = requests.get(f"{API_URL}/check-items/{item_id}", timeout=10)
        log_test(f"GET /check-items/{item_id}", response.status_code == 200)

    # カテゴリ一覧
    response = requests.get(f"{API_URL}/check-items/categories", timeout=10)
    log_test("GET /check-items/categories", response.status_code == 200)


def test_writing_rules_api():
    """記載ルールAPIテスト"""
    print("\n=== 記載ルールAPI ===")

    # 一覧取得
    response = requests.get(f"{API_URL}/writing-rules", timeout=10)
    log_test("GET /writing-rules", response.status_code == 200)
    rules = response.json()
    log_test("記載ルール存在", len(rules) > 0, f"Count: {len(rules)}")

    # 詳細取得
    if rules:
        rule_id = rules[0]["id"]
        response = requests.get(f"{API_URL}/writing-rules/{rule_id}", timeout=10)
        log_test(f"GET /writing-rules/{rule_id}", response.status_code == 200)


def test_documents_api():
    """文書管理APIテスト"""
    print("\n=== 文書管理API ===")

    # 一覧取得
    response = requests.get(f"{API_URL}/documents", timeout=10)
    log_test("GET /documents", response.status_code == 200)


def test_reviews_api():
    """レビューAPIテスト"""
    print("\n=== レビューAPI ===")

    # 一覧取得
    response = requests.get(f"{API_URL}/reviews", timeout=10)
    log_test("GET /reviews", response.status_code == 200)


def test_crud_operations():
    """CRUD操作テスト"""
    print("\n=== CRUD操作 ===")

    # 新規用語登録
    new_term = {
        "term": "テスト用語",
        "definition": "これはテスト用の用語定義です",
        "category": "テスト",
        "aliases": ["別名1", "別名2"],
    }
    response = requests.post(f"{API_URL}/terms", json=new_term, timeout=10)
    log_test("POST /terms (作成)", response.status_code in [200, 201])

    if response.status_code in [200, 201]:
        created = response.json()
        term_id = created["id"]

        # 更新
        update_data = {"usage_note": "テスト用のノート"}
        response = requests.put(f"{API_URL}/terms/{term_id}", json=update_data, timeout=10)
        log_test("PUT /terms/{id} (更新)", response.status_code == 200)

        # 削除
        response = requests.delete(f"{API_URL}/terms/{term_id}", timeout=10)
        log_test("DELETE /terms/{id} (削除)", response.status_code == 200)

        # 削除確認
        response = requests.get(f"{API_URL}/terms/{term_id}", timeout=10)
        log_test("削除確認", response.status_code == 404)


def print_summary():
    """結果サマリー"""
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    total = results["passed"] + results["failed"]
    print(f"合計: {total}件")
    print(f"成功: {results['passed']}件")
    print(f"失敗: {results['failed']}件")

    if results["errors"]:
        print("\n失敗したテスト:")
        for error in results["errors"]:
            print(f"  - {error}")
    print("=" * 50)

    return results["failed"] == 0


def main():
    print("=" * 50)
    print("規程レビューツール APIテスト")
    print("=" * 50)

    try:
        test_basic_endpoints()
        test_terms_api()
        test_check_items_api()
        test_writing_rules_api()
        test_documents_api()
        test_reviews_api()
        test_crud_operations()
    except requests.exceptions.ConnectionError:
        print("\nエラー: サーバーに接続できません")
        print("サーバーを起動してください: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\nエラー: {e}")
        return False

    return print_summary()


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
