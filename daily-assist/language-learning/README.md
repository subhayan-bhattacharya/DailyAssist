# Language Learning

## Deploy The API

The API Lambda runs from a Docker image stored in ECR. Build and push the
image manually, then use Terraform to update the Lambda to the new image tag.

Use a new, immutable image tag for every deployment. Do not push updated code
under a tag that Lambda already uses, because Terraform will not detect a
change to the image URI.

### Prerequisites

- Docker is running.
- The AWS CLI is authenticated for account `498129003450`.
- Terraform has already created the `language-learning-api` ECR repository.

### Build And Push A New Image

Run these commands from `daily-assist/language-learning`:

```bash
cd /Users/subhayanbhattacharya/code/DailyAssist/daily-assist/language-learning

AWS_ACCOUNT_ID=498129003450
AWS_REGION=eu-central-1
ECR_REPOSITORY=language-learning-api
IMAGE_TAG=0.0.2
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_URI="$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker build \
  --platform linux/amd64 \
  -f Dockerfile.lambda \
  -t "$IMAGE_URI" \
  .

docker push "$IMAGE_URI"
```

Increment `IMAGE_TAG` for each deployment, for example from `0.0.1` to
`0.0.2`.

Verify that the image exists in ECR:

```bash
aws ecr describe-images \
  --region "$AWS_REGION" \
  --repository-name "$ECR_REPOSITORY" \
  --image-ids imageTag="$IMAGE_TAG"
```

### Deploy The Image With Terraform

Pass the same image tag to Terraform:

```bash
cd terraform/api

terraform plan -var="api_image_tag=$IMAGE_TAG"
terraform apply -var="api_image_tag=$IMAGE_TAG"
```

The expected plan updates `aws_lambda_function.api.image_uri` to the image
that was just pushed. Terraform does not build or push the API image.

After deployment, confirm the configured Lambda image:

```bash
aws lambda get-function \
  --region "$AWS_REGION" \
  --function-name language-learning-api \
  --query 'Code.ImageUri' \
  --output text
```

## Apply Database Migrations

Database migrations require the target Postgres URL:

```bash
cd /Users/subhayanbhattacharya/code/DailyAssist/daily-assist/language-learning

export DATABASE_URL="$(cd terraform && terraform output -raw app_connection_uri)"
uv run alembic upgrade head
```

Verify that `DATABASE_URL` points to the intended environment before applying
migrations.
