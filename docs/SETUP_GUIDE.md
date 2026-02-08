# セットアップガイド

このドキュメントでは、規程レビューツールのセットアップ手順を詳しく説明します。

## 目次

1. [前提条件](#前提条件)
2. [Azureリソースの作成](#azureリソースの作成)
3. [バックエンドのセットアップ](#バックエンドのセットアップ)
4. [フロントエンドのセットアップ](#フロントエンドのセットアップ)
5. [初期データの投入](#初期データの投入)
6. [動作確認](#動作確認)
7. [本番環境へのデプロイ](#本番環境へのデプロイ)

---

## 前提条件

### ソフトウェア要件

| ソフトウェア | バージョン | 用途 |
|------------|-----------|------|
| Python | 3.11以上 | バックエンド |
| Node.js | 18以上 | フロントエンド |
| pip | 最新 | Pythonパッケージ管理 |
| npm | 9以上 | Node.jsパッケージ管理 |

### Azureサブスクリプション

以下のAzureサービスへのアクセスが必要です：

- Azure OpenAI Service
- Azure AI Document Intelligence（Form Recognizer）

---

## Azureリソースの作成

### 1. リソースグループの作成

```bash
az group create --name rg-policy-reviewer --location japaneast
```

### 2. Azure OpenAI Serviceの作成

```bash
# OpenAIリソースの作成
az cognitiveservices account create \
  --name openai-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --kind OpenAI \
  --sku S0 \
  --location japaneast

# GPT-4oモデルのデプロイ
az cognitiveservices account deployment create \
  --name openai-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --deployment-name gpt-4o-review \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 30 \
  --sku-name GlobalStandard

# Embeddingモデルのデプロイ
az cognitiveservices account deployment create \
  --name openai-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name Standard
```

### 3. Azure Document Intelligenceの作成

```bash
az cognitiveservices account create \
  --name doc-intel-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --kind FormRecognizer \
  --sku S0 \
  --location japaneast
```

### 4. 認証情報の取得

```bash
# OpenAIのキー取得
az cognitiveservices account keys list \
  --name openai-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --query "key1" -o tsv

# OpenAIのエンドポイント取得
az cognitiveservices account show \
  --name openai-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --query "properties.endpoint" -o tsv

# Document Intelligenceのキー取得
az cognitiveservices account keys list \
  --name doc-intel-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --query "key1" -o tsv

# Document Intelligenceのエンドポイント取得
az cognitiveservices account show \
  --name doc-intel-policy-reviewer \
  --resource-group rg-policy-reviewer \
  --query "properties.endpoint" -o tsv
```

---

## バックエンドのセットアップ

### 1. 環境変数の設定

プロジェクトルートに`.env`ファイルを作成：

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<取得したエンドポイント>/
AZURE_OPENAI_API_KEY=<取得したAPIキー>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-review
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure Document Intelligence
AZURE_DOC_INTEL_ENDPOINT=https://<取得したエンドポイント>/
AZURE_DOC_INTEL_KEY=<取得したAPIキー>

# Database
DATABASE_URL=sqlite:///./data/policy_review.db

# App
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true
```

### 2. Python環境のセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. データベースの初期化

```bash
# データディレクトリの作成
mkdir -p ../data

# テーブルの作成
python -c "from app.db.init_db import create_tables; create_tables()"
```

### 4. バックエンドの起動

```bash
# 開発モード
uvicorn app.main:app --reload --port 8080

# 本番モード
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

---

## フロントエンドのセットアップ

### 1. 依存関係のインストール

```bash
cd frontend
npm install
```

### 2. 環境変数の設定（オプション）

`frontend/.env.local`を作成（デフォルト値を変更する場合）：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

### 3. フロントエンドの起動

```bash
# 開発モード
npm run dev

# 本番ビルド
npm run build
npm start
```

---

## 初期データの投入

### マスタデータの投入

```bash
cd backend
python -m app.db.seed_data
```

これにより以下のデータが投入されます：

- 用語辞書: 14件
- チェック項目: 7件
- 記載ルール: 8件

### テスト用PDFの生成

```bash
cd tests
python generate_test_pdf.py
```

`tests/sample_security_policy.pdf`が生成されます。このPDFには意図的に以下の問題が含まれています：

- 用語不統一（従業員/社員/スタッフ）
- 曖昧表現（等、など、適宜）
- 責任主体不明確（受動態の多用）
- フォーマット不統一（条番号、和暦）
- 外来語の英語表記

---

## 動作確認

### 1. APIヘルスチェック

```bash
curl http://localhost:8080/health
```

期待するレスポンス：
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "ok",
    "azure_openai": "ok",
    "azure_doc_intel": "ok"
  }
}
```

### 2. フロントエンドの確認

ブラウザで http://localhost:3030 にアクセスし、以下を確認：

1. ダッシュボードが表示される
2. サイドバーのナビゲーションが機能する
3. 用語辞書ページでデータが表示される

### 3. レビュー機能の確認

1. 文書ページで「アップロード」をクリック
2. テスト用PDF（`tests/sample_security_policy.pdf`）をアップロード
3. アップロード完了後、「レビュー実行」をクリック
4. レビュー完了後、指摘事項が表示されることを確認

---

## 本番環境へのデプロイ

### 環境変数の変更

```env
DEBUG=false
SECRET_KEY=<本番用の強力なキー>
```

### セキュリティ考慮事項

1. **HTTPS**: 本番環境では必ずHTTPSを使用
2. **CORS**: 許可するオリジンを制限
3. **APIキー**: 環境変数で管理、コードにハードコードしない
4. **ログ**: 機密情報がログに出力されないよう注意

### 推奨構成

```
[Nginx/Reverse Proxy]
        │
        ├── /api/* → [Backend (Gunicorn + Uvicorn)]
        │              └── SQLite/PostgreSQL
        │
        └── /* → [Frontend (Next.js)]
```

### Docker Compose（参考）

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "3030:3030"
    depends_on:
      - backend
```

---

## トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| データベース接続エラー | dataディレクトリが存在しない | `mkdir -p data`を実行 |
| Azure認証エラー | APIキーが無効 | Azure Portalで再発行 |
| OCRエラー | ファイルサイズ超過 | 50MB以下のファイルを使用 |
| CORS エラー | オリジンが許可されていない | `cors_origins`設定を確認 |

### ログの確認

```bash
# 全ログ
tail -f logs/app.log

# エラーログのみ
tail -f logs/error.log
```

### サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください：

1. エラーメッセージ
2. 再現手順
3. 環境情報（OS、Pythonバージョン等）
4. 関連するログ出力
