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
LLM_PROVIDER=azure  # azure, aws_bedrock, gcp_vertex, local
LLM_MODEL=gpt-5-2
# LLM_TIER=balanced  # precision, balanced, cost_effective（オプション）

# Azure AI Foundry
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
AZURE_OPENAI_USE_V1_API=true
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# AWS Bedrock（オプション）
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0

# GCP Vertex AI（オプション）
GCP_PROJECT_ID=<your-project-id>
GCP_LOCATION=global
GCP_CREDENTIALS_PATH=/path/to/service-account.json
GCP_VERTEX_MODEL=gemini-3-flash-preview

# Ollama ローカルLLM（オプション、無料）
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:3b

# OCR設定
# OCR_PROVIDER=azure_doc_intel  # azure_doc_intel, tesseract, aws_tesseract

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
LLM_PROVIDER=aws_bedrock  # azure, aws_bedrock, gcp_vertex, local
LLM_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

または、APIで動的に切り替え（開発中）。
