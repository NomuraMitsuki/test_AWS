output "api_endpoint" {
  value = aws_apigatewayv2_api.http.api_endpoint
}

output "health_lambda_function_name" {
  value = aws_lambda_function.health.function_name
}

output "attendance_lambda_function_name" {
  value = aws_lambda_function.attendance.function_name
}

output "http_api_id" {
  value = aws_apigatewayv2_api.http.id
}

output "cognito_jwt_authorizer_id" {
  value = aws_apigatewayv2_authorizer.cognito_jwt.id
}
