module "network" {
  source      = "../../modules/network"
  name_prefix = local.name_prefix
}

module "cognito" {
  source      = "../../modules/cognito"
  name_prefix = local.name_prefix
}

module "data" {
  source                = "../../modules/data"
  name_prefix           = local.name_prefix
  private_subnet_ids    = module.network.private_subnet_ids
  rds_security_group_id = module.network.rds_security_group_id
  db_instance_class     = var.db_instance_class
}

module "storage" {
  source      = "../../modules/storage"
  name_prefix = local.name_prefix
}

module "github_oidc" {
  source          = "../../modules/github_oidc"
  name_prefix     = local.name_prefix
  github_org_repo = var.github_org_repo
}

module "api" {
  source = "../../modules/api"

  name_prefix              = local.name_prefix
  cognito_user_pool_id     = module.cognito.user_pool_id
  cognito_user_pool_arn    = module.cognito.user_pool_arn
  cognito_client_id        = module.cognito.client_id
  cognito_issuer_url       = module.cognito.issuer_url
  health_source_dir        = "${path.root}/../../../backend/health"
  attendance_source_dir    = "${path.root}/../../../backend/attendance"
  leave_source_dir         = "${path.root}/../../../backend/leave"
  users_source_dir         = "${path.root}/../../../backend/users"
  exports_source_dir       = "${path.root}/../../../backend/exports"
  private_subnet_ids       = module.network.private_subnet_ids
  lambda_security_group_id = module.network.lambda_security_group_id
  db_secret_arn            = module.data.db_secret_arn
  exports_bucket_name      = module.storage.exports_bucket_name
  exports_bucket_arn       = module.storage.exports_bucket_arn
  cors_allow_origins       = local.cors_allow_origins
}

module "monitoring" {
  source      = "../../modules/monitoring"
  name_prefix = local.name_prefix
  alarm_email = var.alarm_email

  http_api_id = module.api.http_api_id
  lambda_function_names = {
    health     = module.api.health_lambda_function_name
    attendance = module.api.attendance_lambda_function_name
    leave      = module.api.leave_lambda_function_name
    users      = module.api.users_lambda_function_name
    exports    = module.api.exports_lambda_function_name
  }
  db_instance_id = module.data.db_instance_id
}

module "amplify" {
  source = "../../modules/amplify"

  name_prefix                 = local.name_prefix
  repository_url              = var.amplify_repository_url
  github_access_token         = var.amplify_github_access_token
  branch_name                 = var.amplify_branch_name
  aws_region                  = var.aws_region
  cognito_user_pool_id        = module.cognito.user_pool_id
  cognito_user_pool_client_id = module.cognito.client_id
  api_base_url                = module.api.api_endpoint
}
