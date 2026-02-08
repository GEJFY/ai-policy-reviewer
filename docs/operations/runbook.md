# 運用手順書（Runbook）

## 目次

1. [日常運用](#日常運用)
2. [監視・アラート](#監視アラート)
3. [インシデント対応](#インシデント対応)
4. [メンテナンス手順](#メンテナンス手順)

---

## 日常運用

### ヘルスチェック

サービスの状態を確認：

```bash
# 基本ヘルスチェック
curl http://localhost:8080/health

# 詳細ヘルスチェック（依存サービス含む）
curl http://localhost:8080/health/detailed | jq

# Kubernetes環境
kubectl get pods -n production -l app=policy-reviewer
kubectl top pods -n production -l app=policy-reviewer
```

### ログ確認

```bash
# アプリケーションログ（ローカル）
tail -f backend/logs/app.log | jq

# 監査ログ
tail -f backend/logs/audit.log | jq

# Kubernetesログ
kubectl logs -f deployment/policy-reviewer-backend -n production
```

### メトリクス確認

```bash
# Prometheusメトリクス
curl http://localhost:8080/metrics

# 主要メトリクス
curl http://localhost:8080/metrics | grep -E "^(http_requests_total|llm_tokens_total|active_reviews)"
```

---

## 監視・アラート

### 重要メトリクス

| メトリクス | 警告閾値 | 危険閾値 | 対応 |
|----------|---------|---------|------|
| `http_request_duration_seconds` | p99 > 5s | p99 > 30s | パフォーマンス調査 |
| `llm_errors_total` | > 10/min | > 50/min | LLMプロバイダー確認 |
| `circuit_breaker_state` | = 2 (half_open) | = 1 (open) | 外部サービス確認 |
| `active_reviews` | > 50 | > 100 | スケールアウト検討 |

### サーキットブレーカー状態

```bash
# 状態確認
curl http://localhost:8080/health/detailed | jq '.circuit_breakers'

# 手動リセット（緊急時のみ）
curl -X POST http://localhost:8080/api/v1/admin/circuit-breakers/reset
```

---

## インシデント対応

### LLMプロバイダー障害

**症状:**
- レビュー処理がタイムアウト
- `circuit_breaker_state = 1 (open)`

**対応手順:**

1. 障害確認
```bash
curl http://localhost:8080/health/detailed | jq '.circuit_breakers'
```

2. プロバイダー切り替え（Azure → AWS Bedrock）
```bash
# 環境変数を変更
export LLM_PROVIDER=aws_bedrock

# アプリケーション再起動（Kubernetes）
kubectl rollout restart deployment/policy-reviewer-backend -n production
```

3. 監視継続
```bash
watch -n 5 'curl -s http://localhost:8080/health/detailed | jq ".llm_service"'
```

### データベース障害

**症状:**
- `/health/ready` が503を返す
- ログに "Database connection failed"

**対応手順:**

1. データベース接続確認
```bash
# SQLite（開発環境）
ls -la backend/data/policy_review.db

# PostgreSQL（本番環境）
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
```

2. 接続プール確認
```bash
curl http://localhost:8080/metrics | grep db_connections
```

3. 必要に応じてアプリケーション再起動

### 高負荷対応

**症状:**
- レスポンス時間が増加
- CPU/メモリ使用率が高い

**対応手順:**

1. 現状確認
```bash
# Kubernetes
kubectl top pods -n production
kubectl get hpa -n production
```

2. 手動スケールアウト
```bash
kubectl scale deployment/policy-reviewer-backend -n production --replicas=5
```

3. 原因調査
```bash
# 同時レビュー数確認
curl http://localhost:8080/metrics | grep active_reviews

# レート制限状態
curl http://localhost:8080/metrics | grep rate_limit
```

---

## メンテナンス手順

### アプリケーション更新

```bash
# 1. 現在のバージョン確認
curl http://localhost:8080/ | jq '.version'

# 2. 新バージョンデプロイ（Blue-Green）
gh workflow run cd-prod.yml \
  -f version=v0.2.1 \
  -f strategy=blue-green

# 3. デプロイ状況確認
kubectl get pods -n production -l app=policy-reviewer

# 4. 動作確認
curl http://localhost:8080/health/detailed
```

### データベースバックアップ

```bash
# SQLite（開発環境）
cp backend/data/policy_review.db backend/data/policy_review.db.backup.$(date +%Y%m%d)

# PostgreSQL（本番環境）
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

### ログローテーション

デフォルトで自動ローテーション設定済み：
- アプリケーションログ: 50MB、10世代保持
- 監査ログ: 50MB、10世代保持

手動ローテーション：
```bash
# ログアーカイブ
tar -czvf logs_$(date +%Y%m%d).tar.gz backend/logs/*.log.*

# 古いログ削除
find backend/logs -name "*.log.*" -mtime +30 -delete
```

---

## 連絡先

| 役割 | 連絡先 |
|------|--------|
| 開発チーム | dev@example.com |
| インフラチーム | infra@example.com |
| オンコール | +81-XX-XXXX-XXXX |

## 関連ドキュメント

- [監視設定ガイド](./monitoring.md)
- [バックアップ・リストア手順](./backup-restore.md)
- [インシデント対応フロー](./incident-response.md)
