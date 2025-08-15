#!/bin/bash

# Victory36 Production Readiness Verification
# Classification: DIAMOND SAO ONLY
# Purpose: Comprehensive pre-deployment validation

set -euo pipefail

# Diamond SAO verification functions
export SCRIPT_NAME="verify-production-readiness.sh"
export VERIFICATION_VERSION="v1.0.0"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verification results
declare -a PASSED_CHECKS=()
declare -a FAILED_CHECKS=()
declare -a WARNING_CHECKS=()

# Directory validation per Rule 6jZI1q1m6WTAQcNzPabs9V
check_current_directory() {
    local current_dir=$(pwd)
    local expected_dir="/Users/as/asoos/victory36-repository"
    
    if [[ "$current_dir" != "$expected_dir" ]]; then
        echo -e "${RED}🚨 CRITICAL: Wrong directory!${NC}"
        echo "   Current: $current_dir"
        echo "   Expected: $expected_dir"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Directory validation passed${NC}"
}

# Verification function template
verify_check() {
    local check_name="$1"
    local check_command="$2"
    local is_critical="${3:-false}"
    
    echo -n "🔍 Checking $check_name... "
    
    if eval "$check_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS+=("$check_name")
        return 0
    else
        if [[ "$is_critical" == "true" ]]; then
            echo -e "${RED}❌ FAIL (CRITICAL)${NC}"
            FAILED_CHECKS+=("$check_name")
            return 1
        else
            echo -e "${YELLOW}⚠️  WARNING${NC}"
            WARNING_CHECKS+=("$check_name")
            return 2
        fi
    fi
}

# Critical system checks
check_diamond_sao_authentication() {
    echo -e "\n${BLUE}🔐 Diamond SAO Authentication Checks${NC}"
    echo "========================================"
    
    verify_check "Diamond SAO CLI Access" "aixtiv auth:verify --level=DIAMOND_SAO" true
    verify_check "SallyPort Victory33 Active" "pgrep -f 'sallyport.*victory33'" false
    verify_check "Aixtiv CLI Functional" "aixtiv --version" true
}

# Infrastructure readiness
check_infrastructure() {
    echo -e "\n${BLUE}🏗️ Infrastructure Readiness${NC}"
    echo "=============================="
    
    verify_check "GCP Project Access" "gcloud config get-value project | grep -q asoos-production" true
    verify_check "GKE Clusters Available" "gcloud container clusters list --format='value(name)' | grep -E '(mocoa|mocorix)'" true
    verify_check "Terraform Installed" "terraform --version" true
    verify_check "Docker Daemon Running" "docker info" true
    verify_check "Kubectl Configured" "kubectl version --client" true
}

# Security validation
check_security() {
    echo -e "\n${BLUE}🛡️ Security Configuration${NC}"
    echo "=========================="
    
    verify_check "No Hardcoded Secrets" "! grep -r 'API_KEY\\|PASSWORD\\|SECRET' src/ --exclude-dir=node_modules | grep -v 'process.env'" true
    verify_check "Dockerfile Security" "! grep -q 'FROM.*:latest' Dockerfile" true
    verify_check "Git Signing Configured" "git config user.signingkey" false
    verify_check "SSH Keys Secure" "[[ -f ~/.ssh/id_rsa ]] && [[ \$(stat -c '%a' ~/.ssh/id_rsa) == '600' ]]" false
}

# Code quality validation
check_code_quality() {
    echo -e "\n${BLUE}📝 Code Quality Validation${NC}"
    echo "==========================="
    
    verify_check "ESLint Passes" "npm run lint" true
    verify_check "Tests Pass" "npm test" true
    verify_check "Package Vulnerabilities" "npm audit --audit-level=moderate" false
    verify_check "TypeScript Compilation" "[[ ! -f tsconfig.json ]] || npm run build" false
}

# Victory36 specific checks
check_victory36_config() {
    echo -e "\n${BLUE}🎯 Victory36 Configuration${NC}"
    echo "============================"
    
    verify_check "Connection Pool Manager Exists" "[[ -f src/victory36-connection-pool-manager.js ]]" true
    verify_check "Deployment Script Executable" "[[ -x scripts/deploy-production.sh ]]" true
    verify_check "Terraform Configuration Valid" "cd terraform && terraform validate" true
    verify_check "Kubernetes Manifests Valid" "kubectl apply --dry-run=client -k k8s/base/" true
    verify_check "Docker Build Works" "docker build --no-cache -t victory36-test:latest ." false
}

# Monitoring and observability
check_monitoring() {
    echo -e "\n${BLUE}📊 Monitoring and Observability${NC}"
    echo "================================="
    
    verify_check "Prometheus Config" "[[ -f monitoring/victory36-alerts.yaml ]]" false
    verify_check "Health Endpoints" "grep -q '/health' src/victory36-connection-pool-manager.js" false
    verify_check "Metrics Collection" "grep -q 'prometheus\\|metrics' package.json" false
}

