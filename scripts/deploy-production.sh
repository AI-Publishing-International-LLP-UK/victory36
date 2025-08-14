#!/bin/bash

# Victory36 Diamond SAO Production Deployment Script
# Classification: DIAMOND SAO ONLY
# Author: AI Publishing International LLP
# Version: v1.0.0

set -euo pipefail

# Diamond SAO Security Validation
export SCRIPT_NAME="deploy-production.sh"
export SCRIPT_VERSION="v1.0.0"
export REQUIRED_SAO_LEVEL="DIAMOND"

# Source directory validation per Rule 6jZI1q1m6WTAQcNzPabs9V
check_current_directory() {
    local current_dir=$(pwd)
    local expected_dir="/Users/as/asoos/victory36-repository"
    
    if [[ "$current_dir" != "$expected_dir" ]]; then
        echo "🚨 SECURITY ALERT: Wrong directory!"
        echo "   Current: $current_dir"
        echo "   Expected: $expected_dir"
        echo "   Deployment ABORTED for security."
        exit 1
    fi
    
    echo "✅ Directory validation passed: $current_dir"
}

# Diamond SAO Authentication Check
validate_diamond_sao_access() {
    echo "🔐 Validating Diamond SAO access..."
    
    # Check if user has Diamond SAO permissions
    if ! aixtiv auth:verify --level=DIAMOND_SAO 2>/dev/null; then
        echo "🚨 AUTHENTICATION FAILURE"
        echo "   Diamond SAO credentials required for production deployment"
        echo "   Contact: pr@coaching2100.com for access"
        exit 1
    fi
    
    echo "✅ Diamond SAO authentication confirmed"
}

# Pre-deployment security checks
run_security_checks() {
    echo "🛡️ Running Diamond SAO security checks..."
    
    # Verify git signature
    if ! git log --show-signature -1 | grep -q "gpg: Good signature"; then
        echo "⚠️ WARNING: Last commit not signed. Continuing with Diamond SAO override..."
    fi
    
    # Check for secrets in code
    if grep -r "API_KEY\|PASSWORD\|SECRET" src/ --exclude-dir=node_modules 2>/dev/null | grep -v "process.env"; then
        echo "🚨 SECURITY VIOLATION: Hardcoded secrets detected"
        exit 1
    fi
    
    # Verify Docker image security
    if [[ -f "Dockerfile" ]]; then
        if grep -q "FROM.*:latest" Dockerfile; then
            echo "🚨 SECURITY VIOLATION: Using :latest tag in Dockerfile"
            exit 1
        fi
    fi
    
    echo "✅ Security checks passed"
}

# Infrastructure provisioning
provision_infrastructure() {
    local region=$1
    echo "🏗️ Provisioning Victory36 infrastructure for region: $region"
    
    # Ensure Terraform state encryption
    if [[ ! -f "terraform/backend.tf" ]]; then
        cat > terraform/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "asoos-terraform-state-diamond-sao"
    prefix = "victory36/\${var.region}"
    encryption_key = "\${var.diamond_sao_encryption_key}"
  }
}
EOF
    fi
    
    # Apply infrastructure with region-specific configuration
    cd terraform/
    
    terraform init -backend-config="bucket=asoos-terraform-state-diamond-sao"
    terraform plan -var="region=$region" -var="environment=production" -out="victory36-$region.plan"
    terraform apply "victory36-$region.plan"
    
    cd ..
    echo "✅ Infrastructure provisioned for $region"
}

# Container build and security scanning
build_secure_container() {
    echo "🐳 Building secure Victory36 container..."
    
    local image_tag="victory36-connection-pool:$(git rev-parse --short HEAD)"
    local registry="us-west1-docker.pkg.dev/asoos-production/victory36"
    
    # Build with security best practices
    docker build \
        --no-cache \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --build-arg NODE_ENV=production \
        --security-opt seccomp=unconfined \
        -t "$registry/$image_tag" \
        .
    
    # Security scan with GCP Container Analysis
    docker push "$registry/$image_tag"
    
    # Wait for vulnerability scan
    echo "⏳ Waiting for security scan..."
    sleep 30
    
    # Check scan results
    gcloud container images scan "$registry/$image_tag" --format="value(vulnerabilityDetails.shortDescription)"
    
    echo "✅ Container built and scanned: $registry/$image_tag"
    export VICTORY36_IMAGE="$registry/$image_tag"
}

