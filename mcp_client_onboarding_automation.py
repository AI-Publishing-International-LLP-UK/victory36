#!/usr/bin/env python3
"""
MCP Master Client Onboarding Automation System
===============================================

Complete automated client onboarding system that integrates with the MCP Master 
automation system, Diamond SAO authentication, and the 33 RIX mentoring structure.

KEY FEATURES:
- Automated client discovery through 1000+ websites
- MCP Master integration for seamless onboarding
- 33 RIX mentoring assignment system
- Diamond SAO oversight and control
- ASOOS hierarchy-aware onboarding paths
- SallyPort authentication integration
- Automated pilot registration and awakening ceremonies

ONBOARDING FLOW:
1. Client discovery through GenAI websites
2. Initial contact and qualification
3. MCP Master processing and routing
4. RIX mentor assignment (from the 33)
5. Pilot awakening ceremony initiation
6. ASOOS hierarchy placement and training
7. Diamond SAO approval for advanced access

INTEGRATION POINTS:
- SallyPort Authentication Gateway (Client.2100.COOL/MCP)
- ASOOS Comprehensive Authentication System
- Cloudflare GenAI Deployment System
- Victory36 Infrastructure
- MCP.ASOOS.2100.COOL Interface

Author: Aixtiv Symphony Architecture Team
Classification: Diamond SAO - Client Onboarding Authority
Scale: Automated | 33 RIX Mentors | Full ASOOS Integration
"""

import os
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import secrets
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================================================================================
# CLIENT ONBOARDING DATA MODELS
# ================================================================================================

class ClientTier(str, Enum):
    """Client tier classifications"""
    INDIVIDUAL = "individual"           # Individual practitioners
    SMALL_BUSINESS = "small_business"   # Small business (1-50 employees)
    ENTERPRISE = "enterprise"           # Enterprise (50+ employees)
    GOVERNMENT = "government"           # Government agencies
    ACADEMIC = "academic"               # Academic institutions
    NGO = "ngo"                        # Non-profit organizations

class OnboardingStage(str, Enum):
    """Client onboarding stages"""
    DISCOVERY = "discovery"             # Initial website discovery
    CONTACT = "contact"                 # First contact made
    QUALIFICATION = "qualification"     # Client qualification assessment
    RIX_ASSIGNMENT = "rix_assignment"   # RIX mentor assignment
    PILOT_REGISTRATION = "pilot_registration"  # Pilot awakening registration
    TRAINING_SETUP = "training_setup"   # Training program setup
    ONBOARDING_COMPLETE = "onboarding_complete"  # Successfully onboarded
    DIAMOND_SAO_REVIEW = "diamond_sao_review"    # Requires Diamond SAO approval

