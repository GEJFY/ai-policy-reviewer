# Azure Container Apps Module
# 規程レビューツールのコンテナアプリをデプロイ

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Container Apps 環境
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.name}-env"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# バックエンド Container App
resource "azurerm_container_app" "backend" {
  name                         = "${var.name}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = var.backend_cpu
      memory = var.backend_memory

      # 環境変数
      dynamic "env" {
        for_each = var.backend_env_vars
        content {
          name        = env.key
          secret_name = lookup(env.value, "secret_name", null)
          value       = lookup(env.value, "value", null)
        }
      }

      # ヘルスチェック
      liveness_probe {
        transport = "HTTP"
        path      = "/health/live"
        port      = 8080
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health/ready"
        port      = 8080
      }
    }

    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    # オートスケール設定
    dynamic "http_scale_rule" {
      for_each = var.enable_autoscaling ? [1] : []
      content {
        name                = "http-scale"
        concurrent_requests = var.autoscale_concurrent_requests
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # シークレット
  dynamic "secret" {
    for_each = var.backend_secrets
    content {
      name  = secret.key
      value = secret.value
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# フロントエンド Container App
resource "azurerm_container_app" "frontend" {
  count                        = var.deploy_frontend ? 1 : 0
  name                         = "${var.name}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }
    }

    min_replicas = var.frontend_min_replicas
    max_replicas = var.frontend_max_replicas
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}
