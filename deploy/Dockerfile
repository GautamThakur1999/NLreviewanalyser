FROM python:3.12-slim

# PYTHONUTF8 guards edge.md EC-X-02 (UTF-8 everywhere)
ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Copy source
COPY engine/ ./engine/
COPY config/ ./config/
COPY deploy/ ./deploy/

# Install dependencies and package
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Railway injects $PORT at runtime — uvicorn binds to it
CMD ["sh", "-c", "uvicorn engine.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
