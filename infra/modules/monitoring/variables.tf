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
  description = "Map of Lambda role keys to function names (health, attendance, leave, users, exports)"

  validation {
    condition = alltrue([
      contains(keys(var.lambda_function_names), "health"),
      contains(keys(var.lambda_function_names), "attendance"),
      contains(keys(var.lambda_function_names), "leave"),
      contains(keys(var.lambda_function_names), "users"),
      contains(keys(var.lambda_function_names), "exports"),
    ])
    error_message = "lambda_function_names must include keys: health, attendance, leave, users, exports."
  }
}

variable "db_instance_id" {
  type        = string
  description = "RDS DB instance identifier for AWS/RDS metrics"
}
