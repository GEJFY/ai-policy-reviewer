"""
Alembic migration tests.

マイグレーションファイルの整合性テスト。
"""

import importlib
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


class TestMigrations:
    """マイグレーション テストクラス。"""

    def _get_alembic_config(self) -> Config:
        """Alembic設定オブジェクトを取得。"""
        backend_dir = Path(__file__).parent.parent
        config = Config(str(backend_dir / "alembic.ini"))
        config.set_main_option("script_location", str(backend_dir / "alembic"))
        return config

    def test_migration_chain_is_linear(self):
        """マイグレーションチェーンが線形であること（ブランチなし）。"""
        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)

        revisions = list(script.walk_revisions())
        assert len(revisions) >= 2, "少なくとも2つのマイグレーションが必要"

        # headが1つであることを確認（ブランチなし）
        heads = script.get_heads()
        assert len(heads) == 1, f"ブランチが存在します: {heads}"

    def test_migration_001_is_base(self):
        """初期マイグレーション(001)がベースであること。"""
        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)

        base = script.get_revision("001")
        assert base is not None
        assert base.down_revision is None

    def test_migration_002_depends_on_001(self):
        """マイグレーション002が001に依存すること。"""
        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)

        rev = script.get_revision("002")
        assert rev is not None
        assert rev.down_revision == "001"

    def test_migration_head_is_latest(self):
        """現在のheadが最新であること。"""
        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)

        heads = script.get_heads()
        assert len(heads) == 1
        # Headは数値で最大のリビジョン
        head = heads[0]
        assert int(head) >= 3

    def test_migration_002_has_upgrade_and_downgrade(self):
        """マイグレーション002にupgrade/downgrade関数があること。"""
        migration_path = (
            Path(__file__).parent.parent
            / "alembic"
            / "versions"
            / "002_add_missing_columns.py"
        )
        spec = importlib.util.spec_from_file_location(
            "migration_002", str(migration_path)
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        assert hasattr(migration, "upgrade")
        assert hasattr(migration, "downgrade")
        assert callable(migration.upgrade)
        assert callable(migration.downgrade)

    def test_all_models_are_imported_in_env(self):
        """env.pyで全モデルがimportされていること。"""
        env_path = Path(__file__).parent.parent / "alembic" / "env.py"
        content = env_path.read_text(encoding="utf-8")

        required_models = [
            "Document",
            "DocumentChunk",
            "Review",
            "ReviewCheckItem",
            "ReviewFinding",
            "CheckItem",
            "Term",
            "WritingRule",
        ]

        for model in required_models:
            assert model in content, f"{model} がenv.pyでimportされていません"
