# Azure Container Apps Module Variables
# コンテナアプリモジュールの変数定義

variable "name" {
  description = "アプリケーション名プレフィックス"
  type        = string
}

variable "location" {
  description = "Azure リージョン"
  type        = string
  default     = "japaneast"
}

variable "resource_group_name" {
  description = "リソースグループ名"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics ワークスペースID"
  type        = string
}

# バックエンド設定
variable "backend_image" {
  description = "バックエンドコンテナイメージ"
  type        = string
}

variable "backend_cpu" {
  description = "バックエンドCPU (cores)"
  type        = number
  default     = 0.5
}

variable "backend_memory" {
  description = "バックエンドメモリ (Gi)"
  type        = string
  default     = "1Gi"
}

variable "backend_min_replicas" {
  description = "バックエンド最小レプリカ数"
  type        = number
  default     = 1
}

variable "backend_max_replicas" {
  description = "バックエンド最大レプリカ数"
  type        = number
  default     = 5
}

variable "backend_env_vars" {
  description = "バックエンド環境変数"
  type        = map(map(string))
  default     = {}
}

variable "backend_secrets" {
  description = "バックエンドシークレット"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# フロントエンド設定
variable "deploy_frontend" {
  description = "フロントエンドをデプロイするか"
  type        = bool
  default     = true
}

variable "frontend_image" {
  description = "フロントエンドコンテナイメージ"
  type        = string
  default     = ""
}

variable "frontend_cpu" {
  description = "フロントエンドCPU (cores)"
  type        = number
  default     = 0.25
}

variable "frontend_memory" {
  description = "フロントエンドメモリ (Gi)"
  type        = string
  default     = "0.5Gi"
}

variable "frontend_min_replicas" {
  description = "フロントエンド最小レプリカ数"
  type        = number
  default     = 1
}

variable "frontend_max_replicas" {
  description = "フロントエンド最大レプリカ数"
  type        = number
  default     = 3
}

# オートスケール設定
variable "enable_autoscaling" {
  description = "HTTPベースのオートスケールを有効化"
  type        = bool
  default     = true
}

variable "autoscale_concurrent_requests" {
  description = "スケールアウトのリクエスト閾値"
  type        = number
  default     = 100
}

variable "tags" {
  description = "リソースタグ"
  type        = map(string)
  default     = {}
}
