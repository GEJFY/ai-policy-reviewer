# 規程レビューツール (Policy Review Tool)

AIを活用した社内規程文書のレビューシステムです。マルチクラウドLLM対応で、Azure、AWS、GCPの最新AIモデルを使用して、規程文書の品質チェックを自動化します。

## 主な機能

- **PDF文書のOCR処理**: Azure Document Intelligenceを使用した高精度なテキスト抽出
- **マルチクラウドAIレビュー**: 7カテゴリの品質チェック
  - 用語統一チェック
  - 曖昧表現チェック
  - 責任主体明確化チェック
  - 法令参照チェック
  - 他規程参照チェック
  - セキュリティ要件チェック
  - 実務適合性チェック
- **マルチクラウドLLM対応**:
  - **Azure Foundry**: GPT-5.2, GPT-5-nano, Claude Sonnet 4, Claude Opus 4
  - **AWS Bedrock**: Claude Sonnet 4.6, Claude Opus 4
  - **GCP Vertex AI**: Gemini 3.0 Flash Preview, Gemini 3.0 Pro Preview
- **マスタデータ管理**: 用語辞書、チェック項目、記載ルールの管理
- **承認ワークフロー**: 指摘事項の承認/却下/保留の管理
- **ベクトル検索**: 類似用語の検索機能

## システム構成

```
┌─────────────────────┐     ┌─────────────────────┐
│    フロントエンド     │     │     バックエンド      │
│    Next.js 16       │────▶│    FastAPI          │
│    Port: 3030       │     │    Port: 8080       │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
           │   SQLite     │   │ Multi-Cloud  │   │  Azure Doc   │
           │   Database   │   │     LLM      │   │ Intelligence │
           └──────────────┘   └──────────────┘   └──────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │  Azure   │   │   AWS    │   │   GCP    │
              │ Foundry  │   │ Bedrock  │   │ Vertex   │
              └──────────┘   └──────────┘   └──────────┘
```

## 対応LLMモデル

| プロバイダー | モデル | 説明 |
|-------------|--------|------|
| **Azure Foundry** | GPT-5.2 | 最新のGPT-5シリーズ |
| | GPT-5-nano | 軽量高速モデル |
| | Claude Sonnet 4 | Anthropic Claude（Azure経由） |
| | Claude Opus 4 | 高性能Claudeモデル |
| **AWS Bedrock** | Claude Sonnet 4.6 | 最新Claude Sonnet |
| | Claude Opus 4 | 高性能Claudeモデル |
| **GCP Vertex AI** | Gemini 3.0 Flash Preview | 高速Geminiモデル |
| | Gemini 3.0 Pro Preview | 高性能Geminiモデル |

## 必要条件

- Python 3.11以上
- Node.js 18以上
- 以下のいずれかのLLMプロバイダー:
  - Azure OpenAI Service / Azure Foundry
  - AWS Bedrock
  - GCP Vertex AI
- Azure Document Intelligence（OCR用、オプション）

## クイックスタート（Windows推奨）

### 簡単起動（バッチファイル使用）

1. `.env` ファイルにクラウド認証情報を設定
2. `setup.bat` をダブルクリック（初回のみ）
3. `start_all.bat` をダブルクリック

| バッチファイル | 説明 |
|--------------|------|
| `setup.bat` | 初期セットアップ（依存関係インストール、DB初期化） |
| `start_all.bat` | 全サービス起動（推奨） |
| `start_backend.bat` | バックエンドのみ起動 |
| `start_frontend.bat` | フロントエンドのみ起動 |
| `stop_all.bat` | 全サービス停止 |

---

## 手動セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd ai-policy-reviewer
```

### 2. 環境変数の設定

`.env`ファイルをプロジェクトルートに作成:

```env
# LLMプロバイダー選択
LLM_PROVIDER=azure  # azure, aws_bedrock, gcp_vertex
LLM_MODEL=gpt-5.2

# Azure Foundry / OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# AWS Bedrock（オプション）
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6

# GCP Vertex AI（オプション）
GCP_PROJECT_ID=<your-project-id>
GCP_LOCATION=us-central1
GCP_CREDENTIALS_PATH=/path/to/service-account.json
GCP_VERTEX_MODEL=gemini-3.0-flash-preview

# Azure Document Intelligence
AZURE_DOC_INTEL_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOC_INTEL_KEY=<your-api-key>

# Database
DATABASE_URL=sqlite:///./data/policy_review.db

# App
SECRET_KEY=<your-secret-key>
DEBUG=true
```

### 3. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install -r requirements.txt

# データベース初期化と初期データ投入
python -c "from app.db.init_db import create_tables; create_tables()"
python -m app.db.seed_data

# サーバー起動
uvicorn app.main:app --reload --port 8080
```

### 4. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev
```

### 5. アクセス

- フロントエンド: http://localhost:3030
- バックエンドAPI: http://localhost:8080
- APIドキュメント: http://localhost:8080/docs

## プロジェクト構造

```
ai-policy-reviewer/
├── backend/
│   ├── app/
│   │   ├── api/           # APIエンドポイント
│   │   ├── core/          # ログ、ミドルウェア、例外
│   │   ├── db/            # データベース設定、初期化
│   │   ├── models/        # SQLAlchemyモデル
│   │   ├── prompts/       # AIプロンプトテンプレート
│   │   ├── schemas/       # Pydanticスキーマ
│   │   ├── services/      # ビジネスロジック
│   │   │   ├── llm_service.py  # マルチクラウドLLM統合
│   │   │   └── review_engine.py
│   │   ├── config.py      # 設定
│   │   └── main.py        # FastAPIエントリポイント
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router
│   ├── components/        # Reactコンポーネント
│   ├── lib/               # ユーティリティ、API
│   └── package.json
├── data/                  # SQLiteデータベース
├── logs/                  # アプリケーションログ
├── tests/                 # テストファイル
└── .env                   # 環境変数
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
| `/api/v1/documents/upload` | POST | PDFアップロード |
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

## トラブルシューティング

### LLMプロバイダーの接続エラー

1. `.env`ファイルの設定を確認
2. 選択したプロバイダーの認証情報が正しいか確認
3. `LLM_PROVIDER`環境変数が正しく設定されているか確認

### Azure OpenAIの接続エラー

1. Azure PortalでAPIキーの有効性を確認
2. デプロイメント名が正しいか確認

### AWS Bedrockの接続エラー

1. IAMポリシーでBedrock権限があるか確認
2. リージョンが正しいか確認
3. モデルアクセスが有効化されているか確認

### GCP Vertex AIの接続エラー

1. サービスアカウントの権限を確認
2. プロジェクトIDが正しいか確認
3. Vertex AI APIが有効化されているか確認

### OCRが動作しない

1. Azure Document Intelligenceのキーとエンドポイントを確認
2. PDFファイルが破損していないか確認
3. ファイルサイズが制限内か確認（最大50MB）

### データベースエラー

```bash
# データディレクトリを作成
mkdir -p data

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
```

## ライセンス

Proprietary License - Copyright (c) 2024-2026 Go Yoshizawa. All Rights Reserved.

本ソフトウェアは Go Yoshizawa の書面による明示的な許可を得た者のみが使用できます。
詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 開発者向け情報

### ログの確認

ログは`logs/`ディレクトリに出力されます：
- `app.log`: 全ログ
- `error.log`: エラーログのみ

### LLMプロバイダーの切り替え

環境変数で切り替え:
```env
LLM_PROVIDER=aws_bedrock  # azure, aws_bedrock, gcp_vertex
LLM_MODEL=anthropic.claude-sonnet-4-6
```

または、APIで動的に切り替え（開発中）。
