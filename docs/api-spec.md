# API仕様書

規程レビューツール (ai-policy-reviewer) のREST API仕様書。

ベースURL: `http://localhost:8080`

FastAPI自動生成ドキュメント: `http://localhost:8080/docs`

---

## 認証

JWTトークン認証に対応。現在はデフォルトで無効化されており、全エンドポイントにアクセス可能。

---

## ヘルスチェック

### GET /health
基本ヘルスチェック。

**レスポンス**: `200 OK`
```json
{ "status": "healthy" }
```

### GET /health/detailed
詳細ヘルスチェック（LLM/OCR/DB接続状況）。

**レスポンス**: `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "llm_provider": "azure",
  "llm_status": "available",
  "ocr_provider": "azure_doc_intel",
  "ocr_status": "available"
}
```

---

## 文書管理 (`/api/v1/documents`)

### POST /api/v1/documents/upload
PDFファイルをアップロード。最大50MB。

**Content-Type**: `multipart/form-data`

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| file | File | Yes | PDFファイル |

**レスポンス**: `201 Created`
```json
{
  "id": 1,
  "title": "就業規則.pdf",
  "file_path": "data/uploads/xxx.pdf",
  "file_type": "pdf",
  "ocr_status": "pending",
  "created_at": "2026-01-01T00:00:00"
}
```

### GET /api/v1/documents
文書一覧を取得。

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| skip | int | No | オフセット（デフォルト: 0） |
| limit | int | No | 取得件数（デフォルト: 100） |

### GET /api/v1/documents/{document_id}
文書の詳細を取得。

### DELETE /api/v1/documents/{document_id}
文書を削除。関連するレビュー、比較プロジェクト、グループメンバーシップも自動削除。

**レスポンス**: `204 No Content`

### POST /api/v1/documents/{document_id}/ocr
OCR処理を再実行。

---

## レビュー管理 (`/api/v1/reviews`)

### POST /api/v1/reviews
新規レビューを開始。バックグラウンドで実行（最大10分タイムアウト）。

**リクエスト**:
```json
{
  "document_id": 1,
  "check_item_ids": [1, 2, 3]
}
```

### GET /api/v1/reviews
レビュー一覧を取得。

### GET /api/v1/reviews/{review_id}
レビュー詳細を取得。

### GET /api/v1/reviews/{review_id}/findings
レビューの指摘事項一覧を取得。

### GET /api/v1/reviews/{review_id}/export
レビュー結果をExcelファイルでエクスポート。
2シート構成: 「レビュー概要」+「指摘事項一覧」。

**レスポンス**: Excel file (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)

### POST /api/v1/reviews/bulk-export
複数レビューを一括Excelエクスポート。

**リクエスト**:
```json
{
  "review_ids": [1, 2, 3]
}
```

**レスポンス**: Excel file（レビューごとに1シート）

---

## 指摘事項管理 (`/api/v1/findings`)

### GET /api/v1/findings/{finding_id}
指摘事項の詳細を取得。

### PUT /api/v1/findings/{finding_id}/approve
指摘事項を承認。

### PUT /api/v1/findings/{finding_id}/reject
指摘事項を却下。

### PUT /api/v1/findings/{finding_id}/defer
指摘事項を保留。

### PUT /api/v1/findings/{finding_id}/reset
指摘事項のステータスをPENDINGに戻す。

### POST /api/v1/reviews/{review_id}/findings/bulk-approve
指摘事項を一括ステータス変更。

**リクエスト**:
```json
{
  "finding_ids": [1, 2, 3],
  "action": "approve"
}
```

---

## 用語辞書 (`/api/v1/terms`)

### GET /api/v1/terms
用語一覧を取得。

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| skip | int | No | オフセット |
| limit | int | No | 取得件数 |
| category | string | No | カテゴリでフィルタ |

### POST /api/v1/terms
用語を登録。

