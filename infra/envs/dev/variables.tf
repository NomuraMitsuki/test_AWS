variable "project_name" {
  type        = string
  description = "リソース名のプレフィックス"
  default     = "attendance"
}

variable "environment" {
  type        = string
  description = "環境名"
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS リージョン"
  default     = "ap-northeast-1"
}

variable "github_org_repo" {
  type        = string
  description = "OIDC 信頼に使う GitHub リポジトリ (owner/name)"
  default     = "NomuraMitsuki/test_AWS"
}

variable "db_instance_class" {
  type        = string
  description = "RDS インスタンスクラス"
  default     = "db.t4g.micro"
}

variable "alarm_email" {
  type        = string
  description = "CloudWatch アラーム通知先（空なら SNS 購読なし）"
  default     = ""
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}
