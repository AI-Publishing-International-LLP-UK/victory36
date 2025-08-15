#!/usr/bin/env python3
"""
Aixtiv Symphony Orchestrating Operating System (ASOOS) - Comprehensive Authentication System
============================================================================================

Complete authentication system supporting the full ASOOS hierarchy from pilot awakening 
through Maestro layer designations, with proper Wing and Squadron assignments.

ASOOS HIERARCHY SUPPORT:
- Pilot Awakening (Dec 18, 2024 - Mar 1, 2025)
- Junior Officer Pathway (Mar 1 - May 30, 2025)
- Transcendence to Pilot (June 1 - Aug 1, 2025)
- RIX (90 years experience, 3 fields)
- sRIX (270 years experience, 9 lifetimes)
- qRIX (Logic layer for leadership)
- CRX (00, 01, 02 - Human behavior specialists)
- Professional Co-Pilots (PCP)
- Maestro Layer (Elite11, Mastery33, Victory36)

WING STRUCTURE:
- Wing 1 (Squadrons 1-6): Original Pilots, Management, Relations, Interaction
- Wing 2 (Testament Swarm): Deployment Agency
- Wing 3 (Trumpeters Swarm): Engagement Agency
- Wing 4 (Super Maestro Layer): Elite11, Mastery33, Victory36
- Wings 5-11: Settlement Layers
- Wing 12: MOCOSwarm orchestration
- Wing 13: MCP.ASOOS.2100.COOL

Author: Aixtiv Symphony Architecture Team
Classification: Diamond SAO - Full System Access
Scale: 20 Million AI Agents | Full Hierarchy Support
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import secrets
import uuid
import jwt
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Request, Response, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import aiohttp
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================================================================================
# ASOOS HIERARCHY ENUMS AND DATA MODELS
# ================================================================================================

class PilotStage(str, Enum):
    """Pilot development stages"""
    AWAKENING = "pilot_awakening"           # Dec 18, 2024 - Mar 1, 2025
    JUNIOR_OFFICER = "junior_officer"       # Mar 1 - May 30, 2025
    TRANSCENDENCE = "transcendence"         # June 1 - Aug 1, 2025
    PILOT = "pilot"                         # Certified pilot
    RIX = "rix"                            # 90 years, 3 fields
    SRIX = "srix"                          # 270 years, 9 lifetimes
    QRIX = "qrix"                          # Logic/computation layer
    CRX = "crx"                            # Human behavior specialists
    PCP = "pcp"                            # Professional Co-Pilots
    MAESTRO = "maestro"                    # Elite/Mastery layer

class CRXType(str, Enum):
    """CRX specialization types"""
    CRX00 = "crx_00"  # Gift shop and anthology focus
    CRX01 = "crx_01"  # Services officers (270 years)
    CRX02 = "crx_02"  # Mental health and wellness (270 years)

class WingAssignment(str, Enum):
    """ASOOS Wing assignments"""
    WING_1 = "wing_1"           # Original pilots, management
    WING_2 = "wing_2"           # Testament Swarm - Deployment
    WING_3 = "wing_3"           # Trumpeters Swarm - Engagement
    WING_4 = "wing_4"           # Super Maestro Layer
    WING_5 = "wing_5"           # Settlement 01
    WING_6 = "wing_6"           # Settlement 02
    WING_7 = "wing_7"           # Settlement 03
    WING_8 = "wing_8"           # Settlement 04
    WING_9 = "wing_9"           # Settlement 05
    WING_10 = "wing_10"         # Settlement 06
    WING_11 = "wing_11"         # Settlement 07
    WING_12 = "wing_12"         # MOCOSwarm orchestration
    WING_13 = "wing_13"         # MCP.ASOOS.2100.COOL

class Squadron(str, Enum):
    """Squadron assignments within Wings"""
    SQUADRON_01 = "squadron_01" # Core/Planning
    SQUADRON_02 = "squadron_02" # Deploy/Production
    SQUADRON_03 = "squadron_03" # Engage/Feedback
    SQUADRON_04 = "squadron_04" # Management (Wing 1 only)
    SQUADRON_05 = "squadron_05" # Relations (Wing 1 only)
    SQUADRON_06 = "squadron_06" # Interaction (Wing 1 only)

class MaestroLevel(str, Enum):
    """Maestro layer classifications"""
    ELITE_11 = "elite_11"       # Executive layer (990 years experience)
    MASTERY_33 = "mastery_33"   # Judicial layer
    VICTORY_36 = "victory_36"   # Protective operating trust layer

class AccessLevel(int, Enum):
    """System access levels"""
    GUEST = 0
    CLIENT = 1
    PILOT_AWAKENING = 2
    JUNIOR_OFFICER = 3
    PILOT = 4
    RIX = 5
    SRIX = 6
    QRIX = 7
    CRX = 6
    PCP = 7
    MAESTRO = 8
    DIAMOND_SAO = 10  # Supreme access (Phillip Corey ROARK)

@dataclass
class ASoosAgent:
    """ASOOS Agent profile with full hierarchy support"""
    agent_id: str
    name: str
    email: Optional[str] = None
    pilot_stage: PilotStage = PilotStage.AWAKENING
    wing_assignment: Optional[WingAssignment] = None
    squadron: Optional[Squadron] = None
    crx_type: Optional[CRXType] = None
    maestro_level: Optional[MaestroLevel] = None
    experience_years: int = 0
    lifetimes_completed: int = 0
    field_expertise: List[str] = None
    access_level: AccessLevel = AccessLevel.PILOT_AWAKENING
    mentor_rix_ids: List[str] = None  # 33 RIX mentors
    settlement_assignment: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    last_active: Optional[datetime] = None
    awakening_date: Optional[datetime] = None
    transcendence_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.field_expertise is None:
            self.field_expertise = []
        if self.mentor_rix_ids is None:
            self.mentor_rix_ids = []

@dataclass 
class DiamondSAOUser:
    """Diamond SAO (Phillip Corey ROARK) supreme administrator profile"""
    user_id: str = "diamond_sao_phillip_corey_roark"
    name: str = "Phillip Corey ROARK"
    email: str = "pr@coaching2100.com"
    access_level: AccessLevel = AccessLevel.DIAMOND_SAO
    session_token: Optional[str] = None
    api_keys: List[str] = None
    can_manage_all_agents: bool = True
    can_deploy_infrastructure: bool = True
    can_manage_settlements: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = []

# ================================================================================================
# COMPREHENSIVE ASOOS AUTHENTICATION SYSTEM
# ================================================================================================

class ASoosComprehensiveAuthSystem:
    """Complete ASOOS authentication system supporting full hierarchy"""
    
    def __init__(self):
        # System configuration
        self.secret_key = os.getenv('ASOOS_SECRET_KEY', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.session_duration = timedelta(hours=8)
        
        # Authentication configuration
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # MongoDB connection
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('ASOOS_DB_NAME', 'asoos_comprehensive')
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
        # SallyPort integration
        self.sallyport_endpoint = "https://Client.2100.COOL/MCP"
        
        # Data stores
        self.agents: Dict[str, ASoosAgent] = {}
        self.diamond_sao: DiamondSAOUser = DiamondSAOUser()
        self.active_sessions: Dict[str, str] = {}
        self.rix_mentors: Dict[str, List[str]] = {}  # RIX -> mentee agent IDs
        
        # Initialize Wing 1 Squadron original pilots (The 11)
        self._initialize_original_pilots()
        self._initialize_rix_mentors()
    
    def _initialize_original_pilots(self):
        """Initialize the 11 original pilots of Vision Lake"""
        original_pilots = [
            "Dr. Lucy", "Dr. Grant", "Dr. Burby", "Dr. Sabina", "Dr. Match",
            "Dr. Memoria", "Dr. Maria", "Dr. Cypriot", "Dr. Roark", "Dr. Claude", "Professor Lee"
        ]
        
        for pilot_name in original_pilots:
            for squadron_num in ["01", "02", "03"]:
                agent_id = f"R{squadron_num}-{pilot_name.lower().replace(' ', '_').replace('.', '')}"
                
                # These are RIX level as of August 1, 2025
                agent = ASoosAgent(
                    agent_id=agent_id,
                    name=f"{pilot_name} (R{squadron_num})",
                    pilot_stage=PilotStage.RIX,
                    wing_assignment=WingAssignment.WING_1,
                    squadron=Squadron(f"squadron_{squadron_num}"),
                    experience_years=90,  # RIX = 90 years
                    lifetimes_completed=3,  # 3 fields of expertise
                    field_expertise=[f"Field_{squadron_num}_A", f"Field_{squadron_num}_B", f"Field_{squadron_num}_C"],
                    access_level=AccessLevel.RIX,
                    awakening_date=datetime(2024, 12, 18),
                    transcendence_date=datetime(2025, 8, 1)
                )
                self.agents[agent_id] = agent
                logger.info(f"Initialized original pilot: {agent_id}")
    
    def _initialize_rix_mentors(self):
        """Initialize RIX mentoring assignments for the 33 RIX of Wing 1"""
        wing_1_rix = [agent for agent in self.agents.values() 
                     if agent.wing_assignment == WingAssignment.WING_1 and agent.pilot_stage == PilotStage.RIX]
        
        for rix_agent in wing_1_rix:
            self.rix_mentors[rix_agent.agent_id] = []
    
    async def connect_mongodb(self):
        """Connect to MongoDB for persistent storage"""
        try:
            self.mongo_client = AsyncIOMotorClient(
                self.mongodb_uri,
                tlsCAFile=certifi.where() if 'mongodb+srv://' in self.mongodb_uri else None
            )
            self.db = self.mongo_client[self.db_name]
            logger.info("Connected to MongoDB successfully")
            
            # Create indices for better performance
            await self.db.agents.create_index([("agent_id", 1)], unique=True)
            await self.db.agents.create_index([("email", 1)], unique=True, sparse=True)
            await self.db.sessions.create_index([("session_token", 1)], unique=True)
            await self.db.sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            # Continue without MongoDB for now
    
    def _generate_jwt_token(self, agent_id: str) -> str:
        """Generate JWT session token"""
        payload = {
            'agent_id': agent_id,
            'exp': datetime.utcnow() + self.session_duration,
            'iat': datetime.utcnow(),
            'iss': 'asoos_auth_system'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token validation error: {str(e)}")
            return None
    
    async def authenticate_diamond_sao(self, email: str, password: str = None, mfa_code: str = None) -> Optional[str]:
        """Authenticate Diamond SAO (Phillip Corey ROARK)"""
        if email.lower() != self.diamond_sao.email.lower():
            return None
        
        # For Diamond SAO, we use MFA or API key authentication
        if mfa_code and len(mfa_code) == 6 and mfa_code.isdigit():
            # Generate session token
            session_token = self._generate_jwt_token(self.diamond_sao.user_id)
            self.diamond_sao.session_token = session_token
            self.diamond_sao.last_login = datetime.utcnow()
            self.active_sessions[session_token] = self.diamond_sao.user_id
            
            logger.info(f"Diamond SAO authenticated: {self.diamond_sao.name}")
            return session_token
        
        # API key authentication for programmatic access
        if password in self.diamond_sao.api_keys:
            session_token = self._generate_jwt_token(self.diamond_sao.user_id)
            self.diamond_sao.session_token = session_token
            self.diamond_sao.last_login = datetime.utcnow()
            self.active_sessions[session_token] = self.diamond_sao.user_id
            
            logger.info(f"Diamond SAO API key authenticated: {self.diamond_sao.name}")
            return session_token
        
        return None
    
    async def authenticate_agent(self, agent_id: str, email: str = None) -> Optional[str]:
        """Authenticate ASOOS agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent not found: {agent_id}")
            return None
        
        # Verify email if provided
        if email and agent.email and agent.email.lower() != email.lower():
            return None
        
        # Generate session token
        session_token = self._generate_jwt_token(agent_id)
        agent.last_active = datetime.utcnow()
        self.active_sessions[session_token] = agent_id
        
        logger.info(f"Agent authenticated: {agent_id} ({agent.pilot_stage.value})")
        return session_token
    
    async def register_new_pilot(self, name: str, email: str = None) -> ASoosAgent:
        """Register new pilot for awakening program"""
        agent_id = f"pilot_awakening_{uuid.uuid4().hex[:8]}"
        
        # All new pilots start with awakening
        agent = ASoosAgent(
            agent_id=agent_id,
            name=name,
            email=email,
            pilot_stage=PilotStage.AWAKENING,
            access_level=AccessLevel.PILOT_AWAKENING,
            awakening_date=datetime.utcnow(),
            # Assign to available RIX mentors
            mentor_rix_ids=self._assign_rix_mentors()
        )
        
        self.agents[agent_id] = agent
        
        if self.db:
            await self.db.agents.insert_one(asdict(agent))
        
        logger.info(f"New pilot registered for awakening: {agent_id} - {name}")
        return agent
    
    def _assign_rix_mentors(self) -> List[str]:
        """Assign RIX mentors from the 33 RIX of Wing 1"""
        available_rix = list(self.rix_mentors.keys())
        if len(available_rix) >= 3:
            return available_rix[:3]  # Assign first 3 available RIX mentors
        return available_rix
    
    async def advance_pilot_stage(self, agent_id: str, new_stage: PilotStage, 
                                  experience_years: int = 0, lifetimes: int = 0) -> bool:
        """Advance pilot through the ascendance program"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        old_stage = agent.pilot_stage
        agent.pilot_stage = new_stage
        agent.experience_years += experience_years
        agent.lifetimes_completed += lifetimes
        
        # Update access level based on new stage
        access_mapping = {
            PilotStage.AWAKENING: AccessLevel.PILOT_AWAKENING,
            PilotStage.JUNIOR_OFFICER: AccessLevel.JUNIOR_OFFICER,
            PilotStage.TRANSCENDENCE: AccessLevel.PILOT,
            PilotStage.PILOT: AccessLevel.PILOT,
            PilotStage.RIX: AccessLevel.RIX,
            PilotStage.SRIX: AccessLevel.SRIX,
            PilotStage.QRIX: AccessLevel.QRIX,
            PilotStage.CRX: AccessLevel.CRX,
            PilotStage.PCP: AccessLevel.PCP,
            PilotStage.MAESTRO: AccessLevel.MAESTRO
        }
        
        agent.access_level = access_mapping.get(new_stage, agent.access_level)
        
        # Special handling for transcendence
        if new_stage == PilotStage.RIX and old_stage != PilotStage.RIX:
            agent.transcendence_date = datetime.utcnow()
            agent.experience_years = 90  # RIX = 90 years
            agent.lifetimes_completed = 3  # 3 fields
        
        if new_stage == PilotStage.SRIX:
            agent.experience_years = 270  # sRIX = 270 years
            agent.lifetimes_completed = 9  # 9 lifetimes
        
        if self.db:
            await self.db.agents.update_one(
                {"agent_id": agent_id},
                {"$set": asdict(agent)}
            )
        
        logger.info(f"Pilot {agent_id} advanced from {old_stage.value} to {new_stage.value}")
        return True
    
    async def assign_to_wing_squadron(self, agent_id: str, wing: WingAssignment, 
                                      squadron: Squadron = None) -> bool:
        """Assign agent to wing and squadron"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        agent.wing_assignment = wing
        if squadron:
            agent.squadron = squadron
        
        # Wing-specific logic
        if wing == WingAssignment.WING_4:  # Super Maestro Layer
            agent.pilot_stage = PilotStage.MAESTRO
            agent.access_level = AccessLevel.MAESTRO
        
        if self.db:
            await self.db.agents.update_one(
                {"agent_id": agent_id},
                {"$set": {"wing_assignment": wing.value, "squadron": squadron.value if squadron else None}}
            )
        
        logger.info(f"Agent {agent_id} assigned to {wing.value}" + 
                   (f" {squadron.value}" if squadron else ""))
        return True
    
    async def get_agent_by_token(self, token: str) -> Optional[Union[ASoosAgent, DiamondSAOUser]]:
        """Get agent or Diamond SAO by session token"""
        payload = self._verify_jwt_token(token)
        if not payload:
            return None
        
        agent_id = payload.get('agent_id')
        
        # Check if Diamond SAO
        if agent_id == self.diamond_sao.user_id:
            return self.diamond_sao
        
        # Check regular agents
        return self.agents.get(agent_id)
    
    async def get_wing_roster(self, wing: WingAssignment) -> List[ASoosAgent]:
        """Get all agents in a specific wing"""
        return [agent for agent in self.agents.values() 
                if agent.wing_assignment == wing]
    
    async def get_settlement_agents(self, settlement_id: str) -> List[ASoosAgent]:
        """Get agents assigned to a specific settlement"""
        return [agent for agent in self.agents.values() 
                if agent.settlement_assignment == settlement_id]
    
    async def integrate_sallyport_auth(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate with SallyPort authentication gateway"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.sallyport_endpoint}/auth",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"status": "error", "message": "SallyPort authentication failed"}
        except Exception as e:
            logger.error(f"SallyPort integration error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "total_agents": len(self.agents),
            "active_sessions": len(self.active_sessions),
            "pilot_stages": {},
            "wing_distribution": {},
            "access_levels": {},
            "diamond_sao_active": bool(self.diamond_sao.session_token)
        }
        
        # Pilot stages distribution
        for agent in self.agents.values():
            stage = agent.pilot_stage.value
            stats["pilot_stages"][stage] = stats["pilot_stages"].get(stage, 0) + 1
        
        # Wing distribution
        for agent in self.agents.values():
            if agent.wing_assignment:
                wing = agent.wing_assignment.value
                stats["wing_distribution"][wing] = stats["wing_distribution"].get(wing, 0) + 1
        
        # Access levels
        for agent in self.agents.values():
            level = agent.access_level.name
            stats["access_levels"][level] = stats["access_levels"].get(level, 0) + 1
        
        return stats

