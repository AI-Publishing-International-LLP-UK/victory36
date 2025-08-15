#!/bin/bash

# GCP MongoDB Atlas Configuration for Diamond SAO System
# Classification: Diamond SAO Only
# Project: api-for-warp-drive
# Purpose: Configure MongoDB Atlas on GCP for HR AI CRMS System

set -e

echo "🌐 GCP MongoDB Atlas Configuration"
echo "=================================="
echo "Project: api-for-warp-drive"
echo "Classification: Diamond SAO Only"
echo "=================================="

# Configuration
GCP_PROJECT="api-for-warp-drive"
DATABASE_NAME="hr_ai_crms_system"

# Colors for output
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

# Check GCP authentication
check_gcp_auth() {
    log_info "Checking GCP authentication..."
    
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1 > /dev/null 2>&1; then
        log_error "Not authenticated with GCP"
        echo "Please run: gcloud auth login"
        exit 1
    fi
    
    ACTIVE_ACCOUNT=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1)
    log_success "Authenticated as: $ACTIVE_ACCOUNT"
    
    # Verify project access
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [[ "$CURRENT_PROJECT" != "$GCP_PROJECT" ]]; then
        log_warning "Setting project to $GCP_PROJECT"
        gcloud config set project "$GCP_PROJECT"
    fi
    
    log_success "GCP Project: $CURRENT_PROJECT"
}

# Check for MongoDB Atlas integration
check_mongodb_atlas() {
    log_info "Checking MongoDB Atlas on GCP..."
    
    # Check if MongoDB Atlas is available in the project
    if gcloud services list --enabled --filter="name:mongodb" --format="value(name)" | grep -q mongodb; then
        log_success "MongoDB service found"
    else
        log_warning "MongoDB service not found in enabled services"
        log_info "Available MongoDB options:"
        echo "1. MongoDB Atlas (Third-party service)"
        echo "2. Self-managed MongoDB on Compute Engine"
        echo "3. MongoDB on Google Kubernetes Engine"
    fi
}

# Get MongoDB connection details
get_mongodb_details() {
    log_info "Getting MongoDB connection details..."
    
    # Check for existing MongoDB instances
    log_info "Checking for Compute Engine instances with MongoDB..."
    
    MONGO_INSTANCES=$(gcloud compute instances list --filter="name~mongodb OR labels.service=mongodb" --format="table(name,zone,status)" 2>/dev/null)
    
    if [[ -n "$MONGO_INSTANCES" ]]; then
        echo "Found MongoDB instances:"
        echo "$MONGO_INSTANCES"
    else
        log_warning "No MongoDB instances found on Compute Engine"
    fi
    
    # Check for GKE clusters that might be running MongoDB
    log_info "Checking for GKE clusters..."
    GKE_CLUSTERS=$(gcloud container clusters list --format="table(name,location,status)" 2>/dev/null)
    
    if [[ -n "$GKE_CLUSTERS" ]]; then
        echo "Found GKE clusters:"
        echo "$GKE_CLUSTERS"
        log_info "MongoDB might be running in one of these clusters"
    fi
}

# Generate MongoDB connection URI template
generate_connection_template() {
    log_info "Generating MongoDB connection template..."
    
    cat > mongodb_connection_template.env << 'EOF'
# MongoDB Atlas Connection Configuration
# Project: api-for-warp-drive
# Database: hr_ai_crms_system
# Classification: Diamond SAO Only

# Replace the following with your actual MongoDB Atlas connection details:

# Format for MongoDB Atlas on GCP:
# mongodb+srv://<username>:<password>@<cluster-name>.<region>.gcp.mongodb.net/<database>?retryWrites=true&w=majority

# Example:
# MONGODB_URI="mongodb+srv://diamond_sao_user:password@diamond-sao-cluster.us-west1.gcp.mongodb.net/hr_ai_crms_system?retryWrites=true&w=majority"

# Your connection string (fill in your details):
MONGODB_URI="mongodb+srv://username:password@cluster-name.region.gcp.mongodb.net/hr_ai_crms_system?retryWrites=true&w=majority"

# Database name
DATABASE_NAME="hr_ai_crms_system"

# Diamond SAO Configuration
DIAMOND_SAO_SECRET_KEY="your-diamond-sao-secret-key"

# GCP Project
GCP_PROJECT_ID="api-for-warp-drive"

EOF

    log_success "MongoDB connection template created: mongodb_connection_template.env"
    log_info "Please edit this file with your actual MongoDB Atlas connection details"
}

