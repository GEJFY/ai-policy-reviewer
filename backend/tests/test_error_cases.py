"""
Error case tests.

異常系・エラーケースのテスト。
バリデーション、例外処理、エッジケースを網羅。

Note:
    TermCreateスキーマでは term, definition, category が必須。
"""

from fastapi.testclient import TestClient


class TestValidationErrors:
    """バリデーションエラーのテスト。"""

    def test_create_term_missing_required_field(self, client: TestClient):
        """用語作成：必須フィールド欠落。"""
        # termフィールドなし
        response = client.post("/api/v1/terms", json={"definition": "テスト"})
        assert response.status_code == 422  # Validation Error

    def test_create_term_invalid_type(self, client: TestClient):
        """用語作成：型エラー。"""
        # aliases は list であるべき
        response = client.post(
            "/api/v1/terms",
            json={
                "term": "テスト",
                "definition": "テスト",
                "category": "一般",
                "aliases": "not_a_list",  # リストであるべき
            },
        )
        assert response.status_code == 422

    def test_create_check_item_missing_required_field(self, client: TestClient):
        """チェック項目作成：必須フィールド欠落。"""
        # nameフィールドなし
        response = client.post("/api/v1/check-items", json={"category": "TERMINOLOGY"})
        assert response.status_code == 422

    def test_create_writing_rule_missing_required_field(self, client: TestClient):
        """記載ルール作成：必須フィールド欠落。"""
        # nameフィールドなし（rule_type, correct_formも必須）
        response = client.post("/api/v1/writing-rules", json={"rule_type": "STYLE"})
        assert response.status_code == 422

    def test_pagination_invalid_values(self, client: TestClient):
        """ページネーション：無効な値。"""
        # 負のskip
        response = client.get("/api/v1/terms?skip=-1")
        assert response.status_code == 422

        # limitが上限超過
        response = client.get("/api/v1/terms?limit=10000")
        assert response.status_code == 422

        # limitが0
        response = client.get("/api/v1/terms?limit=0")
        assert response.status_code == 422


