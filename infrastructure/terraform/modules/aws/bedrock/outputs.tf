output "bedrock_policy_name" {
  description = "Bedrock IAMポリシー名"
  value       = aws_iam_role_policy.bedrock_access.name
}
