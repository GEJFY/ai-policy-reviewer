"""
Writing Rules API endpoint tests.

記載ルール管理APIのユニットテスト。
CRUD操作と検証ロジックのテスト。

Note:
    WritingRuleスキーマは以下のフィールドを持つ:
    - name: ルール名（必須）
    - rule_type: STYLE/FORMAT/TERMINOLOGY（必須）
    - correct_form: 正しい形式（必須）
    - pattern, example_bad, example_good: オプション
"""

from fastapi.testclient import TestClient


class TestWritingRulesAPI:
    """記載ルールAPI テストクラス。"""

    def test_list_writing_rules_empty(self, client: TestClient):
        """記載ルール一覧取得（データなし）。"""
        response = client.get("/api/v1/writing-rules")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_writing_rule_success(self, client: TestClient):
        """記載ルール作成（正常系）。"""
        rule_data = {
            "name": "能動態の使用",
            "rule_type": "STYLE",
            "correct_form": "部長が承認する",
            "example_bad": "部長により承認される",
            "example_good": "部長が承認する",
            "is_active": True
        }
        response = client.post("/api/v1/writing-rules", json=rule_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == rule_data["name"]
        assert data["rule_type"] == rule_data["rule_type"]
        assert data["correct_form"] == rule_data["correct_form"]
        assert "id" in data

    def test_create_writing_rule_minimal(self, client: TestClient):
        """記載ルール作成（最小データ）。"""
        minimal_data = {
            "name": "テストルール",
            "rule_type": "STYLE",
            "correct_form": "テスト形式"
        }
        response = client.post("/api/v1/writing-rules", json=minimal_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == minimal_data["name"]

    def test_get_writing_rule_success(self, client: TestClient):
        """記載ルール詳細取得（正常系）。"""
        # 作成
        rule_data = {
            "name": "テストルール",
            "rule_type": "FORMAT",
            "correct_form": "テスト形式"
        }
        create_response = client.post("/api/v1/writing-rules", json=rule_data)
        rule_id = create_response.json()["id"]

        # 取得
        response = client.get(f"/api/v1/writing-rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["name"] == rule_data["name"]

    def test_get_writing_rule_not_found(self, client: TestClient):
        """記載ルール詳細取得（存在しないID）。"""
        response = client.get("/api/v1/writing-rules/9999")
        assert response.status_code == 404

    def test_update_writing_rule_success(self, client: TestClient):
        """記載ルール更新（正常系）。"""
        # 作成
        rule_data = {
            "name": "更新前ルール",
            "rule_type": "STYLE",
            "correct_form": "元の形式"
        }
        create_response = client.post("/api/v1/writing-rules", json=rule_data)
        rule_id = create_response.json()["id"]

        # 更新
        update_data = {
            "correct_form": "更新された形式",
            "example_good": "良い例"
        }
        response = client.put(f"/api/v1/writing-rules/{rule_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["correct_form"] == update_data["correct_form"]

    def test_update_writing_rule_not_found(self, client: TestClient):
        """記載ルール更新（存在しないID）。"""
        response = client.put("/api/v1/writing-rules/9999", json={"correct_form": "テスト"})
        assert response.status_code == 404

    def test_delete_writing_rule_success(self, client: TestClient):
        """記載ルール削除（正常系）。"""
        # 作成
        rule_data = {
            "name": "削除用ルール",
            "rule_type": "TERMINOLOGY",
            "correct_form": "テスト形式"
        }
        create_response = client.post("/api/v1/writing-rules", json=rule_data)
        rule_id = create_response.json()["id"]

        # 削除
        response = client.delete(f"/api/v1/writing-rules/{rule_id}")
        assert response.status_code == 204

        # 確認
        get_response = client.get(f"/api/v1/writing-rules/{rule_id}")
        assert get_response.status_code == 404

    def test_delete_writing_rule_not_found(self, client: TestClient):
        """記載ルール削除（存在しないID）。"""
        response = client.delete("/api/v1/writing-rules/9999")
        assert response.status_code == 404

    def test_list_writing_rules_filter_by_type(self, client: TestClient):
        """記載ルール一覧取得（タイプフィルタ）。"""
        # 異なるタイプのルールを作成
        rules = [
            {"name": "スタイルルール1", "rule_type": "STYLE", "correct_form": "形式1"},
            {"name": "スタイルルール2", "rule_type": "STYLE", "correct_form": "形式2"},
            {"name": "フォーマットルール", "rule_type": "FORMAT", "correct_form": "形式3"},
        ]
        for rule in rules:
            client.post("/api/v1/writing-rules", json=rule)

        # タイプでフィルタ
        response = client.get("/api/v1/writing-rules?rule_type=STYLE")
        data = response.json()
        assert len(data) == 2
        assert all(r["rule_type"] == "STYLE" for r in data)

    def test_list_writing_rules_filter_by_active(self, client: TestClient):
        """記載ルール一覧取得（有効/無効フィルタ）。"""
        # 有効・無効のルールを作成
        client.post("/api/v1/writing-rules", json={
            "name": "有効ルール", "rule_type": "STYLE",
            "correct_form": "テスト", "is_active": True
        })
        client.post("/api/v1/writing-rules", json={
            "name": "無効ルール", "rule_type": "FORMAT",
            "correct_form": "テスト", "is_active": False
        })

        # 有効のみ取得
        response = client.get("/api/v1/writing-rules?is_active=true")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "有効ルール"

    def test_list_writing_rules_pagination(self, client: TestClient):
        """記載ルール一覧取得（ページネーション）。"""
        # 5件作成
        for i in range(5):
            client.post("/api/v1/writing-rules", json={
                "name": f"ルール{i}",
                "rule_type": "STYLE",
                "correct_form": f"形式{i}"
            })

        # skip=2, limit=2
        response = client.get("/api/v1/writing-rules?skip=2&limit=2")
        data = response.json()
        assert len(data) == 2

    def test_create_writing_rule_with_examples(self, client: TestClient):
        """記載ルール作成（例文付き）。"""
        rule_data = {
            "name": "曖昧表現の禁止",
            "rule_type": "TERMINOLOGY",
            "correct_form": "電子メール、チャット、電話で連絡する",
            "example_bad": "電子メール等で連絡する",
            "example_good": "電子メール、チャット、電話で連絡する"
        }
        response = client.post("/api/v1/writing-rules", json=rule_data)

        assert response.status_code == 201
        data = response.json()
        assert data["example_good"] == rule_data["example_good"]
        assert data["example_bad"] == rule_data["example_bad"]

    def test_create_writing_rule_all_types(self, client: TestClient):
        """すべてのルールタイプで作成できることを確認。"""
        for rule_type in ["STYLE", "FORMAT", "TERMINOLOGY"]:
            response = client.post("/api/v1/writing-rules", json={
                "name": f"ルール_{rule_type}",
                "rule_type": rule_type,
                "correct_form": "テスト形式"
            })
            assert response.status_code == 201
            assert response.json()["rule_type"] == rule_type
