"""
Tests for document cascade deletion.

ドキュメント削除時の関連レコードのカスケード削除をテスト。
Reviews, ComparisonProjects, DocumentGroupMembers が
正しく削除されることを検証する。
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
from app.models.review import Review, ReviewFinding, ReviewCheckItem
from app.models.check_item import CheckItem
from app.models.comparison import (
    ComparisonProject,
    ComparisonCheckItem,
    ComparisonResult,
)
from app.models.document_group import DocumentGroup, DocumentGroupMember

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


@pytest.fixture
def document_with_reviews(db_session):
    """レビュー・指摘事項付きドキュメントを作成"""
    doc = Document(
        title="テスト文書.pdf",
        file_path="/tmp/nonexistent_test.pdf",
        ocr_status="completed",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    review = Review(document_id=doc.id, status="completed")
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    finding = ReviewFinding(
        review_id=review.id,
        issue_type="TERMINOLOGY",
        severity="HIGH",
        description="テスト指摘",
        location="第1条",
        status="PENDING",
    )
    db_session.add(finding)

    # ReviewCheckItem needs a valid check_item_id (composite PK)
    ci = CheckItem(
        name="テストチェック",
        category="TERMINOLOGY",
        description="テスト用",
        severity="HIGH",
        is_active=True,
    )
    db_session.add(ci)
    db_session.commit()
    db_session.refresh(ci)

    review_check = ReviewCheckItem(
        review_id=review.id,
        check_item_id=ci.id,
        status="completed",
    )
    db_session.add(review_check)
    db_session.commit()

    return {
        "document": doc,
        "review": review,
        "finding": finding,
        "review_check": review_check,
    }


@pytest.fixture
def document_with_comparison(db_session):
    """比較プロジェクト付きドキュメントを作成"""
    parent_doc = Document(
        title="親会社規程.pdf",
        file_path="/tmp/parent_test.pdf",
        ocr_status="completed",
        extracted_text="親会社の就業規則",
    )
    sub_doc = Document(
        title="子会社規程.pdf",
        file_path="/tmp/sub_test.pdf",
        ocr_status="completed",
        extracted_text="子会社の就業規則",
    )
    db_session.add_all([parent_doc, sub_doc])
    db_session.commit()
    db_session.refresh(parent_doc)
    db_session.refresh(sub_doc)

    project = ComparisonProject(
        name="テスト比較",
        parent_document_id=parent_doc.id,
        subsidiary_document_id=sub_doc.id,
        status="completed",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    check_item = ComparisonCheckItem(
        project_id=project.id,
        item_text="定年年齢の規定",
        category="労務",
    )
    db_session.add(check_item)
    db_session.commit()
    db_session.refresh(check_item)

    result = ComparisonResult(
        project_id=project.id,
        check_item_id=check_item.id,
        status="DIFFERENT",
        parent_text="定年は65歳",
        subsidiary_text="定年は60歳",
        explanation="定年年齢が異なる",
    )
    db_session.add(result)
    db_session.commit()

    return {
        "parent_doc": parent_doc,
        "sub_doc": sub_doc,
        "project": project,
        "check_item": check_item,
        "result": result,
    }


@pytest.fixture
def document_with_group(db_session):
    """グループ所属ドキュメントを作成"""
    doc = Document(
        title="グループ文書.pdf",
        file_path="/tmp/group_test.pdf",
        ocr_status="completed",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    group = DocumentGroup(name="テストグループ", description="テスト用")
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    member = DocumentGroupMember(
        group_id=group.id,
        document_id=doc.id,
    )
    db_session.add(member)
    db_session.commit()

    return {"document": doc, "group": group, "member": member}


class TestDocumentCascadeDelete:
    """ドキュメント削除時のカスケード削除テスト"""

    def test_delete_document_with_reviews(
        self, client: TestClient, db_session, document_with_reviews
    ):
        """レビュー付きドキュメント削除でレビュー・指摘も削除される"""
        doc_id = document_with_reviews["document"].id
        review_id = document_with_reviews["review"].id

        response = client.delete(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 204

        # ドキュメントが削除されている
        assert db_session.query(Document).filter(Document.id == doc_id).first() is None

        # レビューが削除されている
        assert (
            db_session.query(Review).filter(Review.id == review_id).first() is None
        )

        # 指摘事項が削除されている
        assert (
            db_session.query(ReviewFinding)
            .filter(ReviewFinding.review_id == review_id)
            .count()
            == 0
        )

        # レビューチェック項目が削除されている
        assert (
            db_session.query(ReviewCheckItem)
            .filter(ReviewCheckItem.review_id == review_id)
            .count()
            == 0
        )

    def test_delete_parent_document_removes_comparison(
        self, client: TestClient, db_session, document_with_comparison
    ):
        """親文書削除で比較プロジェクトも削除される"""
        parent_id = document_with_comparison["parent_doc"].id
        project_id = document_with_comparison["project"].id

        response = client.delete(f"/api/v1/documents/{parent_id}")
        assert response.status_code == 204

        # 比較プロジェクトが削除されている
        assert (
            db_session.query(ComparisonProject)
            .filter(ComparisonProject.id == project_id)
            .first()
            is None
        )

        # 比較チェック項目が削除されている
        assert (
            db_session.query(ComparisonCheckItem)
            .filter(ComparisonCheckItem.project_id == project_id)
            .count()
            == 0
        )

        # 比較結果が削除されている
        assert (
            db_session.query(ComparisonResult)
            .filter(ComparisonResult.project_id == project_id)
            .count()
            == 0
        )

        # 子会社文書は残っている
        sub_id = document_with_comparison["sub_doc"].id
        assert (
            db_session.query(Document).filter(Document.id == sub_id).first()
            is not None
        )

    def test_delete_subsidiary_document_removes_comparison(
        self, client: TestClient, db_session, document_with_comparison
    ):
        """子文書削除で比較プロジェクトも削除される"""
        sub_id = document_with_comparison["sub_doc"].id
        project_id = document_with_comparison["project"].id

        response = client.delete(f"/api/v1/documents/{sub_id}")
        assert response.status_code == 204

        assert (
            db_session.query(ComparisonProject)
            .filter(ComparisonProject.id == project_id)
            .first()
            is None
        )

    def test_delete_document_removes_group_membership(
        self, client: TestClient, db_session, document_with_group
    ):
        """グループ所属文書削除でメンバーシップが削除される"""
        doc_id = document_with_group["document"].id
        group_id = document_with_group["group"].id

        response = client.delete(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 204

        # メンバーシップが削除されている
        assert (
            db_session.query(DocumentGroupMember)
            .filter(DocumentGroupMember.document_id == doc_id)
            .count()
            == 0
        )

        # グループ自体は残っている
        assert (
            db_session.query(DocumentGroup)
            .filter(DocumentGroup.id == group_id)
            .first()
            is not None
        )

    def test_delete_nonexistent_document(self, client: TestClient):
        """存在しないドキュメント削除で404"""
        response = client.delete("/api/v1/documents/99999")
        assert response.status_code == 404

    def test_delete_document_without_relations(self, client: TestClient, db_session):
        """関連レコードなしのドキュメント削除が正常に動作"""
        doc = Document(
            title="独立文書.pdf",
            file_path="/tmp/standalone_test.pdf",
            ocr_status="completed",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = client.delete(f"/api/v1/documents/{doc.id}")
        assert response.status_code == 204

        assert (
            db_session.query(Document).filter(Document.id == doc.id).first() is None
        )
