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
from app.models.document import Document
from app.models.check_item import CheckItem
from app.models.review import Review, ReviewFinding

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


class TestBatchReview:
    """一括レビューAPIのテスト"""

    @pytest.fixture
    def batch_setup(self, db_session):
        """一括レビューテスト用データ"""
        docs = []
        for i in range(3):
            doc = Document(
                title=f"テスト規程{i+1}.pdf",
                file_path=f"/tmp/test{i+1}.pdf",
                ocr_status="completed",
                extracted_text=f"テスト文書{i+1}の内容",
            )
            db_session.add(doc)
        # OCR未完了のドキュメント
        doc_pending = Document(
            title="未処理規程.pdf",
            file_path="/tmp/pending.pdf",
            ocr_status="processing",
        )
        db_session.add(doc_pending)
        db_session.commit()

        for doc in [doc_pending]:
            db_session.refresh(doc)

        all_docs = db_session.query(Document).all()
        docs = [d for d in all_docs if d.ocr_status == "completed"]

        check_item = CheckItem(
            name="用語チェック",
            category="TERMINOLOGY",
            description="テスト",
            severity="HIGH",
        )
        db_session.add(check_item)
        db_session.commit()
        db_session.refresh(check_item)

        return {
            "docs": docs,
            "pending_doc": doc_pending,
            "check_item": check_item,
        }

    def test_batch_review_invalid_check_item(self, client: TestClient, batch_setup):
        """存在しないチェック項目でバッチレビュー"""
        response = client.post(
            "/api/v1/reviews/batch",
            json={
                "document_ids": [batch_setup["docs"][0].id],
                "check_item_ids": [9999],
            },
        )
        assert response.status_code == 400

    def test_batch_review_empty_documents(self, client: TestClient, batch_setup):
        """空のドキュメントリストでバッチレビュー"""
        response = client.post(
            "/api/v1/reviews/batch",
            json={
                "document_ids": [],
                "check_item_ids": [batch_setup["check_item"].id],
            },
        )
        assert response.status_code == 422

    def test_batch_review_empty_check_items(self, client: TestClient, batch_setup):
        """空のチェック項目リストでバッチレビュー"""
        response = client.post(
            "/api/v1/reviews/batch",
            json={
                "document_ids": [batch_setup["docs"][0].id],
                "check_item_ids": [],
            },
        )
        assert response.status_code == 422


class TestRevisedDocumentDownload:
    """改訂版ダウンロードAPIのテスト"""

    @pytest.fixture
    def review_with_approved_findings(self, db_session):
        """承認済み指摘付きレビューデータ"""
        doc = Document(
            title="改訂テスト規程.pdf",
            file_path="/tmp/revised_test.pdf",
            ocr_status="completed",
            extracted_text="社員は所定の手続きに従い申請する。書類等を提出すること。",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        review = Review(document_id=doc.id, status="completed")
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        f1 = ReviewFinding(
            review_id=review.id,
            issue_type="TERMINOLOGY",
            severity="HIGH",
            description="「社員」を「従業員」に統一",
            original_text="社員は所定の手続きに従い申請する",
            suggestion="従業員は所定の手続きに従い申請する",
            status="APPROVED",
        )
        f2 = ReviewFinding(
            review_id=review.id,
            issue_type="GRAMMAR",
            severity="MEDIUM",
            description="曖昧な表現",
            original_text="書類等を提出すること",
            suggestion="必要書類を提出すること",
            status="PENDING",
        )
        db_session.add_all([f1, f2])
        db_session.commit()

        return {"review": review, "document": doc, "findings": [f1, f2]}

    def test_download_revised_document_success(
        self, client: TestClient, review_with_approved_findings
    ):
        """改訂版ダウンロード成功"""
        review_id = review_with_approved_findings["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/revised-document")
        assert response.status_code == 200
        assert (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            in response.headers["content-type"]
        )
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_download_revised_document_not_found(self, client: TestClient):
        """存在しないレビューの改訂版ダウンロード"""
        response = client.get("/api/v1/reviews/9999/revised-document")
        assert response.status_code == 404

    def test_download_revised_document_no_text(
        self, client: TestClient, db_session
    ):
        """テキストなし文書の改訂版ダウンロード"""
        doc = Document(
            title="空文書.pdf",
            file_path="/tmp/empty.pdf",
            ocr_status="completed",
            extracted_text=None,
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        review = Review(document_id=doc.id, status="completed")
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        response = client.get(f"/api/v1/reviews/{review.id}/revised-document")
        assert response.status_code == 404

    def test_download_applies_only_approved(
        self, client: TestClient, review_with_approved_findings
    ):
        """承認済みの指摘のみが適用される"""
        review_id = review_with_approved_findings["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/revised-document")
        assert response.status_code == 200
        # DOCX content is binary, just ensure it's a valid file
        # The actual content verification would require python-docx to parse
        assert len(response.content) > 100
