#!/usr/bin/env python3
"""
Diamond SAO HR AI CRMS Cloud Integration System
===============================================
Classification: Diamond SAO Only
Author: AI Assistant for Phillip Corey (ROARK) - Diamond SAO
Created: 2025-08-15
Purpose: Cloud-based authentication system integrating MongoDB Atlas HR AI CRMS
         with proper separation of HR/CRM concerns and AI pilot isolation

Key Features:
- Diamond SAO (Phillip) & Emerald EAO (Morgan) authentication
- MongoDB Atlas HR AI CRMS integration
- Proper separation: HR (.hr1-.hr4) vs CRM (Diamond/Emerald/Sapphire/Opal/Onyx)
- AI Pilots stay in AI domain only
- Cloud-to-cloud deployment ready
- Non-technical HR admin interface
- Integration with Victory36 infrastructure
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import hashlib
import secrets
import json
from dataclasses import dataclass, asdict
from enum import Enum

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, Depends, Request, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# Authentication and security
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
import pyotp

# MongoDB integration
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import certifi

# HTTP client for external integrations
import aiohttp
from aiofiles import open as aopen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================================================
# CONFIGURATION AND CONSTANTS
# ================================================================================================

class AdminOwnerType(str, Enum):
    """Administrative Owner Types"""
    SAO = "SAO"  # Super Administrative Owner (Diamond - Phillip)
    EAO = "EAO"  # Executive Administrative Owner (Emerald - Morgan)
    AAO = "AAO"  # Assistant Administrative Owner (Sapphire)
    CAO = "CAO"  # Coordinator Administrative Owner (Opal)
    TAO = "TAO"  # Technical Administrative Owner (Onyx)

class AdminOwnerLevel(str, Enum):
    """Administrative Owner Access Levels"""
    DIAMOND = "diamond"    # Highest - Full system control
    EMERALD = "emerald"    # Executive level
    SAPPHIRE = "sapphire"  # Senior management
    OPAL = "opal"          # Management
    ONYX = "onyx"          # Technical specialist

class HRClass(str, Enum):
    """HR Classification System"""
    HR1 = "HR.1"  # LLP member with contractual obligation
    HR2 = "HR.2"  # LLP member and employee
    HR3 = "HR.3"  # LLP member not contractor nor employee
    HR4 = "HR.4"  # Employee or contractor and not an LLP member

class Role(str, Enum):
    """Primary Role Classifications"""
    PRINCIPAL = "Principal"
    EXECUTIVE = "Executive"
    MEMBER = "Member"
    CONTRACTOR = "Contractor"
    EMPLOYEE = "Employee"

# Configuration from environment variables
class Config:
    # Database Configuration - No default URI for security
    MONGODB_URI = os.getenv("MONGODB_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "hr_ai_crms_system")
    
    # Security Configuration
    SECRET_KEY = os.getenv("DIAMOND_SAO_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Diamond SAO Configuration
    DIAMOND_SAO_EMAIL = "pr@coaching2100.com"
    DIAMOND_SAO_USER_ID = "00000001"
    
    # MOCOA Infrastructure Integration
    MOCOA_API_BASE = os.getenv("MOCOA_API_BASE", "https://api.asoos.com")
    MOCORIX2_ENDPOINT = os.getenv("MOCORIX2_ENDPOINT", "https://mocorix2.asoos.com")
    DR_CLAUDE01_ENDPOINT = os.getenv("DR_CLAUDE01_ENDPOINT", "https://dr-claude01.mocorix2.asoos.com")
    
    # Victory36 Integration
    VICTORY36_CONNECTION_POOL = os.getenv("VICTORY36_POOL_ENDPOINT", "https://v36-pool.mocoa.asoos.com")
    
    # Cloudflare Integration
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
    CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID", "")

config = Config()

# ================================================================================================
# DATA MODELS
# ================================================================================================

class TeamMemberBase(BaseModel):
    """Base model for team members"""
    name: str
    email: EmailStr
    role: Role
    llp_member: bool = False
    executive_status: bool = False
    contractual_responsibility: bool = False
    admin_owner_type: Optional[AdminOwnerType] = None
    admin_owner_level: Optional[AdminOwnerLevel] = None
    hr_class: Optional[HRClass] = None
    system_origin: List[str] = ["HR"]  # ["HR"], ["CRM"], or ["HR", "CRM"]
    permissions: List[str] = []
    status: str = "active"

class TeamMemberCreate(TeamMemberBase):
    """Model for creating team members"""
    employee_id: Optional[str] = None
    subscriber_id: Optional[str] = None

class TeamMemberResponse(TeamMemberBase):
    """Response model for team members"""
    employee_id: str
    subscriber_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    crm_tag: Optional[str] = None

class AuthRequest(BaseModel):
    """Authentication request model"""
    email: str
    password: str
    mfa_code: Optional[str] = None

class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

# ================================================================================================
# DATABASE INTEGRATION
# ================================================================================================

class MongoDBManager:
    """MongoDB Atlas connection and operations manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.hr_collection = None
        self.crm_collection = None
        self.auth_collection = None
        self.audit_collection = None
    
    async def connect(self):
        """Establish connection to MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(
                config.MONGODB_URI,
                tlsCAFile=certifi.where(),
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[config.DATABASE_NAME]
            
            # Initialize collections
            self.hr_collection = self.db.hr_members
            self.crm_collection = self.db.owner_subscribers
            self.auth_collection = self.db.authentication
            self.audit_collection = self.db.audit_log
            
            # Create indexes
            await self._create_indexes()
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB Atlas")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # HR Collection indexes
            await self.hr_collection.create_index("employee_id", unique=True)
            await self.hr_collection.create_index("email", unique=True)
            await self.hr_collection.create_index([("name", 1), ("role", 1)])
            
            # CRM Collection indexes
            await self.crm_collection.create_index("subscriber_id", unique=True)
            await self.crm_collection.create_index("email")
            await self.crm_collection.create_index("admin_owner_level")
            
            # Auth Collection indexes
            await self.auth_collection.create_index("email", unique=True)
            await self.auth_collection.create_index("employee_id")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {str(e)}")
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("📦 Disconnected from MongoDB Atlas")

# Global database manager instance
db_manager = MongoDBManager()

# ================================================================================================
# AUTHENTICATION SYSTEM
# ================================================================================================

class AuthenticationManager:
    """Handles Diamond SAO and team member authentication"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            # Look up user in authentication collection
            user = await db_manager.auth_collection.find_one({"email": email})
            if not user:
                logger.warning(f"Authentication failed - user not found: {email}")
                return None
            
            # Verify password
            if not self.verify_password(password, user["password_hash"]):
                logger.warning(f"Authentication failed - invalid password: {email}")
                return None
            
            # Get user details from appropriate collection
            if user.get("admin_owner_type"):
                # Get from both HR and CRM if dual-system user
                user_details = await self._get_admin_user_details(user["employee_id"])
            else:
                # Get from HR collection
                user_details = await db_manager.hr_collection.find_one({"employee_id": user["employee_id"]})
            
            if not user_details:
                logger.error(f"User details not found for employee_id: {user['employee_id']}")
                return None
            
            # Log successful authentication
            await self._log_auth_event(email, "LOGIN_SUCCESS", user_details.get("name", "Unknown"))
            
            return {
                "employee_id": user["employee_id"],
                "email": email,
                "name": user_details.get("name"),
                "role": user_details.get("role"),
                "admin_owner_type": user_details.get("admin_owner_type"),
                "admin_owner_level": user_details.get("admin_owner_level"),
                "permissions": user_details.get("permissions", []),
                "system_origin": user_details.get("system_origin", ["HR"])
            }
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            await self._log_auth_event(email, "LOGIN_ERROR", str(e))
            return None
    
    async def _get_admin_user_details(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get admin user details from appropriate collections"""
        # Check HR collection first
        hr_details = await db_manager.hr_collection.find_one({"employee_id": employee_id})
        
        # If dual-system user, also get CRM details
        if hr_details and "CRM" in hr_details.get("system_origin", []):
            crm_details = await db_manager.crm_collection.find_one({"employee_id": employee_id})
            if crm_details:
                # Merge details, prioritizing HR for basic info
                hr_details.update({
                    "subscriber_id": crm_details.get("subscriber_id"),
                    "crm_tag": crm_details.get("crm_tag")
                })
        
        return hr_details
    
    async def _log_auth_event(self, email: str, event: str, details: str):
        """Log authentication events for audit trail"""
        try:
            await db_manager.audit_collection.insert_one({
                "timestamp": datetime.utcnow(),
                "event": event,
                "email": email,
                "details": details,
                "ip_address": None  # Will be added by request handler
            })
        except Exception as e:
            logger.error(f"Failed to log auth event: {str(e)}")

# Global authentication manager
auth_manager = AuthenticationManager()

# ================================================================================================
# TEAM MANAGEMENT SYSTEM
# ================================================================================================

class TeamManager:
    """Manages HR and CRM team member operations"""
    
    async def create_team_member(self, member_data: TeamMemberCreate, created_by: str) -> TeamMemberResponse:
        """Create a new team member with proper HR/CRM separation"""
        try:
            # Generate IDs if not provided
            if not member_data.employee_id:
                member_data.employee_id = await self._generate_employee_id()
            
            if "CRM" in member_data.system_origin and not member_data.subscriber_id:
                member_data.subscriber_id = await self._generate_subscriber_id()
            
            # Validate Diamond SAO exclusivity
            if member_data.admin_owner_level == AdminOwnerLevel.DIAMOND:
                if member_data.email != config.DIAMOND_SAO_EMAIL:
                    raise HTTPException(status_code=403, detail="Only authorized Diamond SAO can have Diamond level access")
            
            # Create base document
            current_time = datetime.utcnow()
            base_doc = {
                **member_data.dict(exclude_unset=True),
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": created_by
            }
            
            # Generate CRM tag if applicable
            if "CRM" in member_data.system_origin:
                base_doc["crm_tag"] = self._generate_crm_tag(member_data)
            
            # Insert into appropriate collections
            if "HR" in member_data.system_origin:
                await db_manager.hr_collection.insert_one({
                    **base_doc,
                    "collection_type": "HR"
                })
            
            if "CRM" in member_data.system_origin:
                await db_manager.crm_collection.insert_one({
                    **base_doc,
                    "collection_type": "CRM"
                })
            
            # Create authentication record if admin user
            if member_data.admin_owner_type:
                await self._create_auth_record(member_data)
            
            logger.info(f"✅ Created team member: {member_data.name} ({member_data.email})")
            
            return TeamMemberResponse(**base_doc)
            
        except DuplicateKeyError as e:
            raise HTTPException(status_code=409, detail="Team member with this email or ID already exists")
        except Exception as e:
            logger.error(f"Failed to create team member: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create team member: {str(e)}")
    
    async def _generate_employee_id(self) -> str:
        """Generate unique employee ID"""
        # Get the highest existing employee ID
        last_hr = await db_manager.hr_collection.find_one(
            sort=[("employee_id", -1)]
        )
        
        if last_hr and last_hr.get("employee_id"):
            try:
                last_id = int(last_hr["employee_id"])
                return f"{last_id + 1:08d}"
            except:
                pass
        
        # Default starting ID
        return "00000001"
    
    async def _generate_subscriber_id(self) -> str:
        """Generate unique subscriber ID"""
        # Get the highest existing subscriber ID
        last_crm = await db_manager.crm_collection.find_one(
            sort=[("subscriber_id", -1)]
        )
        
        if last_crm and last_crm.get("subscriber_id"):
            try:
                last_id = int(last_crm["subscriber_id"])
                return f"{last_id + 1:08d}"
            except:
                pass
        
        # Default starting ID
        return "00000001"
    
    def _generate_crm_tag(self, member_data: TeamMemberCreate) -> str:
        """Generate CRM tag based on member data"""
        tag_parts = []
        
        if member_data.llp_member:
            tag_parts.append("OS")  # Owner Subscriber
        
        if member_data.hr_class:
            tag_parts.append(member_data.hr_class.value)
        
        return " + ".join(tag_parts) if tag_parts else "OS"
    
    async def _create_auth_record(self, member_data: TeamMemberCreate):
        """Create authentication record for admin users"""
        # Generate temporary password (should be changed on first login)
        temp_password = secrets.token_urlsafe(12)
        password_hash = auth_manager.get_password_hash(temp_password)
        
        auth_record = {
            "employee_id": member_data.employee_id,
            "email": member_data.email,
            "password_hash": password_hash,
            "admin_owner_type": member_data.admin_owner_type.value if member_data.admin_owner_type else None,
            "temp_password": temp_password,  # Store temporarily for first login
            "password_changed": False,
            "mfa_enabled": False,
            "created_at": datetime.utcnow()
        }
        
        await db_manager.auth_collection.insert_one(auth_record)
        logger.info(f"🔐 Created auth record for {member_data.email} with temp password: {temp_password}")
    
    async def get_team_members(self, system_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team members with optional system filtering"""
        try:
            members = []
            
            if not system_filter or system_filter == "HR":
                # Get HR members
                hr_cursor = db_manager.hr_collection.find({})
                async for member in hr_cursor:
                    member["_id"] = str(member["_id"])
                    members.append(member)
            
            if not system_filter or system_filter == "CRM":
                # Get CRM members
                crm_cursor = db_manager.crm_collection.find({})
                async for member in crm_cursor:
                    member["_id"] = str(member["_id"])
                    # Avoid duplicates for dual-system members
                    if not any(m.get("employee_id") == member.get("employee_id") for m in members):
                        members.append(member)
            
            return members
            
        except Exception as e:
            logger.error(f"Failed to get team members: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve team members")

# Global team manager
team_manager = TeamManager()

# ================================================================================================
# SEED DATA FOR INITIAL SETUP
# ================================================================================================

async def initialize_seed_data():
    """Initialize the system with seed data for your team"""
    try:
        logger.info("🌱 Initializing seed data...")
        
        # Check if Diamond SAO already exists
        existing_diamond = await db_manager.hr_collection.find_one({"email": config.DIAMOND_SAO_EMAIL})
        if existing_diamond:
            logger.info("✅ Diamond SAO already exists, skipping seed data")
            return
        
        # Define your team structure
        team_seed_data = [
            # Phillip Corey Roark - Diamond SAO (Principal)
            {
                "employee_id": "00000001",
                "subscriber_id": "00000001",
                "name": "Phillip Corey Roark",
                "email": "pr@coaching2100.com",
                "role": Role.PRINCIPAL,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "admin_owner_type": AdminOwnerType.SAO,
                "admin_owner_level": AdminOwnerLevel.DIAMOND,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"],
                "permissions": ["orchestration_control", "s2do_admin", "vision_space_owner"],
                "status": "active"
            },
            # Morgan O'Brien - Emerald EAO (Executive)
            {
                "employee_id": "00000002",
                "subscriber_id": "00000002",
                "name": "Morgan O'Brien",
                "email": "morgan@aixtiv.com",  # Placeholder email
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "admin_owner_type": AdminOwnerType.EAO,
                "admin_owner_level": AdminOwnerLevel.EMERALD,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"],
                "permissions": ["s2do_admin", "vision_space_owner"],
                "status": "active"
            },
            # Executive Members with Contractual Responsibility
            {
                "name": "Roger Mahoney",
                "email": "roger@aixtiv.com",
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "Eduardo Testa",
                "email": "eduardo@aixtiv.com", 
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "Joshua Galbreath",
                "email": "joshua@aixtiv.com",
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "Lisa Goldenthal",
                "email": "lisa@aixtiv.com",
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "David Goggin",
                "email": "david@aixtiv.com",
                "role": Role.EXECUTIVE,
                "llp_member": True,
                "executive_status": True,
                "contractual_responsibility": True,
                "hr_class": HRClass.HR1,
                "system_origin": ["HR", "CRM"]
            },
            # Non-Executive Members
            {
                "name": "Steven Jolly",
                "email": "steven@aixtiv.com",
                "role": Role.MEMBER,
                "llp_member": True,
                "executive_status": False,
                "contractual_responsibility": False,
                "hr_class": HRClass.HR3,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "Adam Keith",
                "email": "adam@aixtiv.com",
                "role": Role.MEMBER,
                "llp_member": True,
                "executive_status": False,
                "contractual_responsibility": False,
                "hr_class": HRClass.HR3,
                "system_origin": ["HR", "CRM"]
            },
            {
                "name": "Melika Reife",
                "email": "melika@aixtiv.com",
                "role": Role.MEMBER,
                "llp_member": True,
                "executive_status": False,
                "contractual_responsibility": False,
                "hr_class": HRClass.HR3,
                "system_origin": ["HR", "CRM"]
            }
        ]
        
        # Create team members
        for i, member_data in enumerate(team_seed_data):
            try:
                if not member_data.get("employee_id"):
                    member_data["employee_id"] = f"{i+1:08d}"
                
                if "CRM" in member_data.get("system_origin", []) and not member_data.get("subscriber_id"):
                    member_data["subscriber_id"] = f"{i+1:08d}"
                
                member_create = TeamMemberCreate(**member_data)
                await team_manager.create_team_member(member_create, "SYSTEM_SEED")
                
                logger.info(f"✅ Created team member: {member_data['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create team member {member_data['name']}: {str(e)}")
        
        logger.info("🎉 Seed data initialization completed!")
        
    except Exception as e:
        logger.error(f"❌ Seed data initialization failed: {str(e)}")

# ================================================================================================
# FASTAPI APPLICATION
# ================================================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Diamond SAO HR AI CRMS System",
    description="Cloud-based authentication and team management system for Aixtiv Symphony",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# ================================================================================================
# API ENDPOINTS
# ================================================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup - connect to database and initialize"""
    try:
        # Validate MongoDB URI configuration
        if not config.MONGODB_URI:
            logger.warning("⚠️  MONGODB_URI environment variable not set - running in demo mode")
            logger.info("💡 Set MONGODB_URI environment variable to enable full functionality")
            logger.info("💡 Example: MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/dbname'")
        elif "username:password" in config.MONGODB_URI:
            logger.error("❌ MONGODB_URI contains placeholder credentials - this is a security issue!")
            logger.info("💡 Update MONGODB_URI with real credentials from MongoDB Atlas")
        else:
            await db_manager.connect()
            await initialize_seed_data()
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed: {str(e)} - running in demo mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown - cleanup"""
    await db_manager.disconnect()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token"""
    try:
        user = await auth_manager.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_manager.create_access_token(
            data={"sub": user["email"], "employee_id": user["employee_id"]}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_info": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication service error")

@app.get("/api/team/members")
async def get_team_members(system_filter: Optional[str] = None):
    """Get all team members with optional system filtering"""
    try:
        members = await team_manager.get_team_members(system_filter)
        return {"members": members, "count": len(members)}
    except Exception as e:
        logger.error(f"Failed to get team members: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team members")

@app.post("/api/team/members", response_model=TeamMemberResponse)
async def create_team_member(member_data: TeamMemberCreate):
    """Create a new team member"""
    try:
        # For now, use system as creator - in production, get from JWT token
        created_member = await team_manager.create_team_member(member_data, "ADMIN")
        return created_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create team member")

@app.get("/api/system/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        await db_manager.client.admin.command('ping')
        
        # Get system stats
        hr_count = await db_manager.hr_collection.count_documents({})
        crm_count = await db_manager.crm_collection.count_documents({})
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "collections": {
                "hr_members": hr_count,
                "owner_subscribers": crm_count
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# ================================================================================================
# HTML TEMPLATES (Inline for simplicity)
# ================================================================================================

@app.get("/admin", response_class=HTMLResponse)
async def admin_interface(request: Request):
    """HR Admin Interface for non-technical administrators"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Admin - Diamond SAO System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .diamond-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .emerald-gradient { background: linear-gradient(135deg, #50C9C3 0%, #96DEDA 100%); }
        .access-card { transition: all 0.3s ease; }
        .access-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .access-card.selected { ring: 2px solid #4F46E5; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="diamond-gradient text-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold">💎 HR Admin Portal</h1>
                        <span class="ml-4 px-3 py-1 bg-white/20 rounded-full text-sm">Diamond SAO System</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button class="bg-white/20 px-4 py-2 rounded-lg hover:bg-white/30 transition">Dashboard</button>
                        <button class="bg-white/20 px-4 py-2 rounded-lg hover:bg-white/30 transition">Settings</button>
                    </div>
                </div>
            </div>
        </header>

        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Quick Stats -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="p-2 bg-blue-100 rounded-lg">
                            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Total Team</p>
                            <p class="text-2xl font-bold text-gray-900" id="total-members">-</p>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="p-2 bg-green-100 rounded-lg">
                            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Executives</p>
                            <p class="text-2xl font-bold text-gray-900" id="executives-count">-</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="p-2 bg-purple-100 rounded-lg">
                            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">LLP Partners</p>
                            <p class="text-2xl font-bold text-gray-900" id="partners-count">-</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="p-2 bg-orange-100 rounded-lg">
                            <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Admin Access</p>
                            <p class="text-2xl font-bold text-gray-900" id="admin-count">-</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content Tabs -->
            <div class="bg-white rounded-lg shadow">
                <div class="border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8" aria-label="Tabs">
                        <button class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm active" data-tab="team-list">
                            Team Overview
                        </button>
                        <button class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" data-tab="add-member">
                            Add New Member
                        </button>
                        <button class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" data-tab="system-settings">
                            System Settings
                        </button>
                    </nav>
                </div>

                <!-- Team List Tab -->
                <div id="team-list" class="tab-content p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-lg font-medium text-gray-900">Team Members</h3>
                        <div class="flex space-x-3">
                            <select class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                <option>All Systems</option>
                                <option>HR Only</option>
                                <option>CRM Only</option>
                            </select>
                            <button class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition">
                                Export List
                            </button>
                        </div>
                    </div>
                    
                    <div id="team-members-list" class="space-y-4">
                        <!-- Team members will be loaded here -->
                        <div class="text-center py-8">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                            <p class="mt-2 text-gray-500">Loading team members...</p>
                        </div>
                    </div>
                </div>

                <!-- Add Member Tab -->
                <div id="add-member" class="tab-content p-6 hidden">
                    <h3 class="text-lg font-medium text-gray-900 mb-6">Add New Team Member</h3>
                    
                    <form id="add-member-form" class="space-y-6">
                        <!-- Basic Information -->
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h4 class="text-md font-medium text-gray-900 mb-4">📋 Basic Information</h4>
                            <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Full Name *</label>
                                    <input type="text" name="name" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" placeholder="John Smith">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Email Address *</label>
                                    <input type="email" name="email" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" placeholder="john@company.com">
                                </div>
                            </div>
                        </div>

                        <!-- Company Role -->
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h4 class="text-md font-medium text-gray-900 mb-4">💼 Company Role</h4>
                            <div class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Primary Role</label>
                                    <select name="role" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                        <option value="">Select Role...</option>
                                        <option value="Principal">Principal (Company Leader)</option>
                                        <option value="Executive">Executive (Decision Maker)</option>
                                        <option value="Member">Member (Team Member)</option>
                                        <option value="Contractor">Contractor (External)</option>
                                        <option value="Employee">Employee (Staff)</option>
                                    </select>
                                </div>
                                
                                <div class="space-y-3">
                                    <label class="flex items-center">
                                        <input type="checkbox" name="llp_member" class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                        <span class="ml-2 text-sm text-gray-700">This person is a partner/owner in the company (LLP Member)</span>
                                    </label>
                                    
                                    <label class="flex items-center">
                                        <input type="checkbox" name="executive_status" class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                        <span class="ml-2 text-sm text-gray-700">This person has executive decision-making authority</span>
                                    </label>
                                    
                                    <label class="flex items-center">
                                        <input type="checkbox" name="contractual_responsibility" class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                        <span class="ml-2 text-sm text-gray-700">This person has contractual responsibilities</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Access Levels -->
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h4 class="text-md font-medium text-gray-900 mb-4">🔐 Administrative Access</h4>
                            <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
                                <label class="access-card bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer">
                                    <input type="radio" name="admin_access" value="none" class="sr-only">
                                    <div class="text-center">
                                        <h5 class="font-medium text-gray-900">Standard Access</h5>
                                        <p class="text-sm text-gray-500">Regular system access</p>
                                    </div>
                                </label>
                                
                                <label class="access-card bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer">
                                    <input type="radio" name="admin_access" value="eao" class="sr-only">
                                    <div class="text-center">
                                        <h5 class="font-medium text-gray-900">Executive Admin (EAO)</h5>
                                        <p class="text-sm text-gray-500">Can manage teams and approve decisions</p>
                                        <span class="inline-block mt-2 px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">Emerald Level</span>
                                    </div>
                                </label>
                                
                                <label class="access-card bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer">
                                    <input type="radio" name="admin_access" value="sao" class="sr-only">
                                    <div class="text-center">
                                        <h5 class="font-medium text-gray-900">Super Admin (SAO)</h5>
                                        <p class="text-sm text-gray-500">Full system control and ownership</p>
                                        <span class="inline-block mt-2 px-2 py-1 text-xs font-semibold text-purple-800 bg-purple-100 rounded-full">Diamond Level</span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Submit Button -->
                        <div class="flex justify-end space-x-3">
                            <button type="button" class="bg-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-400 transition">Cancel</button>
                            <button type="submit" class="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 transition">Add Team Member</button>
                        </div>
                    </form>
                </div>

                <!-- System Settings Tab -->
                <div id="system-settings" class="tab-content p-6 hidden">
                    <h3 class="text-lg font-medium text-gray-900 mb-6">System Settings</h3>
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <svg class="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                </svg>
                            </div>
                            <div class="ml-3">
                                <h4 class="text-sm font-medium text-yellow-800">Diamond SAO Access Required</h4>
                                <div class="mt-2 text-sm text-yellow-700">
                                    <p>System settings require Diamond SAO authentication. Contact Phillip Corey (pr@coaching2100.com) for administrative changes.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab functionality
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all tabs
                document.querySelectorAll('.tab-button').forEach(b => {
                    b.classList.remove('border-indigo-500', 'text-indigo-600', 'active');
                    b.classList.add('border-transparent', 'text-gray-500');
                });
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.add('hidden');
                });

                // Add active class to clicked tab
                button.classList.add('border-indigo-500', 'text-indigo-600', 'active');
                button.classList.remove('border-transparent', 'text-gray-500');
                
                const tabId = button.dataset.tab;
                document.getElementById(tabId).classList.remove('hidden');
            });
        });

        // Access card selection
        document.querySelectorAll('.access-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('.access-card').forEach(c => {
                    c.classList.remove('selected');
                });
                card.classList.add('selected');
            });
        });

        // Load team members
        async function loadTeamMembers() {
            try {
                const response = await fetch('/api/team/members');
                const data = await response.json();
                
                updateStats(data.members);
                displayTeamMembers(data.members);
            } catch (error) {
                console.error('Failed to load team members:', error);
                document.getElementById('team-members-list').innerHTML = '<p class="text-red-500 text-center">Failed to load team members</p>';
            }
        }

        function updateStats(members) {
            document.getElementById('total-members').textContent = members.length;
            document.getElementById('executives-count').textContent = members.filter(m => m.executive_status).length;
            document.getElementById('partners-count').textContent = members.filter(m => m.llp_member).length;
            document.getElementById('admin-count').textContent = members.filter(m => m.admin_owner_type).length;
        }

        function displayTeamMembers(members) {
            const container = document.getElementById('team-members-list');
            
            if (members.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-center py-8">No team members found</p>';
                return;
            }

            container.innerHTML = members.map(member => `
                <div class="bg-white border border-gray-200 rounded-lg p-6 flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            ${member.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${member.name}</h4>
                            <p class="text-gray-600">${member.email}</p>
                            <div class="flex items-center space-x-2 mt-1">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    ${member.role}
                                </span>
                                ${member.admin_owner_level ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${member.admin_owner_level === 'diamond' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}">
                                    ${member.admin_owner_level.charAt(0).toUpperCase() + member.admin_owner_level.slice(1)} ${member.admin_owner_type}
                                </span>` : ''}
                                ${member.llp_member ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">LLP Partner</span>' : ''}
                                ${member.contractual_responsibility ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Contractual</span>' : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button class="text-indigo-600 hover:text-indigo-900 font-medium">Edit</button>
                        <button class="text-gray-600 hover:text-gray-900 font-medium">View</button>
                    </div>
                </div>
            `).join('');
        }

        // Form submission
        document.getElementById('add-member-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                role: formData.get('role'),
                llp_member: formData.has('llp_member'),
                executive_status: formData.has('executive_status'),
                contractual_responsibility: formData.has('contractual_responsibility'),
                system_origin: ['HR'] // Default to HR system
            };

            // Handle admin access
            const adminAccess = formData.get('admin_access');
            if (adminAccess === 'sao') {
                data.admin_owner_type = 'SAO';
                data.admin_owner_level = 'diamond';
                data.system_origin = ['HR', 'CRM'];
            } else if (adminAccess === 'eao') {
                data.admin_owner_type = 'EAO';
                data.admin_owner_level = 'emerald';
                data.system_origin = ['HR', 'CRM'];
            }

            try {
                const response = await fetch('/api/team/members', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    alert('Team member added successfully!');
                    e.target.reset();
                    loadTeamMembers(); // Reload the team list
                    
                    // Switch to team list tab
                    document.querySelector('[data-tab="team-list"]').click();
                } else {
                    const error = await response.json();
                    alert('Failed to add team member: ' + error.detail);
                }
            } catch (error) {
                console.error('Error adding team member:', error);
                alert('Failed to add team member. Please try again.');
            }
        });

        // Initialize page
        loadTeamMembers();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# ================================================================================================
# MAIN EXECUTION
# ================================================================================================

if __name__ == "__main__":
    print("🚀 Starting Diamond SAO HR AI CRMS System...")
    print("=" * 60)
    print(f"📧 Diamond SAO Email: {config.DIAMOND_SAO_EMAIL}")
    print(f"🏢 Database: {config.DATABASE_NAME}")
    print(f"🌐 MOCOA Integration: {config.MOCOA_API_BASE}")
    print(f"🔧 MOCORIX2 Orchestration: {config.MOCORIX2_ENDPOINT}")
    print("=" * 60)
    
    # Run the application
    uvicorn.run(
        "diamond_sao_hr_crms_system:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
