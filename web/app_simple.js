/**
 * Simplified CryptoQuest Arbitrage Dashboard
 * Fixed version without complex Chart.js initialization issues
 */

class SimpleDashboard {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.updateInterval = 5000;
        this.currentSection = 'overview';
        this.init();
    }

    async init() {
        console.log('Initializing CryptoQuest Dashboard...');
        
        try {
            this.setupSidebarNavigation();
            this.setupEventListeners();
            await this.loadInitialData();
            this.startPeriodicUpdates();
            
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.handleError(error);
        }
    }

    setupSidebarNavigation() {
        const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all links
                navLinks.forEach(nl => nl.classList.remove('active'));
                
                // Add active class to clicked link
                link.classList.add('active');
                
                // Get target section
                const targetSection = link.getAttribute('data-section');
                this.showSection(targetSection);
            });
        });

        this.setupMobileSidebar();
    }

    setupMobileSidebar() {
        // Create mobile toggle if it doesn't exist
        let toggleBtn = document.querySelector('.sidebar-toggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'sidebar-toggle';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            document.body.appendChild(toggleBtn);
        }

        // Create overlay if it doesn't exist
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }

        const sidebar = document.getElementById('sidebar');

        if (sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('show');
                overlay.classList.toggle('show');
            });

            overlay.addEventListener('click', () => {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            });
        }
    }

    setupEventListeners() {
        // Auto-refresh toggle
        const autoRefreshBtn = document.getElementById('auto-refresh-toggle');
        if (autoRefreshBtn) {
            autoRefreshBtn.addEventListener('click', () => {
                this.toggleAutoRefresh();
            });
        }

        // Refresh buttons
        const refreshButtons = document.querySelectorAll('[id^="refresh-"]');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshCurrentSection();
            });
        });

        // Control buttons
        this.setupControlButtons();
    }

    setupControlButtons() {
        // Start/Stop bot
        const startBtn = document.getElementById('start-bot');
        const stopBtn = document.getElementById('stop-bot');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startBot());
        }
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopBot());
        }

        // Execute arbitrage buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('execute-arbitrage')) {
                const opportunityId = e.target.getAttribute('data-opportunity-id');
                this.executeArbitrage(opportunityId);
            }
        });
    }

    showSection(sectionName) {
        // Hide all sections
        const sections = document.querySelectorAll('.dashboard-section');
        sections.forEach(section => {
            section.style.display = 'none';
        });

        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
            this.currentSection = sectionName;
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }

    async loadInitialData() {
        try {
            // Load status
            await this.updateStatus();
            
            // Load opportunities
            await this.updateOpportunities();
            
            // Load metrics
            await this.updateMetrics();
            
            // Load executions
            await this.updateExecutions();
            
            // Show overview section by default
            this.showSection('overview');
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.handleError(error);
        }
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'overview':
                await this.updateStatus();
                await this.updateMetrics();
                break;
            case 'arbitrage':
                await this.updateOpportunities();
                await this.updateExecutions();
                break;
            case 'ai-miner':
                await this.updateMinerData();
                break;
            case 'liquidity':
                await this.updateLiquidityData();
                break;
            case 'cross-chain':
                await this.updateCrossChainData();
                break;
            case 'analytics':
                await this.updateAnalytics();
                break;
            case 'agent-kit':
                await this.updateAgentData();
                break;
            case 'security':
                await this.updateSecurityData();
                break;
        }
    }

    async updateStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/status`);
            const data = await response.json();
            
            this.displayStatus(data);
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    async updateOpportunities() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/opportunities`);
            const data = await response.json();
            
            this.displayOpportunities(data.opportunities || []);
        } catch (error) {
            console.error('Error updating opportunities:', error);
        }
    }

    async updateMetrics() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/metrics`);
            const data = await response.json();
            
            this.displayMetrics(data);
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    async updateExecutions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/executions`);
            const data = await response.json();
            
            this.displayExecutions(data.executions || []);
        } catch (error) {
            console.error('Error updating executions:', error);
        }
    }

    displayStatus(status) {
        const statusBadge = document.getElementById('status-badge');
        const statusText = document.getElementById('status-text');
        
        if (statusBadge) {
            statusBadge.className = status.status === 'running' ? 'badge bg-success' : 'badge bg-warning';
            statusBadge.innerHTML = `<i class="fas fa-circle pulse"></i> ${status.status}`;
        }
        
        if (statusText) {
            statusText.textContent = `Status: ${status.status} (${status.mode} mode)`;
        }

        // Update database status
        const dbStatus = document.getElementById('database-status');
        if (dbStatus) {
            dbStatus.textContent = status.database_connected ? 'Connected' : 'Disconnected';
            dbStatus.className = status.database_connected ? 'text-success' : 'text-warning';
        }
    }

    displayOpportunities(opportunities) {
        const container = document.getElementById('opportunities-list');
        if (!container) return;

        if (opportunities.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No active arbitrage opportunities found.</div>';
            return;
        }

        const html = opportunities.map(opp => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <div class="d-flex align-items-center">
                                <span class="badge bg-primary me-2">${opp.source}</span>
                                <i class="fas fa-arrow-right mx-2"></i>
                                <span class="badge bg-secondary">${opp.target}</span>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">Profit Potential</small>
                            <div class="fw-bold text-success">${(opp.profit * 100).toFixed(2)}%</div>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">Net Profit</small>
                            <div class="fw-bold">$${opp.net_profit.toFixed(2)}</div>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">Confidence</small>
                            <div class="fw-bold">${(opp.confidence * 100).toFixed(1)}%</div>
                        </div>
                        <div class="col-md-2">
                            <span class="badge bg-${opp.status === 'pending' ? 'warning' : 'success'}">${opp.status}</span>
                        </div>
                        <div class="col-md-1">
                            <button class="btn btn-sm btn-success execute-arbitrage" data-opportunity-id="${opp.id}">
                                <i class="fas fa-play"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    displayMetrics(metrics) {
        // Update metric cards
        const elements = {
            'total-arbitrages': metrics.total_arbitrages,
            'successful-arbitrages': metrics.successful_arbitrages,
            'total-profit': `$${metrics.total_profit.toFixed(2)}`,
            'success-rate': `${((metrics.successful_arbitrages / metrics.total_arbitrages) * 100).toFixed(1)}%`,
            'gas-costs': `$${metrics.total_gas_cost.toFixed(2)}`,
            'uptime': this.formatUptime(metrics.uptime)
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    displayExecutions(executions) {
        const container = document.getElementById('executions-list');
        if (!container) return;

        if (executions.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No recent executions found.</div>';
            return;
        }

        const html = executions.map(exec => `
            <div class="card mb-2">
                <div class="card-body py-2">
                    <div class="row align-items-center">
                        <div class="col-md-2">
                            <span class="badge bg-${exec.success ? 'success' : 'danger'}">
                                ${exec.success ? 'Success' : 'Failed'}
                            </span>
                        </div>
                        <div class="col-md-2">
                            <small>${exec.source_network} → ${exec.target_network}</small>
                        </div>
                        <div class="col-md-2">
                            <small>$${exec.actual_profit.toFixed(2)}</small>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">${exec.transaction_hash.substring(0, 10)}...</small>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">${new Date(exec.created_at).toLocaleString()}</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    // Placeholder methods for other sections
    async updateMinerData() { /* Implementation for AI Miner data */ }
    async updateLiquidityData() { /* Implementation for Liquidity data */ }
    async updateCrossChainData() { /* Implementation for Cross-chain data */ }
    async updateAnalytics() { /* Implementation for Analytics data */ }
    async updateAgentData() { /* Implementation for Agent Kit data */ }
    async updateSecurityData() { /* Implementation for Security data */ }

    // Control methods
    async startBot() {
        console.log('Starting bot...');
        // Implementation for starting bot
    }

    async stopBot() {
        console.log('Stopping bot...');
        // Implementation for stopping bot
    }

    async executeArbitrage(opportunityId) {
        console.log(`Executing arbitrage for opportunity ${opportunityId}`);
        // Implementation for executing arbitrage
    }

    // Utility methods
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }

    toggleAutoRefresh() {
        this.isAutoRefreshEnabled = !this.isAutoRefreshEnabled;
        if (this.isAutoRefreshEnabled) {
            this.startPeriodicUpdates();
        } else {
            this.stopPeriodicUpdates();
        }
    }

    startPeriodicUpdates() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
        }
        
        this.refreshIntervalId = setInterval(() => {
            if (this.isAutoRefreshEnabled) {
                this.loadSectionData(this.currentSection);
            }
        }, this.updateInterval);
    }

    stopPeriodicUpdates() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
            this.refreshIntervalId = null;
        }
    }

    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
    }

    handleError(error) {
        console.error('Dashboard error:', error);
        // Show user-friendly error message
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <strong>Notice:</strong> Some features may be limited in demo mode. 
                    Dashboard is displaying sample data.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SimpleDashboard();
});

// Fallback initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.dashboard) {
            window.dashboard = new SimpleDashboard();
        }
    });
} else {
    window.dashboard = new SimpleDashboard();
}