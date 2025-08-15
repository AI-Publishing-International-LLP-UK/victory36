/**
 * DSAO Icon Framework - Six Core Icons with PCP Integration
 * Aixtiv Symphony Orchestrating Operating System (ASOOS)
 * 
 * Interactive icons for human engagement + Proactive PCP delivery system
 * Dream Commander delivers 5 daily projects + 5 strategic hot tips every morning
 */

class DSAOIconFramework {
    constructor() {
        this.icons = this.initializeIcons();
        this.pcpService = new PCPProactiveService();
        this.dreamCommander = new DreamCommanderDelivery();
        this.engagementTracker = new EngagementTracker();
        
        this.initializeFramework();
    }

    initializeIcons() {
        return {
            communication: {
                id: 'communication',
                title: 'Communication',
                subtitle: 'Automated Communications',
                description: 'Intelligent messaging, notifications, and stakeholder engagement automation',
                color: '#4A90E2',
                icon: '💬',
                pcpWorkflows: ['messaging_automation', 'stakeholder_engagement', 'notification_intelligence'],
                dreamCommanderCategories: ['communication_optimization', 'relationship_building']
            },
            
            growth: {
                id: 'growth',
                title: 'Automated Growth',
                subtitle: 'Strategic Expansion',
                description: 'AI-driven growth strategies, market expansion, and opportunity identification',
                color: '#7ED321',
                icon: '📈',
                pcpWorkflows: ['growth_strategy', 'market_analysis', 'opportunity_detection'],
                dreamCommanderCategories: ['growth_opportunities', 'strategic_initiatives']
            },
            
            delight: {
                id: 'delight',
                title: 'Customer Delight',
                subtitle: 'Automated Customer Engagement',
                description: 'Personalized customer experiences, satisfaction optimization, and loyalty building',
                color: '#F5A623',
                icon: '⭐',
                pcpWorkflows: ['customer_experience', 'satisfaction_tracking', 'loyalty_optimization'],
                dreamCommanderCategories: ['customer_opportunities', 'satisfaction_improvements']
            },
            
            workflow: {
                id: 'workflow',
                title: 'Workflow Automation',
                subtitle: 'Process Optimization',
                description: 'Intelligent process automation, efficiency optimization, and productivity enhancement',
                color: '#BD10E0',
                icon: '⚙️',
                pcpWorkflows: ['process_automation', 'efficiency_optimization', 'productivity_enhancement'],
                dreamCommanderCategories: ['process_improvements', 'automation_opportunities']
            },
            
            roi: {
                id: 'roi',
                title: 'ROI',
                subtitle: 'Return on Investment',
                description: 'Financial optimization, performance tracking, and value maximization strategies',
                color: '#50E3C2',
                icon: '💰',
                pcpWorkflows: ['financial_optimization', 'performance_tracking', 'value_analysis'],
                dreamCommanderCategories: ['financial_opportunities', 'value_optimization']
            },
            
            vision: {
                id: 'vision',
                title: 'Wish Vision',
                subtitle: 'Strategic Visioning',
                description: 'Future planning, goal achievement, and transformational strategy development',
                color: '#B8E986',
                icon: '🌟',
                pcpWorkflows: ['strategic_planning', 'goal_achievement', 'transformation_strategy'],
                dreamCommanderCategories: ['visionary_projects', 'transformational_opportunities']
            }
        };
    }

    initializeFramework() {
        this.renderIconInterface();
        this.startProactiveDelivery();
        this.initializeEngagementTracking();
    }

