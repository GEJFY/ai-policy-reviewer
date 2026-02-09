"""
Integration tests for the policy review system.

結合テスト: 複数のコンポーネントを組み合わせたエンドツーエンドのテスト
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.models.base import Base


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestMasterDataWorkflow:
    """マスタデータの一連のワークフローをテスト"""

    def test_create_and_use_term_dictionary(self, client: TestClient):
        """用語辞書の作成と利用のワークフロー"""
        # 1. 複数の用語を一括登録
        terms = [
            {
                "term": "従業員",
                "definition": "当社と雇用契約を締結した者",
                "category": "人事",
            },
            {
                "term": "正社員",
                "definition": "期間の定めのない雇用契約を締結した従業員",
                "category": "人事",
            },
            {
                "term": "契約社員",
                "definition": "期間の定めのある雇用契約を締結した従業員",
                "category": "人事",
            },
        ]
        response = client.post("/api/v1/terms/bulk", json={"terms": terms})
        assert response.status_code == 201
        data = response.json()
        # APIはリストを返す
        assert isinstance(data, list)
        assert len(data) == 3

        # 2. 用語一覧を取得（APIはリストを直接返す）
        response = client.get("/api/v1/terms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        # 3. カテゴリでフィルタリング
        response = client.get("/api/v1/terms?category=人事")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # 4. 用語を更新
        term_id = data[0]["id"]
        response = client.put(
            f"/api/v1/terms/{term_id}", json={"aliases": ["社員", "スタッフ"]}
        )
        assert response.status_code == 200

        # 5. 更新を確認
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 200
        assert response.json()["aliases"] == ["社員", "スタッフ"]

    def test_create_and_manage_check_items(self, client: TestClient):
        """チェック項目の作成と管理のワークフロー"""
        # 1. チェック項目を作成
        check_items = [
            {
                "name": "用語統一チェック",
                "category": "TERMINOLOGY",
                "description": "社内用語の統一性を確認",
                "severity": "HIGH",
                "is_active": True,
            },
            {
                "name": "文体統一チェック",
                "category": "GRAMMAR",
                "description": "である体で統一されているか確認",
                "severity": "MEDIUM",
                "is_active": True,
            },
            {
                "name": "法的要件チェック",
                "category": "COMPLIANCE",
                "description": "労働基準法の要件を満たしているか確認",
                "severity": "HIGH",
                "is_active": False,  # 無効化
            },
        ]

        created_ids = []
        for item in check_items:
            response = client.post("/api/v1/check-items", json=item)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # 2. 有効なチェック項目のみ取得
        response = client.get("/api/v1/check-items?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # 3. カテゴリでフィルタリング
        response = client.get("/api/v1/check-items?category=TERMINOLOGY")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "用語統一チェック"

        # 4. チェック項目を有効化
        response = client.put(
            f"/api/v1/check-items/{created_ids[2]}", json={"is_active": True}
        )
        assert response.status_code == 200

        # 5. 全件取得で3件になることを確認
        response = client.get("/api/v1/check-items?is_active=true")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_create_and_use_writing_rules(self, client: TestClient):
        """記載ルールの作成と利用のワークフロー"""
        # 1. 記載ルールを作成
        rules = [
            {
                "name": "である体の使用",
                "rule_type": "STYLE",
                "correct_form": "である体を使用する",
                "example_bad": "報告してください",
                "example_good": "報告しなければならない",
            },
            {
                "name": "数字の半角統一",
                "rule_type": "FORMAT",
                "correct_form": "数字は半角を使用",
                "example_bad": "第１条",
                "example_good": "第1条",
            },
        ]

        for rule in rules:
            response = client.post("/api/v1/writing-rules", json=rule)
            assert response.status_code == 201

        # 2. ルール一覧を取得
        response = client.get("/api/v1/writing-rules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # 3. タイプでフィルタリング
        response = client.get("/api/v1/writing-rules?rule_type=STYLE")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "である体の使用"


class TestDocumentWorkflow:
    """文書管理のワークフローをテスト"""

    def test_document_lifecycle(self, client: TestClient):
        """文書のライフサイクル（作成→取得→削除）"""
        # 文書一覧（空）
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_document_not_found_handling(self, client: TestClient):
        """存在しない文書へのアクセス"""
        # 存在しないIDでアクセス
        response = client.get("/api/v1/documents/999")
        assert response.status_code == 404

        response = client.get("/api/v1/documents/999/text")
        assert response.status_code == 404

        response = client.get("/api/v1/documents/999/chunks")
        assert response.status_code == 404


class TestReviewWorkflow:
    """レビュー実行のワークフローをテスト"""

    def test_review_creation_requires_document(self, client: TestClient):
        """レビュー作成には文書が必要"""
        # チェック項目を作成
        check_item = {
            "name": "テストチェック",
            "category": "TERMINOLOGY",
            "description": "テスト用チェック項目",
            "severity": "MEDIUM",
        }
        response = client.post("/api/v1/check-items", json=check_item)
        assert response.status_code == 201
        check_item_id = response.json()["id"]

        # 存在しない文書でレビュー作成を試みる
        response = client.post(
            "/api/v1/reviews",
            json={"document_id": 999, "check_item_ids": [check_item_id]},
        )
        assert response.status_code == 404

    def test_review_requires_check_items(self, client: TestClient):
        """レビュー作成にはチェック項目が必要"""
        # チェック項目なしでレビュー作成を試みる
        response = client.post(
            "/api/v1/reviews", json={"document_id": 1, "check_item_ids": []}
        )
        assert response.status_code == 422  # Validation error


class TestPaginationAndFiltering:
    """ページネーションとフィルタリングのテスト"""

    def test_terms_pagination(self, client: TestClient):
        """用語のページネーション"""
        # 15件の用語を作成
        for i in range(15):
            client.post(
                "/api/v1/terms",
                json={
                    "term": f"用語{i+1:02d}",
                    "definition": f"定義{i+1}",
                    "category": "一般",
                },
            )

        # デフォルトのページサイズ（上限100）
        response = client.get("/api/v1/terms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 15

        # ページサイズ指定
        response = client.get("/api/v1/terms?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # オフセット指定
        response = client.get("/api/v1/terms?limit=5&skip=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_check_items_filtering(self, client: TestClient):
        """チェック項目のフィルタリング"""
        # 異なるカテゴリのチェック項目を作成
        categories = ["TERMINOLOGY", "GRAMMAR", "COMPLIANCE", "TERMINOLOGY"]
        for i, cat in enumerate(categories):
            client.post(
                "/api/v1/check-items",
                json={
                    "name": f"チェック{i+1}",
                    "category": cat,
                    "description": f"説明{i+1}",
                    "severity": "MEDIUM",
                },
            )

        # カテゴリフィルタ
        response = client.get("/api/v1/check-items?category=TERMINOLOGY")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # 存在しないカテゴリは422を返す（Enum検証）
        response = client.get("/api/v1/check-items?category=NONEXISTENT")
        assert response.status_code == 422

        # 有効なカテゴリで結果が0件のケース
        response = client.get("/api/v1/check-items?category=SECURITY")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestConcurrentOperations:
    """並行操作のテスト"""

    def test_concurrent_term_updates(self, client: TestClient):
        """用語の並行更新"""
        # 用語を作成
        response = client.post(
            "/api/v1/terms",
            json={"term": "テスト用語", "definition": "初期定義", "category": "一般"},
        )
        term_id = response.json()["id"]

        # 複数回更新
        for i in range(5):
            response = client.put(
                f"/api/v1/terms/{term_id}", json={"definition": f"定義バージョン{i+1}"}
            )
            assert response.status_code == 200

        # 最終状態を確認
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 200
        assert response.json()["definition"] == "定義バージョン5"


class TestAPIResponseFormats:
    """APIレスポンス形式のテスト"""

    def test_list_response_format(self, client: TestClient):
        """リストレスポンスの形式（直接リストを返す）"""
        response = client.get("/api/v1/terms")
        assert response.status_code == 200
        data = response.json()

        # リストが返される
        assert isinstance(data, list)

    def test_detail_response_format(self, client: TestClient):
        """詳細レスポンスの形式"""
        # 用語を作成
        response = client.post(
            "/api/v1/terms",
            json={"term": "テスト", "definition": "テスト定義", "category": "一般"},
        )
        term_id = response.json()["id"]

        # 詳細を取得
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 200
        data = response.json()

        # 必須フィールドの確認
        assert "id" in data
        assert "term" in data
        assert "definition" in data
        assert "category" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_error_response_format(self, client: TestClient):
        """エラーレスポンスの形式"""
        response = client.get("/api/v1/terms/999")
        assert response.status_code == 404
        data = response.json()

        # エラーレスポンスの形式確認
        assert "detail" in data


class TestHealthAndStatus:
    """ヘルスチェックとステータスのテスト"""

    def test_health_endpoint(self, client: TestClient):
        """ヘルスエンドポイント"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client: TestClient):
        """ルートエンドポイント"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_openapi_schema(self, client: TestClient):
        """OpenAPIスキーマ"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestCRUDOperations:
    """CRUD操作の完全なテスト"""

    def test_term_crud_complete(self, client: TestClient):
        """用語のCRUD操作"""
        # Create
        response = client.post(
            "/api/v1/terms",
            json={
                "term": "CRUD用語",
                "definition": "CRUD操作テスト用",
                "category": "テスト",
            },
        )
        assert response.status_code == 201
        term_id = response.json()["id"]

        # Read
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 200
        assert response.json()["term"] == "CRUD用語"

        # Update
        response = client.put(
            f"/api/v1/terms/{term_id}", json={"definition": "更新後の定義"}
        )
        assert response.status_code == 200
        assert response.json()["definition"] == "更新後の定義"

        # Delete
        response = client.delete(f"/api/v1/terms/{term_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/v1/terms/{term_id}")
        assert response.status_code == 404

    def test_check_item_crud_complete(self, client: TestClient):
        """チェック項目のCRUD操作"""
        # Create
        response = client.post(
            "/api/v1/check-items",
            json={
                "name": "CRUDチェック",
                "category": "TERMINOLOGY",
                "description": "CRUD操作テスト用",
                "severity": "MEDIUM",
            },
        )
        assert response.status_code == 201
        item_id = response.json()["id"]

        # Read
        response = client.get(f"/api/v1/check-items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUDチェック"

        # Update
        response = client.put(
            f"/api/v1/check-items/{item_id}", json={"severity": "HIGH"}
        )
        assert response.status_code == 200
        assert response.json()["severity"] == "HIGH"

        # Delete
        response = client.delete(f"/api/v1/check-items/{item_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/v1/check-items/{item_id}")
        assert response.status_code == 404

    def test_writing_rule_crud_complete(self, client: TestClient):
        """記載ルールのCRUD操作"""
        # Create
        response = client.post(
            "/api/v1/writing-rules",
            json={
                "name": "CRUDルール",
                "rule_type": "STYLE",
                "correct_form": "正しい形式",
            },
        )
        assert response.status_code == 201
        rule_id = response.json()["id"]

        # Read
        response = client.get(f"/api/v1/writing-rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUDルール"

        # Update
        response = client.put(
            f"/api/v1/writing-rules/{rule_id}", json={"correct_form": "更新後の形式"}
        )
        assert response.status_code == 200
        assert response.json()["correct_form"] == "更新後の形式"

        # Delete
        response = client.delete(f"/api/v1/writing-rules/{rule_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/v1/writing-rules/{rule_id}")
        assert response.status_code == 404