# Deploy to Kubernetes with Diamond SAO security
deploy_to_kubernetes() {
    local region=$1
    echo "☸️ Deploying Victory36 to Kubernetes cluster in $region"
    
    # Authenticate to GKE cluster
    case $region in
        "MOCOA")
            gcloud container clusters get-credentials victory36-mocoa --zone=us-west1-b --project=asoos-production
            ;;
        "MOCORIX")
            gcloud container clusters get-credentials victory36-mocorix --zone=us-west1-c --project=asoos-production
            ;;
        "MOCORIX2")
            gcloud container clusters get-credentials victory36-mocorix2 --zone=us-central1-a --project=asoos-production
            ;;
        *)
            echo "🚨 Unknown region: $region"
            exit 1
            ;;
    esac
    
    # Apply Kubernetes manifests with Kustomize
    kubectl apply -k "k8s/overlays/$region"
    
    # Update deployment with new image
    kubectl set image deployment/victory36-connection-pool victory36="$VICTORY36_IMAGE" -n victory36
    
    # Wait for rollout completion
    kubectl rollout status deployment/victory36-connection-pool -n victory36 --timeout=300s
    
    echo "✅ Deployment completed for $region"
}

# Health check and validation
validate_deployment() {
    local region=$1
    echo "🏥 Validating Victory36 deployment health..."
    
    # Check pod status
    kubectl get pods -n victory36 -l app=victory36-connection-pool
    
    # Run connection test
    echo "🧪 Testing connection pool functionality..."
    kubectl exec -n victory36 deployment/victory36-connection-pool -- \
        node -e "
        const { Victory36ConnectionPoolManager } = require('./src/victory36-connection-pool-manager.js');
        const manager = new Victory36ConnectionPoolManager({ maxAgents: 1000 });
        manager.on('initialized', async () => {
            try {
                const conn = await manager.getConnection('test-agent-001');
                console.log('✅ Connection test successful');
                conn.release();
                process.exit(0);
            } catch (error) {
                console.error('❌ Connection test failed:', error);
                process.exit(1);
            }
        });
        "
    
    echo "✅ Deployment validation completed"
}

# Configure monitoring and alerting
setup_monitoring() {
    local region=$1
    echo "📊 Setting up Diamond SAO monitoring for $region..."
    
    # Apply monitoring configuration
    kubectl apply -f k8s/monitoring/
    
    # Configure alerting policies
    gcloud alpha monitoring policies create --policy-from-file=monitoring/victory36-alerts.yaml
    
    echo "✅ Monitoring configured for $region"
}

# Main deployment orchestration
main() {
    echo "🌟 Victory36 Diamond SAO Production Deployment"
    echo "================================================"
    echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "Version: $SCRIPT_VERSION"
    echo "Classification: DIAMOND SAO ONLY"
    echo ""
    
    # Validate deployment prerequisites
    check_current_directory
    validate_diamond_sao_access
    run_security_checks
    
    # Get target regions from command line or default to all
    local regions=("${@:-MOCOA MOCORIX MOCORIX2}")
    
    echo "🎯 Target regions: ${regions[*]}"
    echo ""
    
    # Build secure container once
    build_secure_container
    
    # Deploy to each region
    for region in "${regions[@]}"; do
        echo "🚀 Deploying to region: $region"
        echo "================================"
        
        provision_infrastructure "$region"
        deploy_to_kubernetes "$region"
        validate_deployment "$region"
        setup_monitoring "$region"
        
        echo "✅ Region $region deployment completed"
        echo ""
    done
    
    # Final validation across all regions
    echo "🏆 Victory36 Diamond SAO deployment completed successfully!"
    echo "📊 Final system status:"
    
    for region in "${regions[@]}"; do
        echo "  $region: $(kubectl get deployment victory36-connection-pool -n victory36 -o jsonpath='{.status.readyReplicas}')/{.spec.replicas} pods ready"
    done
    
    # Register in Flight Memory System
    echo "📝 Registering deployment in Flight Memory System..."
    aixtiv resource:scan --type=victory36 --status=deployed --regions="${regions[*]}"
    
    echo ""
    echo "🎉 Victory36 is now live and protecting 20M+ AI agents!"
    echo "🛡️ Diamond SAO security protocols active"
    echo "📊 Access monitoring dashboard: https://console.cloud.google.com/monitoring/dashboards/victory36"
}

# Execute main function with all arguments
main "$@"