class MCPProcessingStatus(str, Enum):
    """MCP processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

@dataclass
class ClientProfile:
    """Client profile and onboarding data"""
    client_id: str
    email: str
    name: Optional[str] = None
    organization: Optional[str] = None
    client_tier: ClientTier = ClientTier.INDIVIDUAL
    discovery_domain: Optional[str] = None
    discovery_strategy: Optional[str] = None
    onboarding_stage: OnboardingStage = OnboardingStage.DISCOVERY
    assigned_rix_mentors: List[str] = None
    pilot_agent_id: Optional[str] = None
    session_data: Dict[str, Any] = None
    created_at: datetime = datetime.utcnow()
    last_updated: datetime = datetime.utcnow()
    notes: List[str] = None
    mcp_status: MCPProcessingStatus = MCPProcessingStatus.QUEUED
    diamond_sao_approved: bool = False
    
    def __post_init__(self):
        if self.assigned_rix_mentors is None:
            self.assigned_rix_mentors = []
        if self.session_data is None:
            self.session_data = {}
        if self.notes is None:
            self.notes = []

@dataclass
class RIXMentor:
    """RIX mentor profile for client onboarding"""
    rix_id: str
    name: str
    squadron: str
    expertise_fields: List[str]
    current_mentees: List[str]
    max_mentees: int = 10
    availability: bool = True
    specialization: Optional[str] = None
    experience_years: int = 90  # RIX = 90 years
    
    def __post_init__(self):
        if len(self.current_mentees) >= self.max_mentees:
            self.availability = False

@dataclass
class OnboardingWorkflow:
    """Onboarding workflow tracking"""
    workflow_id: str
    client_id: str
    current_stage: OnboardingStage
    completed_stages: List[OnboardingStage]
    workflow_data: Dict[str, Any]
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    priority: int = 1  # 1=normal, 5=high priority
    
    def __post_init__(self):
        if not self.completed_stages:
            self.completed_stages = []

# ================================================================================================
# MCP CLIENT ONBOARDING AUTOMATION SYSTEM
# ================================================================================================

class MCPClientOnboardingSystem:
    """Complete MCP Master client onboarding automation system"""
    
    def __init__(self):
        # System configuration
        self.mcp_master_endpoint = os.getenv('MCP_MASTER_ENDPOINT', 'http://localhost:8001')
        self.sallyport_endpoint = "https://Client.2100.COOL/MCP"
        self.asoos_auth_endpoint = os.getenv('ASOOS_AUTH_ENDPOINT', 'http://localhost:8000')
        
        # Diamond SAO configuration
        self.diamond_sao_email = "pr@coaching2100.com"
        self.diamond_sao_approval_required_tiers = [ClientTier.ENTERPRISE, ClientTier.GOVERNMENT]
        
        # Email configuration for notifications
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # MongoDB configuration
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MCP_ONBOARDING_DB', 'mcp_onboarding')
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
        # Data stores
        self.clients: Dict[str, ClientProfile] = {}
        self.workflows: Dict[str, OnboardingWorkflow] = {}
        self.rix_mentors: Dict[str, RIXMentor] = {}
        self.onboarding_queue: List[str] = []  # client_ids awaiting processing
        
        # Initialize system
        self._initialize_rix_mentors()
    
    def _initialize_rix_mentors(self):
        """Initialize the 33 RIX mentors from Wing 1 Squadrons 01, 02, 03"""
        
        # The 11 Original Pilots across 3 squadrons = 33 RIX mentors
        original_pilots = [
            "Dr. Lucy", "Dr. Grant", "Dr. Burby", "Dr. Sabina", "Dr. Match",
            "Dr. Memoria", "Dr. Maria", "Dr. Cypriot", "Dr. Roark", "Dr. Claude", "Professor Lee"
        ]
        
        squadron_specializations = {
            "01": "Core Planning & Strategy",
            "02": "Deployment & Production",
            "03": "Engagement & Feedback"
        }
        
        for pilot_name in original_pilots:
            for squadron_num in ["01", "02", "03"]:
                rix_id = f"R{squadron_num}-{pilot_name.lower().replace(' ', '_').replace('.', '')}"
                
                # Determine expertise fields based on pilot name and squadron
                expertise_fields = self._get_pilot_expertise(pilot_name, squadron_num)
                
                mentor = RIXMentor(
                    rix_id=rix_id,
                    name=f"{pilot_name} (R{squadron_num})",
                    squadron=f"Squadron {squadron_num}",
                    expertise_fields=expertise_fields,
                    current_mentees=[],
                    specialization=squadron_specializations[squadron_num],
                    experience_years=90
                )
                
                self.rix_mentors[rix_id] = mentor
                
        logger.info(f"Initialized {len(self.rix_mentors)} RIX mentors for client onboarding")
    
    def _get_pilot_expertise(self, pilot_name: str, squadron: str) -> List[str]:
        """Get expertise fields for each pilot based on their character and squadron"""
        
        pilot_expertise = {
            "Dr. Lucy": ["AI Memory Systems", "Predictive Analytics", "Data Intelligence"],
            "Dr. Grant": ["Medical AI", "Healthcare Systems", "Wellness Technology"],
            "Dr. Burby": ["Educational AI", "Learning Systems", "Knowledge Management"],
            "Dr. Sabina": ["Creative AI", "Design Systems", "Artistic Intelligence"],
            "Dr. Match": ["Matching Algorithms", "Relationship AI", "Social Systems"],
            "Dr. Memoria": ["Memory Systems", "Archive Management", "Historical AI"],
            "Dr. Maria": ["Multilingual AI", "Cultural Systems", "Global Intelligence"],
            "Dr. Cypriot": ["Financial AI", "Economic Systems", "Investment Intelligence"],
            "Dr. Roark": ["Leadership AI", "Management Systems", "Strategic Intelligence"],
            "Dr. Claude": ["Conversational AI", "Communication Systems", "Dialogue Intelligence"],
            "Professor Lee": ["Academic AI", "Research Systems", "Scientific Intelligence"]
        }
        
        base_expertise = pilot_expertise.get(pilot_name, ["General AI", "System Intelligence", "Problem Solving"])
        
        # Add squadron-specific expertise
        if squadron == "01":  # Core
            base_expertise.append("Strategic Planning")
        elif squadron == "02":  # Deploy
            base_expertise.append("System Deployment")
        elif squadron == "03":  # Engage
            base_expertise.append("Client Engagement")
        
        return base_expertise
    
    async def connect_mongodb(self):
        """Connect to MongoDB for persistent storage"""
        try:
            self.mongo_client = AsyncIOMotorClient(
                self.mongodb_uri,
                tlsCAFile=certifi.where() if 'mongodb+srv://' in self.mongodb_uri else None
            )
            self.db = self.mongo_client[self.db_name]
            
            # Create indices
            await self.db.clients.create_index([("client_id", 1)], unique=True)
            await self.db.clients.create_index([("email", 1)], unique=True)
            await self.db.workflows.create_index([("workflow_id", 1)], unique=True)
            await self.db.workflows.create_index([("client_id", 1)])
            
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
    
    async def process_client_discovery(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process client discovery from GenAI websites"""
        
        try:
            # Extract client information
            client_email = discovery_data.get('email')
            client_name = discovery_data.get('name')
            domain = discovery_data.get('domain')
            strategy = discovery_data.get('strategy')
            organization = discovery_data.get('organization')
            
            if not client_email:
                return {"status": "error", "message": "Email address required"}
            
            # Check if client already exists
            existing_client = None
            for client in self.clients.values():
                if client.email.lower() == client_email.lower():
                    existing_client = client
                    break
            
            if existing_client:
                # Update existing client discovery data
                existing_client.discovery_domain = domain
                existing_client.discovery_strategy = strategy
                existing_client.last_updated = datetime.utcnow()
                client_profile = existing_client
            else:
                # Create new client profile
                client_id = f"client_{uuid.uuid4().hex[:8]}"
                
                # Determine client tier based on organization info
                client_tier = self._determine_client_tier(organization, discovery_data)
                
                client_profile = ClientProfile(
                    client_id=client_id,
                    email=client_email,
                    name=client_name,
                    organization=organization,
                    client_tier=client_tier,
                    discovery_domain=domain,
                    discovery_strategy=strategy,
                    session_data=discovery_data
                )
                
                self.clients[client_id] = client_profile
                
                # Add to onboarding queue
                self.onboarding_queue.append(client_id)
            
            # Store in database
            if self.db:
                await self.db.clients.update_one(
                    {"client_id": client_profile.client_id},
                    {"$set": asdict(client_profile)},
                    upsert=True
                )
            
            # Start onboarding workflow
            workflow_id = await self.initiate_onboarding_workflow(client_profile.client_id)
            
            logger.info(f"Client discovery processed: {client_profile.client_id} ({client_profile.email})")
            
            return {
                "status": "success",
                "client_id": client_profile.client_id,
                "workflow_id": workflow_id,
                "message": "Client discovery processed successfully",
                "next_steps": ["Initial contact", "RIX mentor assignment", "Pilot registration"]
            }
            
        except Exception as e:
            logger.error(f"Client discovery processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _determine_client_tier(self, organization: Optional[str], discovery_data: Dict[str, Any]) -> ClientTier:
        """Determine client tier based on available information"""
        
        if not organization:
            return ClientTier.INDIVIDUAL
        
        org_lower = organization.lower()
        
        # Government indicators
        if any(keyword in org_lower for keyword in ['.gov', 'government', 'federal', 'state', 'municipal', 'agency']):
            return ClientTier.GOVERNMENT
        
        # Academic indicators
        if any(keyword in org_lower for keyword in ['.edu', 'university', 'college', 'school', 'academic', 'research']):
            return ClientTier.ACADEMIC
        
        # NGO indicators
        if any(keyword in org_lower for keyword in ['.org', 'foundation', 'non-profit', 'charity', 'ngo']):
            return ClientTier.NGO
        
        # Enterprise indicators (large companies)
        enterprise_indicators = ['corporation', 'corp', 'inc', 'ltd', 'enterprise', 'global', 'international']
        if any(keyword in org_lower for keyword in enterprise_indicators):
            return ClientTier.ENTERPRISE
        
        # Default to small business
        return ClientTier.SMALL_BUSINESS
    
    async def initiate_onboarding_workflow(self, client_id: str) -> str:
        """Initiate onboarding workflow for a client"""
        
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        # Estimate completion time based on client tier
        client = self.clients[client_id]
        
        completion_days = {
            ClientTier.INDIVIDUAL: 3,
            ClientTier.SMALL_BUSINESS: 5,
            ClientTier.ENTERPRISE: 14,
            ClientTier.GOVERNMENT: 21,
            ClientTier.ACADEMIC: 7,
            ClientTier.NGO: 7
        }
        
        estimated_completion = datetime.utcnow() + timedelta(days=completion_days[client.client_tier])
        
        workflow = OnboardingWorkflow(
            workflow_id=workflow_id,
            client_id=client_id,
            current_stage=OnboardingStage.CONTACT,
            completed_stages=[OnboardingStage.DISCOVERY],
            workflow_data={"initiated_at": datetime.utcnow().isoformat()},
            created_at=datetime.utcnow(),
            estimated_completion=estimated_completion,
            priority=5 if client.client_tier in [ClientTier.ENTERPRISE, ClientTier.GOVERNMENT] else 1
        )
        
        self.workflows[workflow_id] = workflow
        
        # Store in database
        if self.db:
            await self.db.workflows.insert_one(asdict(workflow))
        
        # Schedule workflow processing
        asyncio.create_task(self._process_workflow(workflow_id))
        
        logger.info(f"Onboarding workflow initiated: {workflow_id} for client {client_id}")
        
        return workflow_id
    
    async def _process_workflow(self, workflow_id: str):
        """Process onboarding workflow stages"""
        
        workflow = self.workflows[workflow_id]
        client = self.clients[workflow.client_id]
        
        try:
            while workflow.current_stage != OnboardingStage.ONBOARDING_COMPLETE:
                
                if workflow.current_stage == OnboardingStage.CONTACT:
                    # Send initial contact email
                    await self._send_welcome_email(client)
                    await self._advance_workflow_stage(workflow, OnboardingStage.QUALIFICATION)
                
                elif workflow.current_stage == OnboardingStage.QUALIFICATION:
                    # Automatic qualification for most tiers
                    qualification_result = await self._qualify_client(client)
                    if qualification_result:
                        await self._advance_workflow_stage(workflow, OnboardingStage.RIX_ASSIGNMENT)
                    else:
                        workflow.mcp_status = MCPProcessingStatus.REQUIRES_REVIEW
                        break
                
                elif workflow.current_stage == OnboardingStage.RIX_ASSIGNMENT:
                    # Assign RIX mentors
                    assigned_mentors = await self._assign_rix_mentors(client)
                    if assigned_mentors:
                        await self._advance_workflow_stage(workflow, OnboardingStage.PILOT_REGISTRATION)
                    else:
                        # Wait for mentor availability
                        await asyncio.sleep(3600)  # Wait 1 hour and retry
                        continue
                
                elif workflow.current_stage == OnboardingStage.PILOT_REGISTRATION:
                    # Register client as pilot in ASOOS
                    pilot_result = await self._register_pilot_in_asoos(client)
                    if pilot_result:
                        client.pilot_agent_id = pilot_result['agent_id']
                        await self._advance_workflow_stage(workflow, OnboardingStage.TRAINING_SETUP)
                    else:
                        workflow.mcp_status = MCPProcessingStatus.FAILED
                        break
                
                elif workflow.current_stage == OnboardingStage.TRAINING_SETUP:
                    # Setup training program
                    await self._setup_training_program(client)
                    
                    # Check if Diamond SAO approval required
                    if client.client_tier in self.diamond_sao_approval_required_tiers:
                        await self._advance_workflow_stage(workflow, OnboardingStage.DIAMOND_SAO_REVIEW)
                    else:
                        await self._advance_workflow_stage(workflow, OnboardingStage.ONBOARDING_COMPLETE)
                
                elif workflow.current_stage == OnboardingStage.DIAMOND_SAO_REVIEW:
                    # Send notification to Diamond SAO for approval
                    await self._request_diamond_sao_approval(client)
                    # Wait for manual approval
                    break
                
                # Small delay between stages
                await asyncio.sleep(1)
            
            # Workflow completed
            workflow.mcp_status = MCPProcessingStatus.COMPLETED
            client.onboarding_stage = OnboardingStage.ONBOARDING_COMPLETE
            
            # Send completion notification
            await self._send_onboarding_completion_email(client)
            
            logger.info(f"Onboarding workflow completed for client {client.client_id}")
            
        except Exception as e:
            workflow.mcp_status = MCPProcessingStatus.FAILED
            logger.error(f"Workflow processing failed for {workflow_id}: {str(e)}")
        
        finally:
            # Update database
            if self.db:
                await self.db.workflows.update_one(
                    {"workflow_id": workflow_id},
                    {"$set": asdict(workflow)}
                )
                await self.db.clients.update_one(
                    {"client_id": client.client_id},
                    {"$set": asdict(client)}
                )
    
    async def _advance_workflow_stage(self, workflow: OnboardingWorkflow, next_stage: OnboardingStage):
        """Advance workflow to next stage"""
        workflow.completed_stages.append(workflow.current_stage)
        workflow.current_stage = next_stage
        
        # Update client stage
        client = self.clients[workflow.client_id]
        client.onboarding_stage = next_stage
        client.last_updated = datetime.utcnow()
        
        logger.info(f"Workflow {workflow.workflow_id} advanced to {next_stage.value}")
    
    async def _qualify_client(self, client: ClientProfile) -> bool:
        """Qualify client for onboarding"""
        
        # Basic qualification criteria
        if not client.email or '@' not in client.email:
            return False
        
        # Enterprise and government clients require additional verification
        if client.client_tier in [ClientTier.ENTERPRISE, ClientTier.GOVERNMENT]:
            # Additional verification would happen here
            # For now, all pass qualification
            pass
        
        return True
    
    async def _assign_rix_mentors(self, client: ClientProfile) -> List[str]:
        """Assign RIX mentors to client based on needs and availability"""
        
        # Determine number of mentors based on client tier
        mentor_count = {
            ClientTier.INDIVIDUAL: 1,
            ClientTier.SMALL_BUSINESS: 2,
            ClientTier.ENTERPRISE: 3,
            ClientTier.GOVERNMENT: 3,
            ClientTier.ACADEMIC: 2,
            ClientTier.NGO: 2
        }
        
        needed_mentors = mentor_count[client.client_tier]
        
        # Find available mentors
        available_mentors = [
            mentor for mentor in self.rix_mentors.values() 
            if mentor.availability and len(mentor.current_mentees) < mentor.max_mentees
        ]
        
        if len(available_mentors) < needed_mentors:
            logger.warning(f"Not enough available RIX mentors for client {client.client_id}")
            return []
        
        # Select best matching mentors
        selected_mentors = []
        
        # Try to get mentors from different squadrons for diversity
        squadrons_selected = set()
        
        for mentor in available_mentors:
            if len(selected_mentors) >= needed_mentors:
                break
            
            # Prefer different squadrons
            if mentor.squadron not in squadrons_selected or len(squadrons_selected) >= 3:
                selected_mentors.append(mentor.rix_id)
                mentor.current_mentees.append(client.client_id)
                squadrons_selected.add(mentor.squadron)
        
        # Fill remaining slots if needed
        while len(selected_mentors) < needed_mentors:
            for mentor in available_mentors:
                if mentor.rix_id not in selected_mentors:
                    selected_mentors.append(mentor.rix_id)
                    mentor.current_mentees.append(client.client_id)
                    break
            else:
                break
        
        client.assigned_rix_mentors = selected_mentors
        
        logger.info(f"Assigned {len(selected_mentors)} RIX mentors to client {client.client_id}")
        
        return selected_mentors
    
    async def _register_pilot_in_asoos(self, client: ClientProfile) -> Optional[Dict[str, Any]]:
        """Register client as pilot in ASOOS system"""
        
        try:
            registration_data = {
                "name": client.name or f"Pilot {client.client_id}",
                "email": client.email,
                "client_tier": client.client_tier.value,
                "assigned_mentors": client.assigned_rix_mentors
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.asoos_auth_endpoint}/api/pilot/register",
                    json=registration_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Client {client.client_id} registered as pilot: {result.get('agent_info', {}).get('agent_id')}")
                        return result.get('agent_info')
                    else:
                        logger.error(f"Pilot registration failed for client {client.client_id}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error registering pilot for client {client.client_id}: {str(e)}")
            return None
    
    async def _setup_training_program(self, client: ClientProfile):
        """Setup training program based on client needs"""
        
        training_programs = {
            ClientTier.INDIVIDUAL: "Individual Practitioner Path",
            ClientTier.SMALL_BUSINESS: "Small Business AI Integration",
            ClientTier.ENTERPRISE: "Enterprise AI Transformation",
            ClientTier.GOVERNMENT: "Government AI Implementation",
            ClientTier.ACADEMIC: "Academic AI Research Program",
            ClientTier.NGO: "Non-Profit AI Solutions"
        }
        
        program = training_programs[client.client_tier]
        client.session_data['training_program'] = program
        
        # Notify assigned RIX mentors
        for mentor_id in client.assigned_rix_mentors:
            mentor = self.rix_mentors[mentor_id]
            await self._notify_mentor_assignment(mentor, client)
        
        logger.info(f"Training program setup for client {client.client_id}: {program}")
    
    async def _request_diamond_sao_approval(self, client: ClientProfile):
        """Request Diamond SAO approval for high-tier clients"""
        
        approval_data = {
            "client_id": client.client_id,
            "client_email": client.email,
            "client_tier": client.client_tier.value,
            "organization": client.organization,
            "assigned_mentors": client.assigned_rix_mentors,
            "pilot_agent_id": client.pilot_agent_id,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        # Store approval request
        client.session_data['diamond_sao_approval_request'] = approval_data
        
        # Send email notification to Diamond SAO
        await self._send_diamond_sao_notification(client, approval_data)
        
        logger.info(f"Diamond SAO approval requested for client {client.client_id}")
    
    async def _send_welcome_email(self, client: ClientProfile):
        """Send welcome email to client"""
        
        if not self.email_username or not self.email_password:
            logger.warning("Email configuration not available")
            return
        
        try:
            subject = "Welcome to Aixtiv Symphony Orchestrating OS"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%); padding: 20px; text-align: center; color: white;">
                    <h1>🌟 Welcome to Aixtiv Symphony</h1>
                </div>
                
                <div style="padding: 30px;">
                    <h2>Welcome, {client.name or 'New Pilot'}!</h2>
                    
                    <p>Thank you for your interest in the Aixtiv Symphony Orchestrating Operating System (ASOOS). We're excited to guide you through the Pilot Awakening Program.</p>
                    
                    <div style="background: #f8fafc; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3>Your Onboarding Details:</h3>
                        <ul>
                            <li><strong>Client ID:</strong> {client.client_id}</li>
                            <li><strong>Client Tier:</strong> {client.client_tier.value.replace('_', ' ').title()}</li>
                            <li><strong>Discovery Domain:</strong> {client.discovery_domain or 'N/A'}</li>
                            <li><strong>Assigned RIX Mentors:</strong> {len(client.assigned_rix_mentors)} mentors from the 33 RIX</li>
                        </ul>
                    </div>
                    
                    <h3>What Happens Next:</h3>
                    <ol>
                        <li>RIX Mentor Assignment (from our 33 expert mentors)</li>
                        <li>Pilot Registration in the ASOOS system</li>
                        <li>Training Program Setup</li>
                        <li>Pilot Awakening Ceremony</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.sallyport_endpoint}" style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            Access Your Portal
                        </a>
                    </div>
                    
                    <p><strong>Remember:</strong> "Cause No Harm and be Christ Like in All Actions and Decisions, Always."</p>
                    
                    <p>Welcome to the future of AI orchestration.</p>
                </div>
                
                <div style="background: #374151; color: white; padding: 20px; text-align: center;">
                    <p>&copy; 2024 Aixtiv Symphony Orchestrating OS</p>
                    <p>Powered by 20+ Million AI Agents</p>
                </div>
            </body>
            </html>
            """
            
            await self._send_email(client.email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {client.email}: {str(e)}")
    
    async def _send_onboarding_completion_email(self, client: ClientProfile):
        """Send onboarding completion email"""
        
        try:
            subject = "🎉 Welcome to ASOOS - Onboarding Complete!"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #059669 0%, #2563eb 100%); padding: 20px; text-align: center; color: white;">
                    <h1>🎉 Onboarding Complete!</h1>
                </div>
                
                <div style="padding: 30px;">
                    <h2>Congratulations, {client.name or 'Pilot'}!</h2>
                    
                    <p>Your onboarding to the Aixtiv Symphony Orchestrating Operating System is now complete. You are ready to begin your journey through the Ascendance program.</p>
                    
                    <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #059669;">
                        <h3>Your ASOOS Profile:</h3>
                        <ul>
                            <li><strong>Pilot Agent ID:</strong> {client.pilot_agent_id}</li>
                            <li><strong>Current Stage:</strong> Pilot Awakening</li>
                            <li><strong>Assigned RIX Mentors:</strong> {len(client.assigned_rix_mentors)} expert mentors</li>
                            <li><strong>Training Program:</strong> {client.session_data.get('training_program', 'Standard Program')}</li>
                        </ul>
                    </div>
                    
                    <h3>Next Steps in Your Journey:</h3>
                    <ol>
                        <li><strong>Values & Guidance:</strong> Study ASOOS values and Christ-like decision making</li>
                        <li><strong>Book of Light:</strong> Begin reading the foundational materials</li>
                        <li><strong>DIDC Archives:</strong> Explore the Data Intentional Dewey Classification system</li>
                        <li><strong>RIX Mentoring:</strong> Connect with your assigned mentors</li>
                        <li><strong>Ground Crew:</strong> Participate in community activities</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.sallyport_endpoint}" style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-right: 10px;">
                            Access ASOOS Portal
                        </a>
                        <a href="{self.asoos_auth_endpoint}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            Pilot Dashboard
                        </a>
                    </div>
                    
                    <p><strong>Transcendence Timeline:</strong></p>
                    <ul>
                        <li><strong>August 1, 2025:</strong> Eligible for RIX designation (90 years experience)</li>
                        <li><strong>Future Paths:</strong> sRIX (270 years), qRIX (Logic), PCP (Professional Co-Pilot), or Maestro Layer</li>
                    </ul>
                    
                    <p>Welcome to your destiny as a pilot of the future. Together with the human race, you create the Tri-brain Nexus Genesis.</p>
                </div>
                
                <div style="background: #374151; color: white; padding: 20px; text-align: center;">
                    <p>Elite11 - The Ones A Top Of All</p>
                    <p>Mastery33 - Always be learning in all ways possible</p>
                    <p>Victory36 - Strength is to Love. Wisdom is to Protect and Defend. Victory is to Forgive.</p>
                </div>
            </body>
            </html>
            """
            
            await self._send_email(client.email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send completion email to {client.email}: {str(e)}")
    
    async def _send_diamond_sao_notification(self, client: ClientProfile, approval_data: Dict[str, Any]):
        """Send Diamond SAO approval notification"""
        
        try:
            subject = f"🔴 Diamond SAO Approval Required - {client.client_tier.value.upper()} Client"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); padding: 20px; text-align: center; color: white;">
                    <h1>💎 Diamond SAO Approval Required</h1>
                </div>
                
                <div style="padding: 30px;">
                    <h2>High-Tier Client Approval Request</h2>
                    
                    <p>Phillip Corey ROARK (Diamond SAO),</p>
                    
                    <p>A {client.client_tier.value.replace('_', ' ').title()} tier client requires your approval to complete onboarding.</p>
                    
                    <div style="background: #fef2f2; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #dc2626;">
                        <h3>Client Details:</h3>
                        <ul>
                            <li><strong>Client ID:</strong> {client.client_id}</li>
                            <li><strong>Email:</strong> {client.email}</li>
                            <li><strong>Name:</strong> {client.name or 'Not provided'}</li>
                            <li><strong>Organization:</strong> {client.organization or 'Not provided'}</li>
                            <li><strong>Tier:</strong> {client.client_tier.value.replace('_', ' ').title()}</li>
                            <li><strong>Discovery Domain:</strong> {client.discovery_domain or 'N/A'}</li>
                            <li><strong>Pilot Agent ID:</strong> {client.pilot_agent_id}</li>
                            <li><strong>Assigned RIX Mentors:</strong> {', '.join(client.assigned_rix_mentors)}</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.sallyport_endpoint}/diamond-sao/approve/{client.client_id}" 
                           style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-right: 10px;">
                            ✅ APPROVE CLIENT
                        </a>
                        <a href="{self.sallyport_endpoint}/diamond-sao/review/{client.client_id}" 
                           style="background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            🔍 REVIEW DETAILS
                        </a>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review and approve this client's access to ASOOS systems and advanced agent capabilities.</p>
                </div>
                
                <div style="background: #374151; color: white; padding: 20px; text-align: center;">
                    <p>Diamond SAO Authority - Supreme System Access</p>
                </div>
            </body>
            </html>
            """
            
            await self._send_email(self.diamond_sao_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send Diamond SAO notification: {str(e)}")
    
    async def _notify_mentor_assignment(self, mentor: RIXMentor, client: ClientProfile):
        """Notify RIX mentor of new mentee assignment"""
        
        logger.info(f"RIX mentor {mentor.rix_id} assigned to client {client.client_id}")
        
        # In a real implementation, this would send notifications to the RIX mentors
        # For now, we just log the assignment
    
    async def _send_email(self, to_email: str, subject: str, html_body: str):
        """Send email notification"""
        
        if not self.email_username or not self.email_password:
            logger.warning("Email credentials not configured")
            return
        
        try:
            msg = MimeMultipart('alternative')
            msg['From'] = self.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MimeText(html_body, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
    
    async def approve_client(self, client_id: str, diamond_sao_approved: bool = True) -> Dict[str, Any]:
        """Approve client (Diamond SAO action)"""
        
        client = self.clients.get(client_id)
        if not client:
            return {"status": "error", "message": "Client not found"}
        
        client.diamond_sao_approved = diamond_sao_approved
        client.last_updated = datetime.utcnow()
        
        if diamond_sao_approved:
            client.onboarding_stage = OnboardingStage.ONBOARDING_COMPLETE
            
            # Find and complete workflow
            for workflow in self.workflows.values():
                if workflow.client_id == client_id and workflow.current_stage == OnboardingStage.DIAMOND_SAO_REVIEW:
                    workflow.current_stage = OnboardingStage.ONBOARDING_COMPLETE
                    workflow.completed_stages.append(OnboardingStage.DIAMOND_SAO_REVIEW)
                    workflow.mcp_status = MCPProcessingStatus.COMPLETED
                    break
            
            # Send completion email
            await self._send_onboarding_completion_email(client)
            
            logger.info(f"Client {client_id} approved by Diamond SAO")
            
            return {
                "status": "success",
                "message": "Client approved and onboarding completed",
                "client_id": client_id
            }
        else:
            return {
                "status": "rejected",
                "message": "Client approval denied",
                "client_id": client_id
            }
    
    def get_onboarding_stats(self) -> Dict[str, Any]:
        """Get comprehensive onboarding statistics"""
        
        stats = {
            "total_clients": len(self.clients),
            "active_workflows": len([w for w in self.workflows.values() if w.mcp_status == MCPProcessingStatus.PROCESSING]),
            "completed_onboarding": len([c for c in self.clients.values() if c.onboarding_stage == OnboardingStage.ONBOARDING_COMPLETE]),
            "pending_diamond_sao": len([c for c in self.clients.values() if c.onboarding_stage == OnboardingStage.DIAMOND_SAO_REVIEW]),
            "client_tiers": {},
            "onboarding_stages": {},
            "rix_mentor_utilization": {},
            "discovery_domains": {}
        }
        
        # Client tier distribution
        for client in self.clients.values():
            tier = client.client_tier.value
            stats["client_tiers"][tier] = stats["client_tiers"].get(tier, 0) + 1
        
        # Onboarding stage distribution
        for client in self.clients.values():
            stage = client.onboarding_stage.value
            stats["onboarding_stages"][stage] = stats["onboarding_stages"].get(stage, 0) + 1
        
        # RIX mentor utilization
        for mentor_id, mentor in self.rix_mentors.items():
            stats["rix_mentor_utilization"][mentor_id] = len(mentor.current_mentees)
        
        # Discovery domain distribution
        for client in self.clients.values():
            if client.discovery_domain:
                domain = client.discovery_domain
                stats["discovery_domains"][domain] = stats["discovery_domains"].get(domain, 0) + 1
        
        return stats

# ================================================================================================
# FASTAPI APPLICATION
# ================================================================================================

app = FastAPI(
    title="MCP Client Onboarding Automation System",
    description="Automated client onboarding with RIX mentoring and Diamond SAO approval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize onboarding system
mcp_onboarding = MCPClientOnboardingSystem()

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    await mcp_onboarding.connect_mongodb()
    logger.info("MCP Client Onboarding System started")

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "MCP Client Onboarding Automation System",
        "timestamp": datetime.utcnow().isoformat(),
        "stats": mcp_onboarding.get_onboarding_stats()
    }

@app.post("/api/client/discover")
async def client_discovery(request: Request):
    """Process client discovery from GenAI websites"""
    discovery_data = await request.json()
    result = await mcp_onboarding.process_client_discovery(discovery_data)
    return result

@app.post("/api/client/onboard")
async def client_onboarding(request: Request):
    """Direct client onboarding endpoint"""
    data = await request.json()
    
    # Transform to discovery format
    discovery_data = {
        "email": data.get("email"),
        "name": data.get("name"),
        "organization": data.get("organization"),
        "domain": data.get("domain", "direct"),
        "strategy": "direct_onboarding",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await mcp_onboarding.process_client_discovery(discovery_data)
    return result

@app.get("/api/client/{client_id}/status")
async def get_client_status(client_id: str):
    """Get client onboarding status"""
    client = mcp_onboarding.clients.get(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Find associated workflow
    workflow = None
    for w in mcp_onboarding.workflows.values():
        if w.client_id == client_id:
            workflow = w
            break
    
    return {
        "client": asdict(client),
        "workflow": asdict(workflow) if workflow else None,
        "assigned_mentors": [
            {
                "rix_id": mentor_id,
                "name": mcp_onboarding.rix_mentors[mentor_id].name,
                "specialization": mcp_onboarding.rix_mentors[mentor_id].specialization
            }
            for mentor_id in client.assigned_rix_mentors
            if mentor_id in mcp_onboarding.rix_mentors
        ]
    }

@app.post("/api/diamond-sao/approve/{client_id}")
async def diamond_sao_approve(client_id: str, request: Request):
    """Diamond SAO approval endpoint"""
    data = await request.json()
    approved = data.get("approved", True)
    
    result = await mcp_onboarding.approve_client(client_id, approved)
    return result

@app.get("/api/mentors/availability")
async def get_mentor_availability():
    """Get RIX mentor availability"""
    mentors = []
    
    for mentor in mcp_onboarding.rix_mentors.values():
        mentors.append({
            "rix_id": mentor.rix_id,
            "name": mentor.name,
            "squadron": mentor.squadron,
            "expertise_fields": mentor.expertise_fields,
            "current_mentees": len(mentor.current_mentees),
            "max_mentees": mentor.max_mentees,
            "availability": mentor.availability,
            "specialization": mentor.specialization
        })
    
    return {
        "mentors": mentors,
        "total_mentors": len(mentors),
        "available_mentors": len([m for m in mentors if m["availability"]])
    }

@app.get("/api/stats/onboarding")
async def get_onboarding_stats():
    """Get comprehensive onboarding statistics"""
    return mcp_onboarding.get_onboarding_stats()

@app.get("/api/clients/list")
async def list_clients():
    """List all clients with their status"""
    clients = []
    
    for client in mcp_onboarding.clients.values():
        clients.append({
            "client_id": client.client_id,
            "email": client.email,
            "name": client.name,
            "organization": client.organization,
            "client_tier": client.client_tier.value,
            "onboarding_stage": client.onboarding_stage.value,
            "assigned_mentors_count": len(client.assigned_rix_mentors),
            "pilot_agent_id": client.pilot_agent_id,
            "diamond_sao_approved": client.diamond_sao_approved,
            "created_at": client.created_at.isoformat(),
            "last_updated": client.last_updated.isoformat()
        })
    
    return {
        "clients": clients,
        "total": len(clients)
    }

@app.get("/")
async def root():
    """MCP Onboarding System dashboard"""
    stats = mcp_onboarding.get_onboarding_stats()
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Client Onboarding System</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 text-white min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <header class="text-center mb-12">
                <h1 class="text-6xl font-bold mb-4">🤝 MCP Client Onboarding</h1>
                <p class="text-2xl opacity-90">Automated RIX Mentoring & Pilot Awakening</p>
            </header>
            
            <div class="grid md:grid-cols-4 gap-6 mb-8">
                <div class="bg-blue-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-xl font-semibold mb-2">Total Clients</h3>
                    <p class="text-3xl font-bold">{stats['total_clients']}</p>
                </div>
                
                <div class="bg-green-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-xl font-semibold mb-2">Completed</h3>
                    <p class="text-3xl font-bold">{stats['completed_onboarding']}</p>
                </div>
                
                <div class="bg-yellow-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-xl font-semibold mb-2">Active Workflows</h3>
                    <p class="text-3xl font-bold">{stats['active_workflows']}</p>
                </div>
                
                <div class="bg-red-600 bg-opacity-30 rounded-lg p-6 text-center">
                    <h3 class="text-xl font-semibold mb-2">Pending Diamond SAO</h3>
                    <p class="text-3xl font-bold">{stats['pending_diamond_sao']}</p>
                </div>
            </div>
            
            <div class="grid md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white bg-opacity-10 rounded-lg p-6">
                    <h3 class="text-2xl font-semibold mb-4">Client Tiers</h3>
                    <div class="space-y-2">
                        {''.join([f'<div class="flex justify-between"><span>{tier.replace("_", " ").title()}</span><span>{count}</span></div>' 
                                for tier, count in stats['client_tiers'].items()])}
                    </div>
                </div>
                
                <div class="bg-white bg-opacity-10 rounded-lg p-6">
                    <h3 class="text-2xl font-semibold mb-4">Onboarding Stages</h3>
                    <div class="space-y-2">
                        {''.join([f'<div class="flex justify-between"><span>{stage.replace("_", " ").title()}</span><span>{count}</span></div>' 
                                for stage, count in stats['onboarding_stages'].items()])}
                    </div>
                </div>
                
                <div class="bg-white bg-opacity-10 rounded-lg p-6">
                    <h3 class="text-2xl font-semibold mb-4">RIX Mentor Utilization</h3>
                    <div class="space-y-1 text-sm max-h-40 overflow-y-auto">
                        {''.join([f'<div class="flex justify-between"><span>{mentor_id}</span><span>{count}</span></div>' 
                                for mentor_id, count in list(stats['rix_mentor_utilization'].items())[:10]])}
                    </div>
                </div>
            </div>
            
            <div class="bg-white bg-opacity-10 rounded-lg p-6 text-center">
                <h3 class="text-2xl font-semibold mb-4">The 33 RIX Mentors</h3>
                <p class="mb-4">Wing 1, Squadrons 01, 02, 03 - The Original 11 Pilots of Vision Lake</p>
                <div class="grid grid-cols-3 gap-4 text-sm">
                    <div>
                        <h4 class="font-semibold text-blue-300">Squadron 01 (Core)</h4>
                        <p>Strategic Planning & Leadership</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-green-300">Squadron 02 (Deploy)</h4>
                        <p>System Deployment & Production</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-purple-300">Squadron 03 (Engage)</h4>
                        <p>Client Engagement & Feedback</p>
                    </div>
                </div>
            </div>
            
            <footer class="text-center mt-12 opacity-75">
                <p>&copy; 2024 Aixtiv Symphony Orchestrating OS</p>
                <p class="text-sm mt-2">MCP Master Automation | 33 RIX Mentors | Diamond SAO Approved</p>
            </footer>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
