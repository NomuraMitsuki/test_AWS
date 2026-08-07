locals {
  connect_repo = var.github_access_token != "" && var.repository_url != ""

  build_spec = <<-EOT
    version: 1
    applications:
      - appRoot: ${var.app_root}
        frontend:
          phases:
            preBuild:
              commands:
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: .next
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
              - .next/cache/**/*
  EOT

  environment_variables = {
    AMPLIFY_MONOREPO_APP_ROOT               = var.app_root
    NEXT_PUBLIC_AWS_REGION                  = var.aws_region
    NEXT_PUBLIC_COGNITO_USER_POOL_ID        = var.cognito_user_pool_id
    NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID = var.cognito_user_pool_client_id
    NEXT_PUBLIC_API_BASE_URL                = var.api_base_url
  }
}

resource "aws_amplify_app" "this" {
  name       = "${var.name_prefix}-frontend"
  platform   = "WEB_COMPUTE"
  build_spec = local.build_spec

  # GitHub 連携はトークンがあるときのみ（未設定でも terraform validate 可能）
  repository   = local.connect_repo ? var.repository_url : null
  access_token = local.connect_repo ? var.github_access_token : null

  environment_variables = local.environment_variables

  # Amplify がデプロイ後に custom_rule を追加することがあるため無視
  lifecycle {
    ignore_changes = [custom_rule]
  }
}

resource "aws_amplify_branch" "this" {
  app_id                      = aws_amplify_app.this.id
  branch_name                 = var.branch_name
  framework                   = "Next.js - SSR"
  stage                       = "PRODUCTION"
  enable_auto_build           = var.enable_auto_build
  enable_performance_mode     = false
  enable_pull_request_preview = false

  environment_variables = local.environment_variables
}
