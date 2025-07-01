
// Type definitions for external libraries and APIs

declare interface SpeechSynthesisUtterance {
  text: string;
  lang: string;
  voice: SpeechSynthesisVoice | null;
  volume: number;
  rate: number;
  pitch: number;
}

declare interface SpeechSynthesis {
  speak(utterance: SpeechSynthesisUtterance): void;
  cancel(): void;
  pause(): void;
  resume(): void;
  getVoices(): SpeechSynthesisVoice[];
}

declare interface SpeechSynthesisVoice {
  voiceURI: string;
  name: string;
  lang: string;
  localService: boolean;
  default: boolean;
}

declare var speechSynthesis: SpeechSynthesis;

// Chart.js types
declare namespace Chart {
  interface ChartConfiguration {
    type: string;
    data: ChartData;
    options?: ChartOptions;
  }

  interface ChartData {
    labels?: string[];
    datasets: ChartDataset[];
  }

  interface ChartDataset {
    label?: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }

  interface ChartOptions {
    responsive?: boolean;
    maintainAspectRatio?: boolean;
    scales?: any;
    plugins?: any;
  }
}

declare class Chart {
  constructor(ctx: HTMLCanvasElement | CanvasRenderingContext2D, config: Chart.ChartConfiguration);
  destroy(): void;
  update(): void;
}

// API Response Types
interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}

interface ArbitrageOpportunityAPI {
  id: string;
  pair: string;
  source_exchange: string;
  target_exchange: string;
  price_difference: number;
  potential_profit: number;
  confidence_score: number;
  estimated_gas_cost: number;
  net_profit: number;
  status: 'active' | 'executing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

interface SystemStatusAPI {
  status: 'online' | 'offline' | 'error' | 'maintenance';
  uptime_seconds: number;
  active_connections: number;
  last_arbitrage: string;
  total_arbitrages_today: number;
  success_rate_24h: number;
  total_profit_24h: number;
}

interface StakingRewardAPI {
  network: string;
  token: string;
  staked_amount: number;
  current_apy: number;
  daily_rewards: number;
  total_rewards: number;
  status: 'active' | 'pending' | 'unstaking';
  validator_address?: string;
}

interface LiquidityPoolAPI {
  pool_address: string;
  token_a: string;
  token_b: string;
  network: string;
  liquidity_provided: number;
  fees_earned_24h: number;
  fees_earned_total: number;
  current_apy: number;
  impermanent_loss: number;
  status: 'active' | 'pending' | 'withdrawn';
}

interface CrossChainBridgeAPI {
  transaction_hash: string;
  from_network: string;
  to_network: string;
  token: string;
  amount: number;
  status: 'pending' | 'confirmed' | 'failed';
  gas_fee: number;
  bridge_fee: number;
  confirmation_time_seconds: number;
  created_at: string;
  confirmed_at?: string;
}

// WebSocket Message Types
interface WebSocketMessage {
  type: 'arbitrage_update' | 'system_status' | 'new_opportunity' | 'execution_complete';
  data: any;
  timestamp: string;
}

// Environment Variables
interface ProcessEnv {
  NODE_ENV: 'development' | 'production' | 'test';
  API_BASE_URL: string;
  WS_URL: string;
}
