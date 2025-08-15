FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Create non-root user for security
RUN groupadd -r victory36 && useradd -r -g victory36 victory36

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create necessary directories and set permissions
RUN mkdir -p /mnt/prediction-cache /mnt/temporal-sync /tmp /var/tmp && \
    chmod 1777 /tmp /var/tmp && \
    chown -R victory36:victory36 /app /mnt/prediction-cache /mnt/temporal-sync

# Switch to non-root user
USER victory36

# Expose ports
EXPOSE 8080 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health/pipeline || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "120", "--keep-alive", "5", "main:app"]
