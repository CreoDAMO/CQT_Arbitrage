"""
CryptoQuest Arbitrage Pipeline
Real-time monitoring and arbitrage execution for CQT tokens across Polygon and Base networks
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

import redis
import requests
from web3 import Web3
from web3.contract import Contract
from eth_account import Account

try:
    from MLPredictor import LSTMPredictor
    ML_PREDICTOR_AVAILABLE = True
except ImportError:
    from SimplePredictor import SimplePredictor
    LSTMPredictor = SimplePredictor  # Use simple predictor as fallback
    ML_PREDICTOR_AVAILABLE = False
from CrossChainManager import CrossChainManager
from AgentKitIntegration import AgentKitClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PoolInfo:
    address: str
    network: str
    token0: str
    token1: str
    fee_tier: int
    liquidity: int
    price: float
    last_update: datetime

@dataclass
class ArbitrageOpportunity:
    source_pool: PoolInfo
    target_pool: PoolInfo
    profit_potential: float
    required_amount: float
    execution_cost: float
    net_profit: float
    confidence: float

class CryptoQuestPipeline:
    """Main pipeline for CQT arbitrage operations"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the arbitrage pipeline"""
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize network connections
        self.w3_polygon = Web3(Web3.HTTPProvider(
            os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        ))
        self.w3_base = Web3(Web3.HTTPProvider(
            os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        ))
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )
        
        # Initialize components
        self.ml_predictor = LSTMPredictor()
        self.cross_chain_manager = CrossChainManager(self.w3_polygon, self.w3_base)
        self.agent_client = AgentKitClient(
            api_key=os.getenv("CDP_API_KEY"),
            project_id=os.getenv("CDP_PROJECT_ID", "eb262ee5-9b74-4fa6-8891-0ae680cfea10")
        )
        
        # Load contract ABIs and addresses
        self._load_contracts()
        
        # Initialize account
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            self.account = Account.from_key(private_key)
            logger.info(f"Initialized with account: {self.account.address}")
        else:
            logger.error("PRIVATE_KEY not found in environment variables")
            raise ValueError("Private key required for operation")
        
        # Pool tracking
        self.pools = {}
        self.opportunities = []
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "total_arbitrages": 0,
            "successful_arbitrages": 0,
            "total_profit": 0.0,
            "gas_spent": 0.0,
            "uptime_start": datetime.now()
        }
    
    def _load_contracts(self):
        """Load smart contract instances"""
        
        # Contract addresses from config
        arbitrage_address = self.config.get("contracts", {}).get("arbitrage")
        
        # Load ABIs (simplified - in production, load from files)
        erc20_abi = [
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable", 
                "type": "function"
            }
        ]
        
        uniswap_v3_pool_abi = [
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"name": "sqrtPriceX96", "type": "uint160"},
                    {"name": "tick", "type": "int24"},
                    {"name": "observationIndex", "type": "uint16"},
                    {"name": "observationCardinality", "type": "uint16"},
                    {"name": "observationCardinalityNext", "type": "uint16"},
                    {"name": "feeProtocol", "type": "uint8"},
                    {"name": "unlocked", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "liquidity",
                "outputs": [{"name": "", "type": "uint128"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Initialize contract instances
        self.cqt_polygon = self.w3_polygon.eth.contract(
            address=Web3.toChecksumAddress("0x94ef57abfbff1ad70bd00a921e1d2437f31c1665"),
            abi=erc20_abi
        )
        
        self.cqt_base = self.w3_base.eth.contract(
            address=Web3.toChecksumAddress("0x9d1075b41cd80ab08179f36bc17a7ff8708748ba"),
            abi=erc20_abi
        )
        
        # Pool contracts
        self.pool_contracts = {}
        for pool_addr in self.config.get("pools", []):
            network = pool_addr.get("network")
            address = pool_addr.get("address")
            
            if network == "polygon":
                self.pool_contracts[address] = self.w3_polygon.eth.contract(
                    address=Web3.toChecksumAddress(address),
                    abi=uniswap_v3_pool_abi
                )
            elif network == "base":
                self.pool_contracts[address] = self.w3_base.eth.contract(
                    address=Web3.toChecksumAddress(address),
                    abi=uniswap_v3_pool_abi
                )
    
    async def fetch_pool_data(self) -> Dict[str, PoolInfo]:
        """Fetch current data from all monitored pools"""
        
        pool_data = {}
        
        for pool_config in self.config.get("pools", []):
            try:
                address = pool_config["address"]
                network = pool_config["network"]
                
                # Get contract instance
                contract = self.pool_contracts.get(address)
                if not contract:
                    continue
                
                # Fetch slot0 data
                slot0 = contract.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                
                # Fetch liquidity
                liquidity = contract.functions.liquidity().call()
                
                # Convert sqrtPriceX96 to readable price
                price = (sqrt_price_x96 ** 2) / (2 ** 192)
                
                # Create PoolInfo
                pool_info = PoolInfo(
                    address=address,
                    network=network,
                    token0=pool_config["token0"],
                    token1=pool_config["token1"],
                    fee_tier=pool_config.get("fee_tier", 3000),
                    liquidity=liquidity,
                    price=price,
                    last_update=datetime.now()
                )
                
                pool_data[address] = pool_info
                
                # Cache in Redis
                cache_key = f"pool:{address}:data"
                cache_data = {
                    "price": price,
                    "liquidity": liquidity,
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.setex(cache_key, 300, json.dumps(cache_data))  # 5 min TTL
                
                logger.debug(f"Updated {network} pool {address}: price={price:.6f}, liquidity={liquidity}")
                
            except Exception as e:
                logger.error(f"Failed to fetch data for pool {address}: {e}")
                continue
        
        return pool_data
    
    def identify_arbitrage_opportunities(self, pool_data: Dict[str, PoolInfo]) -> List[ArbitrageOpportunity]:
        """Identify profitable arbitrage opportunities between pools"""
        
        opportunities = []
        pools_list = list(pool_data.values())
        
        # Compare all pool pairs
        for i in range(len(pools_list)):
            for j in range(i + 1, len(pools_list)):
                pool1 = pools_list[i]
                pool2 = pools_list[j]
                
                # Skip if same network and both CQT pools
                if (pool1.network == pool2.network and 
                    pool1.token0 == "CQT" and pool2.token0 == "CQT"):
                    continue
                
                # Calculate price difference
                price_diff = abs(pool1.price - pool2.price)
                avg_price = (pool1.price + pool2.price) / 2
                price_diff_pct = (price_diff / avg_price) * 100
                
                # Check if profitable (considering fees and gas)
                min_profit_threshold = self.config.get("min_profit_threshold", 0.5)  # 0.5%
                
                if price_diff_pct > min_profit_threshold:
                    # Estimate execution cost
                    gas_cost = self._estimate_arbitrage_cost(pool1, pool2)
                    
                    # Calculate optimal arbitrage amount
                    optimal_amount = self._calculate_optimal_amount(pool1, pool2)
                    
                    # Calculate expected profit
                    gross_profit = optimal_amount * (price_diff / avg_price)
                    net_profit = gross_profit - gas_cost
                    
                    if net_profit > 0:
                        # Get ML confidence score
                        confidence = self.ml_predictor.predict_arbitrage_success(
                            pool1, pool2, optimal_amount
                        )
                        
                        opportunity = ArbitrageOpportunity(
                            source_pool=pool1 if pool1.price > pool2.price else pool2,
                            target_pool=pool2 if pool1.price > pool2.price else pool1,
                            profit_potential=price_diff_pct,
                            required_amount=optimal_amount,
                            execution_cost=gas_cost,
                            net_profit=net_profit,
                            confidence=confidence
                        )
                        
                        opportunities.append(opportunity)
                        
                        logger.info(f"Found opportunity: {opportunity.source_pool.network} -> "
                                  f"{opportunity.target_pool.network}, "
                                  f"profit: {net_profit:.4f} ETH ({price_diff_pct:.2f}%)")
        
        # Sort by net profit descending
        opportunities.sort(key=lambda x: x.net_profit, reverse=True)
        
        return opportunities
    
    def _estimate_arbitrage_cost(self, pool1: PoolInfo, pool2: PoolInfo) -> float:
        """Estimate gas cost for arbitrage execution"""
        
        base_gas = 150000  # Base gas for simple arbitrage
        cross_chain_gas = 300000  # Additional gas for cross-chain
        
        # Estimate gas price
        if pool1.network == "polygon":
            gas_price = self.w3_polygon.eth.gas_price
        else:
            gas_price = self.w3_base.eth.gas_price
        
        # Add cross-chain cost if different networks
        total_gas = base_gas
        if pool1.network != pool2.network:
            total_gas += cross_chain_gas
        
        # Convert to ETH
        cost_wei = total_gas * gas_price
        cost_eth = self.w3_polygon.fromWei(cost_wei, 'ether')
        
        return float(cost_eth)
    
    def _calculate_optimal_amount(self, pool1: PoolInfo, pool2: PoolInfo) -> float:
        """Calculate optimal arbitrage amount based on liquidity and slippage"""
        
        # Simple heuristic: use 1% of smaller pool's liquidity
        min_liquidity = min(pool1.liquidity, pool2.liquidity)
        optimal_amount = min_liquidity * 0.01  # 1% of liquidity
        
        # Cap at maximum position size
        max_position = self.config.get("max_position_size", 1000000)  # 1M CQT
        optimal_amount = min(optimal_amount, max_position)
        
        return optimal_amount
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute an arbitrage opportunity"""
        
        try:
            logger.info(f"Executing arbitrage: {opportunity.source_pool.network} -> "
                       f"{opportunity.target_pool.network}")
            
            # Check if cross-chain arbitrage
            if opportunity.source_pool.network != opportunity.target_pool.network:
                success = await self.cross_chain_manager.execute_cross_chain_arbitrage(
                    opportunity
                )
            else:
                success = await self._execute_single_chain_arbitrage(opportunity)
            
            if success:
                self.metrics["successful_arbitrages"] += 1
                self.metrics["total_profit"] += opportunity.net_profit
                
                # Use Agent Kit for follow-up actions
                await self.agent_client.report_arbitrage_success(opportunity)
                
                logger.info(f"Arbitrage executed successfully. Profit: {opportunity.net_profit:.4f} ETH")
            else:
                logger.warning("Arbitrage execution failed")
            
            self.metrics["total_arbitrages"] += 1
            return success
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return False
    
    async def _execute_single_chain_arbitrage(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute arbitrage on single chain"""
        
        # This would implement the actual trading logic
        # For now, we'll simulate the execution
        logger.info("Executing single-chain arbitrage...")
        
        # In production, this would:
        # 1. Build transaction data
        # 2. Sign transaction
        # 3. Submit to network
        # 4. Wait for confirmation
        # 5. Verify success
        
        return True
    
    def update_ml_model(self, pool_data: Dict[str, PoolInfo]):
        """Update ML model with new data"""
        
        try:
            # Prepare training data from recent pool data
            training_data = []
            for pool in pool_data.values():
                # Get historical data from Redis
                history_key = f"pool:{pool.address}:history"
                history = self.redis_client.lrange(history_key, 0, -1)
                
                if len(history) > 10:  # Need sufficient data
                    data_points = [json.loads(h) for h in history]
                    training_data.extend(data_points)
            
            if training_data:
                self.ml_predictor.update_model(training_data)
                logger.info("ML model updated with new data")
            
        except Exception as e:
            logger.error(f"Error updating ML model: {e}")
    
    def store_historical_data(self, pool_data: Dict[str, PoolInfo]):
        """Store pool data for historical analysis"""
        
        for pool in pool_data.values():
            history_key = f"pool:{pool.address}:history"
            
            data_point = {
                "timestamp": pool.last_update.isoformat(),
                "price": pool.price,
                "liquidity": pool.liquidity,
                "network": pool.network
            }
            
            # Add to Redis list (keep last 1000 points)
            self.redis_client.lpush(history_key, json.dumps(data_point))
            self.redis_client.ltrim(history_key, 0, 999)
    
    async def run_monitoring_cycle(self):
        """Single monitoring and arbitrage cycle"""
        
        try:
            # Fetch current pool data
            pool_data = await self.fetch_pool_data()
            self.pools = pool_data
            
            # Store historical data
            self.store_historical_data(pool_data)
            
            # Identify arbitrage opportunities
            opportunities = self.identify_arbitrage_opportunities(pool_data)
            self.opportunities = opportunities
            
            # Execute profitable opportunities
            for opportunity in opportunities[:3]:  # Execute top 3 opportunities
                if opportunity.confidence > 0.7:  # High confidence threshold
                    await self.execute_arbitrage(opportunity)
                    
                    # Wait between executions to avoid rate limits
                    await asyncio.sleep(5)
            
            # Update ML model periodically
            if self.metrics["total_arbitrages"] % 10 == 0:
                self.update_ml_model(pool_data)
            
            # Store metrics
            self._update_metrics()
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    def _update_metrics(self):
        """Update and store performance metrics"""
        
        self.metrics["uptime"] = str(datetime.now() - self.metrics["uptime_start"])
        
        # Store in Redis for web dashboard
        metrics_key = "arbitrage:metrics"
        self.redis_client.setex(metrics_key, 3600, json.dumps(self.metrics, default=str))
        
        # Store current opportunities
        opportunities_key = "arbitrage:opportunities"
        opportunities_data = [
            {
                "source": f"{opp.source_pool.network}:{opp.source_pool.address}",
                "target": f"{opp.target_pool.network}:{opp.target_pool.address}",
                "profit": opp.net_profit,
                "confidence": opp.confidence
            }
            for opp in self.opportunities
        ]
        self.redis_client.setex(opportunities_key, 300, json.dumps(opportunities_data))
    
    async def start(self):
        """Start the arbitrage pipeline"""
        
        logger.info("Starting CryptoQuest Arbitrage Pipeline...")
        self.running = True
        
        # Check network connections
        if not self.w3_polygon.isConnected():
            logger.error("Failed to connect to Polygon network")
            return
        
        if not self.w3_base.isConnected():
            logger.error("Failed to connect to Base network")
            return
        
        logger.info("Network connections established")
        
        # Check account balances
        polygon_balance = self.w3_polygon.eth.get_balance(self.account.address)
        base_balance = self.w3_base.eth.get_balance(self.account.address)
        
        logger.info(f"Polygon balance: {self.w3_polygon.fromWei(polygon_balance, 'ether')} MATIC")
        logger.info(f"Base balance: {self.w3_base.fromWei(base_balance, 'ether')} ETH")
        
        # Main monitoring loop
        cycle_interval = self.config.get("monitoring_interval", 30)  # 30 seconds
        
        while self.running:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(cycle_interval)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                await asyncio.sleep(cycle_interval)
        
        logger.info("Pipeline stopped")
    
    def stop(self):
        """Stop the arbitrage pipeline"""
        self.running = False
    
    def get_status(self) -> Dict:
        """Get current pipeline status"""
        
        return {
            "running": self.running,
            "pools_monitored": len(self.pools),
            "opportunities_found": len(self.opportunities),
            "metrics": self.metrics,
            "last_update": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Create and run pipeline
    pipeline = CryptoQuestPipeline()
    
    try:
        asyncio.run(pipeline.start())
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