**リクエスト**:
```json
{
  "term": "従業員",
  "definition": "当社と雇用契約を締結している者をいう",
  "category": "人事",
  "aliases": ["社員", "スタッフ"],
  "usage_note": "規程全体で統一して使用すること"
}
```

### GET /api/v1/terms/template
CSV インポート用テンプレートをダウンロード。

### POST /api/v1/terms/import
CSV/Excelファイルから用語を一括インポート。

**Content-Type**: `multipart/form-data`

**レスポンス**:
```json
{
  "success": 5,
  "errors": ["行3: '従業員' は既に登録されています"]
}
```

### POST /api/v1/terms/search
ベクトル類似検索。

### POST /api/v1/terms/bulk
複数用語を一括登録。

---

## チェック項目 (`/api/v1/check-items`)

### GET /api/v1/check-items
チェック項目一覧を取得。

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| category | enum | No | TERMINOLOGY, GRAMMAR, STRUCTURE, COMPLIANCE, CONSISTENCY, SECURITY, OPERATIONAL |
| is_active | bool | No | 有効/無効フィルタ |

### POST /api/v1/check-items
チェック項目を登録。

### GET /api/v1/check-items/categories
利用可能なカテゴリ一覧。

### GET /api/v1/check-items/template
CSVインポート用テンプレートをダウンロード。

### POST /api/v1/check-items/import
CSV/Excelファイルからチェック項目を一括インポート。

---

## 記載ルール (`/api/v1/writing-rules`)

### GET /api/v1/writing-rules
記載ルール一覧を取得。

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| rule_type | enum | No | STYLE, FORMAT, TERMINOLOGY |
| is_active | bool | No | 有効/無効フィルタ |

### POST /api/v1/writing-rules
記載ルールを登録。

### GET /api/v1/writing-rules/types
利用可能なルールタイプ一覧。

### GET /api/v1/writing-rules/template
CSVインポート用テンプレートをダウンロード。

### POST /api/v1/writing-rules/import
CSV/Excelファイルから記載ルールを一括インポート。

---

## 規程グループ (`/api/v1/document-groups`)

### GET /api/v1/document-groups
規程グループ一覧を取得。

### POST /api/v1/document-groups
規程グループを作成。

**リクエスト**:
```json
{
  "name": "人事関連規程",
  "description": "就業規則と関連規程のグループ",
  "document_ids": [1, 2, 3]
}
```

### GET /api/v1/document-groups/{group_id}
グループの詳細を取得（メンバー文書一覧含む）。

### PUT /api/v1/document-groups/{group_id}
グループを更新。

### DELETE /api/v1/document-groups/{group_id}
グループを削除。

---

## 親子会社規程比較 (`/api/v1/comparisons`)

### GET /api/v1/comparisons
比較プロジェクト一覧を取得。

### POST /api/v1/comparisons
比較プロジェクトを作成・実行。

**リクエスト**:
```json
{
  "name": "就業規則の親子比較",
  "parent_document_id": 1,
  "subsidiary_document_id": 2
}
```

### GET /api/v1/comparisons/{project_id}
比較プロジェクトの詳細（チェック項目・結果含む）を取得。

### DELETE /api/v1/comparisons/{project_id}
比較プロジェクトを削除。

---

## ダッシュボード (`/api/v1/dashboard`)

### GET /api/v1/dashboard/stats
ダッシュボード統計情報を取得。

---

## 設定 (`/api/v1/settings`)

### GET /api/v1/settings
システム設定情報を取得（プロバイダー情報、モデル情報等）。シークレットはマスク済み。

### GET /api/v1/settings/models
利用可能なLLMモデル一覧を取得。

---

## 共通エラーレスポンス

| ステータス | 説明 |
|-----------|------|
| 400 | リクエストパラメータ不正 |
| 404 | リソースが見つからない |
| 413 | ファイルサイズ超過（50MB制限） |
| 422 | バリデーションエラー |
| 429 | レート制限超過 |
| 500 | サーバー内部エラー |

```json
{
  "detail": "エラーメッセージ"
}
```
