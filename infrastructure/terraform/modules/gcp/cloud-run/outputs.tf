output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = var.deploy_frontend ? google_cloud_run_v2_service.frontend[0].uri : ""
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "database_connection_name" {
  description = "Cloud SQL 接続名"
  value       = google_sql_database_instance.main.connection_name
}

output "service_account_email" {
  description = "Cloud Run サービスアカウント"
  value       = google_service_account.cloud_run.email
}
