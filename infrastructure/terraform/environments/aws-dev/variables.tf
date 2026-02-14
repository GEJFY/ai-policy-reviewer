variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
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
  description = "RDS データベースパスワード"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "アプリケーション SECRET_KEY"
  type        = string
  sensitive   = true
  default     = "aws-dev-secret-change-me"
}
