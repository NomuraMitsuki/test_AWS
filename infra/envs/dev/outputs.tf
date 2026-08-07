output "vpc_id" {
  value = module.network.vpc_id
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "lambda_security_group_id" {
  value = module.network.lambda_security_group_id
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "cognito_client_id" {
  value = module.cognito.client_id
}

output "cognito_issuer_url" {
  value = module.cognito.issuer_url
}

output "db_endpoint" {
  value = module.data.db_instance_endpoint
}

output "db_secret_arn" {
  value = module.data.db_secret_arn
}

output "exports_bucket_name" {
  value = module.storage.exports_bucket_name
}

output "gha_infra_role_arn" {
  value = module.github_oidc.infra_role_arn
}

output "gha_backend_role_arn" {
  value = module.github_oidc.backend_role_arn
}

output "cloudwatch_dashboard_name" {
  value = module.monitoring.dashboard_name
}

output "api_endpoint" {
  value = module.api.api_endpoint
}

output "health_lambda_function_name" {
  value = module.api.health_lambda_function_name
}

output "attendance_lambda_function_name" {
  value = module.api.attendance_lambda_function_name
}

output "leave_lambda_function_name" {
  value = module.api.leave_lambda_function_name
}

output "users_lambda_function_name" {
  value = module.api.users_lambda_function_name
}

output "http_api_id" {
  value = module.api.http_api_id
}
