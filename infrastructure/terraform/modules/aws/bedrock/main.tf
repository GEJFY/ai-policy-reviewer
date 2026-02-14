# =============================================================================
# AWS Bedrock Access Module
# Bedrock InvokeModel用IAMポリシー
# =============================================================================

# ECSタスクロールにBedrock アクセスを付与
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.name}-bedrock-access"
  role = var.ecs_task_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = var.allowed_model_arns
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch メトリクス用ポリシー
resource "aws_iam_role_policy" "bedrock_monitoring" {
  name = "${var.name}-bedrock-monitoring"
  role = var.ecs_task_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "PolicyReviewer/Bedrock"
        }
      }
    }]
  })
}
