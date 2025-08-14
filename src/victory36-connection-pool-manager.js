/**
 * Victory36 Connection Pool Manager
 * Classification: Diamond SAO Only
 * Purpose: High-performance connection pooling for 20M+ AI agents
 */

const EventEmitter = require('events');
const crypto = require('crypto');

// Diamond SAO Security Constants (These should be moved to environment variables in production)
// Note: These constants are reserved for future encryption features
// const DIAMOND_SAO_KEY_ID = process.env.DIAMOND_SAO_KEY_ID || 'v36-default-key';
// const ENCRYPTION_ALGORITHM = 'aes-256-gcm';
const MAX_AGENTS = 20000000; // 20 million agents
const REGIONS = ['MOCOA', 'MOCORIX', 'MOCORIX2'];

/**
 * Elite Agent Classification
 */
const AGENT_TIERS = {
  ELITE_11: 'ELITE_11',      // Highest priority agents
  MASTERY_33: 'MASTERY_33',  // Advanced capability agents
  STANDARD: 'STANDARD'       // Regular agents
};

/**
 * Health Monitor for Connection Pools
 */
class HealthMonitor extends EventEmitter {
  constructor() {
    super();
    this.metrics = new Map();
    this.thresholds = {
      maxLatency: 100,        // 100ms max latency
      minSuccessRate: 99.9,   // 99.9% success rate
      maxErrorRate: 0.1       // 0.1% error rate
    };
    
    this.startMonitoring();
  }
  
  startMonitoring() {
    setInterval(() => {
      this.checkHealth();
    }, 5000); // Check every 5 seconds
  }
  
  recordMetric(poolId, metric, value) {
    if (!this.metrics.has(poolId)) {
      this.metrics.set(poolId, {
        latency: [],
        successRate: 100,
        errorRate: 0,
        connectionCount: 0,
        lastUpdated: Date.now()
      });
    }
    
    const poolMetrics = this.metrics.get(poolId);
    
    switch (metric) {
    case 'latency':
      poolMetrics.latency.push(value);
      if (poolMetrics.latency.length > 100) {
        poolMetrics.latency.shift(); // Keep only last 100 measurements
      }
      break;
    case 'success':
      poolMetrics.successRate = value;
      break;
    case 'error':
      poolMetrics.errorRate = value;
      break;
    case 'connections':
      poolMetrics.connectionCount = value;
      break;
    }
    
    poolMetrics.lastUpdated = Date.now();
  }
  
  checkHealth() {
    for (const [poolId, metrics] of this.metrics.entries()) {
      const avgLatency = metrics.latency.length > 0 
        ? metrics.latency.reduce((a, b) => a + b, 0) / metrics.latency.length 
        : 0;
      
      let isHealthy = true;
      const issues = [];
      
      if (avgLatency > this.thresholds.maxLatency) {
        isHealthy = false;
        issues.push(`High latency: ${avgLatency.toFixed(2)}ms`);
      }
      
      if (metrics.successRate < this.thresholds.minSuccessRate) {
        isHealthy = false;
        issues.push(`Low success rate: ${metrics.successRate}%`);
      }
      
      if (metrics.errorRate > this.thresholds.maxErrorRate) {
        isHealthy = false;
        issues.push(`High error rate: ${metrics.errorRate}%`);
      }
      
      this.emit('health-check', {
        poolId,
        isHealthy,
        issues,
        metrics: {
          avgLatency,
          successRate: metrics.successRate,
          errorRate: metrics.errorRate,
          connectionCount: metrics.connectionCount
        }
      });
      
      if (!isHealthy) {
        console.warn(`🚨 Pool ${poolId} health issues:`, issues);
      }
    }
  }
  
  getPoolHealth(poolId) {
    return this.metrics.get(poolId) || null;
  }
}

/**
 * Metrics Collector for Performance Monitoring
 */
class MetricsCollector {
  constructor() {
    this.metrics = {
      totalConnections: 0,
      activeConnections: 0,
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      avgResponseTime: 0,
      peakConnections: 0,
      uptime: Date.now()
    };
    
    this.regionMetrics = new Map();
    REGIONS.forEach(region => {
      this.regionMetrics.set(region, { ...this.metrics });
    });
  }
  
