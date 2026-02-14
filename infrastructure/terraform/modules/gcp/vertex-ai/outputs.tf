output "vertex_user_role" {
  description = "付与されたVertex AI ユーザーロール"
  value       = google_project_iam_member.vertex_user.role
}
