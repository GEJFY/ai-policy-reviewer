# セットアップガイド

このドキュメントでは、AI規程レビューツールのセットアップ手順をゼロから詳しく説明します。
プログラミング初心者の方でも、手順通りに進めればローカル環境で動作させることができます。

---

## 目次

1. [全体像を理解する](#1-全体像を理解する)
2. [前提条件を確認する](#2-前提条件を確認する)
3. [ソースコードの取得](#3-ソースコードの取得)
4. [LLMプロバイダーの選択と設定](#4-llmプロバイダーの選択と設定)
5. [OCRプロバイダーの選択と設定](#5-ocrプロバイダーの選択と設定)
6. [バックエンドのセットアップ](#6-バックエンドのセットアップ)
7. [フロントエンドのセットアップ](#7-フロントエンドのセットアップ)
8. [初期データの投入](#8-初期データの投入)
9. [動作確認](#9-動作確認)
10. [モデルティア選択（オプション）](#10-モデルティア選択オプション)
11. [ローカルLLM（Ollama）の設定（オプション）](#11-ローカルllmollamaの設定オプション)
12. [本番環境へのデプロイ](#12-本番環境へのデプロイ)
13. [トラブルシューティング](#13-トラブルシューティング)

---

## 1. 全体像を理解する

### このツールは何をするの？

AI規程レビューツールは、社内規程文書（就業規則、セキュリティポリシーなど）をAIが自動チェックするシステムです。

```
┌─────────────────────┐     ┌──────────────────────┐
│   フロントエンド      │     │    バックエンド        │
│   (Next.js 16)      │────▶│    (FastAPI)          │
│   ブラウザ画面        │     │    AI処理エンジン      │
│   Port: 3030        │     │    Port: 8080         │
└─────────────────────┘     └──────────┬───────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
           │   SQLite     │   │ LLMプロバイダー│   │ OCRプロバイダー│
           │  データベース  │   │ (AIモデル)    │   │ (文字認識)    │
           └──────────────┘   └──────────────┘   └──────────────┘
```

### 対応するクラウド/AIサービス

| 機能 | プロバイダー | 説明 |
|------|-------------|------|
| **LLM（AI分析）** | Azure AI Foundry | GPT-5.2, Claude Opus 4.6 等 |
| | AWS Bedrock | Claude Sonnet 4.5, Nova Pro 等 |
| | GCP Vertex AI | Gemini 3 Pro/Flash, Claude 等 |
| | Local (Ollama) | qwen2.5:3b, gemma-2-2b 等（無料） |
| **OCR（文字認識）** | Azure Document Intelligence | 高精度クラウドOCR |
| | Tesseract | ローカル無料OCR |
| | AWS Tesseract | リモートTesseract API |

> **初めての方へ**: まずは1つのLLMプロバイダー（AzureまたはOllama推奨）を設定すれば動作します。
> OCRはオプションで、テキスト埋め込みPDFならOCRなしでも使えます。

---

## 2. 前提条件を確認する

### 必須ソフトウェア

以下のソフトウェアがインストールされていることを確認してください。

| ソフトウェア | 必要バージョン | 確認コマンド | 用途 |
|------------|--------------|-------------|------|
| Python | 3.11以上 | `python --version` | バックエンド |
| Node.js | 20以上 | `node --version` | フロントエンド |
| pip | 最新 | `pip --version` | Pythonパッケージ管理 |
| npm | 9以上 | `npm --version` | Node.jsパッケージ管理 |
| Git | 最新 | `git --version` | ソースコード管理 |

#### Python 3.11のインストール（まだの方）

**Windows:**
1. https://www.python.org/downloads/ にアクセス
2. 「Download Python 3.11.x」をクリック
3. インストーラーを実行し、**「Add Python to PATH」にチェック**を入れてインストール

**確認:**
```powershell
python --version
# Python 3.11.x と表示されればOK
```

#### Node.js 20のインストール（まだの方）

**Windows:**
1. https://nodejs.org/ にアクセス
2. LTS版（推奨版）をダウンロードしてインストール

**確認:**
```powershell
node --version
# v20.x.x と表示されればOK

npm --version
# 9.x.x 以上と表示されればOK
```

### クラウドアカウント（いずれか1つ）

AIによる文書分析を行うため、以下のいずれか1つのアカウントが必要です：

| プロバイダー | 無料枠 | 推奨用途 |
|-------------|--------|---------|
| **Azure** | $200分の無料クレジット（新規） | 企業利用、高精度 |
| **AWS** | 一部モデル無料枠あり | AWS既存ユーザー |
| **GCP** | $300分の無料クレジット（新規） | GCP既存ユーザー |
| **Ollama（ローカル）** | 完全無料 | 試用、個人利用、オフライン |

> **費用を抑えたい場合**: Ollamaを使えばクラウド費用なしで試せます（[セクション11](#11-ローカルllmollamaの設定オプション)参照）。

---

## 3. ソースコードの取得

### リポジトリのクローン

```powershell
# 1. 作業ディレクトリに移動（例: ドキュメントフォルダ）
cd C:\Users\<あなたのユーザー名>\Documents

# 2. リポジトリをクローン
git clone https://github.com/GEJFY/ai-policy-reviewer.git

# 3. プロジェクトフォルダに移動
cd ai-policy-reviewer
```

### フォルダ構成の確認

```
ai-policy-reviewer/
├── backend/              ← バックエンド（Python/FastAPI）
│   ├── app/              ← アプリケーションコード
│   │   ├── api/          ← APIエンドポイント
│   │   ├── services/     ← ビジネスロジック（LLM、OCR等）
│   │   ├── models/       ← データベースモデル
│   │   └── config.py     ← 設定管理
│   ├── tests/            ← テストコード
│   └── requirements.txt  ← Python依存パッケージ一覧
├── frontend/             ← フロントエンド（Next.js/React）
│   ├── app/              ← ページコンポーネント
│   ├── components/       ← UIコンポーネント
│   └── package.json      ← Node.js依存パッケージ一覧
├── infrastructure/       ← インフラ設定（Terraform, Helm等）
├── docs/                 ← ドキュメント
├── samples/              ← サンプル規程文書
├── .env.example          ← 環境変数のテンプレート
└── .env                  ← 環境変数（自分で作成）
```

---

## 4. LLMプロバイダーの選択と設定

### 環境変数ファイルの作成

まず、設定ファイル `.env` を作成します：

```powershell
# プロジェクトルートで実行
copy .env.example .env
```

作成された `.env` ファイルをテキストエディタ（VS Codeなど）で開き、使用するプロバイダーに応じて編集します。

---

### 4A. Azure AI Foundry / Azure OpenAI（推奨）

企業利用に最適。GPT-5.2やClaude Opus 4.6など最新モデルに対応。

#### Azureリソースの作成

```powershell
# 1. リソースグループの作成
az group create --name rg-policy-reviewer --location japaneast

# 2. Azure OpenAI Serviceの作成
az cognitiveservices account create `
  --name openai-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --kind OpenAI `
  --sku S0 `
  --location japaneast

# 3. モデルのデプロイ（GPT-5.2の例）
az cognitiveservices account deployment create `
  --name openai-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --deployment-name gpt-5-2 `
  --model-name gpt-5.2 `
  --model-format OpenAI `
  --sku-capacity 30 `
  --sku-name GlobalStandard

# 4. Embeddingモデルのデプロイ
az cognitiveservices account deployment create `
  --name openai-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --deployment-name text-embedding-3-large `
  --model-name text-embedding-3-large `
  --model-version "1" `
  --model-format OpenAI `
  --sku-capacity 120 `
  --sku-name Standard
```

#### 認証情報の取得

```powershell
# APIキーの取得
az cognitiveservices account keys list `
  --name openai-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --query "key1" -o tsv

# エンドポイントの取得
az cognitiveservices account show `
  --name openai-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --query "properties.endpoint" -o tsv
```

#### .env ファイルの設定

```env
# LLMプロバイダー選択
LLM_PROVIDER=azure

# Azure OpenAI / Azure AI Foundry
AZURE_OPENAI_ENDPOINT=https://<取得したエンドポイント>/
AZURE_OPENAI_API_KEY=<取得したAPIキー>
AZURE_OPENAI_DEPLOYMENT=gpt-5-2
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_USE_V1_API=true
```

#### 利用可能なモデル

| ティア | モデル | 特徴 |
|-------|--------|------|
| Precision | gpt-5.2, gpt-5.2-codex, claude-opus-4-6 | 最高精度、高コスト |
| Balanced | gpt-5-mini, claude-sonnet-4-5 | バランス型 |
| Cost-effective | gpt-5-nano, claude-haiku-4-5 | 低コスト、高速 |

---

### 4B. AWS Bedrock

AWSを既にお使いの方に最適。Claude、Nova、Llamaモデルに対応。

#### 前提条件

1. AWSアカウントを作成
2. IAMユーザーにBedrock権限を付与（`AmazonBedrockFullAccess`）
3. AWS Bedrockコンソールで使用するモデルのアクセスを有効化

#### .env ファイルの設定

```env
# LLMプロバイダー選択
LLM_PROVIDER=aws_bedrock

# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<あなたのアクセスキーID>
AWS_SECRET_ACCESS_KEY=<あなたのシークレットアクセスキー>
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

#### 利用可能なモデル（Inference Profile ID形式）

| ティア | モデル | 特徴 |
|-------|--------|------|
| Precision | us.anthropic.claude-opus-4-6-v1 | 最高精度Claude |
| | us.amazon.nova-premier-v1:0 | Amazon最高性能 |
| Balanced | us.anthropic.claude-sonnet-4-5-20250929-v1:0 | バランス型Claude |
| | us.amazon.nova-pro-v1:0 | Amazon汎用 |
| | us.meta.llama4-maverick-17b-instruct-v1:0 | Meta Llama 4 |
| Cost-effective | us.anthropic.claude-haiku-4-5-20251001-v1:0 | 高速Claude |
| | us.amazon.nova-micro-v1:0 | Amazon軽量 |

---

### 4C. GCP Vertex AI

GCPを既にお使いの方に最適。Gemini 3やClaudeモデルに対応。

#### 前提条件

1. GCPプロジェクトを作成
2. Vertex AI APIを有効化
3. サービスアカウントを作成しJSONキーをダウンロード

#### .env ファイルの設定

```env
# LLMプロバイダー選択
LLM_PROVIDER=gcp_vertex

# GCP Vertex AI
GCP_PROJECT_ID=<あなたのプロジェクトID>
GCP_LOCATION=global
GCP_CREDENTIALS_PATH=<サービスアカウントJSONのパス>
GCP_VERTEX_MODEL=gemini-3-flash-preview
```

#### 利用可能なモデル

| ティア | モデル | 特徴 |
|-------|--------|------|
| Precision | gemini-3-pro-preview, claude-opus-4-6 | 最高性能 |
| Balanced | gemini-3-flash-preview, claude-sonnet-4-5 | バランス型 |
| Cost-effective | claude-haiku-4-5 | 低コスト |

---

### 4D. Ollama（ローカルLLM、無料）

クラウド費用なしで試せます。詳細は[セクション11](#11-ローカルllmollamaの設定オプション)を参照してください。

```env
# LLMプロバイダー選択
LLM_PROVIDER=local

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

---

### 共通設定（全プロバイダー共通）

LLMプロバイダーの設定に加えて、以下も `.env` に設定してください：

```env
# Database
DATABASE_URL=sqlite:///./data/policy_review.db

# App
SECRET_KEY=<ランダムな文字列を設定してください>
DEBUG=true
```

> **SECRET_KEY の生成方法:**
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## 5. OCRプロバイダーの選択と設定

OCR（光学文字認識）は、スキャンされたPDFや画像PDFからテキストを抽出する機能です。
テキスト埋め込みPDFの場合はOCRなしでもテキスト抽出が可能です（PyPDF2によるフォールバック）。

### OCRプロバイダーの比較

| プロバイダー | 精度 | コスト | 要件 |
|-------------|------|--------|------|
| **Azure Document Intelligence** | 高 | 従量課金 | Azureアカウント |
| **Tesseract（ローカル）** | 中 | 無料 | Tesseractインストール |
| **AWS Tesseract（リモート）** | 中 | サーバー運用費 | AWS環境構築 |

### 5A. Azure Document Intelligence（推奨）

高精度OCRが必要な場合に推奨。

```powershell
# Azureリソースの作成
az cognitiveservices account create `
  --name doc-intel-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --kind FormRecognizer `
  --sku S0 `
  --location japaneast

# キーの取得
az cognitiveservices account keys list `
  --name doc-intel-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --query "key1" -o tsv

# エンドポイントの取得
az cognitiveservices account show `
  --name doc-intel-policy-reviewer `
  --resource-group rg-policy-reviewer `
  --query "properties.endpoint" -o tsv
```

`.env` に追加：
```env
OCR_PROVIDER=azure_doc_intel
AZURE_DOC_INTEL_ENDPOINT=https://<取得したエンドポイント>/
AZURE_DOC_INTEL_KEY=<取得したAPIキー>
```

### 5B. Tesseract（ローカル、無料）

コストをかけずにOCRを使いたい場合。

#### Tesseractのインストール

**Windows:**
```powershell
winget install UB-Mannheim.TesseractOCR
```

インストール後、パスを確認：
```powershell
# デフォルトのインストール先
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

`.env` に追加：
```env
OCR_PROVIDER=tesseract
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSERACT_LANG=jpn+eng
```

> **言語パック**: `jpn+eng` は日本語＋英語の同時認識です。
> UB-Mannheimのインストーラーには日本語パックが同梱されています。

### 5C. OCRを使わない場合

テキスト埋め込みPDFのみを扱う場合、OCR設定は不要です。
PyPDF2によるテキスト抽出が自動的に使用されます。

---

## 6. バックエンドのセットアップ

### 手順

```powershell
# 1. backendディレクトリに移動
cd backend

# 2. Python仮想環境の作成
python -m venv venv

# 3. 仮想環境の有効化
.\venv\Scripts\activate
# プロンプトの先頭に (venv) が表示されればOK

# 4. 依存パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt
# ※ 初回は数分かかります
```

> **OneDrive環境での注意**: OneDrive同期フォルダ内でvenvを作成する場合、
> 大量のファイルが同期されるため、一時的にOneDriveの同期を停止することを推奨します。

### データベースの初期化

```powershell
# dataディレクトリの作成（backendディレクトリから実行）
mkdir ..\data

# テーブルの作成
python -c "from app.db.init_db import create_tables; create_tables()"
```

### バックエンドの起動

```powershell
# 開発モード（ファイル変更時に自動リロード）
uvicorn app.main:app --reload --port 8080
```

成功すると以下のように表示されます：
```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     Configuration validated successfully
INFO:     Active LLM Provider: azure
INFO:     Active LLM Model: gpt-5-2
```

> **このターミナルは開いたまま**にしてください。別のターミナルでフロントエンドを起動します。

---

## 7. フロントエンドのセットアップ

### 手順

**新しいターミナル**を開いて実行します：

```powershell
# 1. frontendディレクトリに移動
cd frontend

# 2. 依存パッケージのインストール
npm install
# ※ 初回は数分かかります

# 3. 開発サーバーの起動
npm run dev
```

成功すると以下のように表示されます：
```
  ▲ Next.js 16.1.6
  - Local:   http://localhost:3030
```

### 環境変数の設定（オプション）

バックエンドが別のURLで動作している場合、`frontend/.env.local` を作成：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

---

## 8. 初期データの投入

バックエンドが起動している状態で、**別のターミナル**を開いて実行：

```powershell
cd backend

# 仮想環境の有効化
.\venv\Scripts\activate

# マスタデータの投入
python -m app.db.seed_data
```

以下のデータが投入されます：

| データ種類 | 件数 | 内容 |
|-----------|------|------|
| 用語辞書 | 14件 | 従業員、取締役会、情報セキュリティ 等 |
| チェック項目 | 7件 | 用語統一、曖昧表現、責任主体明確化 等 |
| 記載ルール | 8件 | 文体統一、日付表記、句読点 等 |

---

## 9. 動作確認

### 9.1 APIヘルスチェック

ブラウザまたはターミナルでアクセス：

```powershell
# 基本ヘルスチェック
curl http://localhost:8080/health

# 詳細ヘルスチェック
curl http://localhost:8080/health/detailed
```

期待するレスポンス（Azure + Azure Doc Intel の場合）：
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "services": {
    "database": "ok",
    "llm_service": "ok",
    "ocr_service": "ok"
  }
}
```

### 9.2 システム情報の確認

```powershell
curl http://localhost:8080/api/v1/system/info
```

LLMプロバイダー、OCRプロバイダー、モデル情報などが表示されます。

### 9.3 フロントエンドの確認

ブラウザで http://localhost:3030 にアクセスし、以下を確認：

1. ダッシュボードが表示される
2. サイドバーのナビゲーションが機能する
3. 用語辞書ページでデータが表示される（初期データ投入済みの場合）

### 9.4 レビュー機能の確認

1. サイドバーから「文書管理」をクリック
2. 「アップロード」ボタンをクリック
3. `samples/` フォルダ内のサンプル文書をアップロード
4. アップロード完了後、「レビュー実行」をクリック
5. レビュー完了後、指摘事項が表示されることを確認

### 9.5 APIドキュメント

http://localhost:8080/docs にアクセスすると、Swagger UIで全APIエンドポイントを確認・テストできます。

---

## 10. モデルティア選択（オプション）

プロバイダーごとに精度・コストのバランスを簡単に切り替えられる「ティア選択」機能があります。

### ティアの種類

| ティア | 特徴 | 推奨用途 |
|-------|------|---------|
| `precision` | 最高精度、高コスト | 重要規程の正式レビュー |
| `balanced` | バランス型 | 日常的なレビュー |
| `cost_effective` | 低コスト、高速 | ドラフト段階のチェック |

### 設定方法

`.env` に以下を追加するだけで、プロバイダーに応じた最適モデルが自動選択されます：

```env
LLM_TIER=balanced
```

> `LLM_TIER` を設定すると `LLM_MODEL` や個別のモデル設定より優先されます。

### ティア別デフォルトモデル一覧

| プロバイダー | precision | balanced | cost_effective |
|-------------|-----------|----------|----------------|
| **Azure** | gpt-5.2 | gpt-5-mini | gpt-5-nano |
| **AWS Bedrock** | claude-opus-4-6 | claude-sonnet-4-5 | claude-haiku-4-5 |
| **GCP Vertex** | gemini-3-pro | gemini-3-flash | claude-haiku-4-5 |
| **Local** | qwen2.5:3b | qwen2.5:3b | gemma-2-2b-jpn-it |

---

## 11. ローカルLLM（Ollama）の設定（オプション）

Ollamaを使えば、クラウド費用なしでAIレビュー機能を試すことができます。
ネットワーク不要のオフライン環境でも動作します。

### 11.1 Ollamaのインストール

**Windows:**
1. https://ollama.com/ にアクセス
2. 「Download for Windows」をクリックしてインストール
3. インストール後、自動的にOllamaサービスが起動します

**確認:**
```powershell
ollama --version
```

### 11.2 モデルのダウンロード

```powershell
# 多言語対応モデル（推奨、1.9GB）
ollama pull qwen2.5:3b

# 日本語最適化モデル（1.6GB）
ollama pull schroneko/gemma-2-2b-jpn-it
```

> **ディスク容量**: モデルのサイズは1〜2GB程度です。十分な空き容量を確認してください。

### 11.3 .env の設定

```env
# LLMプロバイダーをローカルに設定
LLM_PROVIDER=local

# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

### 11.4 動作確認

```powershell
# Ollamaが起動中か確認
ollama list

# テスト（直接Ollamaに質問）
ollama run qwen2.5:3b "こんにちは"
```

> **注意**: ローカルLLMはクラウドモデル（GPT-5.2やClaude）と比べて精度が劣る場合があります。
> 本格的なレビューにはクラウドモデルの使用を推奨します。

---

## 12. 本番環境へのデプロイ

### 環境変数の変更

```env
DEBUG=false
SECRET_KEY=<本番用の強力なランダムキー>
```

### セキュリティ考慮事項

1. **HTTPS**: 本番環境では必ずHTTPSを使用
2. **CORS**: 許可するオリジンを制限（`.env` の `CORS_ORIGINS` を設定）
3. **APIキー**: 環境変数で管理、コードにハードコードしない
4. **ログ**: 機密情報がログに出力されないよう注意
5. **SECRET_KEY**: デフォルト値を絶対に使用しない

### 推奨構成

```
[Nginx/Reverse Proxy]
        │
        ├── /api/* → [Backend (Gunicorn + Uvicorn)]
        │              └── SQLite/PostgreSQL
        │
        └── /* → [Frontend (Next.js)]
```

### Docker Compose

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

### バックエンド本番起動

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

---

## 13. トラブルシューティング

### よくある問題と解決策

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `ModuleNotFoundError` | 仮想環境が無効 | `.\venv\Scripts\activate` を実行 |
| データベース接続エラー | dataディレクトリ不在 | `mkdir data` を実行 |
| Azure認証エラー | APIキーが無効 | Azure Portalで再発行 |
| AWS認証エラー | IAMキーが無効 | AWS IAMコンソールで確認 |
| GCP認証エラー | 認証情報JSONのパスが不正 | `GCP_CREDENTIALS_PATH` を確認 |
| Ollama接続エラー | Ollamaが未起動 | `ollama serve` を実行 |
| OCRエラー | ファイルサイズ超過 | 50MB以下のファイルを使用 |
| Tesseract not found | 未インストールまたはパス不正 | `TESSERACT_PATH` を確認 |
| CORSエラー | オリジンが許可されていない | `.env` の設定を確認 |
| フロントエンド接続エラー | バックエンドが未起動 | バックエンドを先に起動 |
| `npm install` エラー | Node.jsバージョン不足 | Node.js 20以上にアップグレード |

### LLMプロバイダーの接続テスト

```powershell
cd backend
.\venv\Scripts\activate

# 全テスト実行
python -m pytest tests/test_llm_providers.py -v

# 特定プロバイダーのみ
python -m pytest tests/test_llm_providers.py -v -k azure
python -m pytest tests/test_llm_providers.py -v -k bedrock
python -m pytest tests/test_llm_providers.py -v -k vertex
python -m pytest tests/test_llm_providers.py -v -k ollama
```

### OCRプロバイダーのテスト

```powershell
python -m pytest tests/test_ocr.py -v
```

### ログの確認

```powershell
# アプリケーションログ
Get-Content logs\app.log -Tail 50

# エラーログのみ
Get-Content logs\error.log -Tail 50
```

### サポート

問題が解決しない場合は、以下の情報を添えてGitHub Issueに報告してください：

1. エラーメッセージ（全文）
2. 再現手順
3. 環境情報（OS、Python/Node.jsバージョン、使用プロバイダー）
4. `.env` の設定内容（**APIキーは絶対に含めないでください**）
5. 関連するログ出力

---

## バッチファイルによる簡単起動（Windows）

Windowsユーザーの方は、バッチファイルで簡単に起動できます：

| バッチファイル | 説明 |
|--------------|------|
| `setup.bat` | 初期セットアップ（依存関係インストール、DB初期化） |
| `start_all.bat` | 全サービス起動（推奨） |
| `start_backend.bat` | バックエンドのみ起動 |
| `start_frontend.bat` | フロントエンドのみ起動 |
| `stop_all.bat` | 全サービス停止 |

**使い方:**
1. `.env` ファイルを設定（セクション4〜5参照）
2. `setup.bat` をダブルクリック（初回のみ）
3. `start_all.bat` をダブルクリック
4. ブラウザで http://localhost:3030 にアクセス
