variable "name_prefix" {
  type = string
}

variable "alarm_email" {
  type    = string
  default = ""
}

variable "http_api_id" {
  type        = string
  description = "HTTP API ID for AWS/ApiGateway metrics (ApiId dimension)"
}

variable "lambda_function_names" {
  type        = map(string)
  description = "Lambda 名のマップ。ダッシュボードは health / attendance / leave / users / exports。migrate は Errors アラームのみ（W-280）"

  validation {
    condition = alltrue([
      contains(keys(var.lambda_function_names), "health"),
      contains(keys(var.lambda_function_names), "attendance"),
      contains(keys(var.lambda_function_names), "leave"),
      contains(keys(var.lambda_function_names), "users"),
      contains(keys(var.lambda_function_names), "exports"),
      contains(keys(var.lambda_function_names), "migrate"),
    ])
    error_message = "lambda_function_names must include keys: health, attendance, leave, users, exports, migrate."
  }
}

variable "db_instance_id" {
  type        = string
  description = "RDS DB instance identifier for AWS/RDS metrics"
}
