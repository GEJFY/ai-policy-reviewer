"""
Tests for CSV/Excel import service and API endpoints.

CSV/Excelインポートサービスおよび各APIエンドポイントのテスト。
"""

import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.models.base import Base
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule
from app.services.csv_import_service import (
    read_import_file,
    validate_required_columns,
    generate_csv_template,
    TERM_HEADERS,
    TERM_SAMPLE,
    CHECK_ITEM_HEADERS,
    CHECK_ITEM_SAMPLE,
    WRITING_RULE_HEADERS,
    WRITING_RULE_SAMPLE,
)

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


def _make_csv(headers: list[str], rows: list[list[str]], encoding: str = "utf-8") -> bytes:
    """CSV bytes を生成するヘルパー"""
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    text = "\n".join(lines)
    if encoding == "utf-8-sig":
        return ("\ufeff" + text).encode("utf-8")
    return text.encode(encoding)


def _make_excel(headers: list[str], rows: list[list[str]]) -> bytes:
    """Excel bytes を生成するヘルパー"""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


class TestReadImportFile:
    """read_import_file のユニットテスト"""

    def test_read_csv_utf8(self):
        """UTF-8 CSV を正常に読み取れる"""
        csv_bytes = _make_csv(
            ["term", "definition", "category"],
            [["従業員", "雇用契約を締結した者", "人事"]],
        )
        rows, errors = read_import_file(csv_bytes, "test.csv")
        assert len(errors) == 0
        assert len(rows) == 1
        assert rows[0]["term"] == "従業員"
        assert rows[0]["definition"] == "雇用契約を締結した者"

    def test_read_csv_utf8_bom(self):
        """UTF-8 BOM付きCSV を正常に読み取れる"""
        csv_bytes = _make_csv(
            ["term", "definition", "category"],
            [["社員", "会社に所属する者", "人事"]],
            encoding="utf-8-sig",
        )
        rows, errors = read_import_file(csv_bytes, "test.csv")
        assert len(errors) == 0
        assert len(rows) == 1
        assert rows[0]["term"] == "社員"

    def test_read_csv_shift_jis(self):
        """Shift_JIS CSV を正常に読み取れる"""
        csv_bytes = _make_csv(
            ["term", "definition", "category"],
            [["取締役", "会社法上の役員", "法務"]],
            encoding="shift_jis",
        )
        rows, errors = read_import_file(csv_bytes, "test.csv")
        assert len(errors) == 0
        assert len(rows) == 1
        assert rows[0]["term"] == "取締役"

    def test_read_csv_multiple_rows(self):
        """複数行CSV を正常に読み取れる"""
        csv_bytes = _make_csv(
            ["term", "definition", "category"],
            [
                ["従業員", "雇用契約を締結した者", "人事"],
                ["取締役", "会社法上の役員", "法務"],
                ["監査役", "監査を行う役員", "法務"],
            ],
        )
        rows, errors = read_import_file(csv_bytes, "test.csv")
        assert len(errors) == 0
        assert len(rows) == 3

    def test_read_excel(self):
        """Excel ファイルを正常に読み取れる"""
        excel_bytes = _make_excel(
            ["term", "definition", "category"],
            [["従業員", "雇用契約を締結した者", "人事"]],
        )
        rows, errors = read_import_file(excel_bytes, "test.xlsx")
        assert len(errors) == 0
        assert len(rows) == 1
        assert rows[0]["term"] == "従業員"

    def test_read_excel_multiple_rows(self):
        """複数行Excel を正常に読み取れる"""
        excel_bytes = _make_excel(
            ["term", "definition", "category"],
            [
                ["従業員", "雇用契約を締結した者", "人事"],
                ["取締役", "会社法上の役員", "法務"],
            ],
        )
        rows, errors = read_import_file(excel_bytes, "test.xlsx")
        assert len(errors) == 0
        assert len(rows) == 2

    def test_unsupported_file_type(self):
        """未対応ファイル形式でエラー"""
        rows, errors = read_import_file(b"data", "test.txt")
        assert len(errors) == 1
        assert "Unsupported" in errors[0]
        assert len(rows) == 0

    def test_read_csv_strips_whitespace(self):
        """CSV のヘッダー・値から空白が除去される"""
        csv_text = " term , definition , category \n 従業員 , 雇用契約者 , 人事 \n"
        rows, errors = read_import_file(csv_text.encode("utf-8"), "test.csv")
        assert len(errors) == 0
        assert len(rows) == 1
        assert rows[0]["term"] == "従業員"
        assert rows[0]["definition"] == "雇用契約者"


class TestValidateRequiredColumns:
    """validate_required_columns のユニットテスト"""

    def test_all_columns_present(self):
        """必須列がすべて存在する場合、エラーなし"""
        rows = [{"term": "A", "definition": "B", "category": "C"}]
        errors = validate_required_columns(rows, ["term", "definition", "category"])
        assert len(errors) == 0

    def test_missing_column(self):
        """必須列が欠けている場合、エラーが返る"""
        rows = [{"term": "A", "category": "C"}]
        errors = validate_required_columns(rows, ["term", "definition", "category"])
        assert len(errors) == 1
        assert "definition" in errors[0]

    def test_empty_rows(self):
        """行がない場合、エラーが返る"""
        errors = validate_required_columns([], ["term"])
        assert len(errors) == 1
        assert "データ行がありません" in errors[0]


