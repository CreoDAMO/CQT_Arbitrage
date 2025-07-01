
// TypeScript Type Definitions for CryptoQuest Arbitrage Bot

export interface PoolInfo {
  address: string;
  network: 'polygon' | 'base';
  token0: string;
  token1: string;
  token0Address: string;
  token1Address: string;
  feeTier: number;
  price: number;
  liquidity: string;
  lastUpdate: Date;
}

export interface ArbitrageOpportunity {
  id: string;
  sourcePool: PoolInfo;
  targetPool: PoolInfo;
  profitPotential: number;
  requiredAmount: number;
  executionCost: number;
  netProfit: number;
  confidence: number;
  timestamp: Date;
  status: 'pending' | 'executing' | 'completed' | 'failed';
}

export interface BridgeTransaction {
  txHash: string;
  sourceNetwork: string;
  targetNetwork: string;
  amount: number;
  status: 'pending' | 'confirmed' | 'failed';
  timestamp: Date;
  gasUsed: number;
  confirmationTime?: number;
}

export interface SystemMetrics {
  totalArbitrages: number;
  successfulArbitrages: number;
  totalProfit: number;
  gasSpent: number;
  uptime: string;
  uptimeStart: Date;
  successRate: number;
}

export interface DashboardState {
  currentSection: string;
  isAutoRefreshEnabled: boolean;
  refreshInterval: number;
  opportunities: ArbitrageOpportunity[];
  metrics: SystemMetrics;
  pools: Record<string, PoolInfo>;
  isConnected: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: Date;
}

export interface WebSocketMessage {
  type: 'opportunity' | 'execution' | 'metrics' | 'status';
  data: any;
  timestamp: Date;
}

export interface SecurityConfig {
  maxSlippage: number;
  gasLimitMultiplier: number;
  maxGasPrice: string;
  minProfitThreshold: number;
  maxPositionSize: number;
  cooldownPeriod: number;
}

export interface CrossChainConfig {
  enabled: boolean;
  bridgeProvider: 'agglayer' | 'layerzero';
  bridgeContracts: Record<string, string>;
  estimatedBridgeTime: Record<string, number>;
  bridgeFees: Record<string, number>;
}

export interface MLPrediction {
  confidence: number;
  predictedPrice: number;
  timeHorizon: number;
  factors: Record<string, number>;
  timestamp: Date;
}

export interface AgentDecision {
  id: string;
  type: 'arbitrage' | 'liquidity' | 'risk_management';
  action: string;
  reasoning: string;
  confidence: number;
  executed: boolean;
  result?: string;
  timestamp: Date;
}

export interface LiquidityPosition {
  poolAddress: string;
  network: string;
  token0Amount: string;
  token1Amount: string;
  lpTokens: string;
  rewards: string;
  apy: number;
  lastUpdate: Date;
}

export interface StakingReward {
  amount: string;
  token: string;
  network: string;
  blockNumber: number;
  timestamp: Date;
  claimed: boolean;
}

// API Client Interface
export interface ApiClient {
  getStatus(): Promise<ApiResponse<{ status: string; timestamp: Date }>>;
  getMetrics(): Promise<ApiResponse<SystemMetrics>>;
  getOpportunities(): Promise<ApiResponse<ArbitrageOpportunity[]>>;
  getPools(): Promise<ApiResponse<Record<string, PoolInfo>>>;
  executeArbitrage(opportunityId: string): Promise<ApiResponse<{ txHash: string }>>;
  startBot(): Promise<ApiResponse<{ status: string }>>;
  stopBot(): Promise<ApiResponse<{ status: string }>>;
  emergencyStop(): Promise<ApiResponse<{ status: string }>>;
}

// Dashboard Component Props
export interface DashboardProps {
  apiBaseUrl: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableWebSocket?: boolean;
}

export interface SectionProps {
  data: any;
  isLoading: boolean;
  onRefresh: () => void;
  onAction?: (action: string, params?: any) => void;
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: Date;
  value: number;
  label?: string;
}

export interface PriceHistoryData {
  poolAddress: string;
  network: string;
  prices: ChartDataPoint[];
  volume: ChartDataPoint[];
  liquidity: ChartDataPoint[];
}

export interface ProfitChartData {
  daily: ChartDataPoint[];
  cumulative: ChartDataPoint[];
  breakdown: {
    arbitrage: number;
    liquidity: number;
    staking: number;
  };
}

// Error Types
export class ArbitrageError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ArbitrageError';
  }
}

export class NetworkError extends ArbitrageError {
  constructor(network: string, details?: any) {
    super(`Network error on ${network}`, 'NETWORK_ERROR', details);
  }
}

export class ValidationError extends ArbitrageError {
  constructor(field: string, value: any) {
    super(`Validation failed for ${field}: ${value}`, 'VALIDATION_ERROR', { field, value });
  }
}

// Utility Types
export type NetworkType = 'polygon' | 'base';
export type TransactionStatus = 'pending' | 'confirmed' | 'failed';
export type BotStatus = 'idle' | 'monitoring' | 'executing' | 'error';
export type SectionType = 'overview' | 'arbitrage' | 'ai-miner' | 'liquidity' | 'cross-chain' | 'analytics' | 'agent-kit' | 'security';

// Configuration Types
export interface AppConfig {
  apiBaseUrl: string;
  wsUrl: string;
  networks: Record<NetworkType, {
    rpcUrl: string;
    chainId: number;
    contracts: Record<string, string>;
  }>;
  security: SecurityConfig;
  crossChain: CrossChainConfig;
  ui: {
    refreshInterval: number;
    enableAnimations: boolean;
    theme: 'light' | 'dark' | 'auto';
  };
}
