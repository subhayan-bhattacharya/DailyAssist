# Use AWS Lambda Python 3.13 base image
FROM public.ecr.aws/lambda/python:3.13

# Copy dependency files from reminders subdirectory
COPY reminders/pyproject.toml reminders/uv.lock ${LAMBDA_TASK_ROOT}/

# Install uv for fast package installation
RUN pip install uv

# Export lockfile to requirements.txt and install dependencies system-wide
RUN cd ${LAMBDA_TASK_ROOT} && \
    uv export --no-dev --frozen --no-hashes > requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt

# Copy application code from reminders subdirectory
COPY reminders/ ${LAMBDA_TASK_ROOT}/

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["app.handler"]
