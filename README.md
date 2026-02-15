# 規程レビューツール (Policy Review Tool)

AIを活用した社内規程文書のレビューシステムです。マルチクラウドLLM対応で、Azure、AWS、GCPの最新AIモデルを使用して、規程文書の品質チェックを自動化します。

## 主な機能

- **PDF文書のOCR処理**: マルチOCR対応（Azure Document Intelligence / Tesseract / AWS Tesseract）
- **マルチクラウドAIレビュー**: 7カテゴリの品質チェック
  - 用語統一チェック
  - 曖昧表現チェック
  - 責任主体明確化チェック
  - 法令参照チェック
  - 他規程参照チェック
  - セキュリティ要件チェック
  - 実務適合性チェック
- **マルチクラウドLLM対応**:
  - **Azure AI Foundry**: GPT-5.2, GPT-5.2-codex, Claude Opus 4.6, Claude Sonnet 4.5
  - **AWS Bedrock**: Claude Opus 4.6, Claude Sonnet 4.5, Nova Premier/Pro/Micro, Llama 4 Maverick
  - **GCP Vertex AI**: Gemini 3 Pro/Flash Preview, Claude Opus 4.6, Claude Sonnet 4.5
  - **Ollama（ローカル）**: qwen2.5:3b, gemma-2-2b-jpn-it（無料、オフライン対応）
- **マスタデータ管理**: 用語辞書、チェック項目、記載ルールの管理
- **承認ワークフロー**: 指摘事項の承認/却下/保留の管理（ローディングスピナー・エラー通知付き）
- **ベクトル検索**: 類似用語の検索機能
- **安全性**: ファイルアップロード50MB制限、レビュー10分タイムアウト、レート制限

## システム構成

```
┌─────────────────────┐     ┌─────────────────────┐
│    フロントエンド     │     │     バックエンド      │
│    Next.js 16       │────▶│    FastAPI          │
│    Port: 3033       │     │    Port: 8004       │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
           │   SQLite     │   │ Multi-Cloud  │   │  Multi-OCR   │
           │   Database   │   │     LLM      │   │   Provider   │
           └──────────────┘   └──────────────┘   └──────────────┘
                                    │                    │
                    ┌───────────────┼──────┐    ┌───────┼───────┐
                    ▼               ▼      ▼    ▼       ▼       ▼
              ┌──────────┐   ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
              │  Azure   │   │  AWS   │ │  GCP   │ │Azure DI│ │Tesseract │
              │ Foundry  │   │Bedrock │ │ Vertex │ │  OCR   │ │ Local/AWS│
              └──────────┘   └────────┘ └────────┘ └────────┘ └──────────┘
                    ▲
                    │ (またはローカル)
              ┌──────────┐
              │  Ollama  │
              └──────────┘
```

## 対応LLMモデル

| プロバイダー | モデル | ティア | 説明 |
|-------------|--------|--------|------|
| **Azure AI Foundry** | GPT-5.2 | precision | 最新のGPT-5シリーズ |
| | GPT-5.2-codex | precision | コード特化モデル |
| | claude-opus-4-6 | precision | Anthropic最高性能 |
| | GPT-5-mini | balanced | バランス型 |
| | claude-sonnet-4-5 | balanced | 高速・高品質 |
| | GPT-5-nano | cost_effective | 軽量高速モデル |
| | claude-haiku-4-5 | cost_effective | 最速レスポンス |
| **AWS Bedrock** | claude-opus-4-6 | precision | 最高性能 |
| | amazon.nova-premier | precision | Amazon最高性能 |
| | claude-sonnet-4-5 | balanced | 高速・高品質 |
| | amazon.nova-pro | balanced | Amazonバランス型 |
| | meta.llama4-maverick | balanced | Meta Llama 4 |
| | claude-haiku-4-5 | cost_effective | 最速レスポンス |
| | amazon.nova-micro | cost_effective | 最軽量 |
| **GCP Vertex AI** | gemini-3-pro-preview | precision | Google最高性能 |
| | claude-opus-4-6 | precision | 最高性能 |
| | gemini-3-flash-preview | balanced | 高速Gemini |
| | claude-sonnet-4-5 | balanced | 高速・高品質 |
| | claude-haiku-4-5 | cost_effective | 最速レスポンス |
| **Ollama（ローカル）** | qwen2.5:3b | balanced | 多言語対応（無料） |
| | gemma-2-2b-jpn-it | cost_effective | 日本語最適化（無料） |

