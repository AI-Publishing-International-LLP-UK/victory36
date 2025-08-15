FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Create user for security
RUN groupadd -r wfa && useradd -r -g wfa wfa

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Create directories and set permissions
RUN mkdir -p /tmp /var/tmp && \
    chmod 1777 /tmp /var/tmp && \
    chown -R wfa:wfa /app

USER wfa

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health/wfa-bridge || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8090", "--workers", "4", "--threads", "2", "main:app"]
