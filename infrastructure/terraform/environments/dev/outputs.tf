# Development Environment Outputs
# 開発環境用出力定義

output "resource_group_name" {
  description = "リソースグループ名"
  value       = azurerm_resource_group.main.name
}

output "openai_endpoint" {
  description = "Azure OpenAI エンドポイント"
  value       = module.openai.endpoint
}

output "openai_deployment" {
  description = "Azure OpenAI デプロイメント名"
  value       = module.openai.gpt5_deployment_name
}

output "backend_url" {
  description = "バックエンドURL"
  value       = module.container_apps.backend_url
}

output "frontend_url" {
  description = "フロントエンドURL"
  value       = module.container_apps.frontend_url
}

output "log_analytics_workspace_id" {
  description = "Log Analytics ワークスペースID"
  value       = azurerm_log_analytics_workspace.main.id
}
