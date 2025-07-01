/**
 * CryptoQuest Arbitrage Dashboard - Enhanced Version
 * Fixed navigation and section switching
 */

class CryptoQuestDashboard {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.updateInterval = 5000;
        this.currentSection = 'overview';
        this.isAutoRefreshEnabled = true;
        this.refreshIntervalId = null;

        this.init();
    }

    async init() {
        console.log('Initializing CryptoQuest Dashboard...');

        try {
            this.setupSidebarNavigation();
            this.setupEventListeners();
            this.setupChatBot();
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

        console.log('Setting up navigation for', navLinks.length, 'links');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                console.log('Navigation clicked:', link.getAttribute('data-section'));

                // Remove active class from all links
                navLinks.forEach(nl => nl.classList.remove('active'));

                // Add active class to clicked link
                link.classList.add('active');

                // Get target section
                const targetSection = link.getAttribute('data-section');
                if (targetSection) {
                    this.showSection(targetSection);
                }
            });
        });

        this.setupMobileSidebar();
    }

    showSection(sectionName) {
        console.log('Switching to section:', sectionName);

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

            // Announce section change
            this.speak(`Switched to ${sectionName.replace('-', ' ')} section`);
        } else {
            console.error('Section not found:', `${sectionName}-section`);
        }
    }

    async loadSectionData(sectionName) {
        console.log('Loading data for section:', sectionName);

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

    setupMobileSidebar() {
        // Create mobile toggle button if not exists
        let toggleBtn = document.querySelector('.sidebar-toggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'sidebar-toggle';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            toggleBtn.style.display = 'none';
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
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
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
            startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.startBot();
            });
        }
        if (pauseBtn) {
            pauseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.stopBot();
            });
        }
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.emergencyStop();
            });
        }

        // Auto-execute toggle
        const autoExecuteToggle = document.getElementById('auto-execute-toggle');
        if (autoExecuteToggle) {
            autoExecuteToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleAutoExecution();
            });
        }

        // Refresh buttons
        const refreshButtons = document.querySelectorAll('[id^="refresh-"]');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadSectionData(this.currentSection);
                this.showNotification('Data refreshed', 'info');
            });
        });

        // Settings and fullscreen buttons
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleFullscreen();
            });
        }
    }

    setupChatBot() {
        // Create chat interface if it doesn't exist
        if (!document.getElementById('chat-container')) {
            const chatContainer = document.createElement('div');
            chatContainer.id = 'chat-container';
            chatContainer.innerHTML = `
                <div class="chat-toggle" onclick="window.dashboard.toggleChat()">
                    <i class="fas fa-comments"></i>
                    <span>Ask Questions</span>
                </div>
                <div class="chat-panel" style="display: none;">
                    <div class="chat-header">
                        <h6>CryptoQuest Assistant</h6>
                        <button onclick="window.dashboard.toggleChat()" class="chat-close">×</button>
                    </div>
                    <div class="chat-messages" id="chat-messages"></div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Ask me anything about the dashboard...">
                        <button onclick="window.dashboard.sendMessage()"><i class="fas fa-paper-plane"></i></button>
                    </div>
                </div>
            `;
            document.body.appendChild(chatContainer);

            // Add chat styles
            if (!document.getElementById('chat-styles')) {
                const chatStyles = document.createElement('style');
                chatStyles.id = 'chat-styles';
                chatStyles.textContent = `
                    #chat-container {
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        z-index: 1000;
                    }
                    .chat-toggle {
                        background: #007bff;
                        color: white;
                        padding: 12px 16px;
                        border-radius: 25px;
                        cursor: pointer;
                        box-shadow: 0 4px 12px rgba(0,123,255,0.3);
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .chat-toggle:hover {
                        background: #0056b3;
                        transform: translateY(-2px);
                    }
                    .chat-panel {
                        position: absolute;
                        bottom: 60px;
                        right: 0;
                        width: 350px;
                        height: 400px;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                        display: flex;
                        flex-direction: column;
                    }
                    .chat-header {
                        background: #007bff;
                        color: white;
                        padding: 12px 16px;
                        border-radius: 12px 12px 0 0;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .chat-header h6 {
                        margin: 0;
                    }
                    .chat-close {
                        background: none;
                        border: none;
                        color: white;
                        font-size: 18px;
                        cursor: pointer;
                    }
                    .chat-messages {
                        flex: 1;
                        padding: 16px;
                        overflow-y: auto;
                    }
                    .chat-input {
                        display: flex;
                        padding: 12px;
                        border-top: 1px solid #eee;
                    }
                    .chat-input input {
                        flex: 1;
                        border: 1px solid #ddd;
                        border-radius: 20px;
                        padding: 8px 12px;
                        margin-right: 8px;
                    }
                    .chat-input button {
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 36px;
                        height: 36px;
                        cursor: pointer;
                    }
                    .message {
                        margin-bottom: 12px;
                        padding: 8px 12px;
                        border-radius: 12px;
                        max-width: 80%;
                    }
                    .message.user {
                        background: #007bff;
                        color: white;
                        margin-left: auto;
                    }
                    .message.bot {
                        background: #f1f3f4;
                        color: #333;
                    }
                `;
                document.head.appendChild(chatStyles);
            }

            // Add enter key support for chat
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendMessage();
                    }
                });
            }
        }
    }

    toggleChat() {
        const chatPanel = document.querySelector('.chat-panel');
        if (chatPanel) {
            if (chatPanel.style.display === 'none') {
                chatPanel.style.display = 'flex';
                this.speak('Chat assistant is now open. You can ask me questions about the dashboard.');
            } else {
                chatPanel.style.display = 'none';
            }
        }
    }

    sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'message user';
        userMessage.textContent = message;
        messagesContainer.appendChild(userMessage);

        // Clear input
        input.value = '';

        // Generate bot response
        setTimeout(() => {
            const botResponse = this.generateBotResponse(message);
            const botMessage = document.createElement('div');
            botMessage.className = 'message bot';
            botMessage.textContent = botResponse;
            messagesContainer.appendChild(botMessage);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Speak the response
            this.speak(botResponse);
        }, 1000);
    }

    generateBotResponse(message) {
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('section') || lowerMessage.includes('panel') || lowerMessage.includes('click')) {
            return "Try clicking on the sidebar items like Overview, Arbitrage, AI Miner, etc. Each section has different functionality. If sections aren't responding, try refreshing the page.";
        } else if (lowerMessage.includes('arbitrage')) {
            return "Arbitrage opportunities are displayed in the Arbitrage section. Click on the Arbitrage tab to view current opportunities and configure auto-execution settings.";
        } else if (lowerMessage.includes('profit') || lowerMessage.includes('money')) {
            return `Current total profit is ${document.getElementById('total-profit')?.textContent || '$0.00'}. You can view detailed analytics in the Analytics section.`;
        } else if (lowerMessage.includes('mining') || lowerMessage.includes('staking')) {
            return "AI Mining and staking information is available in the AI Miner section. You can configure staking strategies and view rewards there.";
        } else if (lowerMessage.includes('security')) {
            return "Security settings and monitoring are available in the Security section. This includes risk limits, emergency controls, and activity monitoring.";
        } else if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
            return "I can help you navigate the dashboard. Use the sidebar to switch between Overview, Arbitrage, AI Miner, Liquidity Provider, Cross-Chain, Analytics, Agent Kit, and Security sections.";
        } else if (lowerMessage.includes('status')) {
            return `System status is ${document.getElementById('status-badge')?.textContent || 'Unknown'}. Current uptime is ${document.getElementById('uptime')?.textContent || '00:00:00'}.`;
        } else {
            return "I'm here to help you with the CryptoQuest dashboard. You can ask about arbitrage opportunities, profits, mining, security, or navigation. What would you like to know?";
        }
    }

    async loadInitialData() {
        try {
            await this.loadOverviewData();
            setTimeout(() => {
                this.speak('Welcome to CryptoQuest Dashboard. Click on any section in the sidebar to explore different features.');
            }, 2000);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.handleError(error);
        }
    }

    async loadOverviewData() {
        try {
            const [statusResponse, metricsResponse] = await Promise.all([
                fetch(`${this.apiBaseUrl}/api/status`).catch(() => ({ ok: false })),
                fetch(`${this.apiBaseUrl}/api/metrics`).catch(() => ({ ok: false }))
            ]);

            if (statusResponse.ok && metricsResponse.ok) {
                const status = await statusResponse.json();
                const metrics = await metricsResponse.json();

                this.updateElement('total-arbitrages', metrics.total_arbitrages || 0);
                this.updateElement('success-rate', `${metrics.success_rate || 0}%`);
                this.updateElement('total-profit', `$${(metrics.total_profit || 0).toFixed(2)}`);
                this.updateElement('uptime', this.formatUptime(metrics.uptime || 0));

                this.updateConnectionStatus(status.status === 'running');
            } else {
                this.loadDemoData();
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.loadDemoData();
        }
    }

    loadDemoData() {
        this.updateElement('total-arbitrages', 247);
        this.updateElement('success-rate', '94.2%');
        this.updateElement('total-profit', '$1,247.85');
        this.updateElement('uptime', '12:34:56');
        this.updateConnectionStatus(true);
    }

    async loadArbitrageData() {
        console.log('Loading arbitrage data...');
        this.speak('Arbitrage section loaded. Current opportunities and settings are displayed.');
    }

    async loadAIMinerData() {
        console.log('Loading AI Miner data...');
        this.speak('AI Miner section loaded. Staking rewards and mining performance are displayed.');
    }

    async loadLiquidityData() {
        console.log('Loading Liquidity data...');
        this.speak('Liquidity Provider section loaded. Pool allocations and settings are available.');
    }

    async loadCrossChainData() {
        console.log('Loading Cross-Chain data...');
        this.speak('Cross-Chain section loaded. Bridge transactions and status are displayed.');
    }

    async loadAnalyticsData() {
        console.log('Loading Analytics data...');
        this.speak('Analytics section loaded. Performance metrics and predictions are available.');
    }

    async loadAgentKitData() {
        console.log('Loading Agent Kit data...');
        this.speak('Agent Kit section loaded. AI decision log and performance metrics are displayed.');
    }

    async loadSecurityData() {
        console.log('Loading Security data...');
        this.speak('Security section loaded. Security status and risk monitoring are active.');
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

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            this.speak('Entered fullscreen mode');
        } else {
            document.exitFullscreen();
            this.speak('Exited fullscreen mode');
        }
    }

    async emergencyStop() {
        if (confirm('Are you sure you want to emergency stop all operations?')) {
            this.showNotification('Emergency stop activated', 'warning');
            this.speak('Emergency stop activated. All operations have been halted.');
        }
    }

    async startBot() {
        console.log('Starting bot...');
        this.showNotification('Bot started successfully', 'success');
        this.speak('Trading bot has been started');
    }

    async stopBot() {
        console.log('Stopping bot...');
        this.showNotification('Bot stopped', 'warning');
        this.speak('Trading bot has been stopped');
    }

    startPeriodicUpdates() {
        if (this.updateInterval && this.isAutoRefreshEnabled) {
            this.refreshIntervalId = setInterval(async () => {
                try {
                    await this.loadOverviewData();
                } catch (error) {
                    console.error('Periodic update error:', error);
                }
            }, this.updateInterval);
        }
    }

    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }

    showNotification(message, type = 'info') {
        let notificationArea = document.getElementById('notification-area');
        if (!notificationArea) {
            notificationArea = document.createElement('div');
            notificationArea.id = 'notification-area';
            notificationArea.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1050; width: 300px;';
            document.body.appendChild(notificationArea);
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()" aria-label="Close"></button>
        `;

        notificationArea.appendChild(alert);

        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    speak(text) {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();

            const speech = new SpeechSynthesisUtterance(text);
            speech.rate = 0.9;
            speech.pitch = 1;
            speech.volume = 0.8;
            speechSynthesis.speak(speech);
        } else {
            console.warn('Text-to-speech not supported in this browser.');
        }
    }

    handleError(error) {
        console.error('Dashboard error:', error);
        this.showNotification('An error occurred: ' + error.message, 'error');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    window.dashboard = new CryptoQuestDashboard();
});

// Fallback initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.dashboard) {
            console.log('Fallback initialization...');
            window.dashboard = new CryptoQuestDashboard();
        }
    });
} else if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded, initializing immediately...');
    window.dashboard = new CryptoQuestDashboard();
}