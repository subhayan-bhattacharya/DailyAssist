terraform {
  backend "s3" {
    bucket = "dailyassist-terraform-state-dev"
    key    = "lambda/terraform.tfstate"
    region = "eu-central-1"
  }
}
