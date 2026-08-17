terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # bootstrap 自身の state はローカル。destroy しない。
  backend "local" {}
}

provider "aws" {
  region = "ap-northeast-1"
}
