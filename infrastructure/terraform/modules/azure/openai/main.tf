# Azure OpenAI / Foundry Module
# Azure OpenAIリソースとデプロイメントを作成

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Azure OpenAI アカウント
resource "azurerm_cognitive_account" "openai" {
  name                  = var.name
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "OpenAI"
  sku_name              = var.sku_name
  custom_subdomain_name = var.custom_subdomain_name

  # ネットワークアクセス制御
  public_network_access_enabled = var.public_network_access_enabled

  dynamic "network_acls" {
    for_each = var.network_acls != null ? [var.network_acls] : []
    content {
      default_action = network_acls.value.default_action
      ip_rules       = network_acls.value.ip_rules

      dynamic "virtual_network_rules" {
        for_each = network_acls.value.virtual_network_subnet_ids
        content {
          subnet_id = virtual_network_rules.value
        }
      }
    }
  }

  # 診断設定
  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# GPT-5.2 デプロイメント
resource "azurerm_cognitive_deployment" "gpt5" {
  count                = var.deploy_gpt5 ? 1 : 0
  name                 = "gpt-5-2"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-5.2"
    version = var.gpt5_model_version
  }

  scale {
    type     = "Standard"
    capacity = var.gpt5_capacity
  }
}

# GPT-5-nano デプロイメント（低コスト用）
resource "azurerm_cognitive_deployment" "gpt5_nano" {
  count                = var.deploy_gpt5_nano ? 1 : 0
  name                 = "gpt-5-nano"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-5-nano"
    version = var.gpt5_nano_model_version
  }

  scale {
    type     = "Standard"
    capacity = var.gpt5_nano_capacity
  }
}

# Embedding デプロイメント
resource "azurerm_cognitive_deployment" "embedding" {
  count                = var.deploy_embedding ? 1 : 0
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = var.embedding_model_version
  }

  scale {
    type     = "Standard"
    capacity = var.embedding_capacity
  }
}

# 診断設定（オプション）
resource "azurerm_monitor_diagnostic_setting" "openai" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "openai-diagnostics"
  target_resource_id         = azurerm_cognitive_account.openai.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "Audit"
  }

  enabled_log {
    category = "RequestResponse"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}
