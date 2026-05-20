FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv export --frozen --no-hashes --group dev > requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt && \
    rm requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
