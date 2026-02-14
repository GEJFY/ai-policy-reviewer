output "alb_url" {
  description = "ALB URL（ブラウザアクセス用）"
  value       = module.ecs.alb_url
}

output "backend_ecr_url" {
  description = "Backend ECR リポジトリURL"
  value       = module.ecs.backend_ecr_url
}

output "frontend_ecr_url" {
  description = "Frontend ECR リポジトリURL"
  value       = module.ecs.frontend_ecr_url
}

output "database_endpoint" {
  description = "RDS エンドポイント"
  value       = module.ecs.database_endpoint
}

output "ecs_cluster_name" {
  description = "ECS クラスター名"
  value       = module.ecs.cluster_name
}
