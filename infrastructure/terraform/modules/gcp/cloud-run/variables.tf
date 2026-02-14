variable "name" {
  description = "リソース名プレフィックス"
  type        = string
}

variable "project_id" {
  description = "GCP プロジェクトID"
  type        = string
}

variable "region" {
  description = "GCP リージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "環境名 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "backend_cpu" {
  description = "Backend CPU (例: 1, 2)"
  type        = string
  default     = "1"
}

variable "backend_memory" {
  description = "Backend メモリ (例: 1Gi, 2Gi)"
  type        = string
  default     = "1Gi"
}

variable "backend_min_instances" {
  description = "Backend 最小インスタンス数"
  type        = number
  default     = 1
}

variable "backend_max_instances" {
  description = "Backend 最大インスタンス数"
  type        = number
  default     = 3
}

variable "frontend_max_instances" {
  description = "Frontend 最大インスタンス数"
  type        = number
  default     = 2
}

variable "deploy_frontend" {
  description = "フロントエンドをデプロイするか"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "コンテナイメージタグ"
  type        = string
  default     = "latest"
}

variable "db_tier" {
  description = "Cloud SQL インスタンスティア"
  type        = string
  default     = "db-f1-micro"
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
  default     = "change-me-in-production"
}

variable "vpc_network_id" {
  description = "VPCネットワークID（Cloud SQL プライベートIP用）"
  type        = string
  default     = ""
}

variable "labels" {
  description = "リソースラベル"
  type        = map(string)
  default     = {}
}