  recordConnection(region, action) {
    const regionStats = this.regionMetrics.get(region);
    
    switch (action) {
    case 'open':
      this.metrics.activeConnections++;
      this.metrics.totalConnections++;
      regionStats.activeConnections++;
      regionStats.totalConnections++;
        
      if (this.metrics.activeConnections > this.metrics.peakConnections) {
        this.metrics.peakConnections = this.metrics.activeConnections;
      }
      break;
        
    case 'close':
      this.metrics.activeConnections--;
      regionStats.activeConnections--;
      break;
    }
  }
  
  recordRequest(region, success, responseTime) {
    const regionStats = this.regionMetrics.get(region);
    
    this.metrics.totalRequests++;
    regionStats.totalRequests++;
    
    if (success) {
      this.metrics.successfulRequests++;
      regionStats.successfulRequests++;
    } else {
      this.metrics.failedRequests++;
      regionStats.failedRequests++;
    }
    
    // Update average response time
    this.metrics.avgResponseTime = 
      (this.metrics.avgResponseTime * (this.metrics.totalRequests - 1) + responseTime) / 
      this.metrics.totalRequests;
    
    regionStats.avgResponseTime = 
      (regionStats.avgResponseTime * (regionStats.totalRequests - 1) + responseTime) / 
      regionStats.totalRequests;
  }
  
  getMetrics(region = null) {
    if (region) {
      return this.regionMetrics.get(region);
    }
    return {
      global: this.metrics,
      regional: Object.fromEntries(this.regionMetrics)
    };
  }
  
  getSuccessRate(region = null) {
    const stats = region ? this.regionMetrics.get(region) : this.metrics;
    if (stats.totalRequests === 0) return 100;
    return (stats.successfulRequests / stats.totalRequests) * 100;
  }
}

/**
 * Connection Pool Implementation
 */
class ConnectionPool extends EventEmitter {
  constructor(config) {
    super();
    this.config = {
      region: config.region || 'MOCOA',
      minConnections: config.minConnections || 1000,
      maxConnections: config.maxConnections || Math.floor(MAX_AGENTS / REGIONS.length),
      connectionTimeout: config.connectionTimeout || 5000,
      idleTimeout: config.idleTimeout || 300000, // 5 minutes
      retryAttempts: config.retryAttempts || 3,
      healthCheckInterval: config.healthCheckInterval || 30000,
      ...config
    };
    
    this.connections = new Set();
    this.availableConnections = [];
    this.pendingRequests = [];
    this.destroyed = false;
    
    this.initialize();
  }
  
  async initialize() {
    console.warn(`🚀 Initializing connection pool for region: ${this.config.region}`);
    console.warn('📊 Pool configuration:', {
      region: this.config.region,
      minConnections: this.config.minConnections,
      maxConnections: this.config.maxConnections
    });
    
    // Create minimum connections
    for (let i = 0; i < this.config.minConnections; i++) {
      await this.createConnection();
    }
    
    // Start health check interval
    setInterval(() => {
      this.performHealthCheck();
    }, this.config.healthCheckInterval);
    
    console.warn(`✅ Connection pool initialized for ${this.config.region} with ${this.connections.size} connections`);
    this.emit('initialized', { region: this.config.region, connections: this.connections.size });
  }
  
  async createConnection() {
    if (this.connections.size >= this.config.maxConnections) {
      throw new Error(`Maximum connections (${this.config.maxConnections}) reached for region ${this.config.region}`);
    }
    
    const connection = {
      id: crypto.randomUUID(),
      region: this.config.region,
      created: Date.now(),
      lastUsed: Date.now(),
      isActive: false,
      healthStatus: 'healthy',
      metadata: {
        totalRequests: 0,
        successfulRequests: 0,
        avgResponseTime: 0
      }
    };
    
    this.connections.add(connection);
    this.availableConnections.push(connection);
    
    this.emit('connection-created', connection);
    return connection;
  }
  
