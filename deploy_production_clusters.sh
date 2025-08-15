#!/bin/bash

# Aixtiv Symphony Orchestrating OS - Production Cluster Deployment
# Project: api-for-warp-drive

set -e

PROJECT_ID="api-for-warp-drive"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "🚀 DEPLOYING AIXTIV SYMPHONY PRODUCTION CLUSTERS"
echo "================================================="
echo "Project: $PROJECT_ID"
echo "Timestamp: $TIMESTAMP"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Function to create cluster if it doesn't exist
create_cluster_if_not_exists() {
    local cluster_name=$1
    local location=$2
    local description=$3
    local num_nodes=${4:-3}
    local machine_type=${5:-e2-standard-4}
    
    echo "🔍 Checking cluster: $cluster_name in $location"
    
    if gcloud container clusters describe $cluster_name --location=$location >/dev/null 2>&1; then
        echo "✅ Cluster $cluster_name already exists in $location"
        echo "   📊 $(gcloud container clusters describe $cluster_name --location=$location --format='value(status)')"
    else
        echo "🏗️ Creating cluster: $cluster_name ($description)"
        echo "   📍 Location: $location"
        echo "   🔧 Machine Type: $machine_type"
        echo "   📊 Nodes: $num_nodes"
        
        gcloud container clusters create $cluster_name \
            --location=$location \
            --machine-type=$machine_type \
            --num-nodes=$num_nodes \
            --enable-autoscaling \
            --min-nodes=1 \
            --max-nodes=10 \
            --enable-autorepair \
            --enable-autoupgrade \
            --disk-size=50GB \
            --disk-type=pd-ssd \
            --enable-ip-alias \
            --network=default \
            --subnetwork=default \
            --enable-network-policy \
            --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
            --enable-shielded-nodes \
            --logging=SYSTEM,WORKLOAD \
            --monitoring=SYSTEM \
            --async
            
        echo "✅ Cluster creation initiated: $cluster_name"
    fi
    echo ""
}

# MOCOA - Client-Facing Infrastructure (us-west1)
echo "🌍 MOCOA - CLIENT-FACING INFRASTRUCTURE"
create_cluster_if_not_exists "aixtiv-mocoa-primary" "us-west1-a" "MOCOA Primary - Client Interface" 5 "e2-standard-4"
create_cluster_if_not_exists "aixtiv-mocoa-secondary" "us-west1-b" "MOCOA Secondary - Load Balancing" 3 "e2-standard-4"

# MOCORIX - AI Intelligence Development (us-west1-c)
echo "🧠 MOCORIX - AI INTELLIGENCE DEVELOPMENT"
create_cluster_if_not_exists "aixtiv-mocorix-ai" "us-west1-c" "MOCORIX AI - RIX/QRIX/CRX Training" 5 "n1-standard-8"

# MOCORIX2 - Master Orchestration (us-central1-a)
echo "🎼 MOCORIX2 - MASTER ORCHESTRATION"
create_cluster_if_not_exists "aixtiv-mocorix2-master" "us-central1-a" "MOCORIX2 Master - Supreme Orchestration" 10 "n1-standard-8"

# MOCOSwarm - Managed Services (distributed)
echo "⚙️ MOCOSWARM - MANAGED SERVICES"
create_cluster_if_not_exists "aixtiv-mocoswarm-west" "us-west1-d" "MOCOSwarm West - SaaS Services" 4 "e2-standard-4"
create_cluster_if_not_exists "aixtiv-mocoswarm-central" "us-central1-d" "MOCOSwarm Central - Core Services" 4 "e2-standard-4"

# European Infrastructure (GDPR Compliance)
echo "🇪🇺 EUROPEAN INFRASTRUCTURE - GDPR COMPLIANCE"
create_cluster_if_not_exists "aixtiv-mocoa-eu" "europe-west1-a" "MOCOA EU - GDPR Compliant Services" 3 "e2-standard-4"
create_cluster_if_not_exists "aixtiv-mocoswarm-eu" "europe-west1-d" "MOCOSwarm EU - European Services" 3 "e2-standard-4"

echo "⏳ Waiting for cluster creation to complete..."
echo "This may take 5-10 minutes..."

# Wait for all clusters to be ready
check_cluster_ready() {
    local cluster_name=$1
    local location=$2
    
    echo "🔄 Waiting for $cluster_name in $location to be ready..."
    
    while true; do
        status=$(gcloud container clusters describe $cluster_name --location=$location --format='value(status)' 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$status" = "RUNNING" ]; then
            echo "✅ $cluster_name is ready!"
            break
        elif [ "$status" = "NOT_FOUND" ] || [ "$status" = "ERROR" ]; then
            echo "❌ $cluster_name failed to create or not found"
            break
        else
            echo "   Status: $status - waiting..."
            sleep 30
        fi
    done
}

# Check all clusters
clusters=(
    "aixtiv-mocoa-primary:us-west1-a"
    "aixtiv-mocoa-secondary:us-west1-b" 
    "aixtiv-mocorix-ai:us-west1-c"
    "aixtiv-mocorix2-master:us-central1-a"
    "aixtiv-mocoswarm-west:us-west1-d"
    "aixtiv-mocoswarm-central:us-central1-d"
    "aixtiv-mocoa-eu:europe-west1-a"
    "aixtiv-mocoswarm-eu:europe-west1-d"
)

for cluster_info in "${clusters[@]}"; do
    IFS=':' read -r cluster_name location <<< "$cluster_info"
    check_cluster_ready "$cluster_name" "$location"
done

echo ""
echo "🎯 PRODUCTION CLUSTER DEPLOYMENT SUMMARY"
echo "========================================"
echo ""

# List all created clusters
gcloud container clusters list --filter="name:aixtiv-*" --format="table(name,location,status,currentMasterVersion,numNodes)"

echo ""
echo "✅ INFRASTRUCTURE FOUNDATION: COMPLETE"
echo "🚀 Ready for service deployment phase"
echo ""
