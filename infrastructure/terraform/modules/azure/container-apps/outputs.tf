# Azure Container Apps Module Outputs
# コンテナアプリモジュールの出力定義

output "environment_id" {
  description = "Container Apps 環境ID"
  value       = azurerm_container_app_environment.main.id
}

output "backend_fqdn" {
  description = "バックエンドのFQDN"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "backend_url" {
  description = "バックエンドURL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "backend_principal_id" {
  description = "バックエンドのマネージドID プリンシパルID"
  value       = azurerm_container_app.backend.identity[0].principal_id
}

output "frontend_fqdn" {
  description = "フロントエンドのFQDN"
  value       = var.deploy_frontend ? azurerm_container_app.frontend[0].ingress[0].fqdn : null
}

output "frontend_url" {
  description = "フロントエンドURL"
  value       = var.deploy_frontend ? "https://${azurerm_container_app.frontend[0].ingress[0].fqdn}" : null
}
