# 5分で始める規程レビューツール

このガイドでは、規程レビューツールをローカル環境で素早くセットアップする方法を説明します。

## 前提条件

- Python 3.11以上
- Node.js 20以上
- 以下のいずれか（LLM API用）:
  - Azure/AWS/GCPいずれかのアカウント
  - Ollama（ローカルLLM、無料）

## Step 1: リポジトリのクローン（30秒）

```bash
git clone https://github.com/GEJFY/ai-policy-reviewer.git
cd ai-policy-reviewer
```

## Step 2: 環境変数の設定（1分）

### 環境変数設定

```powershell
copy .env.example .env
```

`.env`ファイルを編集して、使用するLLMプロバイダーの認証情報を設定：

**Azure AI Foundryの場合：**
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
AZURE_OPENAI_USE_V1_API=true
```

**AWS Bedrockの場合：**
```env
LLM_PROVIDER=aws_bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

**GCP Vertex AIの場合：**
```env
LLM_PROVIDER=gcp_vertex
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=global
GCP_CREDENTIALS_PATH=/path/to/credentials.json
GCP_VERTEX_MODEL=gemini-3-flash-preview
```

**Ollama（ローカル、無料）の場合：**
```env
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

## Step 3: バックエンドの起動（1分）

```bash
# 仮想環境の作成と有効化
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 依存関係のインストール
pip install -r requirements.txt

# サーバー起動
set DISABLE_SQLALCHEMY_CEXT_RUNTIME=1
uvicorn app.main:app --reload --port 8004
```

## Step 4: フロントエンドの起動（1分）

新しいターミナルを開いて：

```bash
cd frontend
npm install
npx next dev --port 3033 --webpack
```

> **Note:** `--webpack` フラグは日本語パス環境で必須（Turbopackバグ回避）

## Step 5: 動作確認（30秒）

ブラウザで以下のURLにアクセス：

- フロントエンド: http://localhost:3033
- API Docs: http://localhost:8004/docs
- ヘルスチェック: http://localhost:8004/health/detailed

## 次のステップ

- [詳細セットアップガイド](../SETUP_GUIDE.md) - 全プロバイダー対応の詳細設定
- [ユーザーマニュアル](../USER_MANUAL.md) - 画面操作の詳細
- [デモガイド](../DEMO_GUIDE.md) - デモ操作の手順

## トラブルシューティング

### LLMプロバイダーが利用不可

```
UnifiedLLMService: No LLM providers available
```

→ `.env`ファイルのAPI認証情報を確認してください。

### ポートが使用中

```
[Errno 10048] error while attempting to bind on address
```

→ 別のポートを指定: `uvicorn app.main:app --port 8005`

### モジュールが見つからない

```
ModuleNotFoundError: No module named 'xxx'
```

→ 仮想環境が有効化されているか確認し、`pip install -r requirements.txt`を再実行

### 日本語パスでフロントエンドがクラッシュ

→ `--webpack` フラグを付けて起動: `npx next dev --port 3033 --webpack`

## サポート

問題が解決しない場合は、[GitHubのIssue](https://github.com/GEJFY/ai-policy-reviewer/issues)で報告してください。
