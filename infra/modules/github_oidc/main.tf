resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "assume_gha" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org_repo}:*"]
    }
  }
}

resource "aws_iam_role" "infra" {
  name               = "${var.name_prefix}-gha-infra"
  assume_role_policy = data.aws_iam_policy_document.assume_gha.json
}

# 学習用: 初期は広め。本番では細分化する。
resource "aws_iam_role_policy_attachment" "infra_admin" {
  role       = aws_iam_role.infra.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_role" "backend" {
  name               = "${var.name_prefix}-gha-backend"
  assume_role_policy = data.aws_iam_policy_document.assume_gha.json
}

resource "aws_iam_role_policy" "backend_lambda" {
  name = "${var.name_prefix}-gha-backend-lambda"
  role = aws_iam_role.backend.id

  # health / attendance / leave / users / exports / migrate（W-280）の UpdateFunctionCode
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction",
          "lambda:PublishVersion",
          "lambda:UpdateAlias",
          "lambda:ListFunctions"
        ]
        Resource = "*"
      }
    ]
  })
}
