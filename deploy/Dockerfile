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

# Default command for Model A (Railway Job)
CMD ["python", "-m", "engine.cli", "--help"]
