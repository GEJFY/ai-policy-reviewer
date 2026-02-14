# =============================================================================
# AWS Development Environment
# AWS開発環境用Terraform設定（ECS Fargate + Bedrock）
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # バックエンド設定（リモート状態管理）
  # backend "s3" {
  #   bucket         = "policy-reviewer-tfstate"
  #   key            = "aws-dev/terraform.tfstate"
  #   region         = "ap-northeast-1"
  #   dynamodb_table = "policy-reviewer-tflock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# ローカル変数
locals {
  environment = "dev"
  project     = "policy-reviewer"

  common_tags = {
    Environment = local.environment
    Project     = local.project
    ManagedBy   = "Terraform"
    Owner       = var.owner
  }
}

# =============================================================================
# ECS Fargate + VPC + RDS + ALB
# =============================================================================
module "ecs" {
  source = "../../modules/aws/ecs"

  name        = "${local.project}-${local.environment}"
  environment = local.environment
  aws_region  = var.aws_region

  # 開発環境では低コスト設定
  backend_cpu       = 512
  backend_memory    = 1024
  backend_min_count = 1
  backend_max_count = 3
  image_tag         = var.image_tag

  # RDS（開発環境は最小スペック）
  db_instance_class = "db.t3.micro"
  db_password       = var.db_password

  # アプリケーション
  app_secret_key     = var.app_secret_key
  log_retention_days = 14

  tags = local.common_tags
}

# =============================================================================
# Bedrock Access（ECSタスクロールにBedrock権限を付与）
# =============================================================================
module "bedrock" {
  source = "../../modules/aws/bedrock"

  name               = "${local.project}-${local.environment}"
  ecs_task_role_name = "${local.project}-${local.environment}-ecs-task"

  # 開発環境では全モデルにアクセス可能
  allowed_model_arns = [
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*::foundation-model/amazon.nova-*",
    "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-*",
    "arn:aws:bedrock:*::foundation-model/meta.llama4-*"
  ]

  depends_on = [module.ecs]
}
