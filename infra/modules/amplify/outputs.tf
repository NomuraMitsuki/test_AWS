output "app_id" {
  value = aws_amplify_app.this.id
}

output "default_domain" {
  value       = aws_amplify_app.this.default_domain
  description = "例: dxxxx.amplifyapp.com"
}

output "branch_name" {
  value = aws_amplify_branch.this.branch_name
}

output "default_branch_url" {
  value       = "https://${aws_amplify_branch.this.branch_name}.${aws_amplify_app.this.default_domain}"
  description = "CORS 用オリジンの目安（例: https://main.dxxxx.amplifyapp.com）"
}
