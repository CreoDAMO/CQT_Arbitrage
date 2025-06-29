/**
 * CryptoQuest Arbitrage Dashboard
 * Real-time monitoring and control interface for the arbitrage bot
 */

class ArbitrageDashboard {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.updateInterval = 5000; // 5 seconds
        this.chartData = {
            labels: [],
            prices: [],
            predictions: []
        };
        this.priceChart = null;
        this.isRunning = false;
        
        this.init();
    }

    async init() {
        console.log('Initializing CryptoQuest Arbitrage Dashboard...');
        
        // Initialize components
        this.initializeChart();
        this.setupEventListeners();
        this.setupWebSocket();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Initial data load
        await this.loadInitialData();
        
        console.log('Dashboard initialized successfully');
    }

    initializeChart() {
        const ctx = document.getElementById('price-chart').getContext('2d');
        
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.labels,
                datasets: [
                    {
                        label: 'CQT Price (Polygon)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'CQT Price (Base)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'ML Prediction',
                        data: [],
                        borderColor: 'rgb(255, 205, 86)',
                        backgroundColor: 'rgba(255, 205, 86, 0.1)',
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

    setupEventListeners() {
        // Bot control buttons
        document.getElementById('start-bot').addEventListener('click', () => this.startBot());
        document.getElementById('pause-bot').addEventListener('click', () => this.pauseBot());
        document.getElementById('stop-bot').addEventListener('click', () => this.stopBot());
        document.getElementById('emergency-withdraw').addEventListener('click', () => this.emergencyWithdraw());
        
        // Refresh buttons
        document.getElementById('refresh-opportunities').addEventListener('click', () => this.loadOpportunities());
        
        // Modal buttons
        document.getElementById('confirm-execute').addEventListener('click', () => this.executeArbitrage());
        document.getElementById('save-settings').addEventListener('click', () => this.saveSettings());
        
        // Auto-refresh toggle
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
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
            // Load system status
            await this.loadSystemStatus();
            
            // Load opportunities
            await this.loadOpportunities();
            
            // Load pool status
            await this.loadPoolStatus();
            
            // Load recent transactions
            await this.loadRecentTransactions();
            
            // Load ML predictions
            await this.loadMLPredictions();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Failed to load initial data', 'error');
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/status`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const status = await response.json();
            
            // Update metrics
            document.getElementById('total-arbitrages').textContent = status.metrics.total_arbitrages || 0;
            
            const successRate = status.metrics.total_arbitrages > 0 
                ? ((status.metrics.successful_arbitrages / status.metrics.total_arbitrages) * 100).toFixed(1)
                : 0;
            document.getElementById('success-rate').textContent = `${successRate}%`;
            
            document.getElementById('total-profit').textContent = `$${(status.metrics.total_profit || 0).toFixed(2)}`;
            document.getElementById('uptime').textContent = this.formatUptime(status.metrics.uptime);
            
            // Update bot status
            this.updateBotStatus(status);
            
        } catch (error) {
            console.error('Error loading system status:', error);
            this.showNotification('Failed to load system status', 'error');
        }
    }

    async loadOpportunities() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/opportunities`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const opportunities = await response.json();
            this.updateOpportunitiesTable(opportunities);
            
        } catch (error) {
            console.error('Error loading opportunities:', error);
            document.getElementById('opportunities-table').innerHTML = 
                '<tr><td colspan="6" class="text-center text-danger">Failed to load opportunities</td></tr>';
        }
    }

    async loadPoolStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/pools`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const pools = await response.json();
            this.updatePoolStatus(pools);
            
        } catch (error) {
            console.error('Error loading pool status:', error);
            document.getElementById('pools-status').innerHTML = 
                '<div class="text-danger">Failed to load pool data</div>';
        }
    }

    async loadRecentTransactions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/transactions`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const transactions = await response.json();
            this.updateTransactionsTimeline(transactions);
            
        } catch (error) {
            console.error('Error loading transactions:', error);
            document.getElementById('transactions-timeline').innerHTML = 
                '<div class="text-danger">Failed to load transaction data</div>';
        }
    }

    async loadMLPredictions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/predictions`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const predictions = await response.json();
            this.updateMLPredictions(predictions);
            
        } catch (error) {
            console.error('Error loading ML predictions:', error);
            this.showNotification('Failed to load ML predictions', 'warning');
        }
    }

    updateOpportunitiesTable(opportunities) {
        const tbody = document.getElementById('opportunities-table');
        
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
                    <span class="badge bg-${this.getStatusColor('active')}">Active</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="dashboard.showExecuteModal('${opp.id}')">
                        <i class="fas fa-play"></i> Execute
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="dashboard.showOpportunityDetails('${opp.id}')">
                        <i class="fas fa-info"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updatePoolStatus(pools) {
        const container = document.getElementById('pools-status');
        
        if (!pools || pools.length === 0) {
            container.innerHTML = '<div class="text-muted">No pool data available</div>';
            return;
        }
        
        container.innerHTML = pools.map(pool => `
            <div class="pool-item d-flex justify-content-between align-items-center mb-3 p-2 rounded bg-light">
                <div>
                    <strong>${pool.token0}/${pool.token1}</strong>
                    <br>
                    <small class="text-muted">${pool.network}</small>
                </div>
                <div class="text-end">
                    <div class="fw-bold">$${pool.price.toFixed(6)}</div>
                    <small class="text-muted">Liquidity: ${this.formatNumber(pool.liquidity)}</small>
                </div>
            </div>
        `).join('');
    }

    updateTransactionsTimeline(transactions) {
        const container = document.getElementById('transactions-timeline');
        
        if (!transactions || transactions.length === 0) {
            container.innerHTML = '<div class="text-muted">No recent transactions</div>';
            return;
        }
        
        container.innerHTML = transactions.map(tx => `
            <div class="timeline-item ${tx.status}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${tx.type}</strong>
                        <br>
                        <small class="text-muted">${tx.network}</small>
                        <br>
                        <small class="text-muted">${moment(tx.timestamp).fromNow()}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold ${tx.profit > 0 ? 'text-success' : 'text-danger'}">
                            ${tx.profit > 0 ? '+' : ''}$${tx.profit.toFixed(4)}
                        </div>
                        <span class="badge bg-${this.getStatusColor(tx.status)}">${tx.status}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateMLPredictions(predictions) {
        // Update liquidity risk
        const liquidityRisk = predictions.liquidity_risk || 0.25;
        document.getElementById('liquidity-risk').textContent = this.getRiskLabel(liquidityRisk);
        document.getElementById('liquidity-risk-bar').style.width = `${liquidityRisk * 100}%`;
        document.getElementById('liquidity-risk-bar').className = 
            `progress-bar bg-${this.getRiskColor(liquidityRisk)}`;
        
        // Update volatility
        const volatility = predictions.volatility || 0.5;
        document.getElementById('volatility').textContent = this.getRiskLabel(volatility);
        document.getElementById('volatility-bar').style.width = `${volatility * 100}%`;
        document.getElementById('volatility-bar').className = 
            `progress-bar bg-${this.getRiskColor(volatility)}`;
        
        // Update arbitrage success probability
        const successProb = predictions.execution_probability || 0.8;
        document.getElementById('arbitrage-success').textContent = this.getRiskLabel(1 - successProb);
        document.getElementById('arbitrage-success-bar').style.width = `${successProb * 100}%`;
        document.getElementById('arbitrage-success-bar').className = 
            `progress-bar bg-${this.getRiskColor(1 - successProb)}`;
    }

    updatePriceChart(priceData) {
        const now = moment().format('HH:mm:ss');
        
        // Add new data point
        this.chartData.labels.push(now);
        
        // Keep only last 50 data points
        if (this.chartData.labels.length > 50) {
            this.chartData.labels.shift();
            this.priceChart.data.datasets.forEach(dataset => {
                if (dataset.data.length > 50) {
                    dataset.data.shift();
                }
            });
        }
        
        // Update chart data
        if (priceData.polygon_price !== undefined) {
            this.priceChart.data.datasets[0].data.push(priceData.polygon_price);
        }
        
        if (priceData.base_price !== undefined) {
            this.priceChart.data.datasets[1].data.push(priceData.base_price);
        }
        
        if (priceData.prediction !== undefined) {
            this.priceChart.data.datasets[2].data.push(priceData.prediction);
        }
        
        this.priceChart.data.labels = this.chartData.labels;
        this.priceChart.update('none');
    }

    async startBot() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/bot/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.showNotification('Bot started successfully', 'success');
            this.updateBotControlButtons(true);
            
        } catch (error) {
            console.error('Error starting bot:', error);
            this.showNotification('Failed to start bot', 'error');
        }
    }

    async pauseBot() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/bot/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.showNotification('Bot paused', 'warning');
            this.updateBotControlButtons(false);
            
        } catch (error) {
            console.error('Error pausing bot:', error);
            this.showNotification('Failed to pause bot', 'error');
        }
    }

    async stopBot() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/bot/stop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.showNotification('Bot stopped', 'info');
            this.updateBotControlButtons(false);
            
        } catch (error) {
            console.error('Error stopping bot:', error);
            this.showNotification('Failed to stop bot', 'error');
        }
    }

    async emergencyWithdraw() {
        if (!confirm('Are you sure you want to perform an emergency withdrawal? This will stop all operations.')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/emergency/withdraw`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.showNotification('Emergency withdrawal initiated', 'warning');
            
        } catch (error) {
            console.error('Error performing emergency withdrawal:', error);
            this.showNotification('Failed to perform emergency withdrawal', 'error');
        }
    }

    showExecuteModal(opportunityId) {
        // Store the opportunity ID for execution
        this.selectedOpportunityId = opportunityId;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('executeModal'));
        modal.show();
    }

    async executeArbitrage() {
        if (!this.selectedOpportunityId) return;
        
        const amount = document.getElementById('arbitrage-amount').value;
        const slippage = document.getElementById('slippage-tolerance').value;
        
        if (!amount || amount <= 0) {
            this.showNotification('Please enter a valid amount', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/arbitrage/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    opportunity_id: this.selectedOpportunityId,
                    amount: parseFloat(amount),
                    slippage_tolerance: parseFloat(slippage)
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('executeModal'));
            modal.hide();
            
            this.showNotification('Arbitrage execution initiated', 'success');
            
        } catch (error) {
            console.error('Error executing arbitrage:', error);
            this.showNotification('Failed to execute arbitrage', 'error');
        }
    }

    updateBotStatus(status) {
        const statusBadge = document.getElementById('status-badge');
        const running = status.running || false;
        
        if (running) {
            statusBadge.innerHTML = '<i class="fas fa-circle pulse"></i> Online';
            statusBadge.className = 'badge bg-success me-2';
        } else {
            statusBadge.innerHTML = '<i class="fas fa-circle"></i> Offline';
            statusBadge.className = 'badge bg-secondary me-2';
        }
        
        this.updateBotControlButtons(running);
    }

    updateBotControlButtons(running) {
        const startBtn = document.getElementById('start-bot');
        const pauseBtn = document.getElementById('pause-bot');
        const stopBtn = document.getElementById('stop-bot');
        
        if (running) {
            startBtn.disabled = true;
            pauseBtn.disabled = false;
            stopBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            pauseBtn.disabled = true;
            stopBtn.disabled = true;
        }
    }

    updateConnectionStatus(connected) {
        // Update network status indicators
        const polygonStatus = document.getElementById('polygon-status');
        const baseStatus = document.getElementById('base-status');
        const bridgeStatus = document.getElementById('bridge-status');
        
        if (connected) {
            polygonStatus.textContent = 'Online';
            polygonStatus.className = 'badge bg-success';
            baseStatus.textContent = 'Online';
            baseStatus.className = 'badge bg-success';
            bridgeStatus.textContent = 'Operational';
            bridgeStatus.className = 'badge bg-success';
        } else {
            polygonStatus.textContent = 'Checking...';
            polygonStatus.className = 'badge bg-warning';
            baseStatus.textContent = 'Checking...';
            baseStatus.className = 'badge bg-warning';
            bridgeStatus.textContent = 'Checking...';
            bridgeStatus.className = 'badge bg-warning';
        }
    }

    startPeriodicUpdates() {
        this.updateTimer = setInterval(async () => {
            if (!document.hidden) {
                await this.loadSystemStatus();
                await this.loadOpportunities();
                await this.loadMLPredictions();
            }
        }, this.updateInterval);
    }

    pauseUpdates() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
    }

    resumeUpdates() {
        this.startPeriodicUpdates();
    }

    showNotification(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Utility functions
    getConfidenceColor(confidence) {
        if (confidence >= 0.8) return 'success';
        if (confidence >= 0.6) return 'warning';
        return 'danger';
    }

    getStatusColor(status) {
        switch (status) {
            case 'success': case 'completed': case 'active': return 'success';
            case 'pending': case 'executing': return 'warning';
            case 'failed': case 'error': return 'danger';
            default: return 'secondary';
        }
    }

    getRiskColor(risk) {
        if (risk <= 0.3) return 'success';
        if (risk <= 0.7) return 'warning';
        return 'danger';
    }

    getRiskLabel(risk) {
        if (risk <= 0.3) return 'Low';
        if (risk <= 0.7) return 'Medium';
        return 'High';
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': case 'danger': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }

    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toFixed(0);
    }

    formatUptime(uptime) {
        if (!uptime) return '00:00:00';
        
        // Parse uptime string or duration
        const match = uptime.match(/(\d+):(\d+):(\d+)/);
        if (match) {
            return uptime;
        }
        
        // If it's a duration in seconds
        const hours = Math.floor(uptime / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);
        const seconds = Math.floor(uptime % 60);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ArbitrageDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (window.dashboard) {
        if (document.hidden) {
            window.dashboard.pauseUpdates();
        } else {
            window.dashboard.resumeUpdates();
        }
    }
});

// Handle WebSocket reconnection on window focus
window.addEventListener('focus', () => {
    if (window.dashboard && (!window.dashboard.ws || window.dashboard.ws.readyState !== WebSocket.OPEN)) {
        window.dashboard.setupWebSocket();
    }
});
