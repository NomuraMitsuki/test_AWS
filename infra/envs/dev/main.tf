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

module "monitoring" {
  source      = "../../modules/monitoring"
  name_prefix = local.name_prefix
  alarm_email = var.alarm_email
}

module "github_oidc" {
  source          = "../../modules/github_oidc"
  name_prefix     = local.name_prefix
  github_org_repo = var.github_org_repo
}