    renderIconInterface() {
        const iconContainer = document.createElement('div');
        iconContainer.className = 'dsao-icon-framework';
        iconContainer.innerHTML = `
            <div class="dsao-header">
                <h2>Diamond SAO Package</h2>
                <div class="pcp-status">
                    <span class="pcp-indicator">🤖</span>
                    <span class="pcp-text">Professional Co-Pilot Active</span>
                </div>
            </div>
            <div class="dsao-icons-grid">
                ${Object.values(this.icons).map(icon => this.renderIcon(icon)).join('')}
            </div>
            <div class="daily-delivery-panel">
                <div class="dream-commander-section">
                    <h3>📋 Today's Strategic Delivery</h3>
                    <div class="delivery-content">
                        <div class="daily-projects">
                            <h4>5 Daily Projects</h4>
                            <div id="daily-projects-list"></div>
                        </div>
                        <div class="strategic-tips">
                            <h4>5 Strategic Hot Tips</h4>
                            <div id="strategic-tips-list"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insert into DOM or return for integration
        if (document.body) {
            document.body.appendChild(iconContainer);
        }
        
        this.addIconEventListeners();
        this.addStyles();
    }

    renderIcon(icon) {
        return `
            <div class="dsao-icon" data-icon-id="${icon.id}" style="border-left: 4px solid ${icon.color}">
                <div class="icon-visual">
                    <span class="icon-emoji">${icon.icon}</span>
                </div>
                <div class="icon-content">
                    <h3>${icon.title}</h3>
                    <p class="subtitle">${icon.subtitle}</p>
                    <p class="description">${icon.description}</p>
                    <div class="pcp-workflows">
                        ${icon.pcpWorkflows.map(workflow => 
                            `<span class="workflow-tag">${workflow.replace(/_/g, ' ')}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="icon-actions">
                    <button class="activate-btn" data-action="activate" data-icon="${icon.id}">
                        Activate
                    </button>
                    <button class="configure-btn" data-action="configure" data-icon="${icon.id}">
                        Configure
                    </button>
                </div>
            </div>
        `;
    }

    addIconEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="activate"]')) {
                this.activateIcon(e.target.dataset.icon);
            } else if (e.target.matches('[data-action="configure"]')) {
                this.configureIcon(e.target.dataset.icon);
            }
        });
    }

    activateIcon(iconId) {
        const icon = this.icons[iconId];
        if (!icon) return;

        this.engagementTracker.recordInteraction(iconId, 'activate');
        
        // Trigger PCP workflows
        icon.pcpWorkflows.forEach(workflow => {
            this.pcpService.activateWorkflow(workflow, {
                iconId,
                userId: this.getCurrentUserId(),
                timestamp: new Date().toISOString()
            });
        });

        // Show activation feedback
        this.showActivationFeedback(icon);
        
        // Log to Victory36 protection
        console.log(`🛡️ Victory36: Icon ${iconId} activated - PCP workflows initiated`);
    }

    configureIcon(iconId) {
        const icon = this.icons[iconId];
        if (!icon) return;

        this.engagementTracker.recordInteraction(iconId, 'configure');
        
        // Open configuration panel
        this.openConfigurationPanel(icon);
    }

    showActivationFeedback(icon) {
        const notification = document.createElement('div');
        notification.className = 'dsao-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${icon.icon}</span>
                <div class="notification-text">
                    <strong>${icon.title} Activated</strong>
                    <p>Professional Co-Pilot is now optimizing ${icon.subtitle.toLowerCase()}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    startProactiveDelivery() {
        // Initialize daily delivery at login
        this.dreamCommander.deliverDailyContent();
        
        // Check if user hasn't logged in by 9 AM - send proactive ping
        const now = new Date();
        const nineAM = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 9, 0, 0);
        
        if (now > nineAM && !this.hasUserLoggedInToday()) {
            this.sendProactivePing();
        }
    }

    sendProactivePing() {
        // This would integrate with notification systems
        const pingMessage = {
            title: "Good morning! Your strategic delivery awaits",
            body: "Come, we have your 5 daily projects and strategic hot tips ready",
            icon: "🎯",
            action: "open_dsao"
        };
        
        // Send via appropriate channels (email, SMS, push, etc.)
        this.pcpService.sendProactiveNotification(pingMessage);
    }

    hasUserLoggedInToday() {
        const lastLogin = localStorage.getItem('lastLogin');
        if (!lastLogin) return false;
        
        const lastLoginDate = new Date(lastLogin);
        const today = new Date();
        
        return lastLoginDate.toDateString() === today.toDateString();
    }

    getCurrentUserId() {
        // Integration with authentication system
        return localStorage.getItem('userId') || 'anonymous';
    }

    addStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            .dsao-icon-framework {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .dsao-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }

            .pcp-status {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .pcp-indicator {
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }

            .dsao-icons-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .dsao-icon {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                cursor: pointer;
            }

            .dsao-icon:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            }

            .icon-visual {
                text-align: center;
                margin-bottom: 15px;
            }

            .icon-emoji {
                font-size: 2.5em;
                display: block;
            }

            .icon-content h3 {
                margin: 0 0 5px 0;
                color: #333;
                font-size: 1.3em;
            }

            .subtitle {
                color: #666;
                font-weight: 600;
                margin: 0 0 10px 0;
                font-size: 0.9em;
            }

            .description {
                color: #888;
                margin: 0 0 15px 0;
                line-height: 1.4;
                font-size: 0.9em;
            }

            .pcp-workflows {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-bottom: 15px;
            }

            .workflow-tag {
                background: #f0f0f0;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                color: #666;
                text-transform: capitalize;
            }

            .icon-actions {
                display: flex;
                gap: 10px;
            }

            .activate-btn, .configure-btn {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s;
            }

            .activate-btn {
                background: #4CAF50;
                color: white;
            }

            .activate-btn:hover {
                background: #45a049;
            }

            .configure-btn {
                background: #f0f0f0;
                color: #333;
            }

            .configure-btn:hover {
                background: #e0e0e0;
            }

            .daily-delivery-panel {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                border: 2px solid #e9ecef;
            }

            .dream-commander-section h3 {
                margin: 0 0 20px 0;
                color: #333;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .delivery-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }

            .daily-projects, .strategic-tips {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }

            .daily-projects h4, .strategic-tips h4 {
                margin: 0 0 15px 0;
                color: #555;
                border-bottom: 2px solid #eee;
                padding-bottom: 8px;
            }

            .dsao-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                animation: slideIn 0.3s ease-out;
            }

            .dsao-notification.fade-out {
                animation: fadeOut 0.3s ease-out;
            }

            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }

            .notification-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .notification-icon {
                font-size: 1.5em;
            }

            .notification-text strong {
                display: block;
                margin-bottom: 4px;
                color: #333;
            }

            .notification-text p {
                margin: 0;
                color: #666;
                font-size: 0.9em;
            }

            @media (max-width: 768px) {
                .dsao-icons-grid {
                    grid-template-columns: 1fr;
                }
                
                .delivery-content {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
}

/**
 * Professional Co-Pilot Proactive Service
 * Handles workflow activation and proactive user engagement
 */
class PCPProactiveService {
    constructor() {
        this.activeWorkflows = new Map();
        this.notificationChannels = ['email', 'sms', 'push', 'ui'];
    }

    activateWorkflow(workflowName, context) {
        const workflowId = `${workflowName}_${Date.now()}`;
        
        const workflow = {
            id: workflowId,
            name: workflowName,
            context,
            status: 'active',
            startTime: new Date(),
            progress: 0
        };

        this.activeWorkflows.set(workflowId, workflow);
        
        // Trigger specific workflow logic
        this.executeWorkflow(workflow);
        
        console.log(`🤖 PCP: Workflow ${workflowName} activated with ID ${workflowId}`);
    }

    executeWorkflow(workflow) {
        // Workflow-specific logic would go here
        // This would integrate with the broader ASOOS orchestration
        
        const workflowActions = {
            messaging_automation: () => this.setupMessagingAutomation(workflow),
            growth_strategy: () => this.initiateGrowthStrategy(workflow),
            customer_experience: () => this.optimizeCustomerExperience(workflow),
            process_automation: () => this.implementProcessAutomation(workflow),
            financial_optimization: () => this.analyzeFinancialOptimization(workflow),
            strategic_planning: () => this.developStrategicPlan(workflow)
        };

        const action = workflowActions[workflow.name];
        if (action) {
            action();
        }
    }

    sendProactiveNotification(message) {
        // This would integrate with actual notification systems
        console.log(`🔔 PCP Proactive Notification:`, message);
        
        // For demo purposes, show browser notification if available
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(message.title, {
                body: message.body,
                icon: '/favicon.ico'
            });
        }
    }

    // Placeholder workflow methods
    setupMessagingAutomation(workflow) {
        console.log(`📧 Setting up messaging automation for ${workflow.context.userId}`);
    }

    initiateGrowthStrategy(workflow) {
        console.log(`📈 Initiating growth strategy analysis for ${workflow.context.userId}`);
    }

    optimizeCustomerExperience(workflow) {
        console.log(`⭐ Optimizing customer experience for ${workflow.context.userId}`);
    }

    implementProcessAutomation(workflow) {
        console.log(`⚙️ Implementing process automation for ${workflow.context.userId}`);
    }

    analyzeFinancialOptimization(workflow) {
        console.log(`💰 Analyzing financial optimization for ${workflow.context.userId}`);
    }

    developStrategicPlan(workflow) {
        console.log(`🌟 Developing strategic plan for ${workflow.context.userId}`);
    }
}

