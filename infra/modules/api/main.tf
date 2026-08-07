data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "health_lambda" {
  name               = "${var.name_prefix}-health-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "health_basic" {
  role       = aws_iam_role.health_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "health" {
  type        = "zip"
  source_dir  = var.health_source_dir
  output_path = "${path.module}/.build/health.zip"
  excludes    = ["__pycache__", "*.pyc", "requirements.txt"]
}

resource "aws_lambda_function" "health" {
  function_name = "${var.name_prefix}-health"
  role          = aws_iam_role.health_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.health.output_path
  source_code_hash = data.archive_file.health.output_base64sha256

  # VPC 外（ヘルスチェックのみ）
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.name_prefix}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

# 後続ルート向け。GET /health には紐付けない。
resource "aws_apigatewayv2_authorizer" "cognito_jwt" {
  api_id           = aws_apigatewayv2_api.http.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.name_prefix}-cognito-jwt"

  jwt_configuration {
    audience = [var.cognito_client_id]
    issuer   = var.cognito_issuer_url
  }
}

resource "aws_apigatewayv2_integration" "health" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.health.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.health.id}"
  # authorization_type 省略 = NONE（JWT 例外）
}

resource "aws_lambda_permission" "health_apigw" {
  statement_id  = "AllowAPIGatewayInvokeHealth"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# -----------------------------------------------------------------------------
# attendance Lambda（VPC 内）+ JWT 必須ルート
# -----------------------------------------------------------------------------

resource "aws_iam_role" "attendance_lambda" {
  name               = "${var.name_prefix}-attendance-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "attendance_basic" {
  role       = aws_iam_role.attendance_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "attendance_vpc" {
  role       = aws_iam_role.attendance_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "attendance_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "attendance_secrets" {
  name   = "${var.name_prefix}-attendance-secrets"
  role   = aws_iam_role.attendance_lambda.id
  policy = data.aws_iam_policy_document.attendance_secrets.json
}

data "archive_file" "attendance" {
  type        = "zip"
  source_dir  = var.attendance_source_dir
  output_path = "${path.module}/.build/attendance.zip"
  excludes    = ["__pycache__", "*.pyc", "requirements.txt"]
}

resource "aws_lambda_function" "attendance" {
  function_name = "${var.name_prefix}-attendance"
  role          = aws_iam_role.attendance_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.attendance.output_path
  source_code_hash = data.archive_file.attendance.output_base64sha256

  environment {
    variables = {
      DB_SECRET_ARN = var.db_secret_arn
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
}

resource "aws_apigatewayv2_integration" "attendance" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.attendance.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "attendance_clock_in" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /attendance/clock-in"
  target             = "integrations/${aws_apigatewayv2_integration.attendance.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "attendance_clock_out" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /attendance/clock-out"
  target             = "integrations/${aws_apigatewayv2_integration.attendance.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "attendance_records" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /attendance/records"
  target             = "integrations/${aws_apigatewayv2_integration.attendance.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "attendance_me" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /attendance/me"
  target             = "integrations/${aws_apigatewayv2_integration.attendance.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "attendance_summary" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /attendance/summary"
  target             = "integrations/${aws_apigatewayv2_integration.attendance.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_lambda_permission" "attendance_apigw" {
  statement_id  = "AllowAPIGatewayInvokeAttendance"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.attendance.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