  async acquire(agentId, agentTier = AGENT_TIERS.STANDARD) {
    if (this.destroyed) {
      throw new Error('Connection pool has been destroyed');
    }
    
    // Priority handling for Elite and Mastery agents
    const priority = this.getAgentPriority(agentTier);
    
    return new Promise((resolve, reject) => {
      const request = {
        agentId,
        agentTier,
        priority,
        timestamp: Date.now(),
        resolve,
        reject,
        timeout: setTimeout(() => {
          reject(new Error(`Connection timeout for agent ${agentId}`));
        }, this.config.connectionTimeout)
      };
      
      // Insert request based on priority
      if (priority > 0) {
        this.pendingRequests.unshift(request); // High priority to front
      } else {
        this.pendingRequests.push(request); // Standard priority to back
      }
      
      this.processNextRequest();
    });
  }
  
  async processNextRequest() {
    if (this.pendingRequests.length === 0) return;
    
    let connection = this.availableConnections.pop();
    
    if (!connection) {
      // Try to create a new connection if under limit
      if (this.connections.size < this.config.maxConnections) {
        try {
          connection = await this.createConnection();
          this.availableConnections.pop(); // Remove it since we're about to use it
        } catch (error) {
          // Can't create more connections, request will wait
          return;
        }
      } else {
        // No connections available and at max capacity
        return;
      }
    }
    
    const request = this.pendingRequests.shift();
    clearTimeout(request.timeout);
    
    connection.isActive = true;
    connection.lastUsed = Date.now();
    connection.currentAgentId = request.agentId;
    connection.currentAgentTier = request.agentTier;
    
    this.emit('connection-acquired', {
      connectionId: connection.id,
      agentId: request.agentId,
      agentTier: request.agentTier,
      waitTime: Date.now() - request.timestamp
    });
    
    request.resolve(connection);
  }
  
  release(connection) {
    if (!connection || !this.connections.has(connection)) {
      console.warn('⚠️ Attempted to release unknown connection');
      return;
    }
    
    connection.isActive = false;
    connection.lastUsed = Date.now();
    connection.metadata.totalRequests++;
    
    delete connection.currentAgentId;
    delete connection.currentAgentTier;
    
    this.availableConnections.push(connection);
    
    this.emit('connection-released', {
      connectionId: connection.id,
      totalRequests: connection.metadata.totalRequests
    });
    
    // Process any pending requests
    if (this.pendingRequests.length > 0) {
      setImmediate(() => this.processNextRequest());
    }
  }
  
  getAgentPriority(agentTier) {
    switch (agentTier) {
    case AGENT_TIERS.ELITE_11:
      return 10;
    case AGENT_TIERS.MASTERY_33:
      return 5;
    case AGENT_TIERS.STANDARD:
    default:
      return 0;
    }
  }
  
  performHealthCheck() {
    const now = Date.now();
    const connectionsToRemove = [];
    
    for (const connection of this.connections) {
      // Remove idle connections that exceed idle timeout
      if (!connection.isActive && 
          (now - connection.lastUsed) > this.config.idleTimeout &&
          this.connections.size > this.config.minConnections) {
        
        connectionsToRemove.push(connection);
      }
      
      // Mark connections as unhealthy if they've been active too long
      if (connection.isActive && (now - connection.lastUsed) > (this.config.connectionTimeout * 2)) {
        connection.healthStatus = 'unhealthy';
      }
    }
    
    // Remove idle connections
    connectionsToRemove.forEach(connection => {
      this.connections.delete(connection);
      const index = this.availableConnections.indexOf(connection);
      if (index > -1) {
        this.availableConnections.splice(index, 1);
      }
      this.emit('connection-removed', connection);
    });
    
    // Ensure minimum connections
    const connectionsNeeded = this.config.minConnections - this.connections.size;
    for (let i = 0; i < connectionsNeeded; i++) {
      this.createConnection().catch(error => {
        console.error('Failed to create connection during health check:', error);
      });
    }
  }
  
  getStats() {
    const activeConnections = Array.from(this.connections).filter(conn => conn.isActive).length;
    const availableConnections = this.availableConnections.length;
    const pendingRequests = this.pendingRequests.length;
    
    return {
      region: this.config.region,
      totalConnections: this.connections.size,
      activeConnections,
      availableConnections,
      pendingRequests,
      maxConnections: this.config.maxConnections,
      utilizationRate: (activeConnections / this.connections.size) * 100,
      queueLength: pendingRequests
    };
  }
  
