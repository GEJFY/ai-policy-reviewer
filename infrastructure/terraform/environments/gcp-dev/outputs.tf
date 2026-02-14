output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = module.cloud_run.backend_url
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = module.cloud_run.frontend_url
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = module.cloud_run.artifact_registry_url
}

output "database_connection_name" {
  description = "Cloud SQL 接続名"
  value       = module.cloud_run.database_connection_name
}
