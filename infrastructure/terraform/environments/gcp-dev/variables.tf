variable "project_id" {
  description = "GCP プロジェクトID"
  type        = string
}

variable "region" {
  description = "GCP リージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "owner" {
  description = "リソースオーナー"
  type        = string
  default     = "dev-team"
}

variable "image_tag" {
  description = "コンテナイメージタグ"
  type        = string
  default     = "latest"
}

variable "db_password" {
  description = "Cloud SQL パスワード"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "アプリケーション SECRET_KEY"
  type        = string
  sensitive   = true
  default     = "gcp-dev-secret-change-me"
}

variable "deploy_frontend" {
  description = "フロントエンドをデプロイするか"
  type        = bool
  default     = true
}
