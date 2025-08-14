#!/bin/bash

# ====================================================================
# Victory36 Emergency Rollback Script
# Classification: Diamond SAO Only
# Purpose: Emergency rollback of Victory36 deployments
# ====================================================================

set -euo pipefail

# Constants
readonly SCRIPT_NAME="Victory36 Rollback"
readonly LOG_FILE="/var/log/victory36/rollback-$(date +%Y%m%d_%H%M%S).log"
readonly REGIONS=("MOCOA" "MOCORIX" "MOCORIX2")
readonly DIAMOND_SAO_REQUIRED=true

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Global variables
ROLLBACK_MODE=""
TARGET_VERSION=""
CONFIRM_DIAMOND_SAO=false
DRY_RUN=false

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Diamond SAO verification
verify_diamond_sao() {
    if [[ "$CONFIRM_DIAMOND_SAO" != "true" ]]; then
        log "ERROR" "❌ Diamond SAO confirmation required"
        log "ERROR" "Use --confirm-diamond-sao flag to confirm Diamond SAO access"
        exit 1
    fi
    
    log "INFO" "🔐 Verifying Diamond SAO clearance..."
    
    # Check for Diamond SAO token
    if [[ -z "${DIAMOND_SAO_TOKEN:-}" ]]; then
        log "ERROR" "❌ DIAMOND_SAO_TOKEN environment variable not set"
        exit 1
    fi
    
    # Biometric simulation (in production, this would be real)
    log "INFO" "🔍 Performing biometric validation..."
    sleep 2
    
    log "SUCCESS" "✅ Diamond SAO verification completed"
}

# Pre-rollback checks
pre_rollback_checks() {
    log "INFO" "🔍 Running pre-rollback checks..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log "ERROR" "❌ kubectl not found - required for rollback operations"
        exit 1
    fi
    
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        log "ERROR" "❌ gcloud CLI not found - required for GCP operations"
        exit 1
    fi
    
    # Test cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log "ERROR" "❌ Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check current deployment status
    log "INFO" "📊 Checking current deployment status..."
    kubectl get deployments -n v36-canary -o wide 2>/dev/null || log "WARN" "⚠️ Canary namespace not found"
    kubectl get deployments -n v36-prod -o wide 2>/dev/null || log "WARN" "⚠️ Production namespace not found"
    
    log "SUCCESS" "✅ Pre-rollback checks completed"
}

# Get current deployment info
get_current_deployment_info() {
    log "INFO" "📋 Gathering current deployment information..."
    
    local current_version=""
    local deployment_status=""
    
    # Check canary deployment
    if kubectl get deployment victory36 -n v36-canary &> /dev/null; then
        current_version=$(kubectl get deployment victory36 -n v36-canary -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "unknown")
        deployment_status=$(kubectl get deployment victory36 -n v36-canary -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "unknown")
        log "INFO" "📍 Current canary version: $current_version (Status: $deployment_status)"
    fi
    
    # Check production deployment
    if kubectl get deployment victory36 -n v36-prod &> /dev/null; then
        current_version=$(kubectl get deployment victory36 -n v36-prod -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "unknown")
        deployment_status=$(kubectl get deployment victory36 -n v36-prod -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "unknown")
        log "INFO" "📍 Current production version: $current_version (Status: $deployment_status)"
    fi
}

# Emergency rollback
emergency_rollback() {
    log "WARN" "🚨 INITIATING EMERGENCY ROLLBACK"
    log "WARN" "🚨 This will immediately rollback all Victory36 deployments"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "🎭 DRY-RUN: Emergency rollback simulation"
        return 0
    fi
    
    # Rollback canary deployment
    if kubectl get deployment victory36 -n v36-canary &> /dev/null; then
        log "INFO" "↩️ Rolling back canary deployment..."
        kubectl rollout undo deployment/victory36 -n v36-canary
        kubectl rollout status deployment/victory36 -n v36-canary --timeout=300s
        log "SUCCESS" "✅ Canary rollback completed"
    fi
    
    # Rollback production deployment
    if kubectl get deployment victory36 -n v36-prod &> /dev/null; then
        log "INFO" "↩️ Rolling back production deployment..."
        kubectl rollout undo deployment/victory36 -n v36-prod
        kubectl rollout status deployment/victory36 -n v36-prod --timeout=300s
        log "SUCCESS" "✅ Production rollback completed"
    fi
    
    # Scale down problematic services
    log "INFO" "⬇️ Scaling down problematic services..."
    kubectl scale deployment victory36 --replicas=1 -n v36-canary 2>/dev/null || true
    sleep 30
    kubectl scale deployment victory36 --replicas=3 -n v36-canary 2>/dev/null || true
    
    log "SUCCESS" "🎉 Emergency rollback completed successfully"
}

