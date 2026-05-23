terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DailyAssist"
      ManagedBy   = "Terraform"
      Application = "LanguageLearning"
    }
  }
}

# ---------- Data sources ----------

data "aws_iam_role" "lambda_role" {
  name = var.lambda_iam_role_name
}

data "aws_ecr_authorization_token" "token" {
  depends_on = [aws_ecr_repository.enrichment]
}

provider "docker" {
  registry_auth {
    address  = data.aws_ecr_authorization_token.token.proxy_endpoint
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

# ---------- Secrets ----------

resource "aws_secretsmanager_secret" "database_url" {
  name        = "daily-assist/language-learning/database-url"
  description = "Database URI for the language-learning enrichment Lambda"
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = var.database_url
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "daily-assist/language-learning/openai-api-key"
  description = "OpenAI API key for the language-learning enrichment Lambda"
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

# ---------- ECR image ----------

resource "aws_ecr_repository" "enrichment" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = var.ecr_repository_name
  }
}

resource "aws_ecr_lifecycle_policy" "enrichment" {
  repository = aws_ecr_repository.enrichment.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only latest image"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

locals {
  source_root = "${path.module}/${var.lambda_source_dir}"
  image_tag = substr(sha256(join("", concat(
    [
      filesha256("${local.source_root}/Dockerfile.scheduled"),
      filesha256("${local.source_root}/pyproject.toml"),
      filesha256("${local.source_root}/uv.lock")
    ],
    [
      for f in fileset("${local.source_root}/scheduled", "**/*.py") :
      filesha256("${local.source_root}/scheduled/${f}")
    ],
    [
      for f in fileset("${local.source_root}/core", "**/*.py") :
      filesha256("${local.source_root}/core/${f}")
    ],
    [
      for f in fileset("${local.source_root}/db", "**/*.py") :
      filesha256("${local.source_root}/db/${f}")
    ]
  ))), 0, 12)
}

resource "docker_image" "enrichment" {
  name = "${aws_ecr_repository.enrichment.repository_url}:${local.image_tag}"

  build {
    context    = local.source_root
    dockerfile = "Dockerfile.scheduled"
    tag = [
      "${aws_ecr_repository.enrichment.repository_url}:${local.image_tag}",
      "${aws_ecr_repository.enrichment.repository_url}:latest"
    ]
    platform = "linux/amd64"
  }

  triggers = {
    image_tag = local.image_tag
  }
}

resource "docker_registry_image" "enrichment" {
  name = docker_image.enrichment.name

  triggers = {
    image_id = docker_image.enrichment.image_id
  }
}

# ---------- IAM permissions ----------

resource "aws_iam_role_policy" "secrets_access" {
  name = "${var.enrichment_function_name}-secrets-access"
  role = data.aws_iam_role.lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.database_url.arn,
          aws_secretsmanager_secret.openai_api_key.arn
        ]
      }
    ]
  })
}

# ---------- Lambda function ----------

resource "aws_lambda_function" "enrichment" {
  function_name                  = var.enrichment_function_name
  role                           = data.aws_iam_role.lambda_role.arn
  timeout                        = var.lambda_timeout
  memory_size                    = var.lambda_memory_size
  reserved_concurrent_executions = var.lambda_reserved_concurrency
  package_type                   = "Image"
  image_uri                      = "${aws_ecr_repository.enrichment.repository_url}:${local.image_tag}"

  environment {
    variables = {
      DATABASE_URL_SECRET_ARN   = aws_secretsmanager_secret.database_url.arn
      OPENAI_API_KEY_SECRET_ARN = aws_secretsmanager_secret.openai_api_key.arn
      OPENAI_MODEL              = var.openai_model
      ENRICHMENT_BATCH_LIMIT    = tostring(var.enrichment_batch_limit)
    }
  }

  depends_on = [
    aws_iam_role_policy.secrets_access,
    docker_registry_image.enrichment
  ]
}

# ---------- EventBridge rule ----------

resource "aws_cloudwatch_event_rule" "enrichment" {
  name                = "DailyAssistLanguageLearningEnrichment"
  description         = "Language-learning enrichment job for pending words"
  schedule_expression = var.enrichment_schedule
}

# ---------- EventBridge target ----------

resource "aws_cloudwatch_event_target" "enrichment" {
  rule = aws_cloudwatch_event_rule.enrichment.name
  arn  = aws_lambda_function.enrichment.arn
}

# ---------- Lambda permission for EventBridge ----------

resource "aws_lambda_permission" "enrichment" {
  statement_id  = "AWSEvents_DailyAssistLanguageLearningEnrichment"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.enrichment.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.enrichment.arn
}
