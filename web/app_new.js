/**
 * Enhanced CryptoQuest Arbitrage Dashboard with Sidebar Navigation
 * Real-time monitoring and control interface for the arbitrage bot
 */

class EnhancedArbitrageDashboard {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.updateInterval = 5000; // 5 seconds
        this.currentSection = 'overview';
        this.isAutoRefreshEnabled = true;
        this.refreshIntervalId = null;
        
        // Chart instances
        this.priceChart = null;
        this.performanceChart = null;
        this.gasChart = null;
        
        // Data storage
        this.chartData = {
            labels: [],
            polygonPrices: [],
            basePrices: [],
            predictions: []
        };
        
        this.init();
    }

    async init() {
        console.log('Initializing Enhanced CryptoQuest Dashboard...');
        
        // Initialize components
        this.setupSidebarNavigation();
        this.setupEventListeners();
        this.initializeCharts();
        this.setupWebSocket();
        
        // Load initial data
        await this.loadInitialData();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        console.log('Enhanced Dashboard initialized successfully');
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

        // Mobile sidebar toggle
        this.setupMobileSidebar();
    }

    setupMobileSidebar() {
        // Create mobile toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        document.body.appendChild(toggleBtn);

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);

        const sidebar = document.getElementById('sidebar');

        // Toggle sidebar
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });

        // Close on overlay click
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });

        // Close on window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1200) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            }
        });
    }

    showSection(sectionName) {
        // Hide all sections
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => {
            section.classList.remove('active');
        });

        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'arbitrage':
                await this.loadArbitrageData();
                break;
            case 'ai-miner':
                await this.loadAIMinerData();
                break;
            case 'liquidity':
                await this.loadLiquidityData();
                break;
            case 'cross-chain':
                await this.loadCrossChainData();
                break;
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'agent-kit':
                await this.loadAgentKitData();
                break;
            case 'security':
                await this.loadSecurityData();
                break;
        }
    }

    setupEventListeners() {
        // Bot control buttons
        this.setupBotControls();
        
        // Range sliders
        this.setupRangeSliders();
        
        // Toggle buttons
        this.setupToggleButtons();
        
        // Form submissions
        this.setupFormHandlers();
        
        // Refresh buttons
        this.setupRefreshButtons();
        
        // Auto-refresh toggle
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    setupBotControls() {
        const startBtn = document.getElementById('start-bot');
        const pauseBtn = document.getElementById('pause-bot');
        const emergencyBtn = document.getElementById('emergency-stop');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.controlBot('start'));
        }
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.controlBot('pause'));
        }
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.emergencyStop());
        }
    }

    setupRangeSliders() {
        // Reinvest slider
        const reinvestSlider = document.getElementById('reinvest-slider');
        const reinvestValue = document.getElementById('reinvest-value');
        
        if (reinvestSlider && reinvestValue) {
            reinvestSlider.addEventListener('input', (e) => {
                reinvestValue.textContent = `${e.target.value}%`;
            });
        }

        // Profit allocation slider
        const profitSlider = document.getElementById('profit-allocation');
        const profitValue = document.getElementById('profit-allocation-value');
        
        if (profitSlider && profitValue) {
            profitSlider.addEventListener('input', (e) => {
                profitValue.textContent = `${e.target.value}%`;
            });
        }

        // Decision threshold slider
        const thresholdSlider = document.getElementById('decision-threshold');
        const thresholdValue = document.getElementById('threshold-value');
        
        if (thresholdSlider && thresholdValue) {
            thresholdSlider.addEventListener('input', (e) => {
                thresholdValue.textContent = `${e.target.value}%`;
            });
        }
    }

    setupToggleButtons() {
        // Auto-execute toggle
        const autoExecuteToggle = document.getElementById('auto-execute-toggle');
        if (autoExecuteToggle) {
            autoExecuteToggle.addEventListener('click', () => {
                this.toggleAutoExecution();
            });
        }

        // Auto-inject toggle
        const autoInjectToggle = document.getElementById('auto-inject-toggle');
        if (autoInjectToggle) {
            autoInjectToggle.addEventListener('click', () => {
                this.toggleAutoInjection();
            });
        }
    }

    setupFormHandlers() {
        // Settings forms would be handled here
        // This is a placeholder for form submission logic
    }

    setupRefreshButtons() {
        const refreshButtons = document.querySelectorAll('[id^="refresh-"]');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshCurrentSection();
            });
        });
    }

    initializeCharts() {
        this.initializePriceChart();
        this.initializePerformanceChart();
        this.initializeGasChart();
    }

    initializePriceChart() {
        const canvas = document.getElementById('price-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.labels,
                datasets: [
                    {
                        label: 'CQT Price (Polygon)',
                        data: this.chartData.polygonPrices,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'CQT Price (Base)',
                        data: this.chartData.basePrices,
                        borderColor: '#764ba2',
                        backgroundColor: 'rgba(118, 75, 162, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'ML Prediction',
                        data: this.chartData.predictions,
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(6)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Price ($)'
                        },
                        beginAtZero: false
                    }
                }
            }
        });
    }

    initializePerformanceChart() {
        const canvas = document.getElementById('performance-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        this.performanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Successful Trades', 'Failed Trades', 'Pending'],
                datasets: [{
                    data: [85, 10, 5],
                    backgroundColor: [
                        '#28a745',
                        '#dc3545',
                        '#ffc107'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }

    initializeGasChart() {
        const canvas = document.getElementById('gas-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        this.gasChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Polygon', 'Base', 'Bridge'],
                datasets: [{
                    label: 'Average Gas Cost (USD)',
                    data: [5.2, 8.7, 12.5],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ],
                    borderColor: [
                        '#667eea',
                        '#764ba2',
                        '#ffc107'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Cost (USD)'
                        }
                    }
                }
            }
        });
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
        } catch (error) {
            console.error('Failed to establish WebSocket connection:', error);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'price_update':
                this.updatePriceChart(data.payload);
                break;
            case 'opportunity_found':
                this.addOpportunityToTable(data.payload);
                this.showNotification('New arbitrage opportunity found!', 'success');
                break;
            case 'arbitrage_executed':
                this.handleArbitrageExecution(data.payload);
                break;
            case 'bot_status':
                this.updateBotStatus(data.payload);
                break;
            case 'error':
                this.showNotification(data.payload.message, 'error');
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    async loadInitialData() {
        try {
            await this.loadOverviewData();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Failed to load initial data', 'error');
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/status`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const status = await response.json();
            
            // Update metrics
            this.updateElement('total-arbitrages', status.metrics?.total_arbitrages || 0);
            
            const successRate = status.metrics?.total_arbitrages > 0 
                ? ((status.metrics.successful_arbitrages / status.metrics.total_arbitrages) * 100).toFixed(1)
                : 0;
            this.updateElement('success-rate', `${successRate}%`);
            
            this.updateElement('total-profit', `$${(status.metrics?.total_profit || 0).toFixed(2)}`);
            this.updateElement('uptime', this.formatUptime(status.metrics?.uptime));
            
            // Update bot status
            this.updateBotStatus(status);
            
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showNotification('Failed to load system status', 'error');
        }
    }

    async loadArbitrageData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/opportunities`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const opportunities = await response.json();
            this.updateOpportunitiesTable(opportunities);
            
        } catch (error) {
            console.error('Error loading arbitrage data:', error);
        }
    }

    async loadAIMinerData() {
        // Load AI Miner specific data
        console.log('Loading AI Miner data...');
    }

    async loadLiquidityData() {
        // Load Liquidity Provider specific data
        console.log('Loading Liquidity data...');
    }

    async loadCrossChainData() {
        // Load Cross-Chain specific data
        console.log('Loading Cross-Chain data...');
    }

    async loadAnalyticsData() {
        // Load Analytics specific data
        console.log('Loading Analytics data...');
    }

    async loadAgentKitData() {
        // Load Agent Kit specific data
        console.log('Loading Agent Kit data...');
    }

    async loadSecurityData() {
        // Load Security specific data
        console.log('Loading Security data...');
    }

    updateOpportunitiesTable(opportunities) {
        const tbody = document.getElementById('opportunities-table');
        if (!tbody) return;
        
        if (!opportunities || opportunities.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No opportunities found</td></tr>';
            return;
        }
        
        tbody.innerHTML = opportunities.map(opp => `
            <tr>
                <td>
                    <span class="badge bg-primary me-1">${opp.source}</span>
                    <i class="fas fa-arrow-right mx-2"></i>
                    <span class="badge bg-secondary">${opp.target}</span>
                </td>
                <td>
                    <span class="text-success fw-bold">${(opp.profit * 100).toFixed(2)}%</span>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="progress flex-grow-1 me-2" style="height: 8px;">
                            <div class="progress-bar bg-${this.getConfidenceColor(opp.confidence)}" 
                                 style="width: ${opp.confidence * 100}%"></div>
                        </div>
                        <small>${(opp.confidence * 100).toFixed(0)}%</small>
                    </div>
                </td>
                <td class="text-success fw-bold">$${opp.profit.toFixed(4)}</td>
                <td>
                    <span class="badge bg-success">Active</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="dashboard.executeArbitrage('${opp.id}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="dashboard.showOpportunityDetails('${opp.id}')">
                        <i class="fas fa-info"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        // Update opportunities count
        this.updateElement('opportunities-count', opportunities.length);
    }

    async controlBot(action) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/bot/${action}`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.showNotification(`Bot ${action} command sent successfully`, 'success');
            
            // Update button states
            this.updateBotControlButtons(action);
            
        } catch (error) {
            console.error(`Error ${action} bot:`, error);
            this.showNotification(`Failed to ${action} bot`, 'error');
        }
    }

    async emergencyStop() {
        if (confirm('Are you sure you want to emergency stop all operations?')) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/api/emergency-stop`, {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                this.showNotification('Emergency stop activated', 'warning');
                
            } catch (error) {
                console.error('Error during emergency stop:', error);
                this.showNotification('Failed to execute emergency stop', 'error');
            }
        }
    }

    toggleAutoExecution() {
        // Toggle auto-execution logic
        const btn = document.getElementById('auto-execute-toggle');
        if (btn) {
            const isOn = btn.textContent.includes('OFF');
            btn.innerHTML = `<i class="fas fa-magic"></i> Auto Execute: ${isOn ? 'ON' : 'OFF'}`;
            btn.className = `btn btn-sm ${isOn ? 'btn-success' : 'btn-outline-secondary'}`;
        }
    }

    toggleAutoInjection() {
        // Toggle auto-injection logic
        const btn = document.getElementById('auto-inject-toggle');
        if (btn) {
            const isOn = btn.textContent.includes('OFF');
            btn.innerHTML = `<i class="fas fa-magic"></i> Auto-Inject: ${isOn ? 'ON' : 'OFF'}`;
            btn.className = `btn btn-sm ${isOn ? 'btn-success' : 'btn-outline-secondary'}`;
        }
    }

    updateBotControlButtons(action) {
        const startBtn = document.getElementById('start-bot');
        const pauseBtn = document.getElementById('pause-bot');
        
        if (action === 'start') {
            if (startBtn) startBtn.disabled = true;
            if (pauseBtn) pauseBtn.disabled = false;
        } else if (action === 'pause' || action === 'stop') {
            if (startBtn) startBtn.disabled = false;
            if (pauseBtn) pauseBtn.disabled = true;
        }
    }

    updateConnectionStatus(connected) {
        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            statusBadge.className = `badge me-2 ${connected ? 'bg-success' : 'bg-danger'}`;
            statusBadge.innerHTML = `<i class="fas fa-circle ${connected ? 'pulse' : ''}"></i> ${connected ? 'Online' : 'Offline'}`;
        }
    }

    updateBotStatus(status) {
        // Update various status indicators based on bot status
        this.updateConnectionStatus(status.running || false);
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    getConfidenceColor(confidence) {
        if (confidence >= 0.8) return 'success';
        if (confidence >= 0.6) return 'warning';
        return 'danger';
    }

    formatUptime(seconds) {
        if (!seconds) return '00:00:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
        this.showNotification('Data refreshed', 'info');
    }

    startPeriodicUpdates() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
        }
        
        this.refreshIntervalId = setInterval(() => {
            if (this.isAutoRefreshEnabled && !document.hidden) {
                this.loadSectionData(this.currentSection);
            }
        }, this.updateInterval);
    }

    pauseUpdates() {
        this.isAutoRefreshEnabled = false;
    }

    resumeUpdates() {
        this.isAutoRefreshEnabled = true;
    }

    showNotification(message, type = 'info') {
        // Create and show toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to page and show
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }

    executeArbitrage(opportunityId) {
        // Execute arbitrage logic
        console.log('Executing arbitrage for opportunity:', opportunityId);
        this.showNotification('Arbitrage execution initiated', 'info');
    }

    showOpportunityDetails(opportunityId) {
        // Show opportunity details logic
        console.log('Showing details for opportunity:', opportunityId);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnhancedArbitrageDashboard();
});

// Export for global access
window.EnhancedArbitrageDashboard = EnhancedArbitrageDashboard;