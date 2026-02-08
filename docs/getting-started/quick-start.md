# 5分で始める規程レビューツール

このガイドでは、規程レビューツールをローカル環境で素早くセットアップする方法を説明します。

## 前提条件

- Python 3.11以上
- Node.js 18以上
- Azure/AWS/GCPいずれかのアカウント（LLM API用）

## Step 1: リポジトリのクローン（30秒）

```bash
git clone https://github.com/your-org/ai-policy-reviewer.git
cd ai-policy-reviewer
```

## Step 2: 環境変数の設定（1分）

### バックエンド設定

```bash
cd backend
cp .env.example .env
```

`.env`ファイルを編集して、使用するLLMプロバイダーの認証情報を設定：

**Azure OpenAIの場合：**
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
```

**AWS Bedrockの場合：**
```env
LLM_PROVIDER=aws_bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

**GCP Vertex AIの場合：**
```env
LLM_PROVIDER=gcp_vertex
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GCP_CREDENTIALS_PATH=/path/to/credentials.json
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
uvicorn app.main:app --reload --port 8080
```

## Step 4: フロントエンドの起動（1分）

新しいターミナルを開いて：

```bash
cd frontend
npm install
npm run dev
```

## Step 5: 動作確認（30秒）

ブラウザで以下のURLにアクセス：

- フロントエンド: http://localhost:3000
- API Docs: http://localhost:8080/docs
- ヘルスチェック: http://localhost:8080/health/detailed

## 次のステップ

- [詳細インストールガイド](./installation.md) - 本番環境向けセットアップ
- [設定リファレンス](./configuration.md) - 全設定オプションの説明
- [初回レビューチュートリアル](./first-review.md) - 実際のレビューを実行

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

→ 別のポートを指定: `uvicorn app.main:app --port 8081`

### モジュールが見つからない

```
ModuleNotFoundError: No module named 'xxx'
```

→ 仮想環境が有効化されているか確認し、`pip install -r requirements.txt`を再実行

## サポート

問題が解決しない場合は、[GitHubのIssue](https://github.com/your-org/ai-policy-reviewer/issues)で報告してください。
