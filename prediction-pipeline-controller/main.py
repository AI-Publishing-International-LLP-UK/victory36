#!/usr/bin/env python3
"""
Victory36 Prediction Pipeline Controller
Coordinates Time Pressors (Dr Lucy) and Time Liners (Dream Commander) 
with Claude 4 direct API integration for anti-gravity power craft
"""

import os
import json
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, Response
import requests
import aiohttp
import anthropic
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import hashlib
import pickle
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@dataclass
class PredictionRequest:
    """Unified prediction request for pipeline coordination"""
    session_id: str
    mission_context: Dict[str, Any]
    time_presser_priority: float = 0.7
    time_liner_priority: float = 0.6
    claude4_integration: bool = True
    temporal_acceleration: float = 1.0
    strategic_horizon: int = 90

@dataclass
class PipelineResponse:
    """Coordinated response from all prediction systems"""
    session_id: str
    timestamp: str
    time_presser_prediction: Optional[Dict[str, Any]] = None
    time_liner_prediction: Optional[Dict[str, Any]] = None
    claude4_analysis: Optional[Dict[str, Any]] = None
    coordination_score: float = 0.0
    temporal_coherence: float = 0.0
    pipeline_status: str = "processing"

class PredictionPipelineController:
    """Main controller orchestrating all prediction services"""
    
    def __init__(self):
        self.dr_lucy_endpoint = os.getenv('DR_LUCY_ENDPOINT')
        self.dream_commander_endpoint = os.getenv('DREAM_COMMANDER_ENDPOINT')
        
        # Claude 4 Configuration
        self.claude4_enabled = os.getenv('CLAUDE4_PIPELINE_ENABLED', 'true').lower() == 'true'
        self.claude4_api_key = os.getenv('CLAUDE4_API_KEY')
        self.claude4_model = os.getenv('CLAUDE4_MODEL_VERSION', 'claude-3-5-sonnet-20241022')
        self.claude4_endpoint = os.getenv('CLAUDE4_API_ENDPOINT', 'https://api.anthropic.com/v1/messages')
        
        # Anti-gravity power craft parameters
        self.time_presser_factor = float(os.getenv('TIME_PRESSER_ACCELERATION_FACTOR', '10.0'))
        self.time_liner_horizon = int(os.getenv('TIME_LINER_STRATEGIC_HORIZON', '90'))
        self.temporal_coherence_threshold = float(os.getenv('TEMPORAL_COHERENCE_THRESHOLD', '0.85'))
        
        # Pipeline configuration
        self.prediction_timeout = int(os.getenv('PREDICTION_TIMEOUT', '30').replace('s', ''))
        self.max_concurrent = int(os.getenv('MAX_CONCURRENT_PREDICTIONS', '10'))
        self.cache_ttl = int(os.getenv('CACHE_TTL', '300').replace('s', ''))
        
        # Initialize Claude 4 client if enabled
        self.claude4_client = None
        if self.claude4_enabled and self.claude4_api_key:
            self.claude4_client = anthropic.Anthropic(api_key=self.claude4_api_key)
            
        # Prediction cache and coordination
        self.prediction_cache = {}
        self.coordination_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        
        logger.info(f"Pipeline Controller initialized - Claude 4: {self.claude4_enabled}")
        logger.info(f"Dr Lucy endpoint: {self.dr_lucy_endpoint}")
        logger.info(f"Dream Commander endpoint: {self.dream_commander_endpoint}")

    def _cache_key(self, session_id: str, context_hash: str) -> str:
        """Generate cache key for prediction requests"""
        return f"prediction:{session_id}:{context_hash}"

    def _context_hash(self, context: Dict[str, Any]) -> str:
        """Generate hash of mission context for caching"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()

    async def _call_dr_lucy(self, prediction_request: PredictionRequest) -> Optional[Dict[str, Any]]:
        """Call Dr Lucy Flight Memory System (Time Pressors)"""
        if not self.dr_lucy_endpoint:
            logger.warning("Dr Lucy endpoint not configured")
            return None
            
        try:
            # Prepare Time Presser specific request
            time_presser_request = {
                "session_id": prediction_request.session_id,
                "context": prediction_request.mission_context,
                "acceleration_factor": self.time_presser_factor,
                "priority": prediction_request.time_presser_priority,
                "temporal_acceleration": prediction_request.temporal_acceleration
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.prediction_timeout)) as session:
                async with session.post(
                    f"{self.dr_lucy_endpoint}/predict",
                    json=time_presser_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Dr Lucy prediction successful for session {prediction_request.session_id}")
                        return result
                    else:
                        logger.error(f"Dr Lucy prediction failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Dr Lucy service: {str(e)}")
            return None

    async def _call_dream_commander(self, prediction_request: PredictionRequest) -> Optional[Dict[str, Any]]:
        """Call Dream Commander Strategic System (Time Liners)"""
        if not self.dream_commander_endpoint:
            logger.warning("Dream Commander endpoint not configured")
            return None
            
        try:
            # Prepare Time Liner specific request
            time_liner_request = {
                "session_id": prediction_request.session_id,
                "context": prediction_request.mission_context,
                "strategic_horizon": min(self.time_liner_horizon, prediction_request.strategic_horizon),
                "priority": prediction_request.time_liner_priority
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.prediction_timeout)) as session:
                async with session.post(
                    f"{self.dream_commander_endpoint}/predict",
                    json=time_liner_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Dream Commander prediction successful for session {prediction_request.session_id}")
                        return result
                    else:
                        logger.error(f"Dream Commander prediction failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Dream Commander service: {str(e)}")
            return None

    async def _claude4_analysis(self, prediction_request: PredictionRequest, 
                               time_presser_result: Optional[Dict], 
                               time_liner_result: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Perform Claude 4 analysis of coordinated predictions"""
        if not self.claude4_enabled or not self.claude4_client:
            return None
            
        try:
            # Prepare analysis context for Claude 4
            analysis_context = {
                "mission_context": prediction_request.mission_context,
                "time_presser_prediction": time_presser_result,
                "time_liner_prediction": time_liner_result,
                "temporal_parameters": {
                    "acceleration_factor": self.time_presser_factor,
                    "strategic_horizon": self.time_liner_horizon,
                    "coherence_threshold": self.temporal_coherence_threshold
                }
            }
            
            # Create Claude 4 analysis prompt
            analysis_prompt = f"""
            Analyze the coordinated predictions from the Victory36 anti-gravity power craft systems:

            Mission Context: {json.dumps(prediction_request.mission_context, indent=2)}
            
            Time Presser (Dr Lucy) Prediction: {json.dumps(time_presser_result, indent=2) if time_presser_result else "Not available"}
            
            Time Liner (Dream Commander) Prediction: {json.dumps(time_liner_result, indent=2) if time_liner_result else "Not available"}
            
            Temporal Parameters:
            - Acceleration Factor: {self.time_presser_factor}
            - Strategic Horizon: {self.time_liner_horizon} days
            - Coherence Threshold: {self.temporal_coherence_threshold}
            
            Please provide:
            1. Coordination assessment between Time Presser and Time Liner predictions
            2. Temporal coherence analysis
            3. Strategic recommendations for anti-gravity power craft operations
            4. Risk assessment and mitigation strategies
            5. Overall confidence score (0.0-1.0)
            
            Respond in JSON format with structured analysis.
            """
            
            # Call Claude 4 API directly
            message = self.claude4_client.messages.create(
                model=self.claude4_model,
                max_tokens=4096,
                temperature=0.7,
                messages=[{
                    "role": "user", 
                    "content": analysis_prompt
                }]
            )
            
            # Parse Claude 4 response
            claude_response = message.content[0].text
            try:
                # Try to extract JSON from response
                if '```json' in claude_response:
                    json_start = claude_response.find('```json') + 7
                    json_end = claude_response.find('```', json_start)
                    claude_analysis = json.loads(claude_response[json_start:json_end])
                else:
                    # Try to parse the whole response as JSON
                    claude_analysis = json.loads(claude_response)
                    
                logger.info(f"Claude 4 analysis completed for session {prediction_request.session_id}")
                return claude_analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text response
                return {
                    "analysis_text": claude_response,
                    "confidence": 0.8,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in Claude 4 analysis: {str(e)}")
            return None

    def _calculate_coordination_score(self, time_presser: Optional[Dict], 
                                    time_liner: Optional[Dict], 
                                    claude4: Optional[Dict]) -> float:
        """Calculate coordination score between prediction systems"""
        score = 0.0
        
        # Base scores for successful predictions
        if time_presser:
            score += 0.3
        if time_liner:
            score += 0.3
        if claude4:
            score += 0.2
            
        # Bonus for Claude 4 confidence
        if claude4 and 'confidence' in claude4:
            score += claude4['confidence'] * 0.2
            
        return min(score, 1.0)

    def _calculate_temporal_coherence(self, time_presser: Optional[Dict], 
                                    time_liner: Optional[Dict]) -> float:
        """Calculate temporal coherence between Time Presser and Time Liner predictions"""
        if not time_presser or not time_liner:
            return 0.5
            
        # Simple coherence calculation based on prediction confidence alignment
        tp_confidence = time_presser.get('prediction', {}).get('confidence', 0.5)
        tl_confidence = time_liner.get('prediction', {}).get('confidence', 0.5)
        
        # Calculate coherence as inverse of confidence difference
        confidence_diff = abs(tp_confidence - tl_confidence)
        coherence = 1.0 - confidence_diff
        
        return max(0.0, min(1.0, coherence))

    async def coordinate_predictions(self, prediction_request: PredictionRequest) -> PipelineResponse:
        """Coordinate predictions from all systems"""
        session_id = prediction_request.session_id
        timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Starting coordinated prediction for session {session_id}")
        
        # Check cache first
        context_hash = self._context_hash(prediction_request.mission_context)
        cache_key = self._cache_key(session_id, context_hash)
        
        with self.coordination_lock:
            if cache_key in self.prediction_cache:
                cached_result, cache_time = self.prediction_cache[cache_key]
                if time.time() - cache_time < self.cache_ttl:
                    logger.info(f"Returning cached prediction for session {session_id}")
                    return cached_result

        try:
            # Execute predictions concurrently
            tasks = [
                self._call_dr_lucy(prediction_request),
                self._call_dream_commander(prediction_request)
            ]
            
            time_presser_result, time_liner_result = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions from concurrent calls
            if isinstance(time_presser_result, Exception):
                logger.error(f"Time Presser error: {time_presser_result}")
                time_presser_result = None
                
            if isinstance(time_liner_result, Exception):
                logger.error(f"Time Liner error: {time_liner_result}")
                time_liner_result = None
            
            # Perform Claude 4 analysis
            claude4_result = None
            if prediction_request.claude4_integration:
                claude4_result = await self._claude4_analysis(
                    prediction_request, time_presser_result, time_liner_result
                )
            
            # Calculate coordination metrics
            coordination_score = self._calculate_coordination_score(
                time_presser_result, time_liner_result, claude4_result
            )
            
            temporal_coherence = self._calculate_temporal_coherence(
                time_presser_result, time_liner_result
            )
            
            # Create coordinated response
            response = PipelineResponse(
                session_id=session_id,
                timestamp=timestamp,
                time_presser_prediction=time_presser_result,
                time_liner_prediction=time_liner_result,
                claude4_analysis=claude4_result,
                coordination_score=coordination_score,
                temporal_coherence=temporal_coherence,
                pipeline_status="completed" if any([time_presser_result, time_liner_result]) else "failed"
            )
            
            # Cache the result
            with self.coordination_lock:
                self.prediction_cache[cache_key] = (response, time.time())
                
            logger.info(f"Coordinated prediction completed for session {session_id}")
            logger.info(f"Coordination score: {coordination_score:.3f}, Temporal coherence: {temporal_coherence:.3f}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in coordinated prediction: {str(e)}")
            return PipelineResponse(
                session_id=session_id,
                timestamp=timestamp,
                pipeline_status="error"
            )

# Initialize the pipeline controller
pipeline_controller = PredictionPipelineController()

@app.route('/health/pipeline', methods=['GET'])
def health_check():
    """Health check for the prediction pipeline"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "dr_lucy": pipeline_controller.dr_lucy_endpoint is not None,
            "dream_commander": pipeline_controller.dream_commander_endpoint is not None,
            "claude4": pipeline_controller.claude4_enabled
        },
        "configuration": {
            "time_presser_factor": pipeline_controller.time_presser_factor,
            "time_liner_horizon": pipeline_controller.time_liner_horizon,
            "temporal_coherence_threshold": pipeline_controller.temporal_coherence_threshold
        }
    }
    return jsonify(health_status)

@app.route('/ready/pipeline', methods=['GET'])
def readiness_check():
    """Readiness check for the prediction pipeline"""
    is_ready = (
        pipeline_controller.dr_lucy_endpoint is not None and
        pipeline_controller.dream_commander_endpoint is not None
    )
    
    status_code = 200 if is_ready else 503
    return jsonify({
        "ready": is_ready,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), status_code

@app.route('/predict/coordinated', methods=['POST'])
def coordinated_prediction():
    """Main endpoint for coordinated predictions"""
    try:
        request_data = request.get_json()
        
        # Validate request
        if not request_data or 'session_id' not in request_data or 'mission_context' not in request_data:
            return jsonify({"error": "Invalid request: session_id and mission_context required"}), 400
        
        # Create prediction request
        prediction_request = PredictionRequest(
            session_id=request_data['session_id'],
            mission_context=request_data['mission_context'],
            time_presser_priority=request_data.get('time_presser_priority', 0.7),
            time_liner_priority=request_data.get('time_liner_priority', 0.6),
            claude4_integration=request_data.get('claude4_integration', True),
            temporal_acceleration=request_data.get('temporal_acceleration', 1.0),
            strategic_horizon=request_data.get('strategic_horizon', 90)
        )
        
        # Execute coordinated prediction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                pipeline_controller.coordinate_predictions(prediction_request)
            )
            return jsonify(asdict(response))
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in coordinated prediction endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status/pipeline', methods=['GET'])
def pipeline_status():
    """Get current pipeline status and metrics"""
    with pipeline_controller.coordination_lock:
        cache_size = len(pipeline_controller.prediction_cache)
        
    return jsonify({
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cache_size": cache_size,
        "configuration": {
            "claude4_enabled": pipeline_controller.claude4_enabled,
            "claude4_model": pipeline_controller.claude4_model,
            "max_concurrent": pipeline_controller.max_concurrent,
            "prediction_timeout": pipeline_controller.prediction_timeout,
            "cache_ttl": pipeline_controller.cache_ttl
        }
    })

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear prediction cache"""
    with pipeline_controller.coordination_lock:
        cache_size = len(pipeline_controller.prediction_cache)
        pipeline_controller.prediction_cache.clear()
        
    return jsonify({
        "message": f"Cache cleared ({cache_size} entries removed)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Victory36 Prediction Pipeline Controller on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
