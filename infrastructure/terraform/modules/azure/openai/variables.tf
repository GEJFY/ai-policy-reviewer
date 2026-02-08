# Azure OpenAI Module Variables
# Azure OpenAIモジュールの変数定義

variable "name" {
  description = "Azure OpenAI アカウント名"
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

variable "sku_name" {
  description = "SKU (S0 推奨)"
  type        = string
  default     = "S0"
}

variable "custom_subdomain_name" {
  description = "カスタムサブドメイン名"
  type        = string
}

variable "public_network_access_enabled" {
  description = "パブリックネットワークアクセスを許可するか"
  type        = bool
  default     = true
}

variable "network_acls" {
  description = "ネットワークアクセス制御設定"
  type = object({
    default_action             = string
    ip_rules                   = list(string)
    virtual_network_subnet_ids = list(string)
  })
  default = null
}

# GPT-5.2 設定
variable "deploy_gpt5" {
  description = "GPT-5.2をデプロイするか"
  type        = bool
  default     = true
}

variable "gpt5_model_version" {
  description = "GPT-5.2 モデルバージョン"
  type        = string
  default     = "2025-01-01"
}

variable "gpt5_capacity" {
  description = "GPT-5.2 キャパシティ (TPM in thousands)"
  type        = number
  default     = 10
}

# GPT-5-nano 設定
variable "deploy_gpt5_nano" {
  description = "GPT-5-nanoをデプロイするか"
  type        = bool
  default     = false
}

variable "gpt5_nano_model_version" {
  description = "GPT-5-nano モデルバージョン"
  type        = string
  default     = "2025-01-01"
}

variable "gpt5_nano_capacity" {
  description = "GPT-5-nano キャパシティ"
  type        = number
  default     = 20
}

# Embedding 設定
variable "deploy_embedding" {
  description = "Embeddingモデルをデプロイするか"
  type        = bool
  default     = true
}

variable "embedding_model_version" {
  description = "Embedding モデルバージョン"
  type        = string
  default     = "1"
}

variable "embedding_capacity" {
  description = "Embedding キャパシティ"
  type        = number
  default     = 50
}

# 診断設定
variable "log_analytics_workspace_id" {
  description = "Log Analytics ワークスペースID（診断ログ用）"
  type        = string
  default     = null
}

variable "tags" {
  description = "リソースタグ"
  type        = map(string)
  default     = {}
}
