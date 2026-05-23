terraform {
  backend "s3" {
    bucket = "dailyassist-terraform-state-dev"
    key    = "language-learning/api/terraform.tfstate"
    region = "eu-central-1"
  }
}
