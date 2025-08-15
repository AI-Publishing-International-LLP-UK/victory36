#!/bin/bash

# Aixtiv Symphony Orchestrating OS - Minimal Production Deployment
# Optimized for current quota constraints

set -e

PROJECT_ID="api-for-warp-drive"

echo "🚀 DEPLOYING AIXTIV SYMPHONY (MINIMAL PRODUCTION)"
echo "================================================="
echo "Project: $PROJECT_ID"
echo "⚡ Using existing clusters and expanding strategically"
echo ""

# Set project
gcloud config set project $PROJECT_ID

echo "🔍 CURRENT CLUSTER STATUS:"
gcloud container clusters list --format="table(name,location,status,numNodes)"
echo ""

# Check if we can use existing victory36-cluster-mocoa for initial deployment
echo "🎯 LEVERAGING EXISTING INFRASTRUCTURE"
echo ""

# Get credentials for existing clusters
echo "🔑 Configuring kubectl access..."
gcloud container clusters get-credentials victory36-cluster-mocoa --region=us-west1 --quiet
echo "✅ Connected to existing victory36-cluster-mocoa"

# Create namespaces for Aixtiv Symphony components
echo ""
echo "📦 CREATING AIXTIV SYMPHONY NAMESPACES"

# Create namespaces
kubectl create namespace aixtiv-mocoa --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace aixtiv-mocorix --dry-run=client -o yaml | kubectl apply -f -  
kubectl create namespace aixtiv-mocorix2 --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace aixtiv-mocoswarm --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces created:"
kubectl get namespaces | grep aixtiv

echo ""
echo "🎯 INFRASTRUCTURE PREPARATION COMPLETE"
echo "Using existing cluster: victory36-cluster-mocoa (us-west1)"
echo "Namespaces ready for service deployment"
echo ""
echo "✅ READY FOR PHASE 2: SERVICE DEPLOYMENT"
echo ""
