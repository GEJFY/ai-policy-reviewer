# Development Environment
# 開発環境用Terraform設定

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  # バックエンド設定（リモート状態管理）
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstatepolicyreview"
  #   container_name       = "tfstate"
  #   key                  = "dev.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
    key_vault {
      purge_soft_deleted_secrets_on_destroy = true
    }
  }

  # サブスクリプションIDを指定する場合
  # subscription_id = var.subscription_id
}

# ローカル変数
locals {
  environment = "dev"
  project     = "policy-reviewer"
  location    = "japaneast"

  common_tags = {
    Environment = local.environment
    Project     = local.project
    ManagedBy   = "Terraform"
    Owner       = var.owner
  }
}

# リソースグループ
resource "azurerm_resource_group" "main" {
  name     = "${local.project}-${local.environment}-rg"
  location = local.location
  tags     = local.common_tags
}

# Log Analytics ワークスペース
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.project}-${local.environment}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

# Azure OpenAI
module "openai" {
  source = "../../modules/azure/openai"

  name                  = "${local.project}-${local.environment}-openai"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  custom_subdomain_name = "${local.project}-${local.environment}"

  # 開発環境では低コスト設定
  deploy_gpt5        = true
  gpt5_capacity      = 5 # 低キャパシティ
  deploy_gpt5_nano   = false
  deploy_embedding   = true
  embedding_capacity = 20

  # パブリックアクセス許可（開発用）
  public_network_access_enabled = true

  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags
}

# Container Apps
module "container_apps" {
  source = "../../modules/azure/container-apps"

  name                       = "${local.project}-${local.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  # バックエンド設定
  backend_image        = var.backend_image
  backend_cpu          = 0.5
  backend_memory       = "1Gi"
  backend_min_replicas = 1
  backend_max_replicas = 3

  backend_env_vars = {
    "DEBUG"                   = { value = "true" }
    "LLM_PROVIDER"            = { value = "azure" }
    "AZURE_OPENAI_ENDPOINT"   = { value = module.openai.endpoint }
    "AZURE_OPENAI_DEPLOYMENT" = { value = module.openai.gpt5_deployment_name }
    "AZURE_OPENAI_API_KEY"    = { secret_name = "azure-openai-key" }
  }

  backend_secrets = {
    "azure-openai-key" = module.openai.primary_access_key
    "secret-key"       = var.app_secret_key
  }

  # フロントエンド設定
  deploy_frontend       = var.deploy_frontend
  frontend_image        = var.frontend_image
  frontend_min_replicas = 1
  frontend_max_replicas = 2

  # オートスケール
  enable_autoscaling            = true
  autoscale_concurrent_requests = 50

  tags = local.common_tags
}
