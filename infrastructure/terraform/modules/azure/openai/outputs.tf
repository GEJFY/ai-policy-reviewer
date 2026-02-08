# Azure OpenAI Module Outputs
# Azure OpenAIモジュールの出力定義

output "id" {
  description = "Azure OpenAI アカウントID"
  value       = azurerm_cognitive_account.openai.id
}

output "endpoint" {
  description = "Azure OpenAI エンドポイントURL"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "primary_access_key" {
  description = "プライマリアクセスキー"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "secondary_access_key" {
  description = "セカンダリアクセスキー"
  value       = azurerm_cognitive_account.openai.secondary_access_key
  sensitive   = true
}

output "principal_id" {
  description = "マネージドID プリンシパルID"
  value       = azurerm_cognitive_account.openai.identity[0].principal_id
}

output "gpt5_deployment_name" {
  description = "GPT-5.2 デプロイメント名"
  value       = var.deploy_gpt5 ? azurerm_cognitive_deployment.gpt5[0].name : null
}

output "gpt5_nano_deployment_name" {
  description = "GPT-5-nano デプロイメント名"
  value       = var.deploy_gpt5_nano ? azurerm_cognitive_deployment.gpt5_nano[0].name : null
}

output "embedding_deployment_name" {
  description = "Embedding デプロイメント名"
  value       = var.deploy_embedding ? azurerm_cognitive_deployment.embedding[0].name : null
}
