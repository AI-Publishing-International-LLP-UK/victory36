# Get MongoDB Atlas URI - Quick Guide

## Your Setup
- **MongoDB Atlas Project**: api-for-warp-drive
- **Database**: hr_ai_crms_system
- **Expected Format**: `mongodb+srv://username:password@cluster-name.xxxxx.mongodb.net/hr_ai_crms_system?retryWrites=true&w=majority`

## Steps to Get Your Connection URI

### 1. Go to MongoDB Atlas
Visit: https://cloud.mongodb.com/

### 2. Select Your Project
- Click on "api-for-warp-drive" project
- Or select it from the project dropdown

### 3. Find Your Cluster
- You should see your existing cluster in the "Deployments" section
- If no cluster exists, you'll need to create one first

### 4. Get Connection String
- Click "Connect" button on your cluster
- Choose "Drivers" 
- Select "Node.js" and latest version
- Copy the connection string

### 5. Your Connection String Will Look Like:
```
mongodb+srv://<username>:<password>@<cluster-name>.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### 6. Add Database Name
Add `/hr_ai_crms_system` before the `?` like this:
```
mongodb+srv://<username>:<password>@<cluster-name>.xxxxx.mongodb.net/hr_ai_crms_system?retryWrites=true&w=majority
```

## If You Don't Have a Cluster Yet

### Quick Free Cluster Setup:
1. In your "api-for-warp-drive" project, click "Create Deployment"
2. Choose **M0 Sandbox (FREE)**
3. Provider: **AWS** or **Google Cloud**
4. Region: **us-east-1** (AWS) or **us-central1** (GCP)
5. Cluster Name: **asoos-prod-cluster**
6. Click "Create Deployment"

### Create Database User:
1. Go to "Database Access" in left sidebar
2. Click "Add New Database User"
3. Username: **asoos-admin**
4. Password: Generate a strong password (save it!)
5. Database User Privileges: **Read and write to any database**
6. Click "Add User"

### Configure Network Access:
1. Go to "Network Access" in left sidebar
2. Click "Add IP Address"
3. Choose "Allow Access from Anywhere" (for now)
4. Click "Confirm"

## Once You Have the URI:
1. Copy your complete MongoDB Atlas URI
2. Run: `./configure-asoos-production.sh`
3. When prompted for MongoDB URI, paste your connection string
4. Continue with the rest of the production setup
