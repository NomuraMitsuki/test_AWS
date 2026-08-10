output "alarm_topic_arn" {
  value = aws_sns_topic.alarms.arn
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.overview.dashboard_name
}

output "lambda_error_alarm_arns" {
  value = { for k, a in aws_cloudwatch_metric_alarm.lambda_errors : k => a.arn }
}

output "api_5xx_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.api_5xx.arn
}

output "api_latency_p99_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.api_latency_p99.arn
}

output "rds_cpu_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.rds_cpu.arn
}

output "rds_connections_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.rds_connections.arn
}