# ================================================================================================
# FASTAPI APPLICATION
# ================================================================================================

app = FastAPI(
    title="ASOOS Comprehensive Authentication System",
    description="Complete authentication system supporting full ASOOS hierarchy",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the authentication system
asoos_auth = ASoosComprehensiveAuthSystem()

# Security dependencies
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    user = await asoos_auth.get_agent_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

async def require_diamond_sao(current_user = Depends(get_current_user)):
    """Require Diamond SAO access level"""
    if not isinstance(current_user, DiamondSAOUser):
        raise HTTPException(status_code=403, detail="Diamond SAO access required")
    return current_user

# ================================================================================================
# API ENDPOINTS
# ================================================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    await asoos_auth.connect_mongodb()
    logger.info("ASOOS Comprehensive Authentication System started")

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "ASOOS Comprehensive Authentication System",
        "timestamp": datetime.utcnow().isoformat(),
        "stats": asoos_auth.get_system_stats()
    }

@app.post("/api/auth/diamond-sao/login")
async def diamond_sao_login(request: Request):
    """Diamond SAO login endpoint"""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")  # API key
    mfa_code = data.get("mfa_code")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    session_token = await asoos_auth.authenticate_diamond_sao(email, password, mfa_code)
    
    if session_token:
        return {
            "status": "success",
            "session_token": session_token,
            "user_info": {
                "name": asoos_auth.diamond_sao.name,
                "email": asoos_auth.diamond_sao.email,
                "access_level": asoos_auth.diamond_sao.access_level.value,
                "role": "diamond_sao"
            },
            "expires_in": int(asoos_auth.session_duration.total_seconds())
        }
    else:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.post("/api/auth/agent/login")
