variable "name_prefix" {
  type = string
}

variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito User Pool ID（JWT authorizer 用）"
}

variable "cognito_client_id" {
  type        = string
  description = "Cognito App Client ID（JWT audience）"
}

variable "cognito_issuer_url" {
  type        = string
  description = "Cognito issuer URL（https://cognito-idp.<region>.amazonaws.com/<pool_id>）"
}

variable "health_source_dir" {
  type        = string
  description = "backend/health のソースディレクトリ（archive_file 用）"
}
