# Victory36 Container Image
# Classification: Diamond SAO Only
# Purpose: Containerized AI Agent Ecosystem Management Platform

FROM node:18-alpine AS base

# Security: Non-root user
RUN addgroup -g 1001 -S victory36 && \
    adduser -S victory36 -u 1001

# Set working directory
WORKDIR /app

# Install security updates
RUN apk update && apk upgrade && \
    apk add --no-cache \
    dumb-init \
    curl \
    ca-certificates && \
    rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY src/ ./src/
COPY victory36-awakening-ceremony.sh ./
COPY *.md ./

# Set permissions
RUN chmod +x victory36-awakening-ceremony.sh && \
    chown -R victory36:victory36 /app

# Security: Switch to non-root user
USER victory36

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Environment variables
ENV NODE_ENV=production
ENV MAX_AGENTS=20000000
ENV REGIONS=MOCOA,MOCORIX,MOCORIX2

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start the application
CMD ["node", "src/victory36-connection-pool-manager.js"]

# Multi-stage build for security scanning
FROM base AS security-scan
USER root
RUN apk add --no-cache git
# Security scanning would happen here in CI/CD

# Final production image
FROM base AS production
LABEL maintainer="ASOOS Infrastructure Team"
LABEL classification="Diamond SAO"
LABEL version="1.0.0"
LABEL description="Victory36 AI Agent Ecosystem Management Platform"
