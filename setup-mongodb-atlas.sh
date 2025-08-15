#!/bin/bash
set -e

# =================================================================================================
# MongoDB Atlas Setup Guide for ASOOS Production
# =================================================================================================
# 
# This script helps you create a MongoDB Atlas cluster and get the connection URI
# for your ASOOS production systems.
#
# Author: Aixtiv Symphony Architecture Team
# Classification: Diamond SAO Production Setup
# =================================================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================================================${NC}"
echo -e "${WHITE}🍃 MongoDB Atlas Setup for ASOOS Production${NC}"
echo -e "${BLUE}===================================================================================${NC}"

print_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# =================================================================================================
# MONGODB ATLAS SETUP INSTRUCTIONS
# =================================================================================================

print_section "MongoDB Atlas Setup Instructions"

cat << EOF
${WHITE}We'll help you create a MongoDB Atlas cluster for your ASOOS production systems.${NC}

${CYAN}OPTION 1: Quick Setup (Recommended)${NC}
I can help you create a MongoDB Atlas cluster automatically if you have the MongoDB CLI installed.

${CYAN}OPTION 2: Manual Setup${NC}
I'll guide you through the web interface step-by-step.

EOF

read -p "Do you have MongoDB Atlas CLI installed? (y/N): " HAS_ATLAS_CLI

if [[ $HAS_ATLAS_CLI =~ ^[Yy]$ ]]; then
    print_section "Option 1: Automated MongoDB Atlas Setup"
    
    print_step "Checking MongoDB Atlas CLI..."
    if command -v atlas >/dev/null 2>&1; then
        print_success "MongoDB Atlas CLI found!"
        
        print_step "Logging into MongoDB Atlas..."
        echo -e "${YELLOW}Please follow the authentication prompts...${NC}"
        atlas auth login
        
        if [ $? -eq 0 ]; then
            print_success "Successfully authenticated with MongoDB Atlas!"
            
            # List existing projects
            print_step "Checking for existing projects..."
            atlas projects list
            
            echo -e "\n${CYAN}Would you like to:${NC}"
            echo "1. Create a new project for ASOOS"
            echo "2. Use an existing project"
            read -p "Choose option (1 or 2): " PROJECT_OPTION
            
            if [[ $PROJECT_OPTION == "1" ]]; then
                read -p "Enter project name (e.g., ASOOS-Production): " PROJECT_NAME
                PROJECT_NAME=${PROJECT_NAME:-"ASOOS-Production"}
                
                print_step "Creating new project: $PROJECT_NAME"
                PROJECT_ID=$(atlas projects create "$PROJECT_NAME" --output json | jq -r '.id')
                
                if [[ -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]]; then
                    print_success "Created project: $PROJECT_NAME (ID: $PROJECT_ID)"
                else
                    print_warning "Failed to create project. Please create manually."
                    PROJECT_ID=""
                fi
            else
                read -p "Enter existing project ID: " PROJECT_ID
            fi
            
            if [[ -n "$PROJECT_ID" ]]; then
                print_step "Creating MongoDB cluster..."
                
                CLUSTER_NAME="asoos-prod-cluster"
                
                # Create M0 free tier cluster (perfect for getting started)
                atlas clusters create "$CLUSTER_NAME" \
                    --projectId "$PROJECT_ID" \
                    --provider AWS \
                    --region US_EAST_1 \
                    --tier M0 \
                    --diskSizeGB 0.5 \
                    --mdbVersion 7.0
                
                if [ $? -eq 0 ]; then
                    print_success "Cluster creation initiated!"
                    print_step "Waiting for cluster to be ready (this may take a few minutes)..."
                    
                    # Wait for cluster to be ready
                    while true; do
                        STATUS=$(atlas clusters describe "$CLUSTER_NAME" --projectId "$PROJECT_ID" --output json | jq -r '.stateName')
                        if [[ "$STATUS" == "IDLE" ]]; then
                            print_success "Cluster is ready!"
                            break
                        else
                            echo -e "${YELLOW}Cluster status: $STATUS (waiting...)${NC}"
                            sleep 30
                        fi
                    done
                    
                    # Create database user
                    print_step "Creating database user..."
                    read -p "Enter username for database (e.g., asoos-admin): " DB_USERNAME
                    DB_USERNAME=${DB_USERNAME:-"asoos-admin"}
                    
                    # Generate secure password
                    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
                    
                    atlas dbusers create --projectId "$PROJECT_ID" \
                        --username "$DB_USERNAME" \
                        --password "$DB_PASSWORD" \
                        --role readWriteAnyDatabase
                    
                    print_success "Database user created: $DB_USERNAME"
                    
                    # Get connection string
                    print_step "Retrieving connection string..."
                    CONNECTION_STRING=$(atlas clusters connectionStrings describe "$CLUSTER_NAME" --projectId "$PROJECT_ID" --output json | jq -r '.standardSrv')
                    
                    # Replace password placeholder
                    MONGODB_URI="${CONNECTION_STRING/<password>/$DB_PASSWORD}"
                    
                    print_success "MongoDB Atlas setup complete!"
                    
                    cat << MONGO_EOF

${GREEN}🎉 Your MongoDB Atlas cluster is ready!${NC}

