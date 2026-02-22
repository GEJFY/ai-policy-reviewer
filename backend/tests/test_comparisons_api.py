"""Tests for Comparisons API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.models.base import Base
from app.models.document import Document

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
    for i in range(2):
        doc = Document(
            title=f"規程{i+1}.pdf",
            file_path=f"/tmp/doc{i+1}.pdf",
            ocr_status="completed",
            extracted_text=f"テスト文書{i+1}の内容です。",
        )
        db_session.add(doc)
        docs.append(doc)
    db_session.commit()
    return db_session.query(Document).all()


class TestListProjects:
    def test_list_empty(self, client: TestClient):
        response = client.get("/api/v1/comparisons")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects(self, client: TestClient, sample_docs):
        client.post(
            "/api/v1/comparisons",
            json={
                "name": "テスト比較",
                "parent_document_id": sample_docs[0].id,
            },
        )
        response = client.get("/api/v1/comparisons")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "テスト比較"


class TestCreateProject:
    def test_create_project(self, client: TestClient, sample_docs):
        response = client.post(
            "/api/v1/comparisons",
            json={
                "name": "テスト比較",
                "description": "テスト用プロジェクト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "テスト比較"
        assert data["description"] == "テスト用プロジェクト"
        assert data["parent_document_id"] == sample_docs[0].id
        assert data["status"] == "created"

    def test_create_project_invalid_parent(self, client: TestClient):
        response = client.post(
            "/api/v1/comparisons",
            json={"name": "テスト", "parent_document_id": 9999},
        )
        assert response.status_code == 404

    def test_create_project_empty_name(self, client: TestClient, sample_docs):
        response = client.post(
            "/api/v1/comparisons",
            json={"name": "", "parent_document_id": sample_docs[0].id},
        )
        assert response.status_code == 422


class TestGetProject:
    def test_get_project(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "テスト比較",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/comparisons/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "テスト比較"
        assert "check_items" in data
        assert "results" in data

    def test_get_project_not_found(self, client: TestClient):
        response = client.get("/api/v1/comparisons/9999")
        assert response.status_code == 404


class TestDeleteProject:
    def test_delete_project(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "削除テスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/comparisons/{project_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/comparisons/{project_id}")
        assert response.status_code == 404

    def test_delete_not_found(self, client: TestClient):
        response = client.delete("/api/v1/comparisons/9999")
        assert response.status_code == 404


class TestSetSubsidiary:
    def test_set_subsidiary(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "子会社設定テスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/comparisons/{project_id}/subsidiary",
            json={"subsidiary_document_id": sample_docs[1].id},
        )
        assert response.status_code == 200

        detail = client.get(f"/api/v1/comparisons/{project_id}").json()
        assert detail["subsidiary_document_id"] == sample_docs[1].id

    def test_set_subsidiary_not_found_project(self, client: TestClient, sample_docs):
        response = client.put(
            "/api/v1/comparisons/9999/subsidiary",
            json={"subsidiary_document_id": sample_docs[0].id},
        )
        assert response.status_code == 404

    def test_set_subsidiary_not_found_doc(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "テスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/comparisons/{project_id}/subsidiary",
            json={"subsidiary_document_id": 9999},
        )
        assert response.status_code == 404


class TestUpdateChecklist:
    def test_update_checklist(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "チェックリストテスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/comparisons/{project_id}/checklist",
            json={
                "items": [
                    {"item_text": "テスト項目1", "category": "組織体制"},
                    {"item_text": "テスト項目2", "category": "情報管理"},
                ]
            },
        )
        assert response.status_code == 200

        detail = client.get(f"/api/v1/comparisons/{project_id}").json()
        assert len(detail["check_items"]) == 2
        assert detail["check_items"][0]["item_text"] == "テスト項目1"


class TestCompare:
    def test_compare_no_subsidiary(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "比較テスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/comparisons/{project_id}/compare")
        assert response.status_code == 400

    def test_compare_no_checklist(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "比較テスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        # Set subsidiary but no checklist
        client.put(
            f"/api/v1/comparisons/{project_id}/subsidiary",
            json={"subsidiary_document_id": sample_docs[1].id},
        )

        response = client.post(f"/api/v1/comparisons/{project_id}/compare")
        assert response.status_code == 400

    def test_compare_project_not_found(self, client: TestClient):
        response = client.post("/api/v1/comparisons/9999/compare")
        assert response.status_code == 404


class TestExport:
    def test_export_not_found(self, client: TestClient):
        response = client.get("/api/v1/comparisons/9999/export")
        assert response.status_code == 404

    def test_export_empty_results(self, client: TestClient, sample_docs):
        create_resp = client.post(
            "/api/v1/comparisons",
            json={
                "name": "エクスポートテスト",
                "parent_document_id": sample_docs[0].id,
            },
        )
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/comparisons/{project_id}/export")
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]