  destroy() {
    this.destroyed = true;
    
    // Reject all pending requests
    this.pendingRequests.forEach(request => {
      clearTimeout(request.timeout);
      request.reject(new Error('Connection pool destroyed'));
    });
    
    this.connections.clear();
    this.availableConnections.length = 0;
    this.pendingRequests.length = 0;
    
    this.emit('destroyed', { region: this.config.region });
  }
}

/**
 * Main Victory36 Connection Pool Manager
 */
class Victory36ConnectionPoolManager extends EventEmitter {
  constructor(config = {}) {
    super();
    
    this.config = {
      regions: REGIONS,
      maxAgents: MAX_AGENTS,
      loadBalancingStrategy: 'round-robin', // 'round-robin', 'least-connections', 'regional-affinity'
      failoverEnabled: true,
      metricsEnabled: true,
      securityEnabled: true,
      ...config
    };
    
    this.pools = new Map();
    this.healthMonitor = new HealthMonitor();
    this.metricsCollector = new MetricsCollector();
    this.currentRegionIndex = 0;
    
    this.initialize();
    this.setupEventHandlers();
  }
  
  async initialize() {
    console.warn('🌟 Initializing Victory36 Connection Pool Manager');
    console.warn(`📊 Configuration: ${this.config.maxAgents} max agents across ${this.config.regions.length} regions`);
    
    // Initialize connection pools for each region
    const poolPromises = this.config.regions.map(async (region) => {
      const poolConfig = {
        region,
        minConnections: Math.floor(this.config.maxAgents / this.config.regions.length / 100), // 1% of capacity
        maxConnections: Math.floor(this.config.maxAgents / this.config.regions.length),
        connectionTimeout: 5000,
        idleTimeout: 300000,
        retryAttempts: 3,
        healthCheckInterval: 30000
      };
      
      const pool = new ConnectionPool(poolConfig);
      this.pools.set(region, pool);
      
      // Forward pool events
      pool.on('connection-created', (_connection) => {
        this.metricsCollector.recordConnection(region, 'open');
        this.healthMonitor.recordMetric(region, 'connections', pool.connections.size);
      });
      
      pool.on('connection-removed', (_connection) => {
        this.metricsCollector.recordConnection(region, 'close');
        this.healthMonitor.recordMetric(region, 'connections', pool.connections.size);
      });
      
      return pool;
    });
    
    await Promise.all(poolPromises);
    
    // Start monitoring
    this.startMonitoring();
    
    console.warn('🎉 Victory36 Connection Pool Manager initialized successfully');
    this.emit('initialized', {
      regions: this.config.regions,
      totalPools: this.pools.size,
      maxCapacity: this.config.maxAgents
    });
  }
  
  setupEventHandlers() {
    // Health monitor events
    this.healthMonitor.on('health-check', (healthData) => {
      if (!healthData.isHealthy && this.config.failoverEnabled) {
        this.handleUnhealthyPool(healthData.poolId);
      }
      
      this.emit('pool-health', healthData);
    });
  }
  
  startMonitoring() {
    // Periodic metrics collection
    setInterval(() => {
      this.collectMetrics();
    }, 10000); // Every 10 seconds
    
    // Periodic health reporting
    setInterval(() => {
      this.reportSystemHealth();
    }, 60000); // Every minute
  }
  
