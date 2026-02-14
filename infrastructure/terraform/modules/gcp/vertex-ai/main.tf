# =============================================================================
# GCP Vertex AI Access Module
# Vertex AI用サービスアカウント権限設定
# =============================================================================

# Vertex AI ユーザー権限
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${var.service_account_email}"
}

# Vertex AI モデルガーデン（Anthropic Claude等の3rdパーティモデル用）
resource "google_project_iam_member" "vertex_model_garden" {
  project = var.project_id
  role    = "roles/aiplatform.serviceAgent"
  member  = "serviceAccount:${var.service_account_email}"
}

# Cloud Logging 権限（メトリクス記録用）
resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${var.service_account_email}"
}

# Cloud Monitoring 権限
resource "google_project_iam_member" "monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${var.service_account_email}"
}
