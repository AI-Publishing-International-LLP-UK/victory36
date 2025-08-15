#!/bin/bash

# Deploy Diamond SAO HR AI CRMS System to Cloud
# Target: victory36-cluster-mocoa (us-west1)
# Project: api-for-warp-drive  
# Classification: Diamond SAO Only
# MongoDB: Cloud (GCP)

set -e

echo "☁️  DIAMOND SAO CLOUD DEPLOYMENT"
echo "================================="
echo "Target: victory36-cluster-mocoa"
echo "Project: api-for-warp-drive"
echo "MongoDB: Cloud (GCP)"
echo "================================="

# Configuration
PROJECT_ID="api-for-warp-drive"
CLUSTER_NAME="victory36-cluster-mocoa"
REGION="us-west1"
IMAGE_NAME="diamond-sao-hr-crms"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check GCP authentication
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1 > /dev/null; then
        log_error "Not authenticated with GCP"
        echo "Please run: gcloud auth login"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Set up GCP project and cluster access
setup_gcp_access() {
    log_info "Setting up GCP access..."
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    # Get cluster credentials
    gcloud container clusters get-credentials "$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable \
        container.googleapis.com \
        cloudbuild.googleapis.com \
        containerregistry.googleapis.com \
        --project="$PROJECT_ID"
    
    log_success "GCP access configured"
}

# Build Docker image for cloud deployment
build_docker_image() {
    log_info "Building Docker image for cloud deployment..."
    
    # Create optimized Dockerfile for cloud
    cat > Dockerfile.cloud << 'EOF'
FROM python:3.11-slim

LABEL maintainer="Phillip Corey (ROARK) - Diamond SAO <pr@coaching2100.com>"
LABEL classification="DIAMOND_SAO_ONLY"
LABEL component="HR_AI_CRMS_CLOUD_SYSTEM"
LABEL project="api-for-warp-drive"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r diamond_sao && useradd -r -g diamond_sao diamond_sao

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY diamond_sao_hr_crms_system.py .
COPY mongodb_schema_setup.py .

# Create necessary directories
RUN mkdir -p /app/logs /tmp/diamond_sao && \
    chown -R diamond_sao:diamond_sao /app /tmp/diamond_sao

# Switch to non-root user
USER diamond_sao

# Expose port
EXPOSE 8003

# Health check for Kubernetes
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
  CMD curl -f http://localhost:8003/api/system/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "diamond_sao_hr_crms_system:app", "--host", "*******", "--port", "8003", "--workers", "1"]
EOF

    # Create requirements.txt optimized for cloud
    cat > requirements.txt << 'EOF'
fastapi==0.116.1
uvicorn[standard]==0.35.0
aiohttp==3.12.15
python-jose[cryptography]==3.5.0
python-multipart==0.0.20
passlib[bcrypt]==1.7.4
jinja2==3.1.6
motor[srv]==3.3.2
pymongo[srv]==4.6.0
certifi==2024.8.30
pyotp==2.9.0
pydantic[email]==2.11.7
aiofiles==23.2.1
EOF

    # Build and tag the image
    IMAGE_TAG="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)"
    LATEST_TAG="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"
    
    log_info "Building Docker image: $LATEST_TAG"
    docker build -f Dockerfile.cloud -t "$LATEST_TAG" -t "$IMAGE_TAG" .
    
    # Push to Google Container Registry
    log_info "Pushing to Google Container Registry..."
    gcloud auth configure-docker --quiet
    docker push "$LATEST_TAG"
    docker push "$IMAGE_TAG"
    
    log_success "Docker image built and pushed: $LATEST_TAG"
    
    # Clean up
    rm Dockerfile.cloud requirements.txt
}

# Create GCP Service Account for Diamond SAO
create_service_account() {
    log_info "Creating GCP Service Account for Diamond SAO..."
    
    SA_NAME="diamond-sao"
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Create service account if it doesn't exist
    if ! gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
        gcloud iam service-accounts create "$SA_NAME" \
            --display-name="Diamond SAO HR AI CRMS Service Account" \
            --description="Service account for Diamond SAO system in victory36-cluster-mocoa" \
            --project="$PROJECT_ID"
        
        log_success "Created service account: $SA_EMAIL"
    else
        log_info "Service account already exists: $SA_EMAIL"
    fi
    
    # Grant necessary permissions
    log_info "Granting IAM permissions..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/monitoring.viewer"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/logging.logWriter"
    
    # Enable workload identity
    gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
        --role="roles/iam.workloadIdentityUser" \
        --member="serviceAccount:${PROJECT_ID}.svc.id.goog[diamond-sao-system/diamond-sao-service-account]" \
        --project="$PROJECT_ID"
    
    log_success "Service account configured with workload identity"
}

# Deploy to Kubernetes cluster
deploy_to_kubernetes() {
    log_info "Deploying Diamond SAO system to victory36-cluster-mocoa..."
    
    # Apply the deployment
    kubectl apply -f deploy-diamond-sao-cloud.yaml
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/diamond-sao-hr-crms-cloud -n diamond-sao-system
    
    log_success "Diamond SAO system deployed to cloud!"
}

# Get deployment status and access information
get_deployment_status() {
    log_info "Getting deployment status..."
    
    echo ""
    echo "📊 DEPLOYMENT STATUS"
    echo "===================="
    
    # Pod status
    echo "Pods:"
    kubectl get pods -n diamond-sao-system -o wide
    
    echo ""
    echo "Services:"
    kubectl get services -n diamond-sao-system
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n diamond-sao-system
    
    # Get external IP
    EXTERNAL_IP=$(kubectl get service diamond-sao-hr-crms-cloud-service -n diamond-sao-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [[ -n "$EXTERNAL_IP" ]]; then
        echo ""
        echo "🌐 ACCESS INFORMATION"
        echo "===================="
        echo "External IP: $EXTERNAL_IP"
        echo "Admin Interface: http://$EXTERNAL_IP/admin"
        echo "Health Check: http://$EXTERNAL_IP/api/system/health"
        echo "API Docs: http://$EXTERNAL_IP/docs"
        echo ""
        echo "Domain Access (when DNS configured):"
        echo "- https://diamond-sao.asoos.com"
        echo "- https://hr.asoos.com"
        echo "- https://admin.asoos.com"
    fi
    
    echo ""
    echo "💎 Diamond SAO Access: pr@coaching2100.com"
    echo "🔐 Classification: DIAMOND SAO ONLY"
}

# Main execution
main() {
    echo "🚀 Starting Diamond SAO cloud deployment..."
    
    check_prerequisites
    setup_gcp_access
    build_docker_image
    create_service_account
    deploy_to_kubernetes
    get_deployment_status
    
    echo ""
    log_success "✅ Diamond SAO HR AI CRMS System deployed to cloud!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Configure MongoDB connection in Kubernetes secrets"
    echo "2. Set up DNS records for your domains"
    echo "3. Configure SSL certificates"
    echo "4. Test the system with Diamond SAO credentials"
    echo ""
    echo "🔧 To update MongoDB connection:"
    echo "kubectl edit secret diamond-sao-cloud-secrets -n diamond-sao-system"
}

# Command handling
case "${1:-deploy}" in
    "build")
        check_prerequisites
        setup_gcp_access
        build_docker_image
        ;;
    "deploy")
        main
        ;;
    "status")
        setup_gcp_access
        get_deployment_status
        ;;
    *)
        echo "Usage: $0 [build|deploy|status]"
        echo "  build  - Only build and push Docker image"
        echo "  deploy - Full deployment (default)"
        echo "  status - Check deployment status"
        ;;
esac