  async getConnection(agentId, options = {}) {
    const {
      agentTier = AGENT_TIERS.STANDARD,
      preferredRegion = null
      // timeout reserved for future use
      // timeout = 5000
    } = options;
    
    const startTime = Date.now();
    
    try {
      const region = this.selectOptimalRegion(agentId, preferredRegion, agentTier);
      const pool = this.pools.get(region);
      
      if (!pool) {
        throw new Error(`No connection pool available for region: ${region}`);
      }
      
      const connection = await pool.acquire(agentId, agentTier);
      const responseTime = Date.now() - startTime;
      
      // Record metrics
      this.metricsCollector.recordRequest(region, true, responseTime);
      this.healthMonitor.recordMetric(region, 'latency', responseTime);
      
      // Add cleanup method to connection
      connection.release = () => {
        pool.release(connection);
      };
      
      this.emit('connection-assigned', {
        agentId,
        agentTier,
        region,
        connectionId: connection.id,
        responseTime
      });
      
      return connection;
      
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      // Try failover if enabled
      if (this.config.failoverEnabled && !options._failoverAttempt) {
        console.warn(`⚠️ Connection failed for agent ${agentId}, attempting failover...`);
        
        const failoverOptions = {
          ...options,
          _failoverAttempt: true,
          preferredRegion: null // Clear region preference for failover
        };
        
        try {
          return await this.getConnection(agentId, failoverOptions);
        } catch (failoverError) {
          this.metricsCollector.recordRequest(preferredRegion || 'unknown', false, responseTime);
          throw failoverError;
        }
      }
      
      this.metricsCollector.recordRequest(preferredRegion || 'unknown', false, responseTime);
      this.emit('connection-failed', {
        agentId,
        agentTier,
        error: error.message,
        responseTime
      });
      
      throw error;
    }
  }
  
  selectOptimalRegion(agentId, preferredRegion, _agentTier) {
    // If preferred region is specified and healthy, use it
    if (preferredRegion && this.pools.has(preferredRegion)) {
      const health = this.healthMonitor.getPoolHealth(preferredRegion);
      if (!health || health.successRate > 95) { // If no health data or healthy
        return preferredRegion;
      }
    }
    
    // Select region based on load balancing strategy
    switch (this.config.loadBalancingStrategy) {
    case 'least-connections':
      return this.selectLeastConnectionsRegion();
      
    case 'regional-affinity':
      return this.selectRegionalAffinityRegion(agentId);
      
    case 'round-robin':
    default:
      return this.selectRoundRobinRegion();
    }
  }
  
  selectRoundRobinRegion() {
    const availableRegions = this.getHealthyRegions();
    if (availableRegions.length === 0) {
      throw new Error('No healthy regions available');
    }
    
    const region = availableRegions[this.currentRegionIndex % availableRegions.length];
    this.currentRegionIndex++;
    return region;
  }
  
  selectLeastConnectionsRegion() {
    const availableRegions = this.getHealthyRegions();
    if (availableRegions.length === 0) {
      throw new Error('No healthy regions available');
    }
    
    let minConnections = Infinity;
    let selectedRegion = availableRegions[0];
    
    for (const region of availableRegions) {
      const pool = this.pools.get(region);
      const stats = pool.getStats();
      
      if (stats.activeConnections < minConnections) {
        minConnections = stats.activeConnections;
        selectedRegion = region;
      }
    }
    
    return selectedRegion;
  }
  
  selectRegionalAffinityRegion(agentId) {
    // Hash agent ID to determine region affinity
    const hash = crypto.createHash('md5').update(agentId).digest('hex');
    const regionIndex = parseInt(hash.substring(0, 8), 16) % this.config.regions.length;
    
    const preferredRegion = this.config.regions[regionIndex];
    const health = this.healthMonitor.getPoolHealth(preferredRegion);
    
    if (!health || health.successRate > 95) {
      return preferredRegion;
    }
    
    // Fallback to round-robin if preferred region is unhealthy
    return this.selectRoundRobinRegion();
  }
  
  getHealthyRegions() {
    return this.config.regions.filter(region => {
      const health = this.healthMonitor.getPoolHealth(region);
      return !health || health.successRate > 90; // Consider healthy if no data or >90% success rate
    });
  }
  
  handleUnhealthyPool(poolId) {
    console.warn(`🚨 Pool ${poolId} is unhealthy - implementing recovery measures`);
    
    // Could implement:
    // - Restart pool connections
    // - Reduce traffic to region
    // - Alert operations team
    
    this.emit('pool-unhealthy', { poolId });
  }
  
