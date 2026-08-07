variable "name_prefix" {
  type = string
}

variable "repository_url" {
  type        = string
  description = "GitHub リポジトリ URL（例: https://github.com/org/repo）。access_token 未設定時は未接続アプリのみ作成"
  default     = ""
}

variable "github_access_token" {
  type        = string
  description = "Amplify の GitHub 連携用トークン。空なら repository を接続しない（validate 可）。apply 前に設定すること"
  default     = ""
  sensitive   = true
}

variable "branch_name" {
  type        = string
  description = "デプロイ対象ブランチ"
  default     = "main"
}

variable "app_root" {
  type        = string
  description = "モノレポ内のフロントルート"
  default     = "frontend"
}

variable "aws_region" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_user_pool_client_id" {
  type = string
}

variable "api_base_url" {
  type        = string
  description = "API Gateway ベース URL（NEXT_PUBLIC_API_BASE_URL）"
}

variable "enable_auto_build" {
  type        = bool
  description = "ブランチの自動ビルド"
  default     = true
}