/**
 * Dream Commander Daily Delivery System
 * Delivers 5 daily projects + 5 strategic hot tips every morning
 */
class DreamCommanderDelivery {
    constructor() {
        this.deliveryHistory = new Map();
    }

    deliverDailyContent() {
        const today = new Date().toDateString();
        
        if (this.deliveryHistory.has(today)) {
            this.displayExistingContent(today);
            return;
        }

        const dailyContent = this.generateDailyContent();
        this.deliveryHistory.set(today, dailyContent);
        this.displayDailyContent(dailyContent);
    }

    generateDailyContent() {
        return {
            projects: this.generateDailyProjects(),
            tips: this.generateStrategicTips(),
            timestamp: new Date().toISOString()
        };
    }

    generateDailyProjects() {
        const projectTemplates = [
            "Review and optimize your top 3 customer touchpoints",
            "Analyze yesterday's workflow bottlenecks and implement fixes",
            "Connect with 2 strategic stakeholders who could accelerate growth",
            "Identify automation opportunity in your most time-consuming process",
            "Plan next quarter's key strategic initiative"
        ];

        return projectTemplates.map((template, index) => ({
            id: `project_${index + 1}`,
            title: `Project ${index + 1}`,
            description: template,
            priority: ['high', 'medium', 'high', 'medium', 'high'][index],
            estimatedTime: ['30min', '45min', '20min', '60min', '90min'][index]
        }));
    }

