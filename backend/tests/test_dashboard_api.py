"""
Tests for Dashboard statistics API endpoint.

ダッシュボード統計APIの集計精度・パフォーマンスのテスト。
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
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestDashboardStats:
    """GET /api/v1/dashboard/stats のテスト"""

    def test_empty_database(self, client: TestClient):
        """空のDBで全カウントが0"""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 0
        assert data["review_count"] == 0
        assert data["term_count"] == 0
        assert data["check_item_count"] == 0
        assert data["writing_rule_count"] == 0
        assert data["finding_total"] == 0
        assert data["finding_by_severity"]["high"] == 0
        assert data["finding_by_severity"]["medium"] == 0
        assert data["finding_by_severity"]["low"] == 0
        assert data["finding_by_status"]["pending"] == 0
        assert data["review_by_status"]["completed"] == 0

    def test_master_data_counts(self, client: TestClient, db_session):
        """マスタデータ件数が正確"""
        # Terms
        for i in range(5):
            db_session.add(
                Term(term=f"用語{i}", definition=f"定義{i}", category="テスト")
            )
        # CheckItems
        for i in range(3):
            db_session.add(
                CheckItem(
                    name=f"チェック{i}",
                    category="TEST",
                    description=f"説明{i}",
                    severity="MEDIUM",
                )
            )
        # WritingRules
        for i in range(4):
            db_session.add(
                WritingRule(
                    name=f"ルール{i}",
                    rule_type="STYLE",
                    correct_form=f"正しい形式{i}",
                )
            )
        db_session.commit()

        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        assert data["term_count"] == 5
        assert data["check_item_count"] == 3
        assert data["writing_rule_count"] == 4

    def test_finding_severity_counts(self, client: TestClient, db_session):
        """Finding件数がseverity別に正確"""
        doc = Document(title="test.pdf", file_path="/tmp/t.pdf", ocr_status="completed")
        db_session.add(doc)
        db_session.commit()

        review = Review(document_id=doc.id, status="completed")
        db_session.add(review)
        db_session.commit()

        findings_data = [
            ("HIGH", "PENDING"),
            ("HIGH", "APPROVED"),
            ("MEDIUM", "PENDING"),
            ("MEDIUM", "REJECTED"),
            ("MEDIUM", "PENDING"),
            ("LOW", "DEFERRED"),
        ]
        for severity, status in findings_data:
            db_session.add(
                ReviewFinding(
                    review_id=review.id,
                    issue_type="TEST",
                    severity=severity,
                    description=f"{severity} finding",
                    status=status,
                )
            )
        db_session.commit()

        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        assert data["finding_total"] == 6
        assert data["finding_by_severity"]["high"] == 2
        assert data["finding_by_severity"]["medium"] == 3
        assert data["finding_by_severity"]["low"] == 1

    def test_finding_status_counts(self, client: TestClient, db_session):
        """Finding件数がstatus別に正確"""
        doc = Document(title="test.pdf", file_path="/tmp/t.pdf", ocr_status="completed")
        db_session.add(doc)
        db_session.commit()

        review = Review(document_id=doc.id, status="completed")
        db_session.add(review)
        db_session.commit()

        findings_data = [
            ("HIGH", "PENDING"),
            ("HIGH", "APPROVED"),
            ("MEDIUM", "PENDING"),
            ("MEDIUM", "REJECTED"),
            ("MEDIUM", "PENDING"),
            ("LOW", "DEFERRED"),
        ]
        for severity, status in findings_data:
            db_session.add(
                ReviewFinding(
                    review_id=review.id,
                    issue_type="TEST",
                    severity=severity,
                    description=f"{severity} finding",
                    status=status,
                )
            )
        db_session.commit()

        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        assert data["finding_by_status"]["pending"] == 3
        assert data["finding_by_status"]["approved"] == 1
        assert data["finding_by_status"]["rejected"] == 1
        assert data["finding_by_status"]["deferred"] == 1

    def test_review_status_counts(self, client: TestClient, db_session):
        """レビュー件数がstatus別に正確"""
        doc = Document(title="test.pdf", file_path="/tmp/t.pdf", ocr_status="completed")
        db_session.add(doc)
        db_session.commit()

        statuses = ["pending", "processing", "completed", "completed", "failed"]
        for s in statuses:
            db_session.add(Review(document_id=doc.id, status=s))
        db_session.commit()

        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        assert data["review_count"] == 5
        assert data["review_by_status"]["pending"] == 1
        assert data["review_by_status"]["processing"] == 1
        assert data["review_by_status"]["completed"] == 2
        assert data["review_by_status"]["failed"] == 1

    def test_comprehensive_stats(self, client: TestClient, db_session):
        """全統計値を同時に検証する統合テスト"""
        # Documents
        doc1 = Document(
            title="規程A.pdf", file_path="/tmp/a.pdf", ocr_status="completed"
        )
        doc2 = Document(title="規程B.pdf", file_path="/tmp/b.pdf", ocr_status="pending")
        db_session.add_all([doc1, doc2])
        db_session.commit()

        # Reviews
        r1 = Review(document_id=doc1.id, status="completed")
        r2 = Review(document_id=doc1.id, status="failed")
        db_session.add_all([r1, r2])
        db_session.commit()

        # Findings for r1
        db_session.add(
            ReviewFinding(
                review_id=r1.id,
                issue_type="TERM",
                severity="HIGH",
                description="用語不統一",
                status="APPROVED",
            )
        )
        db_session.add(
            ReviewFinding(
                review_id=r1.id,
                issue_type="GRAMMAR",
                severity="MEDIUM",
                description="曖昧表現",
                status="PENDING",
            )
        )
        db_session.commit()

        # Master data
        db_session.add(Term(term="従業員", definition="定義", category="人事"))
        db_session.add(
            CheckItem(
                name="用語チェック",
                category="TERM",
                description="desc",
                severity="HIGH",
            )
        )
        db_session.add(
            WritingRule(name="敬体統一", rule_type="STYLE", correct_form="である調")
        )
        db_session.commit()

        response = client.get("/api/v1/dashboard/stats")
        data = response.json()

        assert data["document_count"] == 2
        assert data["review_count"] == 2
        assert data["term_count"] == 1
        assert data["check_item_count"] == 1
        assert data["writing_rule_count"] == 1
        assert data["finding_total"] == 2
        assert data["finding_by_severity"]["high"] == 1
        assert data["finding_by_severity"]["medium"] == 1
        assert data["finding_by_status"]["pending"] == 1
        assert data["finding_by_status"]["approved"] == 1
        assert data["review_by_status"]["completed"] == 1
        assert data["review_by_status"]["failed"] == 1