# Load testing capabilities
check_load_testing() {
    echo -e "\n${BLUE}🚀 Load Testing Readiness${NC}"
    echo "=========================="
    
    verify_check "Load Testing Tools" "command -v locust || npm list -g artillery" false
    verify_check "20M Agent Configuration" "grep -q '20000000\\|MAX_AGENTS' src/victory36-connection-pool-manager.js" true
    verify_check "Multi-Region Support" "grep -q 'MOCOA\\|MOCORIX' src/victory36-connection-pool-manager.js" true
}

# Network and connectivity
check_network() {
    echo -e "\n${BLUE}🌐 Network and Connectivity${NC}"
    echo "============================"
    
    verify_check "GCP API Access" "gcloud auth list --filter=status:ACTIVE --format='value(account)'" true
    verify_check "Docker Registry Access" "gcloud auth configure-docker us-west1-docker.pkg.dev" false
    verify_check "Cluster Connectivity" "kubectl cluster-info" false
    verify_check "DNS Resolution" "nslookup google.com" false
}

# Generate verification report
generate_report() {
    echo -e "\n${BLUE}📋 Victory36 Production Readiness Report${NC}"
    echo "==========================================="
    echo "Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo "Version: $VERIFICATION_VERSION"
    echo "Classification: DIAMOND SAO"
    echo ""
    
    echo -e "${GREEN}✅ PASSED CHECKS (${#PASSED_CHECKS[@]}):${NC}"
    for check in "${PASSED_CHECKS[@]}"; do
        echo "   ✓ $check"
    done
    echo ""
    
    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  WARNING CHECKS (${#WARNING_CHECKS[@]}):${NC}"
        for check in "${WARNING_CHECKS[@]}"; do
            echo "   ⚠ $check"
        done
        echo ""
    fi
    
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        echo -e "${RED}❌ FAILED CHECKS (${#FAILED_CHECKS[@]}):${NC}"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "   ✗ $check"
        done
        echo ""
        
        echo -e "${RED}🚨 DEPLOYMENT BLOCKED${NC}"
        echo "Critical checks failed. Victory36 is NOT ready for production."
        echo "Please resolve the failed checks before proceeding."
        return 1
    fi
    
    local total_checks=$((${#PASSED_CHECKS[@]} + ${#WARNING_CHECKS[@]} + ${#FAILED_CHECKS[@]}))
    local success_rate=$(( (${#PASSED_CHECKS[@]} * 100) / total_checks ))
    
    echo -e "${GREEN}📊 OVERALL STATUS${NC}"
    echo "================="
    echo "Total Checks: $total_checks"
    echo "Success Rate: $success_rate%"
    echo ""
    
    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  PRODUCTION READY WITH WARNINGS${NC}"
        echo "Victory36 can be deployed but some optimizations are recommended."
    else
        echo -e "${GREEN}🎉 FULLY PRODUCTION READY${NC}"
        echo "Victory36 is ready for Diamond SAO production deployment!"
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. Run: ./scripts/deploy-production.sh MOCOA"
    echo "2. Monitor: kubectl get pods -n victory36 -w"
    echo "3. Validate: aixtiv resource:scan --type=victory36 --status=deployed"
    
    return 0
}

# Main verification workflow
main() {
    echo -e "${BLUE}🌟 Victory36 Diamond SAO Production Readiness Verification${NC}"
    echo "=========================================================="
    echo "Starting comprehensive readiness validation..."
    echo ""
    
    check_current_directory
    
    # Run all verification checks
    check_diamond_sao_authentication
    check_infrastructure
    check_security
    check_code_quality
    check_victory36_config
    check_monitoring
    check_load_testing
    check_network
    
    # Generate final report
    generate_report
    
    # Store results
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="verification-results-$timestamp.log"
    
    # Save detailed results
    {
        echo "Victory36 Production Readiness Verification"
        echo "==========================================="
        echo "Timestamp: $(date -u)"
        echo "Passed: ${#PASSED_CHECKS[@]}"
        echo "Warnings: ${#WARNING_CHECKS[@]}"
        echo "Failed: ${#FAILED_CHECKS[@]}"
        echo ""
        echo "Passed Checks:"
        printf '%s\n' "${PASSED_CHECKS[@]}"
        echo ""
        echo "Warning Checks:"
        printf '%s\n' "${WARNING_CHECKS[@]}"
        echo ""
        echo "Failed Checks:"
        printf '%s\n' "${FAILED_CHECKS[@]}"
    } > "$report_file"
    
    echo ""
    echo "📄 Detailed results saved to: $report_file"
    
    # Exit with appropriate code
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        exit 1
    elif [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        exit 2
    else
        exit 0
    fi
}

# Execute main function
main "$@"