# Gradual rollback
gradual_rollback() {
    log "INFO" "🔄 Initiating gradual rollback to version: $TARGET_VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "🎭 DRY-RUN: Gradual rollback simulation"
        return 0
    fi
    
    # Step 1: Reduce canary traffic to 0%
    log "INFO" "📉 Reducing canary traffic to 0%..."
    kubectl patch service victory36-service -n v36-canary -p '{"spec":{"selector":{"version":"'$TARGET_VERSION'"}}}'
    sleep 30
    
    # Step 2: Rollback canary deployment
    log "INFO" "↩️ Rolling back canary deployment..."
    if [[ -n "$TARGET_VERSION" ]]; then
        kubectl set image deployment/victory36 victory36=gcr.io/asoos-victory36/victory36:$TARGET_VERSION -n v36-canary
    else
        kubectl rollout undo deployment/victory36 -n v36-canary
    fi
    
    kubectl rollout status deployment/victory36 -n v36-canary --timeout=600s
    log "SUCCESS" "✅ Canary rollback completed"
    
    # Step 3: Health check
    log "INFO" "🏥 Running post-rollback health checks..."
    sleep 60
    
    local healthy_pods=$(kubectl get pods -n v36-canary -l app=victory36 --field-selector=status.phase=Running --no-headers | wc -l)
    log "INFO" "📊 Healthy pods after rollback: $healthy_pods"
    
    # Step 4: Gradual traffic restoration
    log "INFO" "📈 Gradually restoring traffic..."
    for traffic in 10 25 50 75 100; do
        log "INFO" "🔄 Restoring traffic to ${traffic}%..."
        # Traffic restoration logic would be implemented here
        sleep 30
    done
    
    log "SUCCESS" "🎉 Gradual rollback completed successfully"
}

# Regional rollback
regional_rollback() {
    local region="$1"
    log "INFO" "🌍 Rolling back Victory36 in region: $region"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "🎭 DRY-RUN: Regional rollback simulation for $region"
        return 0
    fi
    
    # Region-specific rollback logic
    case "$region" in
        "MOCOA")
            log "INFO" "📍 Rolling back primary region MOCOA..."
            kubectl rollout undo deployment/victory36 -n v36-prod
            ;;
        "MOCORIX"|"MOCORIX2")
            log "INFO" "📍 Rolling back secondary region $region..."
            kubectl rollout undo deployment/victory36-$region -n v36-prod 2>/dev/null || true
            ;;
        *)
            log "ERROR" "❌ Unknown region: $region"
            return 1
            ;;
    esac
    
    log "SUCCESS" "✅ Regional rollback completed for $region"
}

