terraform {
  backend "s3" {
    bucket = "dailyassist-terraform-state-dev"
    key    = "language-learning/terraform.tfstate"
    region = "eu-central-1"
  }
}