## 必要条件

- Python 3.11以上
- Node.js 20以上
- 以下のいずれかのLLMプロバイダー:
  - Azure AI Foundry
  - AWS Bedrock
  - GCP Vertex AI
  - Ollama（ローカル、無料）
- OCRプロバイダー（オプション）: Azure Document Intelligence / Tesseract / AWS Tesseract

## クイックスタート（Windows推奨）

### 簡単起動（バッチファイル使用）

1. `.env` ファイルにクラウド認証情報を設定
2. `setup.bat` をダブルクリック（初回のみ）
3. `start.bat` をダブルクリック

| バッチファイル | 説明 |
|--------------|------|
| `setup.bat` | 初期セットアップ（依存関係インストール、DB初期化、シードデータ投入） |
| `start.bat` | 全サービス起動（推奨、ブラウザ自動起動） |
| `start_all.bat` | 全サービス起動（詳細メッセージ付き） |
| `start_backend.bat` | バックエンドのみ起動 |
| `start_frontend.bat` | フロントエンドのみ起動 |
| `stop_all.bat` | 全サービス停止 |
| `demo_setup.bat` | デモ環境一括セットアップ（データ投入+PDF生成+起動） |
| `seed_demo.bat` | デモデータ投入のみ |
| `start_demo.bat` | デモデータ投入後にサービス起動 |
| `run_tests.bat` | テスト実行 |

> **注意**: バッチファイルはジャンクション `C:\dev-pr` 経由で動作します。
> 日本語パス環境では `--webpack` フラグが必須（Next.js 16 Turbopackの制約）。

---

## 手動セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/GEJFY/ai-policy-reviewer.git
cd ai-policy-reviewer
```

### 2. 環境変数の設定

`.env`ファイルをプロジェクトルートに作成（`.env.example` をコピー）:

```bash
cp .env.example .env
# .envを編集してクラウド認証情報を設定
```

主要な環境変数:

```env
# LLMプロバイダー選択
LLM_PROVIDER=azure  # azure, aws_bedrock, gcp_vertex, local

# Azure AI Foundry
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
AZURE_OPENAI_USE_V1_API=true
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Embeddingプロバイダー
EMBEDDING_PROVIDER=azure_openai  # azure_openai, aws_bedrock, gcp_vertex, local

# OCR設定（オプション）
OCR_PROVIDER=azure_doc_intel  # azure_doc_intel, tesseract, aws_tesseract
AZURE_DOC_INTEL_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOC_INTEL_KEY=<your-api-key>

# Database
DATABASE_URL=sqlite:///./data/policy_review.db

# App
SECRET_KEY=<your-secret-key>
DEBUG=true
```

> 全設定項目の詳細は `.env.example` を参照してください。

### 3. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成（OneDrive外を推奨）
python -m venv C:\Users\%USERNAME%\.venvs\ai-policy-reviewer
C:\Users\%USERNAME%\.venvs\ai-policy-reviewer\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# データベース初期化と初期データ投入
python -c "from app.db.init_db import create_tables; create_tables()"
python -m app.db.seed_data

# サーバー起動（DISABLE_SQLALCHEMY_CEXT_RUNTIME=1 が必要）
set DISABLE_SQLALCHEMY_CEXT_RUNTIME=1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### 4. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数（バックエンドURL）
# frontend/.env.local を作成（デフォルト: http://localhost:8004）
echo NEXT_PUBLIC_API_URL=http://localhost:8004 > .env.local

# 開発サーバー起動（日本語パスでは --webpack が必須）
npx next dev --port 3033 --webpack
```

### 5. アクセス

