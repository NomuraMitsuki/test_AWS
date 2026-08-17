output "bucket_name" {
  description = "本体スタック用 S3 backend のバケット名（backend.hcl へ転記）"
  value       = aws_s3_bucket.tfstate.id
}

output "dynamodb_table_name" {
  description = "本体スタック用 DynamoDB lock テーブル名（backend.hcl へ転記）"
  value       = aws_dynamodb_table.lock.name
}