class TestGenerateCSVTemplate:
    """generate_csv_template のユニットテスト"""

    def test_term_template(self):
        """用語テンプレートが正しく生成される"""
        content = generate_csv_template(TERM_HEADERS, TERM_SAMPLE)
        text = content.decode("utf-8")
        # BOM 付き
        assert text.startswith("\ufeff")
        assert "term" in text
        assert "従業員" in text

    def test_check_item_template(self):
        """チェック項目テンプレートが正しく生成される"""
        content = generate_csv_template(CHECK_ITEM_HEADERS, CHECK_ITEM_SAMPLE)
        text = content.decode("utf-8")
        assert "name" in text
        assert "severity" in text

    def test_writing_rule_template(self):
        """記載ルールテンプレートが正しく生成される"""
        content = generate_csv_template(WRITING_RULE_HEADERS, WRITING_RULE_SAMPLE)
        text = content.decode("utf-8")
        assert "rule_type" in text
        assert "correct_form" in text


class TestTermImportAPI:
    """POST /api/v1/terms/import のテスト"""

    def test_import_terms_csv(self, client: TestClient, db_session):
        """CSV から用語をインポートできる"""
        csv_bytes = _make_csv(
            ["term", "definition", "category", "aliases", "usage_note"],
            [
                ["従業員", "雇用契約を締結した者", "人事", "", ""],
                ["取締役", "会社法上の役員", "法務", "", ""],
            ],
        )
        response = client.post(
            "/api/v1/terms/import",
            files={"file": ("terms.csv", csv_bytes, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 2
        assert len(data["errors"]) == 0

        # DB に保存されていることを確認
        terms = db_session.query(Term).all()
        assert len(terms) == 2

    def test_import_terms_excel(self, client: TestClient, db_session):
        """Excel から用語をインポートできる"""
        excel_bytes = _make_excel(
            ["term", "definition", "category"],
            [["監査役", "監査を行う役員", "法務"]],
        )
        response = client.post(
            "/api/v1/terms/import",
            files={"file": ("terms.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 1

    def test_import_terms_duplicate_skip(self, client: TestClient, db_session):
        """重複用語はスキップされる"""
        # 先に1件登録
        db_session.add(Term(term="従業員", definition="既存の定義", category="人事"))
        db_session.commit()

        csv_bytes = _make_csv(
            ["term", "definition", "category"],
            [
                ["従業員", "重複データ", "人事"],
                ["取締役", "会社法上の役員", "法務"],
            ],
        )
        response = client.post(
            "/api/v1/terms/import",
            files={"file": ("terms.csv", csv_bytes, "text/csv")},
        )
        data = response.json()
        assert data["success"] == 1
        assert len(data["errors"]) == 1
        assert "既に登録" in data["errors"][0]

    def test_import_terms_missing_column(self, client: TestClient):
        """必須列がない場合エラーが返る"""
        csv_bytes = _make_csv(
            ["term", "aliases"],
            [["従業員", ""]],
        )
        response = client.post(
            "/api/v1/terms/import",
            files={"file": ("terms.csv", csv_bytes, "text/csv")},
        )
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) > 0

    def test_download_term_template(self, client: TestClient):
        """用語テンプレートをダウンロードできる"""
        response = client.get("/api/v1/terms/template")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        text = response.content.decode("utf-8")
        assert "term" in text


class TestCheckItemImportAPI:
    """POST /api/v1/check-items/import のテスト"""

    def test_import_check_items_csv(self, client: TestClient, db_session):
        """CSV からチェック項目をインポートできる"""
        csv_bytes = _make_csv(
            ["name", "category", "description", "severity", "prompt_template", "is_active"],
            [
                ["用語チェック", "TERMINOLOGY", "用語の統一性確認", "HIGH", "", "true"],
                ["文法チェック", "GRAMMAR", "文法の正確性確認", "MEDIUM", "", "true"],
            ],
        )
        response = client.post(
            "/api/v1/check-items/import",
            files={"file": ("items.csv", csv_bytes, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 2

        items = db_session.query(CheckItem).all()
        assert len(items) == 2

    def test_download_check_item_template(self, client: TestClient):
        """チェック項目テンプレートをダウンロードできる"""
        response = client.get("/api/v1/check-items/template")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]


class TestWritingRuleImportAPI:
    """POST /api/v1/writing-rules/import のテスト"""

    def test_import_writing_rules_csv(self, client: TestClient, db_session):
        """CSV から記載ルールをインポートできる"""
        csv_bytes = _make_csv(
            ["name", "rule_type", "pattern", "correct_form", "example_bad", "example_good", "is_active"],
            [
                ["敬体統一", "STYLE", "である調", "です・ます調", "遂行する。", "遂行します。", "true"],
            ],
        )
        response = client.post(
            "/api/v1/writing-rules/import",
            files={"file": ("rules.csv", csv_bytes, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 1

        rules = db_session.query(WritingRule).all()
        assert len(rules) == 1

    def test_download_writing_rule_template(self, client: TestClient):
        """記載ルールテンプレートをダウンロードできる"""
        response = client.get("/api/v1/writing-rules/template")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
