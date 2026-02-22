"""Tests for Document Groups API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.models.base import Base
from app.models.document import Document
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
def sample_docs(db_session):
    docs = []
    for i in range(3):
        doc = Document(
            title=f"規程{i+1}.pdf",
            file_path=f"/tmp/doc{i+1}.pdf",
            ocr_status="completed",
            extracted_text=f"テスト文書{i+1}の内容です。",
        )
        db_session.add(doc)
    db_session.commit()
    return db_session.query(Document).all()


class TestListGroups:
    def test_list_empty(self, client: TestClient):
        response = client.get("/api/v1/document-groups")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_groups(self, client: TestClient):
        # Create a group
        client.post(
            "/api/v1/document-groups",
            json={"name": "テストグループ", "document_ids": []},
        )
        response = client.get("/api/v1/document-groups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "テストグループ"


class TestCreateGroup:
    def test_create_group_basic(self, client: TestClient):
        response = client.post(
            "/api/v1/document-groups",
            json={"name": "テストグループ", "description": "テスト用"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "テストグループ"
        assert data["description"] == "テスト用"
        assert data["member_count"] == 0

    def test_create_group_with_members(self, client: TestClient, sample_docs):
        doc_ids = [d.id for d in sample_docs[:2]]
        response = client.post(
            "/api/v1/document-groups",
            json={"name": "2文書グループ", "document_ids": doc_ids},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["member_count"] == 2
        assert len(data["members"]) == 2

    def test_create_group_empty_name(self, client: TestClient):
        response = client.post(
            "/api/v1/document-groups",
            json={"name": "", "document_ids": []},
        )
        assert response.status_code == 422


class TestGetGroup:
    def test_get_group(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={
                "name": "テストグループ",
                "document_ids": [sample_docs[0].id],
            },
        )
        group_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/document-groups/{group_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "テストグループ"
        assert len(data["members"]) == 1

    def test_get_group_not_found(self, client: TestClient):
        response = client.get("/api/v1/document-groups/9999")
        assert response.status_code == 404


class TestUpdateGroup:
    def test_update_group(self, client: TestClient):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "旧名前"},
        )
        group_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/document-groups/{group_id}",
            json={"name": "新名前"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "新名前"

    def test_update_group_not_found(self, client: TestClient):
        response = client.put(
            "/api/v1/document-groups/9999",
            json={"name": "テスト"},
        )
        assert response.status_code == 404


class TestDeleteGroup:
    def test_delete_group(self, client: TestClient):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "削除テスト"},
        )
        group_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/document-groups/{group_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/document-groups/{group_id}")
        assert response.status_code == 404

    def test_delete_group_not_found(self, client: TestClient):
        response = client.delete("/api/v1/document-groups/9999")
        assert response.status_code == 404


class TestMembers:
    def test_add_member(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "メンバーテスト"},
        )
        group_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/document-groups/{group_id}/members?document_id={sample_docs[0].id}"
        )
        assert response.status_code == 201

        # Verify
        detail = client.get(f"/api/v1/document-groups/{group_id}").json()
        assert detail["member_count"] == 1

    def test_add_duplicate_member(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "重複テスト", "document_ids": [sample_docs[0].id]},
        )
        group_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/document-groups/{group_id}/members?document_id={sample_docs[0].id}"
        )
        assert response.status_code == 400

    def test_remove_member(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "削除テスト", "document_ids": [sample_docs[0].id]},
        )
        group_id = create_resp.json()["id"]

        response = client.delete(
            f"/api/v1/document-groups/{group_id}/members/{sample_docs[0].id}"
        )
        assert response.status_code == 204

        detail = client.get(f"/api/v1/document-groups/{group_id}").json()
        assert detail["member_count"] == 0


class TestConsistencyCheck:
    def test_consistency_check_too_few_members(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/document-groups",
            json={"name": "少数テスト", "document_ids": [sample_docs[0].id]},
        )
        group_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/document-groups/{group_id}/consistency-check"
        )
        assert response.status_code == 400

    def test_consistency_check_group_not_found(self, client: TestClient):
        response = client.post(
            "/api/v1/document-groups/9999/consistency-check"
        )
        assert response.status_code == 404