${WHITE}CLUSTER DETAILS:${NC}
• Cluster Name: ${CLUSTER_NAME}
• Username: ${DB_USERNAME}  
• Password: ${DB_PASSWORD}
• Region: US East (Virginia)
• Tier: M0 (Free)

${WHITE}CONNECTION URI:${NC}
${CYAN}${MONGODB_URI}${NC}

${WHITE}IMPORTANT:${NC}
• Save this connection URI - you'll need it for the production configuration
• The password has been automatically generated for security
• Your cluster is on the free M0 tier (perfect for getting started)
• You can upgrade to a paid tier later if needed

MONGO_EOF
                    
                    # Save to file for reference
                    cat > mongodb-atlas-credentials.txt << CRED_EOF
MongoDB Atlas Credentials for ASOOS Production
==============================================

Cluster Name: $CLUSTER_NAME
Project ID: $PROJECT_ID
Username: $DB_USERNAME
Password: $DB_PASSWORD

Connection URI:
$MONGODB_URI

Created: $(date)
CRED_EOF
                    
                    print_success "Credentials saved to: mongodb-atlas-credentials.txt"
                    
                else
                    print_warning "Failed to create cluster. Please try manual setup."
                fi
            fi
        else
            print_warning "Authentication failed. Please try manual setup."
        fi
    else
        print_warning "MongoDB Atlas CLI not found. Let's try manual setup."
        HAS_ATLAS_CLI="N"
    fi
fi

if [[ ! $HAS_ATLAS_CLI =~ ^[Yy]$ ]]; then
    print_section "Option 2: Manual MongoDB Atlas Setup"
    
    cat << MANUAL_EOF

${WHITE}Follow these steps to set up MongoDB Atlas manually:${NC}

${YELLOW}Step 1: Create MongoDB Atlas Account${NC}
1. Go to: ${CYAN}https://www.mongodb.com/cloud/atlas/register${NC}
2. Sign up with your email address
3. Verify your email

${YELLOW}Step 2: Create a New Project${NC}
1. Click "New Project"
2. Name it: "ASOOS-Production"  
3. Click "Create Project"

${YELLOW}Step 3: Create a Database Cluster${NC}
1. Click "Create a Deployment"
2. Choose "M0 Sandbox" (FREE)
3. Select "AWS" as provider
4. Select "N. Virginia (us-east-1)" as region
5. Name your cluster: "asoos-prod-cluster"
6. Click "Create Deployment"

${YELLOW}Step 4: Create Database User${NC}
1. Click "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: "asoos-admin"
5. Generate a secure password (save it!)
6. Select "Built-in Role" → "Read and write to any database"
7. Click "Add User"

${YELLOW}Step 5: Configure Network Access${NC}
1. Click "Network Access" in the left sidebar  
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for now)
4. Click "Confirm"

${YELLOW}Step 6: Get Connection String${NC}
1. Go back to "Database" (Deployments)
2. Click "Connect" on your cluster
3. Choose "Drivers"
4. Select "Node.js" and version "4.1 or later"
5. Copy the connection string

${WHITE}Your connection string will look like:${NC}
${CYAN}mongodb+srv://asoos-admin:<password>@asoos-prod-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority${NC}

${WHITE}Replace ${YELLOW}<password>${WHITE} with your actual password!${NC}

MANUAL_EOF
    
    echo -e "${WHITE}Press Enter when you've completed the setup and have your connection URI...${NC}"
    read
    
    read -p "Enter your MongoDB Atlas connection URI: " MONGODB_URI
    
    if [[ -n "$MONGODB_URI" ]]; then
        print_success "MongoDB URI received!"
        
        # Save to file for reference
        cat > mongodb-atlas-credentials.txt << MANUAL_CRED_EOF
MongoDB Atlas Credentials for ASOOS Production
==============================================

Connection URI:
$MONGODB_URI

Created: $(date)
Note: This was set up manually through the web interface.
MANUAL_CRED_EOF
        
        print_success "Credentials saved to: mongodb-atlas-credentials.txt"
    else
        print_warning "No URI provided. You can run the production configuration script later."
    fi
fi

# =================================================================================================
# NEXT STEPS
# =================================================================================================

print_section "Next Steps"

if [[ -n "$MONGODB_URI" ]]; then
    cat << NEXT_EOF

${GREEN}✅ MongoDB Atlas is ready for ASOOS production!${NC}

${WHITE}READY TO PROCEED:${NC}
Your MongoDB Atlas connection URI is:
${CYAN}$MONGODB_URI${NC}

${WHITE}NEXT ACTION:${NC}
Run the production configuration script with your new MongoDB URI:

${YELLOW}./configure-asoos-production.sh${NC}

When prompted for "MongoDB Atlas URI", use the connection string above.

${WHITE}SECURITY NOTES:${NC}
• Your credentials are saved in: ${CYAN}mongodb-atlas-credentials.txt${NC}
• Keep this file secure and don't commit it to version control
• The free M0 tier is perfect for development and testing
• You can upgrade to a paid tier later for production scaling

NEXT_EOF

else
    cat << NO_URI_EOF

${YELLOW}⚠ MongoDB setup incomplete${NC}

Please complete the MongoDB Atlas setup and then run:
${YELLOW}./configure-asoos-production.sh${NC}

NO_URI_EOF
fi

echo -e "\n${WHITE}For MongoDB Atlas documentation: ${CYAN}https://docs.atlas.mongodb.com/${NC}"