class TestNotFoundErrors:
    """存在しないリソースへのアクセステスト。"""

    def test_get_nonexistent_term(self, client: TestClient):
        """存在しない用語の取得。"""
        response = client.get("/api/v1/terms/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_nonexistent_term(self, client: TestClient):
        """存在しない用語の更新。"""
        response = client.put("/api/v1/terms/99999", json={"definition": "テスト"})
        assert response.status_code == 404

    def test_delete_nonexistent_term(self, client: TestClient):
        """存在しない用語の削除。"""
        response = client.delete("/api/v1/terms/99999")
        assert response.status_code == 404

    def test_get_nonexistent_check_item(self, client: TestClient):
        """存在しないチェック項目の取得。"""
        response = client.get("/api/v1/check-items/99999")
        assert response.status_code == 404

    def test_get_nonexistent_writing_rule(self, client: TestClient):
        """存在しない記載ルールの取得。"""
        response = client.get("/api/v1/writing-rules/99999")
        assert response.status_code == 404

    def test_get_nonexistent_document(self, client: TestClient):
        """存在しない文書の取得。"""
        response = client.get("/api/v1/documents/99999")
        assert response.status_code == 404

    def test_get_nonexistent_review(self, client: TestClient):
        """存在しないレビューの取得。"""
        response = client.get("/api/v1/reviews/99999")
        assert response.status_code == 404


class TestInvalidOperations:
    """無効な操作のテスト。"""

    def test_invalid_http_method(self, client: TestClient):
        """無効なHTTPメソッド。"""
        # POSTのみのエンドポイントにPUT - FastAPIはバリデーションエラーを返す場合もある
        response = client.put("/api/v1/terms/search", json={"query": "test"})
        assert response.status_code in [
            405,
            422,
        ]  # Method Not Allowed or Validation Error

    def test_invalid_content_type(self, client: TestClient):
        """無効なContent-Type。"""
        response = client.post(
            "/api/v1/terms",
            content="term=test&definition=test",  # JSON以外
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 422

    def test_empty_request_body(self, client: TestClient):
        """空のリクエストボディ。"""
        response = client.post("/api/v1/terms", json={})
        assert response.status_code == 422

    def test_null_required_field(self, client: TestClient):
        """必須フィールドがnull。"""
        response = client.post(
            "/api/v1/terms",
            json={"term": None, "definition": "テスト", "category": "一般"},
        )
        assert response.status_code == 422


class TestEdgeCases:
    """エッジケースのテスト。"""

    def test_very_long_term(self, client: TestClient):
        """非常に長い用語名。"""
        long_term = "あ" * 1000
        response = client.post(
            "/api/v1/terms",
            json={"term": long_term, "definition": "テスト", "category": "一般"},
        )
        # 255文字制限があるのでバリデーションエラー
        assert response.status_code == 422

    def test_special_characters_in_term(self, client: TestClient):
        """特殊文字を含む用語。"""
        response = client.post(
            "/api/v1/terms",
            json={
                "term": "テスト<script>alert('xss')</script>",
                "definition": "テスト用の定義",
                "category": "一般",
            },
        )
        # 特殊文字を含むがDBに保存される（出力時にエスケープ）
        assert response.status_code == 201
        data = response.json()
        assert "script" in data["term"]

    def test_unicode_in_term(self, client: TestClient):
        """各種Unicode文字。"""
        response = client.post(
            "/api/v1/terms",
            json={
                "term": "従業員👨‍💼",  # 絵文字
                "definition": "日本語と絵文字のテスト",
                "category": "一般",
            },
        )
        assert response.status_code == 201

    def test_empty_string_fields(self, client: TestClient):
        """空文字列のフィールド。"""
        response = client.post(
            "/api/v1/terms",
            json={"term": "", "definition": "テスト", "category": "一般"},
        )
        # 空文字列はmin_length=1に違反
        assert response.status_code == 422

    def test_whitespace_only_fields(self, client: TestClient):
        """空白のみのフィールド。"""
        response = client.post(
            "/api/v1/terms",
            json={"term": "   ", "definition": "テスト", "category": "一般"},
        )
        # 空白のみでも許可される場合がある
        assert response.status_code in [201, 422]

    def test_concurrent_same_term_creation(self, client: TestClient):
        """同一用語の同時作成試行。"""
        term_data = {"term": "重複テスト", "definition": "テスト", "category": "一般"}

        # 1回目
        response1 = client.post("/api/v1/terms", json=term_data)
        assert response1.status_code == 201

        # 2回目（重複）
        response2 = client.post("/api/v1/terms", json=term_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


class TestReviewErrors:
    """レビュー関連のエラーテスト。"""

    def test_create_review_document_not_found(self, client: TestClient):
        """レビュー作成：文書が存在しない。"""
        response = client.post(
            "/api/v1/reviews", json={"document_id": 99999, "check_item_ids": [1, 2, 3]}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_review_empty_check_items(self, client: TestClient):
        """レビュー作成：チェック項目が空。"""
        response = client.post(
            "/api/v1/reviews", json={"document_id": 1, "check_item_ids": []}
        )
        # 空リストでも文書が見つからないエラーになる
        assert response.status_code in [400, 404, 422]

    def test_get_review_status_not_found(self, client: TestClient):
        """レビュー進捗取得：レビューが存在しない。"""
        response = client.get("/api/v1/reviews/99999/status")
        assert response.status_code == 404


class TestDocumentErrors:
    """文書関連のエラーテスト。"""

    def test_get_document_text_not_found(self, client: TestClient):
        """文書テキスト取得：文書が存在しない。"""
        response = client.get("/api/v1/documents/99999/text")
        assert response.status_code == 404

    def test_get_document_chunks_not_found(self, client: TestClient):
        """文書チャンク取得：文書が存在しない。"""
        response = client.get("/api/v1/documents/99999/chunks")
        assert response.status_code == 404

    def test_trigger_ocr_not_found(self, client: TestClient):
        """OCR再実行：文書が存在しない。"""
        response = client.post("/api/v1/documents/99999/ocr")
        assert response.status_code == 404
