



規程レビューツール

要件定義・技術設計書


～ ローカル実行版 / 将来サーバーデプロイ対応 ～





目次
第1部　要件定義
　1. プロジェクト概要
　2. 機能要件
　3. 非機能要件
　4. 画面一覧
　5. データ要件

第2部　技術設計
　6. 設計方針・アーキテクチャ
　7. 技術スタック詳細
　8. 主要機能の実装方針
　9. 環境構築・起動方法
　10. サーバーデプロイ（将来）
　11. 開発計画・コスト

付録
　A. 用語定義
　B. 改訂履歴

第1部　要件定義

1. プロジェクト概要
1.1 背景と目的
企業における規程類（社内規程、業務マニュアル、各種ポリシー等）の管理・レビュー業務は、従来人手による確認作業が中心であり、以下の課題が存在する。
大量の規程文書に対するレビューの工数・時間的負担
レビュー担当者の経験・スキルによる品質のばらつき
用語の統一性や記載ルールの遵守状況の確認漏れ
変更履歴の管理と承認プロセスの煩雑さ

本プロジェクトでは、生成AIを活用した規程レビューツールを開発し、以下を実現する。
規程レビューの自動化による工数削減（目標：従来比70%削減）
チェック項目・記載ルールに基づく一貫性のあるレビュー品質の確保
変更提案の可視化と承認ワークフローの効率化
社内用語・表記ルールの統一促進

1.2 対象スコープ

1.3 システム概要
本システムは以下の主要機能で構成される。


2. 機能要件
2.1 マスタ管理機能
2.1.1 社内用語辞書管理
社内で使用される固有の用語、略語、表記ルールを一元管理する機能。

2.1.2 チェック項目管理
AIレビュー時に適用するチェック項目を定義・管理する機能。

2.1.3 記載ルール管理
文書作成時の記載ルール・スタイルガイドを定義・管理する機能。

2.2 AIレビュー機能
2.2.1 レビュー実行

2.2.2 変更提案生成

2.2.3 比較表示

2.3 承認機能

2.4 履歴管理・レポート機能

3. 非機能要件
3.1 性能要件

3.2 セキュリティ要件

3.3 可用性・運用要件

4. 画面一覧

5. データ要件
5.1 主要エンティティ

第2部　技術設計

6. 設計方針・アーキテクチャ
6.1 基本コンセプト
ローカルファースト：開発者のPCでDocker Composeにより即座に起動可能
クラウドAI活用：LLM/OCR処理はAzure OpenAI・Document Intelligenceを利用
デプロイ容易性：同一コードベースでローカル→サーバーへシームレス移行
シンプル構成：過剰な分散構成を避け、モノリシック構成を採用
データポータビリティ：SQLite（ローカル）→ PostgreSQL（サーバー）切替可能

6.2 環境別構成

6.3 アーキテクチャ構成図

┌─────────────────────────────────────────────────────────────────┐
│                    ユーザーのローカルPC                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Docker Compose                        │   │
│  │                                                         │   │
│  │   ┌─────────────────┐      ┌─────────────────┐         │   │
│  │   │   Frontend      │      │    Backend      │         │   │
│  │   │   (Next.js)     │◄────►│    (FastAPI)    │         │   │
│  │   │   Port: 3030    │      │    Port: 8080   │         │   │
│  │   └─────────────────┘      └────────┬────────┘         │   │
│  │                                     │                   │   │
│  │            ┌────────────────────────┼──────────┐       │   │
│  │            ▼                        ▼          ▼       │   │
│  │   ┌─────────────────┐    ┌──────────────┐ ┌────────┐  │   │
│  │   │   SQLite DB     │    │  ./uploads   │ │./data  │  │   │
│  │   │   + sqlite-vec  │    │  (規程保存)   │ │(永続化)│  │   │
│  │   └─────────────────┘    └──────────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS (外部API)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                            │
│   ┌─────────────────────┐    ┌─────────────────────┐          │
│   │   Azure OpenAI      │    │ Document Intelligence│          │
│   │   - GPT-4o          │    │ - PDF OCR            │          │
│   │   - Embedding       │    │ - 表抽出             │          │
│   └─────────────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘

6.4 技術スタック概要