- フロントエンド: http://localhost:3033
- バックエンドAPI: http://localhost:8004
- APIドキュメント: http://localhost:8004/docs
- ヘルスチェック: http://localhost:8004/health

## プロジェクト構造

```
ai-policy-reviewer/
├── backend/
│   ├── app/
│   │   ├── api/              # APIエンドポイント
│   │   │   ├── documents.py  # 文書管理（50MBサイズ制限付き）
│   │   │   ├── reviews.py    # レビュー管理（10分タイムアウト付き）
│   │   │   ├── terms.py      # 用語辞書
│   │   │   ├── check_items.py # チェック項目
│   │   │   ├── writing_rules.py # 記載ルール
│   │   │   └── health.py     # ヘルスチェック
│   │   ├── auth/             # JWT認証
│   │   ├── core/             # ログ、ミドルウェア、例外、セキュリティ
│   │   │   ├── security/     # レート制限、セキュリティヘッダー
│   │   │   ├── resilience/   # サーキットブレーカー
│   │   │   └── observability/ # メトリクス、監査ログ
│   │   ├── db/               # データベース設定、初期化、シードデータ
│   │   ├── models/           # SQLAlchemyモデル
│   │   ├── prompts/          # AIプロンプトテンプレート
│   │   ├── schemas/          # Pydanticスキーマ
│   │   ├── services/         # ビジネスロジック
│   │   │   ├── llm_service.py      # マルチクラウドLLM統合
│   │   │   ├── review_engine.py    # レビュー実行エンジン
│   │   │   ├── ocr_service.py      # マルチOCR統合
│   │   │   ├── embedding_service.py # マルチEmbedding統合
│   │   │   └── vector_store.py     # ベクトル検索
│   │   ├── config.py         # マルチクラウド設定管理
│   │   └── main.py           # FastAPIエントリポイント
│   ├── tests/                # テストファイル
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   │   └── (dashboard)/      # ダッシュボード、文書、レビュー等
│   ├── components/           # Reactコンポーネント（UI/Layout）
│   ├── lib/                  # APIクライアント（タイムアウト付き）
│   ├── .env.example          # フロントエンド環境変数テンプレート
│   └── package.json
├── infrastructure/           # Terraform（Azure/AWS/GCP）、Helm Charts
├── docs/                     # ドキュメント
├── samples/                  # サンプル規程文書
├── .github/workflows/ci.yml  # CI/CD（Lint, Test, Build, Security Scan）
├── .env.example              # 環境変数テンプレート
└── *.bat                     # Windows起動バッチファイル
```

## API概要

### マスタデータ管理

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/terms` | GET/POST | 用語辞書の一覧/登録 |
| `/api/v1/terms/{id}` | GET/PUT/DELETE | 用語の詳細/更新/削除 |
| `/api/v1/terms/search` | POST | ベクトル検索 |
| `/api/v1/check-items` | GET/POST | チェック項目の一覧/登録 |
| `/api/v1/writing-rules` | GET/POST | 記載ルールの一覧/登録 |

### 文書・レビュー管理

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/documents` | GET/POST | 文書の一覧/アップロード |
| `/api/v1/documents/upload` | POST | PDFアップロード（最大50MB） |
| `/api/v1/documents/{id}/ocr` | POST | OCR再処理 |
| `/api/v1/reviews` | GET/POST | レビューの一覧/実行 |
| `/api/v1/reviews/{id}` | GET | レビュー詳細 |
| `/api/v1/reviews/{id}/findings` | GET | 指摘事項一覧 |

### 承認ワークフロー

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/findings/{id}/approve` | PUT | 承認 |
| `/api/v1/findings/{id}/reject` | PUT | 却下 |
| `/api/v1/findings/{id}/defer` | PUT | 保留 |
| `/api/v1/reviews/{id}/findings/bulk-update` | POST | 一括更新 |

### システム

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/health` | GET | 基本ヘルスチェック |
| `/health/detailed` | GET | 詳細ヘルスチェック（LLM/OCR/DB状態） |
| `/metrics` | GET | Prometheusメトリクス |

## チェックカテゴリ

