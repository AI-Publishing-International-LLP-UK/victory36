"""
Diamond SAO Cloud Patch - Enhances demo mode functionality for cloud deployment
"""

import os
import sys
import json
from datetime import datetime

# Function to patch health check endpoint
def patch_health_check():
    return """
@app.get("/api/system/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Check if we're in demo mode
        if not config.MONGODB_URI or "username:password" in config.MONGODB_URI:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "demo-mode",
                "collections": {
                    "hr_members": 0,
                    "owner_subscribers": 0
                },
                "version": "1.0.0-cloud"
            }
        
        # Test database connection if not in demo mode
        await db_manager.client.admin.command('ping')
        
        # Get system stats
        hr_count = await db_manager.hr_collection.count_documents({})        hr_count = await db_manager.hr_collection.count_documents({})        h   
        return {
            "status            "status         imestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "collections": {
                "hr_members": hr_count,
                "owner_subscribers": crm_count
            },
            "version": "1.0.0-cloud"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "warning",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "demo-mode-fallback",
            "error": str(e),
            "version": "1.0.0-cloud"
        }
"""

# Main function to apply all patches
def apply_patches():
    print("Applying Diamond SAO Cloud Patches...")
    
    # Read the original file
    with open("diamond_sao_hr_crms_system.py", "r") as f:
        content = f.read()
    
    # Replace the health check endpoint
    health_check_start = content.find("@app.get(\"/api/system/health\")")
    health_check_end = content.find("# HTML TEMPLATES", he    health_check_end = content.find("# eck_start > 0 and health_check_end > 0:
        ne        ne        ne        ne     health_check_start] + 
            patch_health_check() + 
                                                
        
        # Write the patched file
        with open("diamond_sao_hr_crms_system_cloud.py", "w") as f:
            f.write(new_content)
        
        print("✅ Cloud patches applied successfully")
        print("📦 Created diamond_sao_hr_crms_system_cloud.py")
    else:
        print("❌ Failed to apply patches - health check section not found")
        sys.exit(1)

if __name__ == "__main__":
    apply_patches()
