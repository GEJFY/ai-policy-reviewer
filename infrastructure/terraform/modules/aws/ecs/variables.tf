variable "name" {
  description = "リソース名プレフィックス"
  type        = string
}

variable "environment" {
  description = "環境名 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "vpc_cidr" {
  description = "VPC CIDRブロック"
  type        = string
  default     = "10.0.0.0/16"
}

variable "backend_cpu" {
  description = "Backend タスクCPU (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Backend タスクメモリ (MB)"
  type        = number
  default     = 1024
}

variable "backend_min_count" {
  description = "Backend 最小タスク数"
  type        = number
  default     = 1
}

variable "backend_max_count" {
  description = "Backend 最大タスク数"
  type        = number
  default     = 3
}

variable "image_tag" {
  description = "コンテナイメージタグ"
  type        = string
  default     = "latest"
}

variable "db_instance_class" {
  description = "RDS インスタンスクラス"
  type        = string
  default     = "db.t3.micro"
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
  default     = "change-me-in-production"
}

variable "log_retention_days" {
  description = "CloudWatch ログ保持日数"
  type        = number
  default     = 30
}

variable "tags" {
  description = "リソースタグ"
  type        = map(string)
  default     = {}
}
