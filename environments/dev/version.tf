terraform {
  required_version = ">=1.13.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.0"
    }
  }
  backend "s3" {
    bucket  = "terraform-tfstate-linebot"
    key     = "linebot/dev/terraform.tfvars"
    region  = "ap-northeast-1"
    profile = "terraform"
  }
}