# Setup MongoDB collections and schema
setup_mongodb_schema() {
    if [[ -f "mongodb_connection_template.env" ]]; then
        source mongodb_connection_template.env
        
        if [[ "$MONGODB_URI" == *"username:password"* ]]; then
            log_warning "Please update mongodb_connection_template.env with your actual connection details"
            return
        fi
        
        log_info "Setting up MongoDB schema..."
        
        # Export environment variables
        export MONGODB_URI="$MONGODB_URI"
        export DATABASE_NAME="$DATABASE_NAME"
        
        # Run the MongoDB schema setup
        source diamond_sao_env/bin/activate
        python3 mongodb_schema_setup.py
        
        log_success "MongoDB schema setup completed"
    else
        log_error "mongodb_connection_template.env not found"
    fi
}

# Start Diamond SAO system with MongoDB
start_diamond_sao_system() {
    if [[ -f "mongodb_connection_template.env" ]]; then
        log_info "Starting Diamond SAO system with MongoDB integration..."
        
        source mongodb_connection_template.env
        
        if [[ "$MONGODB_URI" == *"username:password"* ]]; then
            log_warning "Starting in demo mode - please configure MongoDB connection"
            log_info "Edit mongodb_connection_template.env with your MongoDB Atlas details"
        fi
        
        # Export environment variables
        export MONGODB_URI="$MONGODB_URI"
        export DATABASE_NAME="$DATABASE_NAME"
        export DIAMOND_SAO_SECRET_KEY="$DIAMOND_SAO_SECRET_KEY"
        export GCP_PROJECT_ID="$GCP_PROJECT_ID"
        
        # Start the system
        source diamond_sao_env/bin/activate
        echo "🚀 Starting Diamond SAO HR AI CRMS System..."
        python3 diamond_sao_hr_crms_system.py &
        
        sleep 3
        
        # Check if system is running
        if pgrep -f "diamond_sao_hr_crms_system.py" > /dev/null; then
            log_success "Diamond SAO system is running!"
            echo ""
            echo "🌐 Access URLs:"
            echo "   Admin Interface: http://localhost:8003/admin"
            echo "   Health Check: http://localhost:8003/api/system/health"
            echo "   API Documentation: http://localhost:8003/docs"
            echo ""
            echo "💎 Diamond SAO Access: pr@coaching2100.com"
            echo ""
        else
            log_error "Failed to start Diamond SAO system"
        fi
    else
        log_error "Configuration file not found"
    fi
}

# Main execution
main() {
    check_gcp_auth
    check_mongodb_atlas
    get_mongodb_details
    generate_connection_template
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Edit mongodb_connection_template.env with your MongoDB Atlas connection details"
    echo "2. Run: ./gcp_mongodb_config.sh setup_schema"
    echo "3. Run: ./gcp_mongodb_config.sh start_system"
    echo ""
    echo "🔐 For MongoDB Atlas setup on GCP:"
    echo "   - Go to MongoDB Atlas console"
    echo "   - Create cluster in GCP region (e.g., us-west1)"
    echo "   - Get connection string"
    echo "   - Update mongodb_connection_template.env"
}

# Command handling
case "${1:-main}" in
    "setup_schema")
        setup_mongodb_schema
        ;;
    "start_system")
        start_diamond_sao_system
        ;;
    *)
        main
        ;;
esac
