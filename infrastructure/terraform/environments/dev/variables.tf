# Development Environment Variables
# 開発環境用変数定義

variable "owner" {
  description = "リソース所有者"
  type        = string
  default     = "dev-team"
}

variable "backend_image" {
  description = "バックエンドDockerイメージ"
  type        = string
  default     = "ghcr.io/your-org/policy-reviewer-backend:latest"
}

variable "frontend_image" {
  description = "フロントエンドDockerイメージ"
  type        = string
  default     = "ghcr.io/your-org/policy-reviewer-frontend:latest"
}

variable "deploy_frontend" {
  description = "フロントエンドをデプロイするか"
  type        = bool
  default     = true
}

variable "app_secret_key" {
  description = "アプリケーション秘密鍵"
  type        = string
  sensitive   = true
}
