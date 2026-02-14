output "cluster_name" {
  description = "ECS クラスター名"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Backend ECS サービス名"
  value       = aws_ecs_service.backend.name
}

output "alb_dns_name" {
  description = "ALB DNS名"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "ALB URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "backend_ecr_url" {
  description = "Backend ECR リポジトリURL"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_url" {
  description = "Frontend ECR リポジトリURL"
  value       = aws_ecr_repository.frontend.repository_url
}

output "database_endpoint" {
  description = "RDS エンドポイント"
  value       = aws_db_instance.main.endpoint
}

output "database_url" {
  description = "データベース接続URL"
  value       = "postgresql://app:${var.db_password}@${aws_db_instance.main.endpoint}/policy_review"
  sensitive   = true
}

output "ecs_task_role_arn" {
  description = "ECS タスクロールARN（Bedrock用）"
  value       = aws_iam_role.ecs_task.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
