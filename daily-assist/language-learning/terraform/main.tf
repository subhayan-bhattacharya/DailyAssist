terraform {
  required_version = ">= 1.5.0"
  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6.0"
    }
  }
}

provider "neon" {
  api_key = var.neon_api_key
}

resource "neon_project" "language_learning" {
  name                      = "Language Learning"
  pg_version                = 16
  region_id                 = "aws-eu-central-1"
  org_id                    = var.neon_org_id
  history_retention_seconds = 21600
}

resource "neon_role" "app_owner" {
  project_id = neon_project.language_learning.id
  branch_id  = neon_project.language_learning.default_branch_id
  name       = "language_app_owner"
}

resource "neon_database" "language_learning" {
  project_id = neon_project.language_learning.id
  branch_id  = neon_project.language_learning.default_branch_id
  name       = "language_learning"
  owner_name = neon_role.app_owner.name
}
