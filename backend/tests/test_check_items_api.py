"""
Check Items API endpoint tests.

チェック項目管理APIのユニットテスト。
CRUD操作と検証ロジックのテスト。
"""

from fastapi.testclient import TestClient


class TestCheckItemsAPI:
    """チェック項目API テストクラス。"""

    def test_list_check_items_empty(self, client: TestClient):
        """チェック項目一覧取得（データなし）。"""
        response = client.get("/api/v1/check-items")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_check_item_success(self, client: TestClient, sample_check_item_data: dict):
        """チェック項目作成（正常系）。"""
        response = client.post("/api/v1/check-items", json=sample_check_item_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_check_item_data["name"]
        assert data["category"] == sample_check_item_data["category"]
        assert data["severity"] == sample_check_item_data["severity"]
        assert "id" in data

    def test_create_check_item_minimal(self, client: TestClient):
        """チェック項目作成（最小データ）。"""
        minimal_data = {
            "name": "テストチェック項目",
            "category": "TERMINOLOGY",
            "description": "テスト用"
        }
        response = client.post("/api/v1/check-items", json=minimal_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == minimal_data["name"]

    def test_get_check_item_success(self, client: TestClient, sample_check_item_data: dict):
        """チェック項目詳細取得（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/check-items", json=sample_check_item_data)
        item_id = create_response.json()["id"]

        # 取得
        response = client.get(f"/api/v1/check-items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == sample_check_item_data["name"]

    def test_get_check_item_not_found(self, client: TestClient):
        """チェック項目詳細取得（存在しないID）。"""
        response = client.get("/api/v1/check-items/9999")
        assert response.status_code == 404

    def test_update_check_item_success(self, client: TestClient, sample_check_item_data: dict):
        """チェック項目更新（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/check-items", json=sample_check_item_data)
        item_id = create_response.json()["id"]

        # 更新
        update_data = {"description": "更新された説明", "severity": "MEDIUM"}
        response = client.put(f"/api/v1/check-items/{item_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["severity"] == update_data["severity"]

    def test_update_check_item_not_found(self, client: TestClient):
        """チェック項目更新（存在しないID）。"""
        response = client.put("/api/v1/check-items/9999", json={"description": "テスト"})
        assert response.status_code == 404

    def test_delete_check_item_success(self, client: TestClient, sample_check_item_data: dict):
        """チェック項目削除（正常系）。"""
        # 作成
        create_response = client.post("/api/v1/check-items", json=sample_check_item_data)
        item_id = create_response.json()["id"]

        # 削除
        response = client.delete(f"/api/v1/check-items/{item_id}")
        assert response.status_code == 204

        # 確認
        get_response = client.get(f"/api/v1/check-items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_check_item_not_found(self, client: TestClient):
        """チェック項目削除（存在しないID）。"""
        response = client.delete("/api/v1/check-items/9999")
        assert response.status_code == 404

    def test_list_check_items_filter_by_category(self, client: TestClient):
        """チェック項目一覧取得（カテゴリフィルタ）。"""
        # 異なるカテゴリのチェック項目を作成
        items = [
            {"name": "用語チェック", "category": "TERMINOLOGY", "description": "テスト"},
            {"name": "文法チェック", "category": "GRAMMAR", "description": "テスト"},
            {"name": "構成チェック", "category": "STRUCTURE", "description": "テスト"},
        ]
        for item in items:
            client.post("/api/v1/check-items", json=item)

        # カテゴリでフィルタ
        response = client.get("/api/v1/check-items?category=TERMINOLOGY")
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "TERMINOLOGY"

    def test_list_check_items_filter_by_active(self, client: TestClient):
        """チェック項目一覧取得（有効/無効フィルタ）。"""
        # 有効・無効のチェック項目を作成
        client.post("/api/v1/check-items", json={
            "name": "有効項目", "category": "TERMINOLOGY",
            "description": "テスト", "is_active": True
        })
        client.post("/api/v1/check-items", json={
            "name": "無効項目", "category": "GRAMMAR",
            "description": "テスト", "is_active": False
        })

        # 有効のみ取得
        response = client.get("/api/v1/check-items?is_active=true")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "有効項目"

    def test_list_check_items_pagination(self, client: TestClient):
        """チェック項目一覧取得（ページネーション）。"""
        # 5件作成
        for i in range(5):
            client.post("/api/v1/check-items", json={
                "name": f"チェック項目{i}",
                "category": "TERMINOLOGY",
                "description": f"説明{i}"
            })

        # skip=2, limit=2
        response = client.get("/api/v1/check-items?skip=2&limit=2")
        data = response.json()
        assert len(data) == 2

    def test_create_check_item_with_prompt_template(self, client: TestClient):
        """チェック項目作成（プロンプトテンプレート付き）。"""
        item_data = {
            "name": "カスタムチェック",
            "category": "TERMINOLOGY",
            "description": "カスタムプロンプトを使用",
            "prompt_template": "以下のテキストで{term}の使用状況を確認してください:\n{text}"
        }
        response = client.post("/api/v1/check-items", json=item_data)

        assert response.status_code == 201
        data = response.json()
        assert data["prompt_template"] == item_data["prompt_template"]
