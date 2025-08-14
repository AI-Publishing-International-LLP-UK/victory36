# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for Victory36 AI Agent Ecosystem
# Classification: Diamond SAO Only
# Supports BuildKit secret injection and minimal Alpine runtime

# Build arguments for cross-platform builds
ARG NODE_VERSION=18
ARG ALPINE_VERSION=3.19
ARG TARGET_ENV=production
ARG TARGETARCH
ARG BUILDPLATFORM

# Builder stage - install dependencies and build application
FROM --platform=$BUILDPLATFORM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy application source
COPY . .

# Build application with secrets if needed
RUN --mount=type=secret,id=build_secrets,target=/run/secrets/build_secrets \
    if [ -f /run/secrets/build_secrets ]; then \
        export $(cat /run/secrets/build_secrets | xargs); \
    fi && \
    npm run build 2>/dev/null || echo "No build script found"

# Production dependencies stage
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production && \
    npm cache clean --force

# Security scanning stage (optional)
FROM deps AS security-scan
USER root
RUN apk add --no-cache git
# Security scanning would happen here in CI/CD

# Runtime stage - minimal production image
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS runtime

# Build arguments for runtime configuration
ARG TARGET_ENV=production
ARG SERVICE_NAME=victory36
ARG SERVICE_VERSION=1.0.0

# OCI labels following best practices
LABEL org.opencontainers.image.title="${SERVICE_NAME}" \
      org.opencontainers.image.description="Victory36 AI Agent Ecosystem Management Platform" \
      org.opencontainers.image.version="${SERVICE_VERSION}" \
      org.opencontainers.image.vendor="AI Publishing International LLP" \
      org.opencontainers.image.licenses="Proprietary" \
      org.opencontainers.image.source="https://github.com/aixtiv/asoos" \
      org.opencontainers.image.documentation="https://docs.asoos.com/victory36" \
      classification="Diamond SAO" \
      maintainer="ASOOS Infrastructure Team"

# Install runtime dependencies only
RUN apk add --no-cache \
    tini \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S victory36 && \
    adduser -S victory36 -u 1001 -G victory36

# Set working directory
WORKDIR /app

# Copy production dependencies
COPY --from=deps --chown=victory36:victory36 /app/node_modules ./node_modules

# Copy application files
COPY --chown=victory36:victory36 package*.json ./
COPY --chown=victory36:victory36 src/ ./src/
COPY --chown=victory36:victory36 victory36-awakening-ceremony.sh ./
COPY --chown=victory36:victory36 *.md ./

# Set permissions
RUN chmod +x victory36-awakening-ceremony.sh

# Environment variables with secret injection support
ENV NODE_ENV=${TARGET_ENV} \
    SERVICE_NAME=${SERVICE_NAME} \
    PORT=8080 \
    NODE_OPTIONS="--max-old-space-size=1024" \
    MAX_AGENTS=20000000 \
    REGIONS=MOCOA,MOCORIX,MOCORIX2

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER victory36

# Expose port
EXPOSE 8080

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application with runtime secret injection
CMD ["sh", "-c", "if [ -f /run/secrets/runtime_secrets ]; then export $(cat /run/secrets/runtime_secrets | xargs); fi && exec node src/victory36-connection-pool-manager.js"]
