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
      Application = "Reminders"
    }
  }
}

# Data source to reference existing IAM role
data "aws_iam_role" "lambda_role" {
  name = var.lambda_iam_role_name
}

# Data source to reference existing API Gateway
data "aws_api_gateway_rest_api" "existing_api" {
  name = var.api_gateway_name
}

# ECR repository for Lambda container image
resource "aws_ecr_repository" "lambda" {
  name                 = var.lambda_function_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = var.lambda_function_name
  }
}

# ECR lifecycle policy to keep only the latest image
resource "aws_ecr_lifecycle_policy" "lambda" {
  repository = aws_ecr_repository.lambda.name

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

# Get ECR authorization token
data "aws_ecr_authorization_token" "token" {
  depends_on = [aws_ecr_repository.lambda]
}

# Docker provider for building and pushing images
provider "docker" {
  registry_auth {
    address  = data.aws_ecr_authorization_token.token.proxy_endpoint
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

# Generate a unique image tag based on source code hash
locals {
  # Hash all Python files and Dockerfile to create a unique tag
  code_hash = substr(sha256(join("", [
    for f in fileset("${path.module}/${var.lambda_source_dir}/reminders", "**/*.py") :
    filesha256("${path.module}/${var.lambda_source_dir}/reminders/${f}")
  ])), 0, 8)
  dockerfile_hash = substr(filesha256("${path.module}/${var.lambda_source_dir}/reminders/Dockerfile"), 0, 8)
  image_tag = "${local.code_hash}-${local.dockerfile_hash}"
}

# Build and push Docker image
resource "docker_image" "lambda" {
  name = "${aws_ecr_repository.lambda.repository_url}:${local.image_tag}"

  build {
    context    = "${path.module}/${var.lambda_source_dir}"
    dockerfile = "reminders/Dockerfile"
    tag        = [
      "${aws_ecr_repository.lambda.repository_url}:${local.image_tag}",
      "${aws_ecr_repository.lambda.repository_url}:latest"
    ]
    platform   = "linux/amd64"
  }

  triggers = {
    # Rebuild if source code or Dockerfile changes
    image_tag = local.image_tag
  }
}

# Push image to ECR
resource "docker_registry_image" "lambda" {
  name = docker_image.lambda.name

  triggers = {
    image_id = docker_image.lambda.image_id
  }
}

# Lambda function using container image
resource "aws_lambda_function" "api" {
  function_name = var.lambda_function_name
  role          = data.aws_iam_role.lambda_role.arn
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:${local.image_tag}"

  environment {
    variables = {
      ENVIRONMENT     = "production"
      DYNAMODB_TABLE  = var.dynamodb_table_name
      AWS_REGION_NAME = var.aws_region
    }
  }

  tags = {
    Name = var.lambda_function_name
  }

  depends_on = [docker_registry_image.lambda]
}

# =============================================================================
# API Gateway Integration
# =============================================================================

# Lambda permission for API Gateway to invoke the function
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.aws_api_gateway_rest_api.existing_api.execution_arn}/*/*"
}

# Get root resource of API Gateway
data "aws_api_gateway_resource" "root" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  path        = "/"
}

# Create proxy resource for catching all paths
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  parent_id   = data.aws_api_gateway_resource.root.id
  path_part   = "{proxy+}"
}

# =============================================================================
# Cognito Authorization
# =============================================================================
# Create Cognito authorizer for API Gateway
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "cognito-user-pool-authorizer"
  rest_api_id     = data.aws_api_gateway_rest_api.existing_api.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [var.cognito_user_pool_arn]
  identity_source = "method.request.header.Authorization"
}

# ANY method on proxy resource (with Cognito authorization)
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id   = data.aws_api_gateway_rest_api.existing_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

# Integration for proxy ANY method
resource "aws_api_gateway_integration" "proxy_lambda" {
  rest_api_id             = data.aws_api_gateway_rest_api.existing_api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# ANY method on root resource (with Cognito authorization)
resource "aws_api_gateway_method" "root_any" {
  rest_api_id   = data.aws_api_gateway_rest_api.existing_api.id
  resource_id   = data.aws_api_gateway_resource.root.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

# Integration for root ANY method
resource "aws_api_gateway_integration" "root_lambda" {
  rest_api_id             = data.aws_api_gateway_rest_api.existing_api.id
  resource_id             = data.aws_api_gateway_resource.root.id
  http_method             = aws_api_gateway_method.root_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# =============================================================================
# CORS - OPTIONS method for proxy resource (no auth, returns CORS headers)
# =============================================================================
resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id   = data.aws_api_gateway_rest_api.existing_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "proxy_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  response_models = { "application/json" = "Empty" }
}

resource "aws_api_gateway_integration_response" "proxy_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
  depends_on = [aws_api_gateway_integration.proxy_options]
}

# =============================================================================
# CORS - OPTIONS method for root resource
# =============================================================================
resource "aws_api_gateway_method" "root_options" {
  rest_api_id   = data.aws_api_gateway_rest_api.existing_api.id
  resource_id   = data.aws_api_gateway_resource.root.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = data.aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.root_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "root_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = data.aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.root_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  response_models = { "application/json" = "Empty" }
}

resource "aws_api_gateway_integration_response" "root_options" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id
  resource_id = data.aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.root_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
  depends_on = [aws_api_gateway_integration.root_options]
}

# =============================================================================
# API Gateway Deployment
# =============================================================================
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = data.aws_api_gateway_rest_api.existing_api.id

  triggers = {
    redeployment = sha256(jsonencode([
      aws_api_gateway_integration.proxy_lambda.id,
      aws_api_gateway_integration.root_lambda.id,
      aws_api_gateway_integration.proxy_options.id,
      aws_api_gateway_integration.root_options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.proxy_lambda,
    aws_api_gateway_integration.root_lambda,
    aws_api_gateway_integration_response.proxy_options,
    aws_api_gateway_integration_response.root_options,
  ]
}

# API Gateway stage
resource "aws_api_gateway_stage" "api" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = data.aws_api_gateway_rest_api.existing_api.id
  stage_name    = "api"
}
