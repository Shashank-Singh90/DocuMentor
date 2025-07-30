# Multi-stage build optimized for Railway
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Create wheels directory
WORKDIR /tmp
COPY requirements-railway.txt .

# Build wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements-railway.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy wheels and install
COPY --from=builder /tmp/wheels /tmp/wheels
COPY requirements-railway.txt .
RUN pip install --no-cache-dir --no-index --find-links /tmp/wheels -r requirements-railway.txt \
    && rm -rf /tmp/wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p data/models data/vectordb data/raw data/processed logs \
    && chown -R appuser:appuser data logs

# Switch to non-root user
USER appuser

# Expose port (Railway will set $PORT automatically)
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080/health || exit 1

# Start script that can run both Streamlit and API
CMD ["python", "start.py"]