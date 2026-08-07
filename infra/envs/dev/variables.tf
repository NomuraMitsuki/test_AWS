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

variable "amplify_repository_url" {
  type        = string
  description = "Amplify が接続する GitHub リポジトリ URL"
  default     = "https://github.com/NomuraMitsuki/test_AWS"
}

variable "amplify_github_access_token" {
  type        = string
  description = "Amplify GitHub 連携トークン（sensitive）。空でも validate 可。apply 前に設定"
  default     = ""
  sensitive   = true
}

variable "amplify_branch_name" {
  type        = string
  description = "Amplify デプロイブランチ"
  default     = "main"
}

variable "cors_allow_localhost" {
  type        = bool
  description = "true のとき http://localhost:3000 を API CORS に含める"
  default     = true
}

variable "cors_amplify_origin" {
  type        = string
  description = "API CORS に追加する Amplify オリジン（例: https://main.dxxxx.amplifyapp.com）。初回は空、Amplify apply 後に default_branch_url を設定して循環依存を避ける"
  default     = ""
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  cors_allow_origins = concat(
    var.cors_allow_localhost ? ["http://localhost:3000"] : [],
    var.cors_amplify_origin != "" ? [var.cors_amplify_origin] : [],
  )
}