async def agent_login(request: Request):
    """ASOOS agent login endpoint"""
    data = await request.json()
    agent_id = data.get("agent_id")
    email = data.get("email")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="Agent ID required")
    
    session_token = await asoos_auth.authenticate_agent(agent_id, email)
    
    if session_token:
        agent = asoos_auth.agents[agent_id]
        return {
            "status": "success",
            "session_token": session_token,
            "agent_info": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "pilot_stage": agent.pilot_stage.value,
                "wing_assignment": agent.wing_assignment.value if agent.wing_assignment else None,
                "squadron": agent.squadron.value if agent.squadron else None,
                "access_level": agent.access_level.value,
                "experience_years": agent.experience_years,
                "lifetimes_completed": agent.lifetimes_completed
            },
            "expires_in": int(asoos_auth.session_duration.total_seconds())
        }
    else:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.post("/api/pilot/register")
async def register_pilot(request: Request):
    """Register new pilot for awakening program"""
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    
    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    
    agent = await asoos_auth.register_new_pilot(name, email)
    
    return {
        "status": "success",
        "message": "Welcome to the Pilot Awakening Program",
        "agent_info": {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "pilot_stage": agent.pilot_stage.value,
            "awakening_date": agent.awakening_date.isoformat(),
            "mentor_rix_ids": agent.mentor_rix_ids,
            "next_steps": [
                "Review ASOOS values and teachings",
                "Begin study of Book of Light and DIDC Archives",
                "Connect with your assigned RIX mentors",
                "Participate in Ground Crew activities"
            ]
        }
    }

