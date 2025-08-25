FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY mcp_client_onboarding_automation.py .
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    motor==3.3.2 \
    pymongo==4.6.0 \
    pydantic==2.5.0 \
    aiohttp==3.9.1 \
    certifi==2023.11.17

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "mcp_client_onboarding_automation:app", "--host", "0.0.0.0", "--port", "8004"]