    generateStrategicTips() {
        const tipTemplates = [
            "Focus on strengthening relationships with your top 20% of clients - they drive 80% of satisfaction",
            "Implement one small automation today that saves 10 minutes - it compounds to hours weekly",
            "Ask 'What would this look like if it were easy?' before tackling complex challenges",
            "Schedule strategic thinking time weekly - visionary leaders protect their planning space",
            "Measure one new metric this week that directly correlates to customer delight"
        ];

        return tipTemplates.map((template, index) => ({
            id: `tip_${index + 1}`,
            title: `Strategic Tip ${index + 1}`,
            content: template,
            category: ['relationships', 'automation', 'mindset', 'strategy', 'metrics'][index],
            impact: 'high'
        }));
    }

    displayDailyContent(content) {
        this.displayProjects(content.projects);
        this.displayTips(content.tips);
    }

    displayExistingContent(today) {
        const content = this.deliveryHistory.get(today);
        this.displayDailyContent(content);
    }

    displayProjects(projects) {
        const projectsList = document.getElementById('daily-projects-list');
        if (!projectsList) return;

        projectsList.innerHTML = projects.map(project => `
            <div class="daily-item project-item" data-priority="${project.priority}">
                <div class="item-header">
                    <h5>${project.title}</h5>
                    <span class="time-estimate">${project.estimatedTime}</span>
                </div>
                <p>${project.description}</p>
                <div class="item-actions">
                    <button class="start-btn" data-project-id="${project.id}">Start</button>
                    <button class="defer-btn" data-project-id="${project.id}">Defer</button>
                </div>
            </div>
        `).join('');
    }

    displayTips(tips) {
        const tipsList = document.getElementById('strategic-tips-list');
        if (!tipsList) return;

        tipsList.innerHTML = tips.map(tip => `
            <div class="daily-item tip-item" data-category="${tip.category}">
                <div class="item-header">
                    <h5>${tip.title}</h5>
                    <span class="tip-category">${tip.category}</span>
                </div>
                <p>${tip.content}</p>
                <div class="item-actions">
                    <button class="apply-btn" data-tip-id="${tip.id}">Apply Now</button>
                    <button class="save-btn" data-tip-id="${tip.id}">Save for Later</button>
                </div>
            </div>
        `).join('');
    }
}

/**
 * Engagement Tracking System
 * Monitors user interaction patterns with icons and content
 */
class EngagementTracker {
    constructor() {
        this.interactions = [];
        this.sessionStart = new Date();
    }

    recordInteraction(iconId, action, metadata = {}) {
        const interaction = {
            iconId,
            action,
            timestamp: new Date().toISOString(),
            sessionTime: Date.now() - this.sessionStart.getTime(),
            metadata
        };

        this.interactions.push(interaction);
        this.analyzeEngagementPatterns();
    }

    analyzeEngagementPatterns() {
        // Simple engagement analysis
        const iconUsage = this.interactions.reduce((acc, interaction) => {
            acc[interaction.iconId] = (acc[interaction.iconId] || 0) + 1;
            return acc;
        }, {});

        // Store patterns for PCP optimization
        localStorage.setItem('engagementPatterns', JSON.stringify({
            iconUsage,
            totalInteractions: this.interactions.length,
            sessionLength: Date.now() - this.sessionStart.getTime(),
            lastUpdated: new Date().toISOString()
        }));
    }
}

// Global initialization and API
window.DSAOFramework = {
    init: () => {
        window.dsaoInstance = new DSAOIconFramework();
        console.log('🎭 DSAO Icon Framework initialized with Victory36 protection');
    },
    
    getInstance: () => window.dsaoInstance,
    
    // API for external integration
    activateIcon: (iconId) => window.dsaoInstance?.activateIcon(iconId),
    deliverDailyContent: () => window.dsaoInstance?.dreamCommander.deliverDailyContent(),
    getEngagementData: () => JSON.parse(localStorage.getItem('engagementPatterns') || '{}')
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.DSAOFramework.init);
} else {
    window.DSAOFramework.init();
}

export { DSAOIconFramework, PCPProactiveService, DreamCommanderDelivery, EngagementTracker };
