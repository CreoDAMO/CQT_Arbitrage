
import { 
  PoolInfo, 
  ArbitrageOpportunity, 
  SystemMetrics, 
  DashboardState, 
  ApiClient, 
  ApiResponse,
  WebSocketMessage,
  SectionType,
  NetworkError,
  ValidationError,
  AppConfig 
} from '../src/types';
import DOMPurify from 'dompurify';

class CryptoQuestDashboard {
  private state: DashboardState;
  private apiClient: ApiClient;
  private websocket: WebSocket | null = null;
  private refreshIntervalId: number | null = null;
  private config: AppConfig;

  constructor(config: AppConfig) {
    this.config = config;
    this.state = {
      currentSection: 'overview',
      isAutoRefreshEnabled: true,
      refreshInterval: config.ui.refreshInterval || 5000,
      opportunities: [],
      metrics: {
        totalArbitrages: 0,
        successfulArbitrages: 0,
        totalProfit: 0,
        gasSpent: 0,
        uptime: '0h 0m',
        uptimeStart: new Date(),
        successRate: 0
      },
      pools: {},
      isConnected: false
    };

    this.apiClient = new ApiClientImpl(config.apiBaseUrl);
    this.init();
  }

  private async init(): Promise<void> {
    try {
      console.log('Initializing CryptoQuest Dashboard...');
      
      this.setupEventListeners();
      this.setupNavigation();
      this.setupWebSocket();
      
      await this.loadInitialData();
      this.startPeriodicUpdates();
      
      console.log('Dashboard initialized successfully');
      this.speak('Welcome to CryptoQuest Dashboard. System is online and monitoring opportunities.');
    } catch (error) {
      console.error('Dashboard initialization error:', error);
      this.handleError(error as Error);
    }
  }