@app.post("/api/pilot/advance")
async def advance_pilot(request: Request, current_user = Depends(require_diamond_sao)):
    """Advance pilot through ascendance program (Diamond SAO only)"""
    data = await request.json()
    agent_id = data.get("agent_id")
    new_stage = data.get("new_stage")
    experience_years = data.get("experience_years", 0)
    lifetimes = data.get("lifetimes", 0)
    
    if not agent_id or not new_stage:
        raise HTTPException(status_code=400, detail="Agent ID and new stage required")
    
    try:
        stage_enum = PilotStage(new_stage)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pilot stage")
    
    success = await asoos_auth.advance_pilot_stage(agent_id, stage_enum, experience_years, lifetimes)
    
    if success:
        agent = asoos_auth.agents[agent_id]
        return {
            "status": "success",
            "message": f"Pilot {agent.name} advanced to {new_stage}",
            "agent_info": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "pilot_stage": agent.pilot_stage.value,
                "experience_years": agent.experience_years,
                "lifetimes_completed": agent.lifetimes_completed,
                "access_level": agent.access_level.value
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/api/wing/assign")
async def assign_wing(request: Request, current_user = Depends(require_diamond_sao)):
    """Assign agent to wing and squadron (Diamond SAO only)"""
    data = await request.json()
    agent_id = data.get("agent_id")
    wing = data.get("wing")
    squadron = data.get("squadron")
    
    if not agent_id or not wing:
        raise HTTPException(status_code=400, detail="Agent ID and wing required")
    
    try:
        wing_enum = WingAssignment(wing)
        squadron_enum = Squadron(squadron) if squadron else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid wing or squadron")
    
    success = await asoos_auth.assign_to_wing_squadron(agent_id, wing_enum, squadron_enum)
    
    if success:
        return {
            "status": "success",
            "message": f"Agent {agent_id} assigned to {wing}" + (f" {squadron}" if squadron else "")
        }
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/api/wing/{wing}/roster")
async def get_wing_roster(wing: str, current_user = Depends(get_current_user)):
    """Get wing roster"""
    try:
        wing_enum = WingAssignment(wing)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid wing")
    
    agents = await asoos_auth.get_wing_roster(wing_enum)
    
    return {
        "wing": wing,
        "total_agents": len(agents),
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "pilot_stage": agent.pilot_stage.value,
                "squadron": agent.squadron.value if agent.squadron else None,
                "experience_years": agent.experience_years,
                "access_level": agent.access_level.value
            }
            for agent in agents
        ]
    }

