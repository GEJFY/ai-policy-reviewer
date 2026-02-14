variable "project_id" {
  description = "GCP プロジェクトID"
  type        = string
}

variable "service_account_email" {
  description = "Vertex AI アクセスを付与するサービスアカウント"
  type        = string
}
