#!/usr/bin/env python3
"""
MongoDB Atlas HR AI CRMS Schema Setup
=====================================
Classification: Diamond SAO Only
Purpose: Define and deploy the unified entity schema for HR/CRM integration
         with proper separation of concerns and AI pilot isolation

This script sets up:
1. HR Collection Schema (.hr1-.hr4 classifications)
2. CRM Owner Subscribers Collection (Diamond/Emerald/Sapphire/Opal/Onyx)
3. AI Pilots Collection (isolated from HR/CRM)
4. Authentication Collection
5. Audit Log Collection

Key Features:
- Proper separation: HR ≠ CRM ≠ AI Pilots
- Diamond SAO (Phillip) exclusive authentication
- Emerald EAO (Morgan) executive access
- LLP member tracking with contractual responsibilities
- System origin tracking for dual-system users
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBSchemaSetup:
    """MongoDB Atlas Schema Setup and Configuration"""
    
    def __init__(self, connection_string: str, database_name: str = "hr_ai_crms_system"):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                tlsCAFile=certifi.where(),
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[self.database_name]
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB Atlas database: {self.database_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
            raise
    
    async def create_collections_with_schemas(self):
        """Create collections with JSON Schema validation"""
        
        # 1. HR Members Collection Schema
        hr_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["employee_id", "name", "email", "role", "llp_member", "executive_status", "hr_class", "system_origin", "created_at"],
                "properties": {
                    "employee_id": {
                        "bsonType": "string",
                        "pattern": "^[0-9]{8}$",
                        "description": "8-digit employee ID, must be unique"
                    },
                    "name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 100,
                        "description": "Full name of the team member"
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                        "description": "Valid email address"
                    },
                    "role": {
                        "bsonType": "string",
                        "enum": ["Principal", "Executive", "Member", "Contractor", "Employee"],
                        "description": "Primary role in the organization"
                    },
                    "llp_member": {
                        "bsonType": "bool",
                        "description": "Is this person a partner/owner in the LLP"
                    },
                    "executive_status": {
                        "bsonType": "bool",
                        "description": "Has executive decision-making authority"
                    },
                    "contractual_responsibility": {
                        "bsonType": "bool",
                        "description": "Has contractual obligations to the LLP"
                    },
                    "hr_class": {
                        "bsonType": "string",
                        "enum": ["HR.1", "HR.2", "HR.3", "HR.4"],
                        "description": "HR classification level"
                    },
                    "admin_owner_type": {
                        "bsonType": ["string", "null"],
                        "enum": ["SAO", "EAO", "AAO", "CAO", "TAO", None],
                        "description": "Administrative owner type if applicable"
                    },
                    "admin_owner_level": {
                        "bsonType": ["string", "null"],
                        "enum": ["diamond", "emerald", "sapphire", "opal", "onyx", None],
                        "description": "Administrative access level"
                    },
                    "system_origin": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "string",
                            "enum": ["HR", "CRM"]
                        },
                        "minItems": 1,
                        "description": "Which systems this record belongs to"
                    },
                    "permissions": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                        "description": "List of system permissions"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["active", "inactive", "suspended"],
                        "description": "Current status of the team member"
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "created_by": {"bsonType": "string"}
                }
            }
        }
        
        # 2. CRM Owner Subscribers Collection Schema  
        crm_schema = {
            "$jsonSchema": {
                "bsonType": "object", 
                "required": ["subscriber_id", "name", "email", "admin_owner_level", "system_origin", "created_at"],
                "properties": {
                    "subscriber_id": {
                        "bsonType": "string",
                        "pattern": "^[0-9]{8}$",
                        "description": "8-digit subscriber ID, must be unique"
                    },
                    "employee_id": {
                        "bsonType": ["string", "null"],
                        "pattern": "^[0-9]{8}$",
                        "description": "Link to HR record if dual-system user"
                    },
                    "name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 100
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                    },
                    "admin_owner_level": {
                        "bsonType": "string",
                        "enum": ["diamond", "emerald", "sapphire", "opal", "onyx"],
                        "description": "CRM access level - Diamond, Emerald, Sapphire, Opal, Onyx"
                    },
                    "crm_tag": {
                        "bsonType": "string",
                        "description": "Generated tag like 'OS + HR.1' for dual-system users"
                    },
                    "subscription_tier": {
                        "bsonType": ["string", "null"],
                        "enum": ["premium", "enterprise", "custom", None],
                        "description": "Subscription tier for services"
                    },
                    "system_origin": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "string", 
                            "enum": ["HR", "CRM"]
                        },
                        "minItems": 1,
                        "description": "Must include CRM, may also include HR"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["active", "inactive", "suspended"]
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        # 3. AI Pilots Collection Schema (Isolated from HR/CRM)
        ai_pilots_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["pilot_id", "name", "ai_type", "specialization", "deployment_status", "created_at"],
                "properties": {
                    "pilot_id": {
                        "bsonType": "string",
                        "pattern": "^AI-[0-9]{6}$",
                        "description": "AI Pilot ID format: AI-000001"
                    },
                    "name": {
                        "bsonType": "string",
                        "description": "AI Pilot designation name"
                    },
                    "ai_type": {
                        "bsonType": "string",
                        "enum": ["RIX", "QRIX", "CRX", "PCP", "Elite11", "Mastery33"],
                        "description": "Type of AI agent"
                    },
                    "specialization": {
                        "bsonType": "string",
                        "description": "Specialized function or industry focus"
                    },
                    "deployment_status": {
                        "bsonType": "string",
                        "enum": ["training", "staging", "deployed", "retired"],
                        "description": "Current deployment status"
                    },
                    "mocoa_region": {
                        "bsonType": ["string", "null"],
                        "enum": ["us-west1-a", "us-west1-b", "us-central1", "eu-west1", None],
                        "description": "Deployment region if active"
                    },
                    "dr_claude_oversight": {
                        "bsonType": "string",
                        "enum": ["dr-claude01", "dr-claude02", "dr-claude03", "dr-claude04", "dr-claude05"],
                        "description": "Which Dr. Claude instance provides oversight"
                    },
                    "performance_metrics": {
                        "bsonType": "object",
                        "properties": {
                            "success_rate": {"bsonType": "double"},
                            "response_time_ms": {"bsonType": "int"},
                            "total_interactions": {"bsonType": "long"}
                        }
                    },
                    "created_at": {"bsonType": "date"},
                    "last_active": {"bsonType": "date"}
                }
            }
        }
        
        # 4. Authentication Collection Schema
        auth_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["employee_id", "email", "password_hash", "created_at"],
                "properties": {
                    "employee_id": {
                        "bsonType": "string",
                        "pattern": "^[0-9]{8}$"
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                    },
                    "password_hash": {
                        "bsonType": "string",
                        "description": "Bcrypt hashed password"
                    },
                    "admin_owner_type": {
                        "bsonType": ["string", "null"],
                        "enum": ["SAO", "EAO", "AAO", "CAO", "TAO", None]
                    },
                    "mfa_enabled": {
                        "bsonType": "bool",
                        "description": "Multi-factor authentication enabled"
                    },
                    "mfa_secret": {
                        "bsonType": ["string", "null"],
                        "description": "TOTP secret for MFA"
                    },
                    "temp_password": {
                        "bsonType": ["string", "null"],
                        "description": "Temporary password for first login"
                    },
                    "password_changed": {
                        "bsonType": "bool",
                        "description": "Has user changed from temp password"
                    },
                    "last_login": {"bsonType": ["date", "null"]},
                    "failed_login_attempts": {"bsonType": "int"},
                    "account_locked": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        # 5. Audit Log Collection Schema
        audit_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["timestamp", "event", "user_id", "details"],
                "properties": {
                    "timestamp": {"bsonType": "date"},
                    "event": {
                        "bsonType": "string",
                        "enum": ["LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", "MEMBER_CREATED", "MEMBER_UPDATED", "MEMBER_DELETED", "PERMISSION_CHANGED", "SYSTEM_ACCESS", "DATA_EXPORT"]
                    },
                    "user_id": {
                        "bsonType": ["string", "null"],
                        "description": "Employee ID or system identifier"
                    },
                    "email": {
                        "bsonType": ["string", "null"]
                    },
                    "ip_address": {
                        "bsonType": ["string", "null"]
                    },
                    "user_agent": {
                        "bsonType": ["string", "null"]
                    },
                    "details": {
                        "bsonType": "string",
                        "description": "Additional event details"
                    },
                    "affected_resource": {
                        "bsonType": ["string", "null"],
                        "description": "Resource that was affected by the action"
                    },
                    "success": {
                        "bsonType": "bool",
                        "description": "Whether the action was successful"
                    }
                }
            }
        }
        
        # Create collections with validation
        collections_config = [
            ("hr_members", hr_schema),
            ("owner_subscribers", crm_schema), 
            ("ai_pilots", ai_pilots_schema),
            ("authentication", auth_schema),
            ("audit_log", audit_schema)
        ]
        
        for collection_name, schema in collections_config:
            try:
                await self.db.create_collection(
                    collection_name,
                    validator=schema
                )
                logger.info(f"✅ Created collection: {collection_name}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"📋 Collection {collection_name} already exists")
                    # Update validator for existing collection
                    await self.db.command("collMod", collection_name, validator=schema)
                    logger.info(f"🔄 Updated validator for: {collection_name}")
                else:
                    logger.error(f"❌ Failed to create collection {collection_name}: {str(e)}")
    
    async def create_indexes(self):
        """Create indexes for optimal performance"""
        
        index_configs = [
            # HR Members indexes
            ("hr_members", [
                ("employee_id", 1),  # Unique
                ("email", 1),        # Unique  
                ("name", 1),
                ("role", 1),
                ("admin_owner_level", 1),
                ("llp_member", 1),
                ("status", 1),
                ([("name", 1), ("role", 1)], {}),  # Compound index
                ([("llp_member", 1), ("executive_status", 1)], {})
            ]),
            
            # CRM Owner Subscribers indexes
            ("owner_subscribers", [
                ("subscriber_id", 1),  # Unique
                ("employee_id", 1),    # For dual-system lookup
                ("email", 1),
                ("admin_owner_level", 1),
                ("subscription_tier", 1),
                ("status", 1),
                ([("admin_owner_level", 1), ("status", 1)], {})
            ]),
            
            # AI Pilots indexes
            ("ai_pilots", [
                ("pilot_id", 1),       # Unique
                ("ai_type", 1),
                ("specialization", 1),
                ("deployment_status", 1),
                ("mocoa_region", 1),
                ("dr_claude_oversight", 1),
                ([("ai_type", 1), ("deployment_status", 1)], {}),
                ([("mocoa_region", 1), ("deployment_status", 1)], {})
            ]),
            
            # Authentication indexes
            ("authentication", [
                ("email", 1),          # Unique
                ("employee_id", 1),    # Unique
                ("admin_owner_type", 1),
                ("account_locked", 1),
                ("last_login", -1)     # Descending for recent logins
            ]),
            
            # Audit Log indexes
            ("audit_log", [
                ("timestamp", -1),     # Descending for recent events
                ("event", 1),
                ("user_id", 1),
                ("email", 1),
                ("success", 1),
                ([("timestamp", -1), ("event", 1)], {}),
                ([("user_id", 1), ("timestamp", -1)], {})
            ])
        ]
        
        for collection_name, indexes in index_configs:
            collection = self.db[collection_name]
            
            for index_spec in indexes:
                try:
                    if isinstance(index_spec, tuple) and len(index_spec) == 2:
                        # Compound index with options
                        keys, options = index_spec
                        unique = options.get('unique', False)
                        await collection.create_index(keys, unique=unique)
                        logger.info(f"✅ Created compound index on {collection_name}: {keys}")
                    else:
                        # Simple index
                        field, direction = index_spec
                        unique = field in ["employee_id", "email", "subscriber_id", "pilot_id"]
                        await collection.create_index([(field, direction)], unique=unique)
                        logger.info(f"✅ Created index on {collection_name}.{field}")
                        
                except Exception as e:
                    if "already exists" in str(e):
                        logger.info(f"📋 Index already exists on {collection_name}")
                    else:
                        logger.error(f"❌ Failed to create index on {collection_name}: {str(e)}")
    
    async def insert_seed_data(self):
        """Insert seed data for system initialization"""
        
        # Check if data already exists
        existing_hr = await self.db.hr_members.count_documents({})
        if existing_hr > 0:
            logger.info("📋 Seed data already exists, skipping insertion")
            return
        
        logger.info("🌱 Inserting seed data...")
        
        # Seed data based on your team structure
        hr_seed_data = [
            {
                "employee_id": "00000001",
                "name": "Phillip Corey Roark", 
                "email": "pr@coaching2100.com",
                "role": "Principal",
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": "HR.1",
                "admin_owner_type": "SAO",
                "admin_owner_level": "diamond",
                "system_origin": ["HR", "CRM"],
                "permissions": ["orchestration_control", "s2do_admin", "vision_space_owner"],
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "SYSTEM_SEED",
                "collection_type": "HR"
            },
            {
                "employee_id": "00000002",
                "name": "Morgan O'Brien",
                "email": "morgan@aixtiv.com",
                "role": "Executive",
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": "HR.1",
                "admin_owner_type": "EAO", 
                "admin_owner_level": "emerald",
                "system_origin": ["HR", "CRM"],
                "permissions": ["s2do_admin", "vision_space_owner"],
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "SYSTEM_SEED",
                "collection_type": "HR"
            }
            # Add more team members as needed
        ]
        
        # Insert HR seed data
        if hr_seed_data:
            await self.db.hr_members.insert_many(hr_seed_data)
            logger.info(f"✅ Inserted {len(hr_seed_data)} HR seed records")
        
        # CRM seed data for dual-system users
        crm_seed_data = [
            {
                "subscriber_id": "00000001",
                "employee_id": "00000001",
                "name": "Phillip Corey Roark",
                "email": "pr@coaching2100.com",
                "admin_owner_level": "diamond",
                "crm_tag": "OS + HR.1",
                "subscription_tier": "custom",
                "system_origin": ["HR", "CRM"],
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "collection_type": "CRM"
            },
            {
                "subscriber_id": "00000002", 
                "employee_id": "00000002",
                "name": "Morgan O'Brien",
                "email": "morgan@aixtiv.com",
                "admin_owner_level": "emerald",
                "crm_tag": "OS + HR.1",
                "subscription_tier": "enterprise",
                "system_origin": ["HR", "CRM"],
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "collection_type": "CRM"
            }
        ]
        
        if crm_seed_data:
            await self.db.owner_subscribers.insert_many(crm_seed_data)
            logger.info(f"✅ Inserted {len(crm_seed_data)} CRM seed records")
        
        # Sample AI Pilots data
        ai_pilots_seed = [
            {
                "pilot_id": "AI-000001",
                "name": "RIX-Alpha-01",
                "ai_type": "RIX",
                "specialization": "Refined Intelligence Analysis",
                "deployment_status": "deployed",
                "mocoa_region": "us-west1-a",
                "dr_claude_oversight": "dr-claude02",
                "performance_metrics": {
                    "success_rate": 98.5,
                    "response_time_ms": 150,
                    "total_interactions": 1000000
                },
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            },
            {
                "pilot_id": "AI-000002", 
                "name": "QRIX-Beta-01",
                "ai_type": "QRIX",
                "specialization": "Quantum-Neared Math Simulation",
                "deployment_status": "deployed",
                "mocoa_region": "us-west1-c",
                "dr_claude_oversight": "dr-claude05", 
                "performance_metrics": {
                    "success_rate": 99.1,
                    "response_time_ms": 95,
                    "total_interactions": 750000
                },
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
        ]
        
        if ai_pilots_seed:
            await self.db.ai_pilots.insert_many(ai_pilots_seed)
            logger.info(f"✅ Inserted {len(ai_pilots_seed)} AI Pilot seed records")
    
    async def setup_complete_schema(self):
        """Complete schema setup process"""
        logger.info("🚀 Starting MongoDB Atlas schema setup...")
        
        await self.connect()
        await self.create_collections_with_schemas()
        await self.create_indexes()
        await self.insert_seed_data()
        
        logger.info("🎉 MongoDB Atlas schema setup completed successfully!")
        
        # Print summary
        summary = await self.get_database_summary()
        logger.info("📊 Database Summary:")
        for collection, count in summary.items():
            logger.info(f"  {collection}: {count} documents")
    
    async def get_database_summary(self) -> Dict[str, int]:
        """Get summary of all collections"""
        collections = ["hr_members", "owner_subscribers", "ai_pilots", "authentication", "audit_log"]
        summary = {}
        
        for collection_name in collections:
            try:
                count = await self.db[collection_name].count_documents({})
                summary[collection_name] = count
            except Exception as e:
                logger.error(f"Failed to count {collection_name}: {str(e)}")
                summary[collection_name] = 0
        
        return summary
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("📦 Disconnected from MongoDB Atlas")

async def main():
    """Main execution function"""
    # Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "hr_ai_crms_system")
    
    if "username:password" in MONGODB_URI:
        logger.error("❌ Please set MONGODB_URI environment variable with your actual connection string")
        logger.info("💡 Example: export MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/'")
        return
    
    # Setup schema
    schema_setup = MongoDBSchemaSetup(MONGODB_URI, DATABASE_NAME)
    
    try:
        await schema_setup.setup_complete_schema()
    except Exception as e:
        logger.error(f"❌ Schema setup failed: {str(e)}")
    finally:
        await schema_setup.disconnect()

if __name__ == "__main__":
    print("🔧 MongoDB Atlas HR AI CRMS Schema Setup")
    print("=" * 50)
    print("This script will:")
    print("1. Create collections with JSON Schema validation")
    print("2. Set up indexes for optimal performance") 
    print("3. Insert seed data for your team")
    print("4. Separate HR, CRM, and AI Pilots domains")
    print("=" * 50)
    
    asyncio.run(main())