  private setupNavigation(): void {
    const navLinks = document.querySelectorAll<HTMLElement>('.sidebar-nav .nav-link');
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        
        const targetSection = link.getAttribute('data-section') as SectionType;
        if (targetSection) {
          this.switchSection(targetSection);
        }
      });
    });
  }

  private async switchSection(sectionName: SectionType): Promise<void> {
    try {
      console.log(`Switching to section: ${sectionName}`);
      
      // Update navigation state
      document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
      });
      document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');
      
      // Hide all sections
      document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
      });
      
      // Show target section
      const targetSection = document.getElementById(`${sectionName}-section`);
      if (targetSection) {
        targetSection.classList.add('active');
        this.state.currentSection = sectionName;
        
        await this.loadSectionData(sectionName);
        this.speak(`Switched to ${sectionName.replace('-', ' ')} section`);
      } else {
        throw new ValidationError('section', sectionName);
      }
    } catch (error) {
      console.error('Error switching section:', error);
      this.handleError(error as Error);
    }
  }

  private async loadSectionData(sectionName: SectionType): Promise<void> {
    const loadingIndicator = this.showLoadingIndicator(sectionName);
    
    try {
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
        default:
          throw new ValidationError('sectionName', sectionName);
      }
    } catch (error) {
      console.error(`Error loading ${sectionName} data:`, error);
      this.handleError(error as Error);
    } finally {
      this.hideLoadingIndicator(loadingIndicator);
    }
  }

  private async loadOverviewData(): Promise<void> {
    try {
      const [statusResponse, metricsResponse] = await Promise.all([
        this.apiClient.getStatus(),
        this.apiClient.getMetrics()
      ]);

      if (statusResponse.success && metricsResponse.success) {
        this.state.metrics = metricsResponse.data!;
        this.state.isConnected = statusResponse.data!.status === 'running';
        
        this.updateOverviewUI();
      } else {
        throw new NetworkError('API');
      }
    } catch (error) {
      console.warn('Loading demo data due to API error:', error);
      this.loadDemoData();
    }
  }

  private async loadArbitrageData(): Promise<void> {
    try {
      const opportunitiesResponse = await this.apiClient.getOpportunities();
      
      if (opportunitiesResponse.success) {
        this.state.opportunities = opportunitiesResponse.data!;
        this.updateArbitrageUI();
      } else {
        throw new NetworkError('Arbitrage API');
      }
    } catch (error) {
      console.error('Error loading arbitrage data:', error);
      this.loadDemoArbitrageData();
    }
  }

  private async loadAIMinerData(): Promise<void> {
    // Implementation for AI Miner data loading
    console.log('Loading AI Miner data...');
  }

  private async loadLiquidityData(): Promise<void> {
    // Implementation for Liquidity data loading
    console.log('Loading Liquidity data...');
  }

  private async loadCrossChainData(): Promise<void> {
    // Implementation for Cross-Chain data loading
    console.log('Loading Cross-Chain data...');
  }

  private async loadAnalyticsData(): Promise<void> {
    // Implementation for Analytics data loading
    console.log('Loading Analytics data...');
  }

  private async loadAgentKitData(): Promise<void> {
    // Implementation for Agent Kit data loading
    console.log('Loading Agent Kit data...');
  }

  private async loadSecurityData(): Promise<void> {
    // Implementation for Security data loading
    console.log('Loading Security data...');
  }

  private loadDemoData(): void {
    this.state.metrics = {
      totalArbitrages: 247,
      successfulArbitrages: 233,
      totalProfit: 1247.85,
      gasSpent: 12.34,
      uptime: '12h 34m',
      uptimeStart: new Date(Date.now() - 45240000), // 12h 34m ago
      successRate: 94.2
    };
    this.state.isConnected = true;
    this.updateOverviewUI();
  }

  private loadDemoArbitrageData(): void {
    this.state.opportunities = [
      {
        id: 'demo-1',
        sourcePool: {
          address: '0xb1e0b26c31a2e8c3eeBd6d5ff0E386A9c073d24F',
          network: 'polygon',
          token0: 'CQT',
          token1: 'WETH',
          token0Address: '0x94ef57abfbff1ad70bd00a921e1d2437f31c1665',
          token1Address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
          feeTier: 3000,
          price: 10.67,
          liquidity: '1500000000000000000000000',
          lastUpdate: new Date()
        },
        targetPool: {
          address: '0xd874aeaef376229c8d41d392c9ce272bd41e57d6',
          network: 'base',
          token0: 'CQT',
          token1: 'USDC',
          token0Address: '0x9d1075b41cd80ab08179f36bc17a7ff8708748ba',
          token1Address: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
          feeTier: 3000,
          price: 0.10,
          liquidity: '800000000000000000000000',
          lastUpdate: new Date()
        },
        profitPotential: 9800.0, // Huge opportunity!
        requiredAmount: 10000,
        executionCost: 0.05,
        netProfit: 980.0,
        confidence: 0.95,
        timestamp: new Date(),
        status: 'pending'
      }
    ];
    this.updateArbitrageUI();
  }

  private updateOverviewUI(): void {
    this.updateElement('total-arbitrages', this.state.metrics.totalArbitrages.toString());
    this.updateElement('success-rate', `${this.state.metrics.successRate.toFixed(1)}%`);
    this.updateElement('total-profit', `$${this.state.metrics.totalProfit.toFixed(2)}`);
    this.updateElement('uptime', this.state.metrics.uptime);
    
    this.updateConnectionStatus(this.state.isConnected);
  }

  private updateArbitrageUI(): void {
    const container = document.getElementById('arbitrage-opportunities');
    if (!container) return;

    container.innerHTML = this.state.opportunities.map(opp => `
      <div class="opportunity-card" data-id="${opp.id}">
        <div class="opportunity-header">
          <span class="network-badge ${opp.sourcePool.network}">${opp.sourcePool.network.toUpperCase()}</span>
          <span class="arrow">→</span>
          <span class="network-badge ${opp.targetPool.network}">${opp.targetPool.network.toUpperCase()}</span>
          <span class="confidence-badge ${this.getConfidenceClass(opp.confidence)}">${(opp.confidence * 100).toFixed(0)}%</span>
        </div>
        <div class="opportunity-details">
          <div class="profit-info">
            <span class="profit-amount">$${opp.netProfit.toFixed(2)}</span>
            <span class="profit-percent">${opp.profitPotential.toFixed(2)}%</span>
          </div>
          <div class="execution-info">
            <small>Amount: ${opp.requiredAmount.toLocaleString()} CQT</small>
            <small>Cost: $${opp.executionCost.toFixed(4)}</small>
          </div>
        </div>
        <button class="execute-btn" onclick="dashboard.executeArbitrage('${opp.id}')">
          Execute
        </button>
      </div>
    `).join('');
  }

  private getConfidenceClass(confidence: number): string {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.6) return 'medium';
    return 'low';
  }

  private updateElement(id: string, value: string): void {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  private updateConnectionStatus(connected: boolean): void {
    const statusBadge = document.getElementById('status-badge');
    if (statusBadge) {
      statusBadge.className = `badge me-2 ${connected ? 'bg-success' : 'bg-danger'}`;
      statusBadge.innerHTML = `<i class="fas fa-circle ${connected ? 'pulse' : ''}"></i> ${connected ? 'Online' : 'Offline'}`;
    }
  }

  private setupEventListeners(): void {
    // Bot control buttons
    document.getElementById('start-bot')?.addEventListener('click', () => this.startBot());
    document.getElementById('pause-bot')?.addEventListener('click', () => this.stopBot());
    document.getElementById('emergency-stop')?.addEventListener('click', () => this.emergencyStop());
    
    // Auto-execute toggle
    document.getElementById('auto-execute-toggle')?.addEventListener('click', () => this.toggleAutoExecution());
    
    // Refresh buttons
    document.querySelectorAll('[id^="refresh-"]').forEach(btn => {
      btn.addEventListener('click', () => this.refreshCurrentSection());
    });
  }

  private setupWebSocket(): void {
    if (!this.config.wsUrl) return;

    try {
      this.websocket = new WebSocket(this.config.wsUrl);
      
      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.state.isConnected = true;
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        this.state.isConnected = false;
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.setupWebSocket(), 5000);
      };
      
      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
    }
  }

  private handleWebSocketMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'opportunity':
        this.state.opportunities = message.data;
        if (this.state.currentSection === 'arbitrage') {
          this.updateArbitrageUI();
        }
        break;
      case 'metrics':
        this.state.metrics = message.data;
        if (this.state.currentSection === 'overview') {
          this.updateOverviewUI();
        }
        break;
      case 'execution':
        this.showNotification(`Arbitrage executed: ${message.data.result}`, 'success');
        break;
      case 'status':
        this.state.isConnected = message.data.connected;
        this.updateConnectionStatus(this.state.isConnected);
        break;
    }
  }

  private startPeriodicUpdates(): void {
    if (this.state.isAutoRefreshEnabled && !this.refreshIntervalId) {
      this.refreshIntervalId = window.setInterval(async () => {
        try {
          await this.loadSectionData(this.state.currentSection as SectionType);
        } catch (error) {
          console.error('Periodic update error:', error);
        }
      }, this.state.refreshInterval);
    }
  }

  private showLoadingIndicator(section: string): HTMLElement {
    const indicator = document.createElement('div');
    indicator.className = 'loading-indicator';
    indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    const sectionElement = document.getElementById(`${section}-section`);
    if (sectionElement) {
      sectionElement.appendChild(indicator);
    }
    
    return indicator;
  }

  private hideLoadingIndicator(indicator: HTMLElement): void {
    indicator.remove();
  }

  private async refreshCurrentSection(): Promise<void> {
    await this.loadSectionData(this.state.currentSection as SectionType);
    this.showNotification('Data refreshed', 'info');
  }

  public async executeArbitrage(opportunityId: string): Promise<void> {
    try {
      const response = await this.apiClient.executeArbitrage(opportunityId);
      
      if (response.success) {
        this.showNotification(`Arbitrage execution started: ${response.data?.txHash}`, 'success');
      } else {
        throw new Error(response.error || 'Execution failed');
      }
    } catch (error) {
      console.error('Error executing arbitrage:', error);
      this.showNotification('Arbitrage execution failed', 'error');
    }
  }

  public async startBot(): Promise<void> {
    try {
      const response = await this.apiClient.startBot();
      if (response.success) {
        this.showNotification('Bot started successfully', 'success');
        this.speak('Trading bot has been started');
      }
    } catch (error) {
      this.handleError(error as Error);
    }
  }

  public async stopBot(): Promise<void> {
    try {
      const response = await this.apiClient.stopBot();
      if (response.success) {
        this.showNotification('Bot stopped', 'warning');
        this.speak('Trading bot has been stopped');
      }
    } catch (error) {
      this.handleError(error as Error);
    }
  }

  public async emergencyStop(): Promise<void> {
    if (confirm('Are you sure you want to emergency stop all operations?')) {
      try {
        const response = await this.apiClient.emergencyStop();
        if (response.success) {
          this.showNotification('Emergency stop activated', 'warning');
          this.speak('Emergency stop activated. All operations have been halted.');
        }
      } catch (error) {
        this.handleError(error as Error);
      }
    }
  }

  private toggleAutoExecution(): void {
    const btn = document.getElementById('auto-execute-toggle');
    if (btn) {
      const isOn = btn.textContent?.includes('OFF');
      btn.innerHTML = `<i class="fas fa-magic"></i> Auto Execute: ${isOn ? 'ON' : 'OFF'}`;
      btn.className = `btn btn-sm ${isOn ? 'btn-success' : 'btn-outline-secondary'}`;
      
      this.showNotification(`Auto execution ${isOn ? 'enabled' : 'disabled'}`, 'info');
      this.speak(`Auto execution ${isOn ? 'enabled' : 'disabled'}`);
    }
  }

  private showNotification(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info'): void {
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
      ${DOMPurify.sanitize(message)}
      <button type="button" class="btn-close" onclick="this.parentElement.remove()" aria-label="Close"></button>
    `;

    notificationArea.appendChild(alert);

    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 5000);
  }

  private speak(text: string): void {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
      
      const speech = new SpeechSynthesisUtterance(text);
      speech.rate = 0.9;
      speech.pitch = 1;
      speech.volume = 0.8;
      speechSynthesis.speak(speech);
    }
  }

  private handleError(error: Error): void {
    console.error('Dashboard error:', error);
    
    let message = 'An unexpected error occurred';
    if (error instanceof NetworkError) {
      message = `Network error: ${error.message}`;
    } else if (error instanceof ValidationError) {
      message = `Validation error: ${error.message}`;
    } else {
      message = error.message;
    }
    
    this.showNotification(message, 'error');
  }
}

// API Client Implementation
class ApiClientImpl implements ApiClient {
  constructor(private baseUrl: string) {}

  async getStatus(): Promise<ApiResponse<{ status: string; timestamp: Date }>> {
    return this.request('/api/status');
  }

  async getMetrics(): Promise<ApiResponse<SystemMetrics>> {
    return this.request('/api/metrics');
  }

  async getOpportunities(): Promise<ApiResponse<ArbitrageOpportunity[]>> {
    return this.request('/api/opportunities');
  }

  async getPools(): Promise<ApiResponse<Record<string, PoolInfo>>> {
    return this.request('/api/pools');
  }

  async executeArbitrage(opportunityId: string): Promise<ApiResponse<{ txHash: string }>> {
    return this.request(`/api/execute/${opportunityId}`, { method: 'POST' });
  }

  async startBot(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/api/bot/start', { method: 'POST' });
  }

  async stopBot(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/api/bot/stop', { method: 'POST' });
  }

  async emergencyStop(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/api/bot/emergency-stop', { method: 'POST' });
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new NetworkError(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      return {
        success: true,
        data,
        timestamp: new Date(),
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }
}

// Global dashboard instance
declare global {
  interface Window {
    dashboard: CryptoQuestDashboard;
  }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const config: AppConfig = {
    apiBaseUrl: window.location.origin,
    wsUrl: `ws://${window.location.host}/ws`,
    networks: {
      polygon: {
        rpcUrl: 'https://polygon-rpc.com',
        chainId: 137,
        contracts: {
          cqt: '0x94ef57abfbff1ad70bd00a921e1d2437f31c1665',
          arbitrage: '0x...',
        }
      },
      base: {
        rpcUrl: 'https://mainnet.base.org',
        chainId: 8453,
        contracts: {
          cqt: '0x9d1075b41cd80ab08179f36bc17a7ff8708748ba',
          arbitrage: '0x...',
        }
      }
    },
    security: {
      maxSlippage: 0.02,
      gasLimitMultiplier: 1.2,
      maxGasPrice: '100000000000', // 100 Gwei
      minProfitThreshold: 0.005,
      maxPositionSize: 1000000,
      cooldownPeriod: 60
    },
    crossChain: {
      enabled: true,
      bridgeProvider: 'agglayer',
      bridgeContracts: {},
      estimatedBridgeTime: {},
      bridgeFees: {}
    },
    ui: {
      refreshInterval: 5000,
      enableAnimations: true,
      theme: 'auto'
    }
  };

  window.dashboard = new CryptoQuestDashboard(config);
});

export { CryptoQuestDashboard };
