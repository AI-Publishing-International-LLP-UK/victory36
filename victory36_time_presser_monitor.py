#!/usr/bin/env python3
"""
Victory36 Time Presser Monitor
Monitors temporal acceleration performance and system health
Provides metrics and alerting for time compression operations
"""

import logging
import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify
import requests
import json
from collections import deque, defaultdict

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Victory36TimePresserMonitor:
    """Monitor for Victory36 Time Presser operations"""
    
    def __init__(self):
        self.service_name = "victory36-time-presser-monitor"
        self.version = "1.0.0"
        
        # Monitoring configuration
        self.check_interval = int(os.getenv('MONITOR_CHECK_INTERVAL', '30'))  # seconds
        self.retention_period = int(os.getenv('METRICS_RETENTION_HOURS', '24'))  # hours
        
        # Service endpoints to monitor
        self.time_presser_endpoint = "http://victory36-time-presser-service:8080"
        self.dr_lucy_endpoint = "https://dr-lucy-predictions-859242575175.us-west1.run.app"
        self.dream_commander_endpoint = "https://dream-commander-predictions-859242575175.us-west1.run.app"
        
        # Metrics storage
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.alerts = deque(maxlen=100)
        self.system_health = {
            'overall_status': 'unknown',
            'last_check': None,
            'services': {}
        }
        
        # Performance thresholds
        self.thresholds = {
            'response_time_ms': float(os.getenv('MAX_RESPONSE_TIME_MS', '5000')),
            'error_rate_percent': float(os.getenv('MAX_ERROR_RATE', '5')),
            'temporal_coherence_min': float(os.getenv('MIN_TEMPORAL_COHERENCE', '0.8')),
            'acceleration_efficiency_min': float(os.getenv('MIN_ACCELERATION_EFFICIENCY', '1000'))
        }
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_active = True
        
        logger.info("Victory36 Time Presser Monitor initialized")
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_thread.is_alive():
            self.monitoring_thread.start()
            logger.info("Monitoring thread started")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._check_system_health()
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.check_interval)
    
    def _check_system_health(self):
        """Check health of all services"""
        services = {
            'time_presser': f"{self.time_presser_endpoint}/health/time-presser",
            'dr_lucy': f"{self.dr_lucy_endpoint}/health",
            'dream_commander': f"{self.dream_commander_endpoint}/health"
        }
        
        self.system_health['services'] = {}
        overall_healthy = True
        
        for service_name, health_url in services.items():
            try:
                start_time = time.time()
                response = requests.get(health_url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    status = 'healthy'
                else:
                    status = 'unhealthy'
                    overall_healthy = False
                
                self.system_health['services'][service_name] = {
                    'status': status,
                    'response_time_ms': response_time,
                    'last_check': datetime.utcnow().isoformat(),
                    'details': health_data if response.status_code == 200 else None
                }
                
                # Record metrics
                self._record_metric(f"{service_name}_response_time", response_time)
                self._record_metric(f"{service_name}_status", 1 if status == 'healthy' else 0)
                
            except Exception as e:
                logger.warning(f"Health check failed for {service_name}: {e}")
                self.system_health['services'][service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
                overall_healthy = False
                self._record_metric(f"{service_name}_status", 0)
        
        self.system_health['overall_status'] = 'healthy' if overall_healthy else 'degraded'
        self.system_health['last_check'] = datetime.utcnow().isoformat()
    
    def _collect_metrics(self):
        """Collect performance metrics"""
        try:
            # Test time presser performance
            if self.system_health['services'].get('time_presser', {}).get('status') == 'healthy':
                self._test_time_presser_performance()
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def _test_time_presser_performance(self):
        """Test time presser coordination performance"""
        try:
            test_scenario = {
                'scenario': 'Performance monitoring test',
                'context': 'Automated system health check',
                'time_horizon': '1 minute'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.time_presser_endpoint}/predict/temporal",
                json=test_scenario,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract coordination metrics
                coordination_metrics = result.get('coordination_metrics', {})
                temporal_coherence = coordination_metrics.get('temporal_coherence', 0)
                acceleration_efficiency = coordination_metrics.get('acceleration_efficiency', 0)
                
                # Record performance metrics
                self._record_metric('coordination_response_time', response_time)
                self._record_metric('temporal_coherence', temporal_coherence)
                self._record_metric('acceleration_efficiency', acceleration_efficiency)
                
                logger.debug(f"Performance test completed: {response_time:.1f}ms, coherence: {temporal_coherence:.3f}")
            else:
                self._record_metric('coordination_errors', 1)
                logger.warning(f"Performance test failed: HTTP {response.status_code}")
                
        except Exception as e:
            self._record_metric('coordination_errors', 1)
            logger.warning(f"Performance test error: {e}")
    
    def _record_metric(self, metric_name, value):
        """Record a metric value with timestamp"""
        timestamp = datetime.utcnow()
        self.metrics[metric_name].append({
            'timestamp': timestamp.isoformat(),
            'value': value
        })
        
        # Clean up old metrics
        cutoff_time = timestamp - timedelta(hours=self.retention_period)
        while (self.metrics[metric_name] and 
               datetime.fromisoformat(self.metrics[metric_name][0]['timestamp']) < cutoff_time):
            self.metrics[metric_name].popleft()
    
    def _check_alerts(self):
        """Check for alert conditions"""
        alerts_triggered = []
        
        # Check response time alerts
        for service in ['time_presser', 'dr_lucy', 'dream_commander']:
            response_times = [m['value'] for m in list(self.metrics[f"{service}_response_time"])[-5:]]
            if response_times and max(response_times) > self.thresholds['response_time_ms']:
                alerts_triggered.append({
                    'type': 'high_response_time',
                    'service': service,
                    'value': max(response_times),
                    'threshold': self.thresholds['response_time_ms']
                })
        
        # Check temporal coherence
        coherence_values = [m['value'] for m in list(self.metrics['temporal_coherence'])[-5:]]
        if coherence_values and min(coherence_values) < self.thresholds['temporal_coherence_min']:
            alerts_triggered.append({
                'type': 'low_temporal_coherence',
                'value': min(coherence_values),
                'threshold': self.thresholds['temporal_coherence_min']
            })
        
        # Record alerts
        for alert in alerts_triggered:
            alert['timestamp'] = datetime.utcnow().isoformat()
            self.alerts.append(alert)
            logger.warning(f"Alert triggered: {alert}")
    
    def get_metrics_summary(self):
        """Get summary of recent metrics"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                recent_values = [v['value'] for v in list(values)[-10:]]
                summary[metric_name] = {
                    'current': recent_values[-1] if recent_values else None,
                    'average': sum(recent_values) / len(recent_values),
                    'min': min(recent_values),
                    'max': max(recent_values),
                    'count': len(values)
                }
        
        return summary

# Initialize monitor
monitor = Victory36TimePresserMonitor()

@app.route('/health', methods=['GET'])
def health_check():
    """Monitor service health check"""
    return jsonify({
        "service": monitor.service_name,
        "status": "healthy",
        "version": monitor.version,
        "monitoring_active": monitor.monitoring_active,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/system-health', methods=['GET'])
def system_health():
    """Get overall system health status"""
    return jsonify(monitor.system_health)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics summary"""
    return jsonify({
        "metrics_summary": monitor.get_metrics_summary(),
        "collection_interval": monitor.check_interval,
        "retention_hours": monitor.retention_period,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    return jsonify({
        "alerts": list(monitor.alerts),
        "alert_count": len(monitor.alerts),
        "thresholds": monitor.thresholds,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Get complete monitoring dashboard data"""
    return jsonify({
        "system_health": monitor.system_health,
        "metrics_summary": monitor.get_metrics_summary(),
        "recent_alerts": list(monitor.alerts)[-10:],
        "thresholds": monitor.thresholds,
        "monitor_info": {
            "service": monitor.service_name,
            "version": monitor.version,
            "monitoring_active": monitor.monitoring_active,
            "check_interval": monitor.check_interval
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# Start monitoring when the app starts
@app.before_first_request
def start_monitoring():
    monitor.start_monitoring()

if __name__ == '__main__':
    monitor.start_monitoring()
    app.run(host='0.0.0.0', port=8080, debug=False)
