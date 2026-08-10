data "aws_region" "current" {}

locals {
  region = data.aws_region.current.name

  lambda_keys = ["health", "attendance", "leave", "users", "exports"]

  lambda_invocations_metrics = [
    for i, key in local.lambda_keys : concat(
      i == 0 ? ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_names[key]] : ["...", "Invocations", ".", var.lambda_function_names[key]],
      [{ stat = "Sum", label = key }]
    )
  ]

  lambda_errors_metrics = [
    for i, key in local.lambda_keys : concat(
      i == 0 ? ["AWS/Lambda", "Errors", "FunctionName", var.lambda_function_names[key]] : ["...", "Errors", ".", var.lambda_function_names[key]],
      [{ stat = "Sum", label = key }]
    )
  ]

  lambda_duration_metrics = [
    for i, key in local.lambda_keys : concat(
      i == 0 ? ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_names[key]] : ["...", "Duration", ".", var.lambda_function_names[key]],
      [{ stat = "Average", label = key }]
    )
  }

  lambda_error_log_widgets = [
    for i, key in local.lambda_keys : {
      type   = "log"
      x      = (i % 2) * 12
      y      = 32 + floor(i / 2) * 6
      width  = 12
      height = 6
      properties = {
        query  = <<-EOT
          SOURCE '/aws/lambda/${var.lambda_function_names[key]}'
          | filter @message like /(?i)ERROR/
          | fields @timestamp, @message
          | sort @timestamp desc
          | limit 20
        EOT
        region = local.region
        title  = "Lambda ERROR — ${key}"
        view   = "table"
      }
    }
  ]
}

resource "aws_sns_topic" "alarms" {
  name = "${var.name_prefix}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_dashboard" "overview" {
  dashboard_name = "${var.name_prefix}-overview"

  dashboard_body = jsonencode({
    widgets = concat(
      [
        {
          type   = "text"
          x      = 0
          y      = 0
          width  = 24
          height = 2
          properties = {
            markdown = "# ${var.name_prefix} overview\nAPI / Lambda / RDS metrics and Lambda ERROR logs."
          }
        },
        {
          type   = "metric"
          x      = 0
          y      = 2
          width  = 24
          height = 6
          properties = {
            title  = "API Gateway (HTTP API)"
            region = local.region
            period = 300
            stat   = "Sum"
            metrics = [
              ["AWS/ApiGateway", "Count", "ApiId", var.http_api_id, { stat = "Sum", label = "Count" }],
              [".", "4xx", ".", ".", { stat = "Sum", label = "4xx" }],
              [".", "5xx", ".", ".", { stat = "Sum", label = "5xx" }],
              [".", "Latency", ".", ".", { stat = "p99", label = "Latency p99" }],
            ]
          }
        },
        {
          type   = "metric"
          x      = 0
          y      = 8
          width  = 8
          height = 6
          properties = {
            title   = "Lambda Invocations"
            region  = local.region
            period  = 60
            metrics = local.lambda_invocations_metrics
          }
        },
        {
          type   = "metric"
          x      = 8
          y      = 8
          width  = 8
          height = 6
          properties = {
            title   = "Lambda Errors"
            region  = local.region
            period  = 60
            metrics = local.lambda_errors_metrics
          }
        },
        {
          type   = "metric"
          x      = 16
          y      = 8
          width  = 8
          height = 6
          properties = {
            title   = "Lambda Duration (avg)"
            region  = local.region
            period  = 60
            metrics = local.lambda_duration_metrics
          }
        },
        {
          type   = "metric"
          x      = 0
          y      = 14
          width  = 24
          height = 6
          properties = {
            title  = "RDS"
            region = local.region
            period = 300
            metrics = [
              ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id, { stat = "Average", label = "CPU %" }],
              [".", "DatabaseConnections", ".", ".", { stat = "Average", yAxis = "right", label = "Connections" }],
              [".", "FreeStorageSpace", ".", ".", { stat = "Average", yAxis = "right", label = "Free storage" }],
            ]
          }
        },
        {
          type   = "text"
          x      = 0
          y      = 20
          width  = 24
          height = 2
          properties = {
            markdown = "## Lambda ERROR logs\nLog groups are name-referenced (`/aws/lambda/<function>`). Retention IaC is out of scope for W-270."
          }
        },
      ],
      [
        for i, key in local.lambda_keys : {
          type   = "log"
          x      = (i % 2) * 12
          y      = 22 + floor(i / 2) * 6
          width  = 12
          height = 6
          properties = {
            query  = "SOURCE '/aws/lambda/${var.lambda_function_names[key]}'\n| filter @message like /(?i)ERROR/\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 20"
            region = local.region
            title  = "Lambda ERROR — ${key}"
            view   = "table"
          }
        }
      ]
    )
  })
}
