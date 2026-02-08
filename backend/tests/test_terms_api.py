"""
Terms API endpoint tests.

用語管理APIのユニットテスト。
CRUD操作と検証ロジックのテスト。

Note:
    TermCreateスキーマでは以下が必須:
    - term: 用語名
    - definition: 定義
    - category: カテゴリ
"""

import pytest
from fastapi.testclient import TestClient


class TestTermsAPI:
    """用語API テストクラス。"""

    def test_list_terms_empty(self, client: TestClient):
        """用語一覧取得（データなし）。"""
        response = client.get("/api/v1/terms")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_term_success(self, client: TestClient, sample_term_data: dict):
        """用語作成（正常系）。"""
        response = client.post("/api/v1/terms", json=sample_term_data)

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == sample_term_data["term"]
        assert data["definition"] == sample_term_data["definition"]
        assert data["category"] == sample_term_data["category"]
        assert "id" in data
        assert data["id"] > 0

    def test_create_term_duplicate(self, client: TestClient, sample_term_data: dict):
        """用語作成（重複エラー）。"""
        # 1回目：成功
        response = client.post("/api/v1/terms", json=sample_term_data)
        assert response.status_code == 201

        # 2回目：重複エラー
        response = client.post("/api/v1/terms", json=sample_term_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_term_required_fields(self, client: TestClient):
        """用語作成（必須フィールド確認）。"""
        # 必須フィールド（term, definition, category）を含むデータ
        required_data = {
            "term": "テスト用語",
            "definition": "テスト用の定義",
            "category": "一般"
        }
        response = client.post("/api/v1/terms", json=required_data)

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == required_data["term"]
        assert data["category"] == required_data["category"]

    def test_get_term_success(self, client: TestClient, sample_term_data: dict):
        """用語詳細取得（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/terms", json=sample_term_data)
        term_id = create_response.json()["id"]

        # 取得
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["term"] == sample_term_data["term"]
        assert data["id"] == term_id

    def test_get_term_not_found(self, client: TestClient):
        """用語詳細取得（存在しないID）。"""
        response = client.get("/api/v1/terms/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_term_success(self, client: TestClient, sample_term_data: dict):
        """用語更新（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/terms", json=sample_term_data)
        term_id = create_response.json()["id"]

        # 更新
        update_data = {"definition": "更新された定義"}
        response = client.put(f"/api/v1/terms/{term_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["definition"] == update_data["definition"]
        assert data["term"] == sample_term_data["term"]  # 他のフィールドは変わらない

    def test_update_term_not_found(self, client: TestClient):
        """用語更新（存在しないID）。"""
        update_data = {"definition": "テスト"}
        response = client.put("/api/v1/terms/9999", json=update_data)
        assert response.status_code == 404

    def test_delete_term_success(self, client: TestClient, sample_term_data: dict):
        """用語削除（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/terms", json=sample_term_data)
        term_id = create_response.json()["id"]

        # 削除
        response = client.delete(f"/api/v1/terms/{term_id}")
        assert response.status_code == 204

        # 確認
        get_response = client.get(f"/api/v1/terms/{term_id}")
        assert get_response.status_code == 404

    def test_delete_term_not_found(self, client: TestClient):
        """用語削除（存在しないID）。"""
        response = client.delete("/api/v1/terms/9999")
        assert response.status_code == 404

    def test_list_terms_with_filter(self, client: TestClient):
        """用語一覧取得（カテゴリフィルタ）。"""
        # 異なるカテゴリの用語を作成
        terms = [
            {"term": "従業員", "definition": "テスト", "category": "人事"},
            {"term": "取締役", "definition": "テスト", "category": "人事"},
            {"term": "機密情報", "definition": "テスト", "category": "情報セキュリティ"},
        ]
        for term in terms:
            client.post("/api/v1/terms", json=term)

        # フィルタなし
        response = client.get("/api/v1/terms")
        assert len(response.json()) == 3

        # カテゴリでフィルタ
        response = client.get("/api/v1/terms?category=人事")
        data = response.json()
        assert len(data) == 2
        assert all(t["category"] == "人事" for t in data)

    def test_list_terms_pagination(self, client: TestClient):
        """用語一覧取得（ページネーション）。"""
        # 5件作成（カテゴリは必須）
        for i in range(5):
            client.post("/api/v1/terms", json={
                "term": f"用語{i}",
                "definition": f"定義{i}",
                "category": "一般"
            })

        # skip=2, limit=2
        response = client.get("/api/v1/terms?skip=2&limit=2")
        data = response.json()
        assert len(data) == 2

    def test_bulk_create_terms(self, client: TestClient):
        """用語一括作成。"""
        bulk_data = {
            "terms": [
                {"term": "用語A", "definition": "定義A", "category": "一般"},
                {"term": "用語B", "definition": "定義B", "category": "一般"},
                {"term": "用語C", "definition": "定義C", "category": "一般"},
            ]
        }
        response = client.post("/api/v1/terms/bulk", json=bulk_data)

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 3

    def test_bulk_create_terms_skip_duplicates(self, client: TestClient):
        """用語一括作成（重複はスキップ）。"""
        # 事前に1件作成
        client.post("/api/v1/terms", json={
            "term": "用語A",
            "definition": "既存",
            "category": "一般"
        })

        # 重複含む一括作成
        bulk_data = {
            "terms": [
                {"term": "用語A", "definition": "重複", "category": "一般"},  # スキップされる
                {"term": "用語B", "definition": "新規", "category": "一般"},
            ]
        }
        response = client.post("/api/v1/terms/bulk", json=bulk_data)

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1  # 用語Bのみ作成
        assert data[0]["term"] == "用語B"