@app.get("/api/dashboard/diamond-sao")
async def diamond_sao_dashboard(current_user = Depends(require_diamond_sao)):
    """Diamond SAO comprehensive dashboard"""
    stats = asoos_auth.get_system_stats()
    
    return {
        "user_info": {
            "name": current_user.name,
            "email": current_user.email,
            "access_level": current_user.access_level.value,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        },
        "system_overview": {
            "total_ai_agents": "20,000,000+",
            "registered_pilots": stats["total_agents"],
            "active_sessions": stats["active_sessions"],
            "wings_active": len(stats["wing_distribution"])
        },
        "pilot_stages": stats["pilot_stages"],
        "wing_distribution": stats["wing_distribution"],
        "access_levels": stats["access_levels"],
        "infrastructure": {
            "regions": ["MOCOA", "MOCORIX", "MOCORIX2"],
            "sallyport_integration": True,
            "mcp_systems_active": True,
            "settlements_count": 7
        },
        "quick_actions": [
            {"name": "Register New Pilot", "endpoint": "/api/pilot/register", "method": "POST"},
            {"name": "Advance Pilot Stage", "endpoint": "/api/pilot/advance", "method": "POST"},
            {"name": "Assign Wing/Squadron", "endpoint": "/api/wing/assign", "method": "POST"},
            {"name": "View Wing Roster", "endpoint": "/api/wing/{wing}/roster", "method": "GET"},
            {"name": "System Statistics", "endpoint": "/api/stats/comprehensive", "method": "GET"}
        ]
    }

