terraform {
  backend "s3" {
    bucket = "dailyassist-terraform-state-dev"
    key    = "scheduled/terraform.tfstate"
    region = "eu-central-1"
  }
}
