variable "name_prefix" {
  type = string
}

variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito User Pool ID（JWT authorizer / users Lambda 用）"
}

variable "cognito_user_pool_arn" {
  type        = string
  description = "Cognito User Pool ARN（users Lambda の Admin API IAM スコープ）"
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

variable "attendance_source_dir" {
  type        = string
  description = "backend/attendance のソースディレクトリ（archive_file 用）"
}

variable "leave_source_dir" {
  type        = string
  description = "backend/leave のソースディレクトリ（archive_file 用）"
}

variable "users_source_dir" {
  type        = string
  description = "backend/users のソースディレクトリ（archive_file 用）"
}

variable "exports_source_dir" {
  type        = string
  description = "backend/exports のソースディレクトリ（archive_file 用）"
}

variable "migrate_source_dir" {
  type        = string
  description = "backend/migrate のソースディレクトリ（archive_file 用）"
}

variable "migrations_source_dir" {
  type        = string
  description = "backend/migrations の SQL ディレクトリ（migrate zip に migrations/ として同梱）"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "ドメイン Lambda（attendance / leave / users / exports）と migrate Lambda を配置するプライベートサブネット"
}

variable "lambda_security_group_id" {
  type        = string
  description = "ドメイン Lambda 用セキュリティグループ"
}

variable "db_secret_arn" {
  type        = string
  description = "RDS 接続情報 Secrets Manager ARN（GetSecretValue 用）"
}

variable "exports_bucket_name" {
  type        = string
  description = "CSV エクスポート用 S3 バケット名"
}

variable "exports_bucket_arn" {
  type        = string
  description = "CSV エクスポート用 S3 バケット ARN（PutObject / GetObject IAM スコープ）"
}

variable "cors_allow_origins" {
  type        = list(string)
  description = "HTTP API CORS 許可オリジン（Amplify URL / localhost 等）"
  default     = []
}