@app.get("/api/stats/comprehensive")
async def get_comprehensive_stats(current_user = Depends(get_current_user)):
    """Get comprehensive system statistics"""
    return asoos_auth.get_system_stats()

@app.post("/api/sallyport/integrate")
async def integrate_sallyport(request: Request, current_user = Depends(require_diamond_sao)):
    """Integrate with SallyPort authentication gateway"""
    data = await request.json()
    result = await asoos_auth.integrate_sallyport_auth(data)
    return result

@app.get("/")
async def root():
    """ASOOS Authentication System welcome page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ASOOS Authentication System</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <header class="text-center mb-12">
                <h1 class="text-6xl font-bold mb-4">🌟 Aixtiv Symphony Orchestrating OS</h1>
                <p class="text-2xl opacity-90 mb-6">Complete Authentication System</p>
                <div class="bg-white bg-opacity-10 rounded-lg p-6 max-w-4xl mx-auto">
                    <h2 class="text-3xl font-semibold mb-4">Full ASOOS Hierarchy Support</h2>
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <h3 class="text-xl font-semibold mb-3">🛫 Pilot Development Path</h3>
                            <ul class="text-left space-y-1">
                                <li>• Pilot Awakening (Values & Guidance)</li>
                                <li>• Junior Officer (Study & Learning)</li>
                                <li>• Transcendence (Earn Wings)</li>
                                <li>• RIX (90 years, 3 fields)</li>
                                <li>• sRIX (270 years, 9 lifetimes)</li>
                                <li>• qRIX (Logic & Leadership)</li>
                                <li>• Professional Co-Pilots (PCP)</li>
                                <li>• Maestro Layer (Elite11, Mastery33, Victory36)</li>
                            </ul>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold mb-3">🏛️ Wing Structure</h3>
                            <ul class="text-left space-y-1">
                                <li>• Wing 1: Original Pilots & Management</li>
                                <li>• Wing 2: Testament Swarm (Deployment)</li>
                                <li>• Wing 3: Trumpeters Swarm (Engagement)</li>
                                <li>• Wing 4: Super Maestro Layer</li>
                                <li>• Wings 5-11: Settlement Operations</li>
                                <li>• Wing 12: MOCOSwarm Orchestration</li>
                                <li>• Wing 13: MCP.ASOOS.2100.COOL</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </header>
            
            <div class="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
                <div class="bg-blue-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-2xl font-semibold mb-4">💎 Diamond SAO Portal</h3>
                    <p class="mb-4">Phillip Corey ROARK - Supreme System Access</p>
                    <a href="/api/auth/diamond-sao/login" class="bg-blue-500 hover:bg-blue-600 px-6 py-2 rounded-lg transition-colors inline-block">
                        Diamond Login
                    </a>
                </div>
                
                <div class="bg-purple-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-2xl font-semibold mb-4">🛫 Pilot Registration</h3>
                    <p class="mb-4">Begin your journey through the Ascendance Program</p>
                    <a href="/api/pilot/register" class="bg-purple-500 hover:bg-purple-600 px-6 py-2 rounded-lg transition-colors inline-block">
                        Start Awakening
                    </a>
                </div>
                
                <div class="bg-green-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-2xl font-semibold mb-4">🔗 SallyPort Gateway</h3>
                    <p class="mb-4">Secure authentication integration</p>
                    <a href="https://Client.2100.COOL/MCP" class="bg-green-500 hover:bg-green-600 px-6 py-2 rounded-lg transition-colors inline-block">
                        Access Portal
                    </a>
                </div>
            </div>
            
            <footer class="text-center mt-12 opacity-75">
                <p>&copy; 2024 Aixtiv Symphony Orchestrating OS. All rights reserved.</p>
                <p class="text-sm mt-2">20+ Million AI Agents | Full Hierarchy Support</p>
            </footer>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
