terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # 初回はローカル state。リモート化時はコメントを外す。
  # backend "s3" {
  #   bucket         = "attendance-tfstate-dev"
  #   key            = "attendance/dev/terraform.tfstate"
  #   region         = "ap-northeast-1"
  #   dynamodb_table = "attendance-tfstate-lock-dev"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
