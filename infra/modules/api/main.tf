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

  dynamic "cors_configuration" {
    for_each = length(var.cors_allow_origins) > 0 ? [1] : []
    content {
      allow_headers     = ["authorization", "content-type"]
      allow_methods     = ["GET", "POST", "PATCH", "OPTIONS"]
      allow_origins     = var.cors_allow_origins
      allow_credentials = false
      max_age           = 300
    }
  }
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

# -----------------------------------------------------------------------------
# leave Lambda（VPC 内）+ JWT 必須ルート
# -----------------------------------------------------------------------------

resource "aws_iam_role" "leave_lambda" {
  name               = "${var.name_prefix}-leave-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "leave_basic" {
  role       = aws_iam_role.leave_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "leave_vpc" {
  role       = aws_iam_role.leave_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "leave_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "leave_secrets" {
  name   = "${var.name_prefix}-leave-secrets"
  role   = aws_iam_role.leave_lambda.id
  policy = data.aws_iam_policy_document.leave_secrets.json
}

data "archive_file" "leave" {
  type        = "zip"
  source_dir  = var.leave_source_dir
  output_path = "${path.module}/.build/leave.zip"
  excludes    = ["__pycache__", "*.pyc", "requirements.txt"]
}

resource "aws_lambda_function" "leave" {
  function_name = "${var.name_prefix}-leave"
  role          = aws_iam_role.leave_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.leave.output_path
  source_code_hash = data.archive_file.leave.output_base64sha256

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

resource "aws_apigatewayv2_integration" "leave" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.leave.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "leave_list" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /leave-requests"
  target             = "integrations/${aws_apigatewayv2_integration.leave.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "leave_create" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /leave-requests"
  target             = "integrations/${aws_apigatewayv2_integration.leave.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "leave_approve" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /leave-requests/{id}/approve"
  target             = "integrations/${aws_apigatewayv2_integration.leave.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "leave_reject" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /leave-requests/{id}/reject"
  target             = "integrations/${aws_apigatewayv2_integration.leave.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_lambda_permission" "leave_apigw" {
  statement_id  = "AllowAPIGatewayInvokeLeave"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.leave.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# -----------------------------------------------------------------------------
# users Lambda（VPC 内）+ JWT 必須ルート + Cognito Admin
# -----------------------------------------------------------------------------

resource "aws_iam_role" "users_lambda" {
  name               = "${var.name_prefix}-users-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "users_basic" {
  role       = aws_iam_role.users_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "users_vpc" {
  role       = aws_iam_role.users_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "users_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "users_secrets" {
  name   = "${var.name_prefix}-users-secrets"
  role   = aws_iam_role.users_lambda.id
  policy = data.aws_iam_policy_document.users_secrets.json
}

data "aws_iam_policy_document" "users_cognito" {
  statement {
    effect = "Allow"
    actions = [
      "cognito-idp:AdminCreateUser",
      "cognito-idp:AdminAddUserToGroup",
      "cognito-idp:AdminRemoveUserFromGroup",
      "cognito-idp:AdminDeleteUser",
      "cognito-idp:AdminGetUser",
      "cognito-idp:AdminListGroupsForUser",
    ]
    resources = [var.cognito_user_pool_arn]
  }
}

resource "aws_iam_role_policy" "users_cognito" {
  name   = "${var.name_prefix}-users-cognito"
  role   = aws_iam_role.users_lambda.id
  policy = data.aws_iam_policy_document.users_cognito.json
}

data "archive_file" "users" {
  type        = "zip"
  source_dir  = var.users_source_dir
  output_path = "${path.module}/.build/users.zip"
  excludes    = ["__pycache__", "*.pyc", "requirements.txt"]
}

resource "aws_lambda_function" "users" {
  function_name = "${var.name_prefix}-users"
  role          = aws_iam_role.users_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.users.output_path
  source_code_hash = data.archive_file.users.output_base64sha256

  environment {
    variables = {
      DB_SECRET_ARN        = var.db_secret_arn
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
}

resource "aws_apigatewayv2_integration" "users" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.users.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "users_list" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /users"
  target             = "integrations/${aws_apigatewayv2_integration.users.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "users_invite" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /users"
  target             = "integrations/${aws_apigatewayv2_integration.users.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_apigatewayv2_route" "users_update" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "PATCH /users/{id}"
  target             = "integrations/${aws_apigatewayv2_integration.users.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_lambda_permission" "users_apigw" {
  statement_id  = "AllowAPIGatewayInvokeUsers"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.users.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# -----------------------------------------------------------------------------
# exports Lambda（VPC 内）+ JWT 必須ルート + S3 Put/Presign
# -----------------------------------------------------------------------------

resource "aws_iam_role" "exports_lambda" {
  name               = "${var.name_prefix}-exports-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "exports_basic" {
  role       = aws_iam_role.exports_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "exports_vpc" {
  role       = aws_iam_role.exports_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "exports_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "exports_secrets" {
  name   = "${var.name_prefix}-exports-secrets"
  role   = aws_iam_role.exports_lambda.id
  policy = data.aws_iam_policy_document.exports_secrets.json
}

data "aws_iam_policy_document" "exports_s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
    ]
    resources = ["${var.exports_bucket_arn}/*"]
  }
}

resource "aws_iam_role_policy" "exports_s3" {
  name   = "${var.name_prefix}-exports-s3"
  role   = aws_iam_role.exports_lambda.id
  policy = data.aws_iam_policy_document.exports_s3.json
}

data "archive_file" "exports" {
  type        = "zip"
  source_dir  = var.exports_source_dir
  output_path = "${path.module}/.build/exports.zip"
  excludes    = ["__pycache__", "*.pyc", "requirements.txt"]
}

resource "aws_lambda_function" "exports" {
  function_name = "${var.name_prefix}-exports"
  role          = aws_iam_role.exports_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.exports.output_path
  source_code_hash = data.archive_file.exports.output_base64sha256

  environment {
    variables = {
      DB_SECRET_ARN       = var.db_secret_arn
      EXPORTS_BUCKET_NAME = var.exports_bucket_name
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
}

resource "aws_apigatewayv2_integration" "exports" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.exports.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "exports_attendance" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /exports/attendance"
  target             = "integrations/${aws_apigatewayv2_integration.exports.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
}

resource "aws_lambda_permission" "exports_apigw" {
  statement_id  = "AllowAPIGatewayInvokeExports"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.exports.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
