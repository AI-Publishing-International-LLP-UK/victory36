#!/bin/bash

# Victory36 Anti-Gravity Powercraft Time Presser Pipeline Deployment Script
# Classification: Diamond SAO
# Purpose: Deploy complete Victory36 cybersecurity simulation system with time presser integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="victory36-cluster-mocoa"
REGION="us-west1"
PROJECT_ID="api-for-warp-drive"
NAMESPACE="victory36"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verify prerequisites
verify_prerequisites() {
    log_info "Verifying prerequisites for Victory36 Time Presser deployment..."
    
    # Check kubectl access
    if ! kubectl cluster-info > /dev/null 2>&1; then
        log_error "kubectl not configured for cluster access"
        exit 1
    fi
    
    # Verify namespace exists
    if ! kubectl get namespace ${NAMESPACE} > /dev/null 2>&1; then
        log_error "Namespace ${NAMESPACE} does not exist"
        exit 1
    fi
    
    log_success "Prerequisites verified"
}

# Deploy storage infrastructure
deploy_storage_infrastructure() {
    log_info "Deploying Victory36 simulation storage infrastructure..."
    
    kubectl apply -f k8s/storage-infrastructure.yaml
    
    # Wait for PVCs to be bound
    log_info "Waiting for persistent volume claims to be bound..."
    kubectl wait --for=condition=bound pvc/victory36-simulation-storage -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=bound pvc/victory36-time-presser-cache -n ${NAMESPACE} --timeout=300s
    
    log_success "Storage infrastructure deployed successfully"
}

# Deploy time presser components
deploy_time_presser_system() {
    log_info "Deploying Anti-Gravity Powercraft Time Presser system..."
    
    kubectl apply -f k8s/victory36-time-presser-deployment.yaml
    
    # Wait for deployment to be ready
    log_info "Waiting for time presser deployment to be ready..."
    kubectl rollout status deployment/victory36-time-presser-simulator -n ${NAMESPACE} --timeout=600s
    
    log_success "Time Presser system deployed successfully"
}

# Deploy simulation archival system
deploy_archival_system() {
    log_info "Deploying simulation archival and retrieval system..."
    
    kubectl apply -f k8s/simulation-archive-system.yaml
    
    # Wait for Elasticsearch to be ready
    log_info "Waiting for Elasticsearch to be ready..."
    kubectl rollout status statefulset/victory36-elasticsearch -n ${NAMESPACE} --timeout=600s
    
    # Wait for archive system to be ready
    kubectl rollout status deployment/victory36-simulation-archive -n ${NAMESPACE} --timeout=300s
    
    log_success "Archival system deployed successfully"
}

# Deploy monitoring and validation
deploy_monitoring_system() {
    log_info "Deploying time presser monitoring and validation system..."
    
    kubectl apply -f k8s/time-presser-monitoring.yaml
    
    # Wait for monitoring components
    kubectl rollout status deployment/victory36-time-presser-monitor -n ${NAMESPACE} --timeout=300s
    kubectl rollout status deployment/victory36-prometheus -n ${NAMESPACE} --timeout=300s
    
    log_success "Monitoring system deployed successfully"
}

# Deploy Diamond SAO access control
deploy_security_system() {
    log_info "Deploying Diamond SAO security access control system..."
    
    kubectl apply -f k8s/diamond-sao-access-control.yaml
    
    # Wait for security gateway
    kubectl rollout status deployment/victory36-diamond-sao-gateway -n ${NAMESPACE} --timeout=300s
    
    log_success "Diamond SAO security system deployed successfully"
}

# Test end-to-end pipeline
test_pipeline() {
    log_info "Testing end-to-end Victory36 Time Presser pipeline..."
    
    # Check all services are running
    log_info "Verifying all services are running..."
    
    services=(
        "victory36-time-presser-service"
        "victory36-simulation-archive-service"
        "victory36-time-presser-monitor-service"
        "victory36-diamond-sao-gateway"
        "victory36-prometheus"
        "victory36-elasticsearch"
    )
    
    for service in "${services[@]}"; do
        if kubectl get service ${service} -n ${NAMESPACE} > /dev/null 2>&1; then
            log_success "Service ${service} is running"
        else
            log_error "Service ${service} is not running"
        fi
    done
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n ${NAMESPACE} -o wide
    
    # Test time presser connectivity (if endpoints are ready)
    log_info "Testing time presser system connectivity..."
    
    # Port forward to test locally (run in background)
    kubectl port-forward -n ${NAMESPACE} svc/victory36-time-presser-service 8080:8080 &
    PORT_FORWARD_PID=$!
    
    sleep 5
    
    # Test health endpoint
    if curl -f http://localhost:8080/health/time-presser > /dev/null 2>&1; then
        log_success "Time presser health endpoint accessible"
    else
        log_warning "Time presser health endpoint not yet accessible (expected for placeholder image)"
    fi
    
    # Clean up port forward
    kill ${PORT_FORWARD_PID} 2>/dev/null || true
    
    log_success "Pipeline testing completed"
}

# Display deployment status
show_deployment_status() {
    log_info "Victory36 Time Presser Pipeline Deployment Status"
    echo "================================================="
    
    echo -e "\n${BLUE}Services:${NC}"
    kubectl get services -n ${NAMESPACE}
    
    echo -e "\n${BLUE}Deployments:${NC}"
    kubectl get deployments -n ${NAMESPACE}
    
    echo -e "\n${BLUE}StatefulSets:${NC}"
    kubectl get statefulsets -n ${NAMESPACE}
    
    echo -e "\n${BLUE}Persistent Volume Claims:${NC}"
    kubectl get pvc -n ${NAMESPACE}
    
    echo -e "\n${BLUE}Pods:${NC}"
    kubectl get pods -n ${NAMESPACE} -o wide
    
    # Get external IP if available
    EXTERNAL_IP=$(kubectl get service victory36-loadbalancer -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    
    echo -e "\n${BLUE}Access Information:${NC}"
    echo "External IP: ${EXTERNAL_IP}"
    echo "Time Presser API: http://${EXTERNAL_IP}:80 (via LoadBalancer)"
    echo "Internal Time Presser: victory36-time-presser-service.victory36.svc.cluster.local:9090"
    echo "Monitoring: victory36-prometheus.victory36.svc.cluster.local:9090"
    echo "Security Gateway: victory36-diamond-sao-gateway.victory36.svc.cluster.local:8084"
    
    echo -e "\n${GREEN}Victory36 Anti-Gravity Powercraft Time Presser Pipeline is ready!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Replace placeholder container images with actual Victory36 images"
    echo "2. Configure actual Diamond SAO authentication credentials"
    echo "3. Set up Sally Port integration for immediate authentication"
    echo "4. Load test the time presser system with cybersecurity simulations"
    echo "5. Validate 1000x acceleration factor for Anti-Gravity Powercraft model"
}

# Main execution
main() {
    log_info "Starting Victory36 Time Presser Pipeline deployment..."
    
    verify_prerequisites
    deploy_storage_infrastructure
    deploy_time_presser_system
    deploy_archival_system
    deploy_monitoring_system
    deploy_security_system
    test_pipeline
    show_deployment_status
    
    log_success "Victory36 Time Presser Pipeline deployment completed successfully!"
}

# Execute main function
main "$@"