  collectMetrics() {
    const systemMetrics = {
      timestamp: new Date().toISOString(),
      totalAgents: 0,
      activeConnections: 0,
      regions: {}
    };
    
    for (const [region, pool] of this.pools) {
      const stats = pool.getStats();
      systemMetrics.totalAgents += stats.totalConnections;
      systemMetrics.activeConnections += stats.activeConnections;
      
      systemMetrics.regions[region] = {
        ...stats,
        health: this.healthMonitor.getPoolHealth(region)
      };
      
      // Update health monitor with current stats
      this.healthMonitor.recordMetric(region, 'connections', stats.totalConnections);
    }
    
    this.emit('metrics-collected', systemMetrics);
  }
  
  reportSystemHealth() {
    const overallMetrics = this.metricsCollector.getMetrics();
    const healthyRegions = this.getHealthyRegions();
    
    const systemHealth = {
      timestamp: new Date().toISOString(),
      status: healthyRegions.length === this.config.regions.length ? 'healthy' : 'degraded',
      healthyRegions: healthyRegions.length,
      totalRegions: this.config.regions.length,
      globalMetrics: overallMetrics.global,
      regionalMetrics: overallMetrics.regional,
      capacity: {
        maxAgents: this.config.maxAgents,
        currentAgents: overallMetrics.global.activeConnections,
        utilizationPercentage: (overallMetrics.global.activeConnections / this.config.maxAgents) * 100
      }
    };
    
    console.warn('📊 Victory36 System Health Report:', {
      status: systemHealth.status,
      healthyRegions: `${systemHealth.healthyRegions}/${systemHealth.totalRegions}`,
      utilization: `${systemHealth.capacity.utilizationPercentage.toFixed(2)}%`,
      activeConnections: systemHealth.capacity.currentAgents,
      successRate: `${this.metricsCollector.getSuccessRate().toFixed(2)}%`
    });
    
    this.emit('health-report', systemHealth);
  }
  
  getSystemStats() {
    const stats = {
      regions: {},
      summary: {
        totalPools: this.pools.size,
        totalConnections: 0,
        activeConnections: 0,
        availableConnections: 0,
        pendingRequests: 0,
        healthyRegions: this.getHealthyRegions().length
      }
    };
    
    for (const [region, pool] of this.pools) {
      const poolStats = pool.getStats();
      stats.regions[region] = poolStats;
      
      stats.summary.totalConnections += poolStats.totalConnections;
      stats.summary.activeConnections += poolStats.activeConnections;
      stats.summary.availableConnections += poolStats.availableConnections;
      stats.summary.pendingRequests += poolStats.pendingRequests;
    }
    
    return stats;
  }
  
  async shutdown() {
    console.warn('🔄 Shutting down Victory36 Connection Pool Manager...');
    
    // Destroy all pools
    const shutdownPromises = Array.from(this.pools.values()).map(pool => {
      return new Promise(resolve => {
        pool.destroy();
        resolve();
      });
    });
    
    await Promise.all(shutdownPromises);
    
    this.pools.clear();
    
    console.warn('✅ Victory36 Connection Pool Manager shutdown complete');
    this.emit('shutdown');
  }
}

// Export classes and constants
module.exports = {
  Victory36ConnectionPoolManager,
  ConnectionPool,
  HealthMonitor,
  MetricsCollector,
  AGENT_TIERS,
  MAX_AGENTS,
  REGIONS
};

// Example usage and testing
if (require.main === module) {
  const manager = new Victory36ConnectionPoolManager({
    regions: ['MOCOA', 'MOCORIX'],
    maxAgents: 100000, // Reduced for testing
    loadBalancingStrategy: 'least-connections'
  });
  
  manager.on('initialized', async () => {
    console.warn('🧪 Running connection pool tests...');
    
    try {
      // Test standard agent connection
      const connection1 = await manager.getConnection('agent-001', {
        agentTier: 'STANDARD'
      });
      console.warn('✅ Standard agent connection successful');
      connection1.release();
      
      // Test Elite 11 agent connection
      const connection2 = await manager.getConnection('agent-elite-001', {
        agentTier: 'ELITE_11',
        preferredRegion: 'MOCOA'
      });
      console.warn('✅ Elite 11 agent connection successful');
      connection2.release();
      
      // Test system stats
      const stats = manager.getSystemStats();
      console.warn('📊 System Stats:', JSON.stringify(stats, null, 2));
      
    } catch (error) {
      console.error('❌ Test failed:', error);
    }
  });
}
