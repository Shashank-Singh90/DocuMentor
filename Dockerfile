# Simplified Dockerfile for Railway - No build issues
FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p data logs \
    && chown -R appuser:appuser data logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Start the application
CMD ["python", "start.py"]