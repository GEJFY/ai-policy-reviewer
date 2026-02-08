"""
Pytest configuration and fixtures.

テスト用のセットアップとフィクスチャを提供する。
各テストはインメモリSQLiteデータベースを使用し、
テスト間で独立した状態を維持する。
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.models.base import Base


# テスト用インメモリSQLiteデータベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """テスト用DBセッションを生成する。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    各テスト用の独立したDBセッションを提供する。

    テスト開始時にテーブルを作成し、
    テスト終了時にセッションをロールバックしてクリーンアップ。
    """
    # テーブル作成
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # テスト後にテーブルをドロップしてクリーンな状態に
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    テスト用のFastAPI TestClientを提供する。

    DBセッションをオーバーライドし、
    テスト用のインメモリDBを使用する。
    """
    app.dependency_overrides[get_db] = override_get_db

    # テーブル作成（clientフィクスチャ用）
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """asyncioイベントループを提供する。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# テスト用サンプルデータ
@pytest.fixture
def sample_term_data() -> dict:
    """サンプル用語データ。"""
    return {
        "term": "従業員",
        "definition": "当社と雇用契約を締結している者をいう",
        "category": "人事",
        "aliases": ["社員", "スタッフ"],
        "usage_note": "規程全体で統一して使用すること"
    }


@pytest.fixture
def sample_check_item_data() -> dict:
    """サンプルチェック項目データ。"""
    return {
        "name": "用語の統一性",
        "category": "TERMINOLOGY",
        "description": "同一概念に対して統一された用語が使用されているか確認",
        "prompt_template": "文書内で用語の統一性を確認してください。",
        "severity": "HIGH",
        "is_active": True
    }


@pytest.fixture
def sample_writing_rule_data() -> dict:
    """サンプル記載ルールデータ。"""
    return {
        "name": "能動態の使用",
        "rule_type": "STYLE",
        "correct_form": "部長が承認する",
        "example_bad": "部長により承認される",
        "example_good": "部長が承認する",
        "is_active": True
    }