| カテゴリ | 説明 |
|---------|------|
| TERMINOLOGY | 用語の統一性、表記ゆれ |
| GRAMMAR | 曖昧表現、文法 |
| STRUCTURE | 責任主体、条文構造 |
| COMPLIANCE | 法令参照の正確性 |
| CONSISTENCY | 他規程との整合性 |
| SECURITY | セキュリティ要件 |
| OPERATIONAL | 実務適合性 |

## CI/CD

GitHub Actionsで自動実行:

| ジョブ | 内容 |
|-------|------|
| Lint & Format | Ruff + Black + MyPy |
| Security Scan | Bandit + Safety + pip-audit |
| Backend Tests | pytest（カバレッジ55%以上） |
| Frontend Build | TypeScript型チェック + Next.js ビルド |
| Docker Build | コンテナイメージビルド（PR時） |
| Container Security Scan | Trivy脆弱性スキャン（PR時） |
| Terraform Validate | dev/aws-dev/gcp-dev環境バリデーション |
| Helm Lint | Helmチャート検証 |

## トラブルシューティング

### バックエンドが起動しない

1. `DISABLE_SQLALCHEMY_CEXT_RUNTIME=1` 環境変数を設定しているか確認
2. `.env`ファイルの設定を確認
3. ポート8004が空いているか確認: `netstat -ano | findstr 8004`

### フロントエンドが起動しない

1. 日本語パスの場合は `--webpack` フラグが必須
2. `NEXT_PUBLIC_API_URL` が正しく設定されているか確認
3. ポート3033が空いているか確認

### LLMプロバイダーの接続エラー

1. `.env`ファイルの設定を確認
2. 選択したプロバイダーの認証情報が正しいか確認
3. `LLM_PROVIDER`環境変数が正しく設定されているか確認

### OCRが動作しない

1. Azure Document Intelligenceのキーとエンドポイントを確認
2. PDFファイルが破損していないか確認
3. ファイルサイズが制限内か確認（最大50MB）

### レビューが完了しない

1. レビューには最大10分のタイムアウトが設定されています
2. LLMプロバイダーの接続状態を確認: `curl http://localhost:8004/health/detailed`
3. レビュー詳細ページでステータスを確認（3〜10秒間隔で自動更新）

### データベースエラー

```bash
# データディレクトリを作成
mkdir data

# データベースを再初期化
python -c "from app.db.init_db import create_tables; create_tables()"
```

## テストの実行

```bash
cd backend

# 全テスト実行
pytest tests/ -v

# LLMプロバイダーテスト
pytest tests/test_llm_providers.py -v

# 統合テスト
pytest tests/test_integration.py -v

# カバレッジ付き
pytest tests/ --cov=app --cov-report=term-missing
```

## ライセンス

Proprietary License - Copyright (c) 2024-2026 Go Yoshizawa. All Rights Reserved.

本ソフトウェアは Go Yoshizawa の書面による明示的な許可を得た者のみが使用できます。
詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 開発者向け情報

### ログの確認

ログは`logs/`ディレクトリに出力されます：
- `app.log`: 全ログ（JSON形式）
- `error.log`: エラーログのみ
- `audit.log`: 監査ログ

### LLMプロバイダーの切り替え

環境変数で切り替え:
```env
LLM_PROVIDER=aws_bedrock  # azure, aws_bedrock, gcp_vertex, local
LLM_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

ティアによる自動選択:
```env
LLM_TIER=balanced  # precision, balanced, cost_effective
```

### 関連ドキュメント

- [セットアップガイド](docs/SETUP_GUIDE.md) - 詳細なセットアップ手順
- [ユーザーマニュアル](docs/USER_MANUAL.md) - 画面操作の詳細
- [デモガイド](docs/DEMO_GUIDE.md) - デモ操作の手順
- [機能仕様書](docs/functional-specification.md) - プロンプト設計・API設計
- [クイックスタート](docs/getting-started/quick-start.md) - 5分で始める
- [運用手順書](docs/operations/runbook.md) - 監視・インシデント対応
