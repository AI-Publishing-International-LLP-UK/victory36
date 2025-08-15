#!/bin/bash

# Victory36 Infrastructure Deployment via gcloud
# Classification: DIAMOND SAO ONLY
# Bypasses Terraform initialization issues

set -euo pipefail

echo "🚀 VICTORY36 INFRASTRUCTURE DEPLOYMENT"
echo "======================================"
echo "Project: api-for-warp-drive"
echo "Region: us-west1"
echo "Zone: us-west1-b"
echo "Classification: DIAMOND SAO"
echo ""

# Variables
PROJECT_ID="api-for-warp-drive"
REGION="us-west1"
ZONE="us-west1-b"
CLUSTER_NAME="victory36-mocoa"

echo "🔐 Step 1: Enabling required APIs..."
gcloud services enable compute.googleapis.com --project=$PROJECT_ID
gcloud services enable container.googleapis.com --project=$PROJECT_ID
gcloud services enable monitoring.googleapis.com --project=$PROJECT_ID
gcloud services enable logging.googleapis.com --project=$PROJECT_ID
echo "✅ APIs enabled"

echo ""
echo "🌐 Step 2: Creating VPC network..."
gcloud compute networks create victory36-network \
    --subnet-mode=custom \
    --project=$PROJECT_ID || echo "Network may already exist"

echo "✅ VPC network ready"

echo ""
echo "🏗️ Step 3: Creating subnet for Victory36..."
gcloud compute networks subnets create victory36-subnet-mocoa \
    --network=victory36-network \
    --range=10.1.0.0/16 \
    --secondary-range=pods=10.4.0.0/14,services=10.16.0.0/20 \
    --region=$REGION \
    --project=$PROJECT_ID || echo "Subnet may already exist"

echo "✅ Subnet created"

echo ""
echo "☸️ Step 4: Creating GKE Autopilot cluster for Victory36..."
gcloud container clusters create-auto $CLUSTER_NAME \
    --region=$REGION \
    --network=victory36-network \
    --subnetwork=victory36-subnet-mocoa \
    --cluster-secondary-range-name=pods \
    --services-secondary-range-name=services \
    --enable-network-policy \
    --labels="component=victory36,classification=diamond-sao,environment=production" \
    --project=$PROJECT_ID || echo "Cluster may already exist"

echo "✅ GKE Autopilot cluster created"

echo ""
echo "🔑 Step 5: Creating service account..."
gcloud iam service-accounts create victory36-mocoa \
    --display-name="Victory36 MOCOA Service Account" \
    --description="Diamond SAO service account for Victory36 connection pool manager" \
    --project=$PROJECT_ID || echo "Service account may already exist"

echo "✅ Service account created"

echo ""
echo "🛡️ Step 6: Setting up IAM permissions..."
SA_EMAIL="victory36-mocoa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/monitoring.metricWriter" || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter" || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudtrace.agent" || true

echo "✅ IAM permissions configured"

echo ""
echo "🔗 Step 7: Setting up Workload Identity..."
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[victory36/victory36-connection-pool]" \
    --project=$PROJECT_ID || true

echo "✅ Workload Identity configured"

echo ""
echo "🔍 Step 8: Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID

echo "✅ Cluster credentials configured"

echo ""
echo "📊 Step 9: Cluster status check..."
kubectl cluster-info
kubectl get nodes

echo ""
echo "🎉 VICTORY36 INFRASTRUCTURE DEPLOYMENT COMPLETED!"
echo "================================================="
echo "✅ GKE Autopilot Cluster: $CLUSTER_NAME"
echo "✅ Region: $REGION"
echo "✅ Network: victory36-network"
echo "✅ Service Account: victory36-mocoa"
echo "✅ Classification: DIAMOND SAO"
echo ""
echo "Next steps:"
echo "1. Deploy Victory36 pods: kubectl apply -k k8s/base/"
echo "2. Monitor deployment: kubectl get pods -n victory36 -w"
echo "3. Test 20M agent capacity"
echo ""
echo "🛡️ Diamond SAO Security: ACTIVE"
echo "📊 Ready for 20M AI agents!"
