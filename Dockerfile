# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        postgresql-client \
        redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY ai_shopify_search/requirements_minimal.txt /app/requirements_minimal.txt
COPY ai_shopify_search/requirements_dev.txt /app/requirements_dev.txt

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements_minimal.txt

# Copy application code
COPY ai_shopify_search/ /app/

# Create necessary directories
RUN mkdir -p logs data/databases reports

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 