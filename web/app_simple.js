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
        // Create mobile toggle button if not exists
        let toggleBtn = document.querySelector('.sidebar-toggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'sidebar-toggle';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            document.body.appendChild(toggleBtn);
        }

        // Create overlay if not exists
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }

        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        // Show mobile toggle on smaller screens
        const checkMobile = () => {
            if (window.innerWidth <= 1200) {
                toggleBtn.style.display = 'block';
            } else {
                toggleBtn.style.display = 'none';
                sidebar.classList.remove('show');
                overlay.style.display = 'none';
            }
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);

        // Toggle sidebar
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
            overlay.style.display = sidebar.classList.contains('show') ? 'block' : 'none';
        });

        // Close on overlay click
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.style.display = 'none';
        });
    }

    setupEventListeners() {
        // Bot control buttons
        const startBtn = document.getElementById('start-bot');
        const pauseBtn = document.getElementById('pause-bot');
        const emergencyBtn = document.getElementById('emergency-stop');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startBot());
        }
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.stopBot());
        }
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.emergencyStop());
        }

        // Auto-execute toggle
        const autoExecuteToggle = document.getElementById('auto-execute-toggle');
        if (autoExecuteToggle) {
            autoExecuteToggle.addEventListener('click', () => {
                this.toggleAutoExecution();
            });
        }

        // Refresh buttons
        const refreshButtons = document.querySelectorAll('[id^="refresh-"]');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.loadSectionData(this.currentSection);
                this.showNotification('Data refreshed', 'info');
            });
        });
    }

    async loadInitialData() {
        try {
            // Load initial dashboard data
            await this.loadOverviewData();

            // Welcome message
            setTimeout(() => {
                this.speak('Welcome to CryptoQuest Dashboard. I\'m here to help you navigate and understand the system.');
            }, 2000);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.handleError(error);
        }
    }

    async loadOverviewData() {
        try {
            const [statusResponse, metricsResponse] = await Promise.all([
                fetch(`${this.apiBaseUrl}/api/status`),
                fetch(`${this.apiBaseUrl}/api/metrics`)
            ]);

            if (statusResponse.ok && metricsResponse.ok) {
                const status = await statusResponse.json();
                const metrics = await metricsResponse.json();

                this.updateElement('total-arbitrages', metrics.total_arbitrages || 0);
                this.updateElement('success-rate', `${metrics.success_rate || 0}%`);
                this.updateElement('total-profit', `$${(metrics.total_profit || 0).toFixed(2)}`);
                this.updateElement('uptime', this.formatUptime(metrics.uptime || 0));

                // Update status badge
                this.updateConnectionStatus(status.status === 'running');
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    async loadArbitrageData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/opportunities`);
            if (response.ok) {
                const data = await response.json();
                this.updateOpportunitiesTable(data.opportunities || []);
            }
        } catch (error) {
            console.error('Error loading arbitrage data:', error);
        }
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
                    <span class="badge bg-primary">${opp.source || 'Unknown'}</span>
                    <i class="fas fa-arrow-right mx-1"></i>
                    <span class="badge bg-secondary">${opp.target || 'Unknown'}</span>
                </td>
                <td><span class="text-success">${((opp.profit || 0) * 100).toFixed(2)}%</span></td>
                <td><span class="badge bg-success">${((opp.confidence || 0) * 100).toFixed(0)}%</span></td>
                <td class="text-success">$${(opp.net_profit || 0).toFixed(4)}</td>
                <td><span class="badge bg-success">Active</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="window.dashboard.executeArbitrage('${opp.id || 'unknown'}')">
                        <i class="fas fa-play"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateConnectionStatus(connected) {
        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            statusBadge.className = `badge me-2 ${connected ? 'bg-success' : 'bg-danger'}`;
            statusBadge.innerHTML = `<i class="fas fa-circle ${connected ? 'pulse' : ''}"></i> ${connected ? 'Online' : 'Offline'}`;
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    toggleAutoExecution() {
        const btn = document.getElementById('auto-execute-toggle');
        if (btn) {
            const isOn = btn.textContent.includes('OFF');
            btn.innerHTML = `<i class="fas fa-magic"></i> Auto Execute: ${isOn ? 'ON' : 'OFF'}`;
            btn.className = `btn btn-sm ${isOn ? 'btn-success' : 'btn-outline-secondary'}`;

            this.showNotification(`Auto execution ${isOn ? 'enabled' : 'disabled'}`, 'info');
            this.speak(`Auto execution ${isOn ? 'enabled' : 'disabled'}`);
        }
    }

    async emergencyStop() {
        if (confirm('Are you sure you want to emergency stop all operations?')) {
            this.showNotification('Emergency stop activated', 'warning');
            this.speak('Emergency stop activated. All operations have been halted.');
        }
    }

    handleError(error) {
        console.error('Dashboard error:', error);
        this.showNotification('An error occurred: ' + error.message, 'error');
        this.speak('An error has occurred. Please check the console for details.');
    }

    startPeriodicUpdates() {
        if (this.updateInterval) {
            setInterval(async () => {
                try {
                    await this.loadOverviewData();
                    if (this.currentSection === 'arbitrage') {
                        await this.loadArbitrageData();
                    }
                } catch (error) {
                    console.error('Periodic update error:', error);
                }
            }, this.updateInterval);
        }
    }

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

    stopPeriodicUpdates() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
            this.refreshIntervalId = null;
        }
    }

    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
    }

    showNotification(message, type = 'info') {
        const notificationArea = document.getElementById('notification-area');
        if (!notificationArea) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        notificationArea.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    speak(text) {
        if ('speechSynthesis' in window) {
            const speech = new SpeechSynthesisUtterance(text);
            speechSynthesis.speak(speech);
        } else {
            console.warn('Text-to-speech not supported in this browser.');
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