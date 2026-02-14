variable "name" {
  description = "リソース名プレフィックス"
  type        = string
}

variable "ecs_task_role_name" {
  description = "Bedrock アクセスを付与するECSタスクロール名"
  type        = string
}

variable "allowed_model_arns" {
  description = "アクセスを許可するBedrockモデルARN"
  type        = list(string)
  default = [
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*::foundation-model/amazon.nova-*",
    "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-*",
    "arn:aws:bedrock:*::foundation-model/meta.llama4-*"
  ]
}
