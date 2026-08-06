output "infra_role_arn" {
  value = aws_iam_role.infra.arn
}

output "backend_role_arn" {
  value = aws_iam_role.backend.arn
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}