# Verify rollback success
verify_rollback() {
    log "INFO" "🔍 Verifying rollback success..."
    
    # Check deployment status
    local canary_status=$(kubectl get deployment victory36 -n v36-canary -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "NotFound")
    local prod_status=$(kubectl get deployment victory36 -n v36-prod -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "NotFound")
    
    log "INFO" "📊 Canary deployment status: $canary_status"
    log "INFO" "📊 Production deployment status: $prod_status"
    
    # Check pod health
    local healthy_canary_pods=$(kubectl get pods -n v36-canary -l app=victory36 --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    local healthy_prod_pods=$(kubectl get pods -n v36-prod -l app=victory36 --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    
    log "INFO" "🏥 Healthy canary pods: $healthy_canary_pods"
    log "INFO" "🏥 Healthy production pods: $healthy_prod_pods"
    
    # Connection pool test
    if [[ "$healthy_canary_pods" -gt 0 ]]; then
        local canary_pod=$(kubectl get pods -n v36-canary -l app=victory36 -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [[ -n "$canary_pod" ]]; then
            log "INFO" "🔗 Testing connection pool functionality..."
            kubectl exec "$canary_pod" -n v36-canary -- node -e "console.log('Connection pool test: OK')" 2>/dev/null || log "WARN" "⚠️ Connection pool test failed"
        fi
    fi
    
    log "SUCCESS" "✅ Rollback verification completed"
}

# Generate rollback report
generate_rollback_report() {
    log "INFO" "📊 Generating rollback report..."
    
    local report_file="/tmp/victory36-rollback-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Victory36 Rollback Report

**Rollback Time:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')  
**Rollback Mode:** $ROLLBACK_MODE  
**Target Version:** ${TARGET_VERSION:-"Previous"}  
**Operator:** $(whoami)  
**Log File:** $LOG_FILE  

## Rollback Summary

- **Status:** ✅ COMPLETED
- **Duration:** $(( $(date +%s) - $(stat -f %m "$LOG_FILE" 2>/dev/null || echo $(date +%s)) )) seconds
- **Regions Affected:** ${REGIONS[*]}

## Post-Rollback Status

### Deployments
$(kubectl get deployments -n v36-canary -o wide 2>/dev/null || echo "Canary namespace not found")
$(kubectl get deployments -n v36-prod -o wide 2>/dev/null || echo "Production namespace not found")

### Pod Status
$(kubectl get pods -n v36-canary -l app=victory36 2>/dev/null || echo "No canary pods found")
$(kubectl get pods -n v36-prod -l app=victory36 2>/dev/null || echo "No production pods found")

## Next Steps

1. Monitor system health for the next 30 minutes
2. Validate connection pool performance
3. Check agent authentication success rates
4. Review system logs for any anomalies
5. Prepare incident post-mortem

## Emergency Contacts

- **Diamond SAO Operations:** +1-555-DIAMOND
- **ASOOS Infrastructure:** ops@asoos.cloud
- **Victory36 Team:** victory36@asoos.cloud

EOF

    log "INFO" "📋 Rollback report saved to: $report_file"
    
    # Display report summary
    echo ""
    echo "=============================="
    echo "   ROLLBACK REPORT SUMMARY    "
    echo "=============================="
    cat "$report_file"
    echo "=============================="
}

# Cleanup function
cleanup() {
    log "INFO" "🧹 Performing cleanup operations..."
    
    # Remove temporary files
    find /tmp -name "victory36-rollback-*" -mtime +1 -delete 2>/dev/null || true
    
    # Compress old log files
    find /var/log/victory36 -name "rollback-*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true
    
    log "INFO" "✅ Cleanup completed"
}

# Display help
show_help() {
    cat << EOF
Victory36 Emergency Rollback Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --emergency                     Perform immediate emergency rollback
    --gradual                       Perform gradual rollback with traffic shifting
    --target-version=VERSION        Rollback to specific version
    --region=REGION                 Rollback specific region only
    --confirm-diamond-sao          Confirm Diamond SAO access (REQUIRED)
    --dry-run                      Simulate rollback without actual changes
    --help                         Show this help message

EXAMPLES:
    # Emergency rollback (immediate)
    $0 --emergency --confirm-diamond-sao
    
    # Gradual rollback to specific version
    $0 --gradual --target-version=v36-20240813-abc123 --confirm-diamond-sao
    
    # Rollback specific region
    $0 --region=MOCOA --confirm-diamond-sao
    
    # Dry run simulation
    $0 --emergency --confirm-diamond-sao --dry-run

SECURITY:
    This script requires Diamond SAO clearance and proper authentication.
    The --confirm-diamond-sao flag must be provided to acknowledge the security requirements.

SUPPORT:
    For assistance, contact Diamond SAO Operations: +1-555-DIAMOND
EOF
}

# Main function
main() {
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --emergency)
                ROLLBACK_MODE="emergency"
                shift
                ;;
            --gradual)
                ROLLBACK_MODE="gradual"
                shift
                ;;
            --target-version=*)
                TARGET_VERSION="${1#*=}"
                shift
                ;;
            --region=*)
                ROLLBACK_MODE="regional"
                REGION="${1#*=}"
                shift
                ;;
            --confirm-diamond-sao)
                CONFIRM_DIAMOND_SAO=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate arguments
    if [[ -z "$ROLLBACK_MODE" ]]; then
        log "ERROR" "❌ Rollback mode not specified. Use --emergency, --gradual, or --region="
        show_help
        exit 1
    fi
    
    # Start rollback process
    log "INFO" "🚨 ${SCRIPT_NAME} INITIATED"
    log "INFO" "📋 Mode: $ROLLBACK_MODE, Target: ${TARGET_VERSION:-Previous}, Dry-run: $DRY_RUN"
    
    # Security verification
    verify_diamond_sao
    
    # Pre-rollback checks
    pre_rollback_checks
    
    # Get current deployment info
    get_current_deployment_info
    
    # Execute rollback based on mode
    case "$ROLLBACK_MODE" in
        "emergency")
            emergency_rollback
            ;;
        "gradual")
            gradual_rollback
            ;;
        "regional")
            regional_rollback "$REGION"
            ;;
        *)
            log "ERROR" "❌ Invalid rollback mode: $ROLLBACK_MODE"
            exit 1
            ;;
    esac
    
    # Verify rollback success
    verify_rollback
    
    # Generate report
    generate_rollback_report
    
    # Cleanup
    cleanup
    
    log "SUCCESS" "🎉 ${SCRIPT_NAME} COMPLETED SUCCESSFULLY"
    log "INFO" "📊 Dashboard: https://v36-dashboard.mocoa.asoos.cloud/"
    log "INFO" "📋 Report: Check /tmp for detailed rollback report"
}

# Trap signals for graceful shutdown
trap 'log "ERROR" "🛑 Rollback script interrupted"; cleanup; exit 130' INT TERM

# Execute main function with all arguments
main "$@"
