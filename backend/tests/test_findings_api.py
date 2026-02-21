"""
Tests for Findings API endpoints.

指摘事項（Findings）のCRUD操作、承認/却下/保留/リセット、
一括承認のAPIテスト。
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


@pytest.fixture
def sample_review(db_session):
    """レビューと指摘事項のテストデータを作成"""
    doc = Document(
        title="テスト規程.pdf",
        file_path="/tmp/test.pdf",
        ocr_status="completed",
        extracted_text="テスト文書の内容",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    review = Review(document_id=doc.id, status="completed")
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    findings = [
        ReviewFinding(
            review_id=review.id,
            issue_type="TERMINOLOGY",
            severity="HIGH",
            description="「社員」は正式用語「従業員」に統一すべき",
            location="第3条",
            original_text="社員は所定の手続きに従い申請する",
            suggestion="「従業員」に変更",
            rationale="用語辞書の定義に基づく",
            confidence=0.95,
            status="PENDING",
        ),
        ReviewFinding(
            review_id=review.id,
            issue_type="GRAMMAR",
            severity="MEDIUM",
            description="「等」の使用が曖昧",
            location="第5条第2項",
            original_text="書類等を提出する",
            suggestion="具体的な書類名を列挙",
            confidence=0.8,
            status="PENDING",
        ),
        ReviewFinding(
            review_id=review.id,
            issue_type="COMPLIANCE",
            severity="LOW",
            description="参照先の条文番号が不明確",
            location="第10条",
            original_text="関連法令に従う",
            suggestion="具体的な法令名と条文番号を記載",
            confidence=0.6,
            status="PENDING",
        ),
    ]
    for f in findings:
        db_session.add(f)
    db_session.commit()

    for f in findings:
        db_session.refresh(f)

    return {"review": review, "findings": findings, "document": doc}


class TestListFindings:
    """GET /reviews/{review_id}/findings のテスト"""

    def test_list_findings_success(self, client: TestClient, sample_review):
        """指摘事項一覧を正常に取得"""
        review_id = sample_review["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/findings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_findings_filter_by_severity(self, client: TestClient, sample_review):
        """severityフィルタが正しく機能"""
        review_id = sample_review["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/findings?severity=HIGH")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "HIGH"

    def test_list_findings_filter_by_status(self, client: TestClient, sample_review):
        """statusフィルタが正しく機能"""
        review_id = sample_review["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/findings?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_findings_combined_filter(self, client: TestClient, sample_review):
        """severity + status の複合フィルタ"""
        review_id = sample_review["review"].id
        response = client.get(
            f"/api/v1/reviews/{review_id}/findings?severity=MEDIUM&status=PENDING"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "MEDIUM"

    def test_list_findings_review_not_found(self, client: TestClient):
        """存在しないレビューIDで404"""
        response = client.get("/api/v1/reviews/9999/findings")
        assert response.status_code == 404

    def test_list_findings_empty(self, client: TestClient, db_session):
        """指摘事項が0件のレビュー"""
        doc = Document(
            title="空レビュー.pdf",
            file_path="/tmp/empty.pdf",
            ocr_status="completed",
        )
        db_session.add(doc)
        db_session.commit()
        review = Review(document_id=doc.id, status="completed")
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/api/v1/reviews/{review.id}/findings")
        assert response.status_code == 200
        assert response.json() == []


class TestGetFinding:
    """GET /findings/{finding_id} のテスト"""

    def test_get_finding_success(self, client: TestClient, sample_review):
        """指摘事項を個別に取得"""
        finding = sample_review["findings"][0]
        response = client.get(f"/api/v1/findings/{finding.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == finding.id
        assert data["severity"] == "HIGH"
        assert data["issue_type"] == "TERMINOLOGY"
        assert data["confidence"] == 0.95

    def test_get_finding_not_found(self, client: TestClient):
        """存在しないfinding IDで404"""
        response = client.get("/api/v1/findings/9999")
        assert response.status_code == 404


class TestApproveFinding:
    """PUT /findings/{finding_id}/approve のテスト"""

    def test_approve_finding_with_comment(self, client: TestClient, sample_review):
        """コメント付きで承認"""
        finding = sample_review["findings"][0]
        response = client.put(
            f"/api/v1/findings/{finding.id}/approve",
            json={"comment": "修正を確認しました"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["comment"] == "修正を確認しました"
        assert data["reviewed_at"] is not None

    def test_approve_finding_without_comment(self, client: TestClient, sample_review):
        """コメントなしで承認"""
        finding = sample_review["findings"][1]
        response = client.put(
            f"/api/v1/findings/{finding.id}/approve",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["comment"] is None

    def test_approve_finding_not_found(self, client: TestClient):
        """存在しないfindingの承認で404"""
        response = client.put(
            "/api/v1/findings/9999/approve",
            json={"comment": "テスト"},
        )
        assert response.status_code == 404


class TestRejectFinding:
    """PUT /findings/{finding_id}/reject のテスト"""

    def test_reject_finding(self, client: TestClient, sample_review):
        """指摘事項を却下"""
        finding = sample_review["findings"][0]
        response = client.put(
            f"/api/v1/findings/{finding.id}/reject",
            json={"comment": "誤検知のため却下"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["comment"] == "誤検知のため却下"

    def test_reject_finding_not_found(self, client: TestClient):
        """存在しないfindingの却下で404"""
        response = client.put(
            "/api/v1/findings/9999/reject",
            json={},
        )
        assert response.status_code == 404


class TestDeferFinding:
    """PUT /findings/{finding_id}/defer のテスト"""

    def test_defer_finding(self, client: TestClient, sample_review):
        """指摘事項を保留"""
        finding = sample_review["findings"][1]
        response = client.put(
            f"/api/v1/findings/{finding.id}/defer",
            json={"comment": "次回改訂時に対応"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEFERRED"
        assert data["comment"] == "次回改訂時に対応"

    def test_defer_finding_not_found(self, client: TestClient):
        """存在しないfindingの保留で404"""
        response = client.put(
            "/api/v1/findings/9999/defer",
            json={},
        )
        assert response.status_code == 404


class TestResetFinding:
    """PUT /findings/{finding_id}/reset のテスト"""

    def test_reset_approved_finding(self, client: TestClient, sample_review):
        """承認済みの指摘事項をリセット"""
        finding = sample_review["findings"][0]
        # まず承認
        client.put(
            f"/api/v1/findings/{finding.id}/approve",
            json={"comment": "承認"},
        )
        # リセット
        response = client.put(f"/api/v1/findings/{finding.id}/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["reviewed_at"] is None
        assert data["comment"] is None

    def test_reset_finding_not_found(self, client: TestClient):
        """存在しないfindingのリセットで404"""
        response = client.put("/api/v1/findings/9999/reset")
        assert response.status_code == 404


class TestBulkApprove:
    """POST /reviews/{review_id}/findings/bulk-approve のテスト"""

    def test_bulk_approve(self, client: TestClient, sample_review):
        """複数の指摘事項を一括承認"""
        review_id = sample_review["review"].id
        finding_ids = [f.id for f in sample_review["findings"][:2]]
        response = client.post(
            f"/api/v1/reviews/{review_id}/findings/bulk-approve",
            json={
                "finding_ids": finding_ids,
                "action": "APPROVED",
                "comment": "一括承認",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["status"] == "APPROVED"
            assert item["comment"] == "一括承認"

    def test_bulk_reject(self, client: TestClient, sample_review):
        """複数の指摘事項を一括却下"""
        review_id = sample_review["review"].id
        finding_ids = [f.id for f in sample_review["findings"]]
        response = client.post(
            f"/api/v1/reviews/{review_id}/findings/bulk-approve",
            json={
                "finding_ids": finding_ids,
                "action": "REJECTED",
                "comment": "全件却下",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for item in data:
            assert item["status"] == "REJECTED"

    def test_bulk_approve_mismatched_ids(self, client: TestClient, sample_review):
        """他レビューのfinding IDを含む場合400エラー"""
        review_id = sample_review["review"].id
        response = client.post(
            f"/api/v1/reviews/{review_id}/findings/bulk-approve",
            json={
                "finding_ids": [9999],
                "action": "APPROVED",
            },
        )
        assert response.status_code == 400

    def test_bulk_approve_review_not_found(self, client: TestClient):
        """存在しないレビューで404"""
        response = client.post(
            "/api/v1/reviews/9999/findings/bulk-approve",
            json={
                "finding_ids": [1],
                "action": "APPROVED",
            },
        )
        assert response.status_code == 404


class TestFindingsSummary:
    """GET /reviews/{review_id}/findings/summary のテスト"""

    def test_summary_all_pending(self, client: TestClient, sample_review):
        """全件PENDING状態のサマリー"""
        review_id = sample_review["review"].id
        response = client.get(f"/api/v1/reviews/{review_id}/findings/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_findings"] == 3
        assert data["high_count"] == 1
        assert data["medium_count"] == 1
        assert data["low_count"] == 1
        assert data["pending_count"] == 3
        assert data["approved_count"] == 0
        assert data["rejected_count"] == 0
        assert data["deferred_count"] == 0

    def test_summary_after_actions(self, client: TestClient, sample_review):
        """承認/却下後のサマリー更新確認"""
        review_id = sample_review["review"].id
        findings = sample_review["findings"]

        # 1件承認、1件却下
        client.put(f"/api/v1/findings/{findings[0].id}/approve", json={})
        client.put(f"/api/v1/findings/{findings[1].id}/reject", json={})

        response = client.get(f"/api/v1/reviews/{review_id}/findings/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_findings"] == 3
        assert data["pending_count"] == 1
        assert data["approved_count"] == 1
        assert data["rejected_count"] == 1

    def test_summary_review_not_found(self, client: TestClient):
        """存在しないレビューのサマリーで404"""
        response = client.get("/api/v1/reviews/9999/findings/summary")
        assert response.status_code == 404


class TestFindingWorkflow:
    """指摘事項の一連のワークフローテスト"""

    def test_full_review_workflow(self, client: TestClient, sample_review):
        """承認→リセット→却下の完全ワークフロー"""
        finding_id = sample_review["findings"][0].id

        # Step 1: 承認
        response = client.put(
            f"/api/v1/findings/{finding_id}/approve",
            json={"comment": "初回承認"},
        )
        assert response.json()["status"] == "APPROVED"

        # Step 2: リセット
        response = client.put(f"/api/v1/findings/{finding_id}/reset")
        assert response.json()["status"] == "PENDING"
        assert response.json()["comment"] is None

        # Step 3: 却下
        response = client.put(
            f"/api/v1/findings/{finding_id}/reject",
            json={"comment": "再検討の結果、誤検知と判断"},
        )
        assert response.json()["status"] == "REJECTED"
        assert response.json()["comment"] == "再検討の結果、誤検知と判断"

    def test_filter_after_bulk_action(self, client: TestClient, sample_review):
        """一括操作後のフィルタリング確認"""
        review_id = sample_review["review"].id
        finding_ids = [f.id for f in sample_review["findings"][:2]]

        # 2件を一括承認
        client.post(
            f"/api/v1/reviews/{review_id}/findings/bulk-approve",
            json={
                "finding_ids": finding_ids,
                "action": "APPROVED",
            },
        )

        # PENDING のみ取得 → 1件
        response = client.get(f"/api/v1/reviews/{review_id}/findings?status=PENDING")
        assert len(response.json()) == 1

        # APPROVED のみ取得 → 2件
        response = client.get(f"/api/v1/reviews/{review_id}/findings?status=APPROVED")
        assert len(response.json()) == 2