7. 技術スタック詳細
7.1 フロントエンド（Next.js）

7.2 バックエンド（FastAPI）

7.3 Azure サービス
7.3.1 Azure OpenAI Service

リージョン：Japan East 推奨（低レイテンシ）

7.3.2 Azure Document Intelligence
PDF/画像からのOCRテキスト抽出に使用。スキャンPDFや画像埋め込みPDFに対応。

SKU：S0（従量課金）— 月額数千円程度

7.4 データベース設計
ローカル環境ではSQLite、サーバー環境ではPostgreSQLを使用。環境変数切替のみで移行可能。


8. 主要機能の実装方針
8.1 PDF OCR処理
Azure Document Intelligence を使用してPDFからテキスト抽出を行う。

# backend/app/services/ocr_service.py

class OCRService:
    async def extract_text_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            poller = self.client.begin_analyze_document(
                'prebuilt-read', body=f, content_type='application/pdf'
            )
        result = poller.result()
        return '\n'.join(line.content for page in result.pages
                         for line in page.lines)

8.2 RAGレビュー処理
用語辞書・チェック項目をベクトル検索でコンテキストとして取得し、LLMに送信する。

# backend/app/services/review_engine.py

class ReviewEngine:
    async def execute_review(self, document_id, check_item_ids):
        doc_chunks = await self.get_document_chunks(document_id)
        
        for check_item_id in check_item_ids:
            check_item = await self.get_check_item(check_item_id)
            relevant_terms = await self.vector_search_terms(check_item.name)
            
            messages = self.build_prompt(check_item, relevant_terms, doc_chunks)
            
            response = await self.openai_client.chat.completions.create(
                model='gpt-4o-review', messages=messages, temperature=0.3
            )
            await self.save_findings(document_id, check_item_id, response)

8.3 ベクトル検索（sqlite-vec）
# backend/app/db/vector_store.py

class VectorStore:
    def search_similar(self, query_embedding, table, top_k=5):
        query = f'''
            SELECT id, content, vec_distance_cosine(embedding, ?) as dist
            FROM {table} ORDER BY dist ASC LIMIT ?
        '''
        return self.conn.execute(query, (query_embedding, top_k)).fetchall()

9. 環境構築・起動方法
9.1 前提条件
Docker Desktop インストール済み
Azure OpenAI リソース作成済み（GPT-4o, Embeddingデプロイ済み）
Azure Document Intelligence リソース作成済み

9.2 環境変数設定（.env）

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-review
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=embedding-large
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure Document Intelligence
AZURE_DOC_INTEL_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOC_INTEL_KEY=your-api-key

# Database
DATABASE_URL=sqlite:///./data/policy_review.db

# App
SECRET_KEY=your-secret-key

9.3 起動コマンド

# 1. リポジトリクローン
git clone https://github.com/your-org/policy-review-tool.git
cd policy-review-tool

# 2. 環境変数設定
cp .env.example .env
# .envを編集してAzure認証情報を設定

# 3. 起動
docker-compose up -d

# 4. アクセス
# フロントエンド: http://localhost:3030
# API Docs: http://localhost:8080/docs

9.4 ディレクトリ構成

policy-review-tool/
├── docker-compose.yml
├── .env.example
├── frontend/                # Next.js
│   ├── Dockerfile
│   ├── app/
│   │   ├── (dashboard)/     # メイン画面群
│   │   └── api/             # API Routes（オプション）
│   └── components/
├── backend/                 # FastAPI
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── api/             # エンドポイント
│   │   ├── services/        # ビジネスロジック
│   │   ├── models/          # SQLAlchemy
│   │   └── db/              # DB接続
│   └── tests/
└── data/                    # 永続化（Git対象外）
    ├── policy_review.db
    └── uploads/

10. サーバーデプロイ（将来）
10.1 Azure構成（推奨）

10.2 移行時の変更点

※ 抽象化レイヤーにより、アプリケーションコードの大部分は変更不要。

11. 開発計画・コスト
11.1 開発スケジュール

11.2 ランニングコスト

※ ローカル実行時はAzure AI系サービスのみ課金。インフラコストなし。

付録
A. 用語定義

B. 改訂履歴
