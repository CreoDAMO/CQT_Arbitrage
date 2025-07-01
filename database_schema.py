"""
Database Schema for CryptoQuest Arbitrage Bot
PostgreSQL database schema with tables for storing trading data, opportunities, and metrics
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
import json

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Data class for arbitrage opportunities"""
    id: Optional[int] = None
    source_network: str = ""
    target_network: str = ""
    source_pool: str = ""
    target_pool: str = ""
    profit_potential: float = 0.0
    required_amount: float = 0.0
    execution_cost: float = 0.0
    net_profit: float = 0.0
    confidence: float = 0.0
    status: str = "pending"
    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

@dataclass
class ArbitrageExecution:
    """Data class for arbitrage executions"""
    id: Optional[int] = None
    opportunity_id: int = 0
    transaction_hash: str = ""
    gas_used: float = 0.0
    gas_price: float = 0.0
    actual_profit: float = 0.0
    execution_time: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class SystemMetrics:
    """Data class for system metrics"""
    id: Optional[int] = None
    total_arbitrages: int = 0
    successful_arbitrages: int = 0
    total_profit: float = 0.0
    total_gas_cost: float = 0.0
    uptime_seconds: int = 0
    last_updated: Optional[datetime] = None

@dataclass
class MiningReward:
    """Data class for mining rewards"""
    id: Optional[int] = None
    network: str = ""
    amount: float = 0.0
    reward_type: str = ""
    transaction_hash: str = ""
    created_at: Optional[datetime] = None

@dataclass
class LiquidityPosition:
    """Data class for liquidity positions"""
    id: Optional[int] = None
    pool_address: str = ""
    network: str = ""
    token0: str = ""
    token1: str = ""
    liquidity_amount: float = 0.0
    fees_earned: float = 0.0
    apy: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DatabaseManager:
    """Database manager for CryptoQuest Arbitrage Bot"""
    
    def __init__(self):
        self.connection = None
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not found")
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")
    
    def create_tables(self):
        """Create all required tables"""
        try:
            cursor = self.connection.cursor()
            
            # Create arbitrage_opportunities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                    id SERIAL PRIMARY KEY,
                    source_network VARCHAR(50) NOT NULL,
                    target_network VARCHAR(50) NOT NULL,
                    source_pool VARCHAR(100) NOT NULL,
                    target_pool VARCHAR(100) NOT NULL,
                    profit_potential DECIMAL(18, 8) NOT NULL,
                    required_amount DECIMAL(18, 8) NOT NULL,
                    execution_cost DECIMAL(18, 8) NOT NULL,
                    net_profit DECIMAL(18, 8) NOT NULL,
                    confidence DECIMAL(5, 4) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_opportunities_status 
                ON arbitrage_opportunities(status);
                CREATE INDEX IF NOT EXISTS idx_opportunities_created 
                ON arbitrage_opportunities(created_at);
            """)
            
            # Create arbitrage_executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arbitrage_executions (
                    id SERIAL PRIMARY KEY,
                    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id),
                    transaction_hash VARCHAR(100) UNIQUE,
                    gas_used DECIMAL(18, 8),
                    gas_price DECIMAL(18, 8),
                    actual_profit DECIMAL(18, 8),
                    execution_time DECIMAL(10, 4),
                    success BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_executions_success 
                ON arbitrage_executions(success);
                CREATE INDEX IF NOT EXISTS idx_executions_created 
                ON arbitrage_executions(created_at);
            """)
            
            # Create system_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    total_arbitrages INTEGER DEFAULT 0,
                    successful_arbitrages INTEGER DEFAULT 0,
                    total_profit DECIMAL(18, 8) DEFAULT 0,
                    total_gas_cost DECIMAL(18, 8) DEFAULT 0,
                    uptime_seconds INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    daily_metrics JSONB,
                    network_metrics JSONB
                );
            """)
            
            # Create mining_rewards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mining_rewards (
                    id SERIAL PRIMARY KEY,
                    network VARCHAR(50) NOT NULL,
                    amount DECIMAL(18, 8) NOT NULL,
                    reward_type VARCHAR(50) NOT NULL,
                    transaction_hash VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_rewards_network 
                ON mining_rewards(network);
                CREATE INDEX IF NOT EXISTS idx_rewards_created 
                ON mining_rewards(created_at);
            """)
            
            # Create liquidity_positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liquidity_positions (
                    id SERIAL PRIMARY KEY,
                    pool_address VARCHAR(100) NOT NULL,
                    network VARCHAR(50) NOT NULL,
                    token0 VARCHAR(100) NOT NULL,
                    token1 VARCHAR(100) NOT NULL,
                    liquidity_amount DECIMAL(18, 8) NOT NULL,
                    fees_earned DECIMAL(18, 8) DEFAULT 0,
                    apy DECIMAL(8, 4) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_liquidity_pool 
                ON liquidity_positions(pool_address);
                CREATE INDEX IF NOT EXISTS idx_liquidity_network 
                ON liquidity_positions(network);
            """)
            
            # Create price_history table for ML training
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(100) NOT NULL,
                    network VARCHAR(50) NOT NULL,
                    price_usd DECIMAL(18, 8) NOT NULL,
                    volume_24h DECIMAL(18, 8),
                    liquidity DECIMAL(18, 8),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) DEFAULT 'uniswap'
                );
                
                CREATE INDEX IF NOT EXISTS idx_price_history_token 
                ON price_history(token_address, network);
                CREATE INDEX IF NOT EXISTS idx_price_history_timestamp 
                ON price_history(timestamp);
            """)
            
            # Create agent_decisions table for AI tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    id SERIAL PRIMARY KEY,
                    decision_type VARCHAR(50) NOT NULL,
                    confidence DECIMAL(5, 4) NOT NULL,
                    reasoning TEXT,
                    parameters JSONB,
                    outcome VARCHAR(50),
                    actual_result JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_agent_decisions_type 
                ON agent_decisions(decision_type);
                CREATE INDEX IF NOT EXISTS idx_agent_decisions_created 
                ON agent_decisions(created_at);
            """)
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def insert_opportunity(self, opportunity: ArbitrageOpportunity) -> Optional[int]:
        """Insert new arbitrage opportunity"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO arbitrage_opportunities 
                (source_network, target_network, source_pool, target_pool, 
                 profit_potential, required_amount, execution_cost, net_profit, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                opportunity.source_network, opportunity.target_network,
                opportunity.source_pool, opportunity.target_pool,
                opportunity.profit_potential, opportunity.required_amount,
                opportunity.execution_cost, opportunity.net_profit, opportunity.confidence
            ))
            
            opportunity_id = cursor.fetchone()['id']
            self.connection.commit()
            logger.info(f"Inserted opportunity with ID: {opportunity_id}")
            return opportunity_id
            
        except Exception as e:
            logger.error(f"Failed to insert opportunity: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()
    
    def get_active_opportunities(self) -> List[Dict[str, Any]]:
        """Get all active arbitrage opportunities"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM arbitrage_opportunities 
                WHERE status = 'pending' 
                ORDER BY net_profit DESC, created_at DESC
                LIMIT 50;
            """)
            
            opportunities = cursor.fetchall()
            return [dict(opp) for opp in opportunities]
            
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            return []
        finally:
            cursor.close()
    
    def insert_execution(self, execution: ArbitrageExecution) -> Optional[int]:
        """Insert arbitrage execution record"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO arbitrage_executions 
                (opportunity_id, transaction_hash, gas_used, gas_price, 
                 actual_profit, execution_time, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                execution.opportunity_id, execution.transaction_hash,
                execution.gas_used, execution.gas_price, execution.actual_profit,
                execution.execution_time, execution.success, execution.error_message
            ))
            
            execution_id = cursor.fetchone()['id']
            
            # Update opportunity status
            cursor.execute("""
                UPDATE arbitrage_opportunities 
                SET status = %s, executed_at = CURRENT_TIMESTAMP 
                WHERE id = %s;
            """, ('executed' if execution.success else 'failed', execution.opportunity_id))
            
            self.connection.commit()
            logger.info(f"Inserted execution with ID: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to insert execution: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()
    
    def update_system_metrics(self, metrics: SystemMetrics) -> bool:
        """Update system metrics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO system_metrics 
                (total_arbitrages, successful_arbitrages, total_profit, 
                 total_gas_cost, uptime_seconds)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    total_arbitrages = EXCLUDED.total_arbitrages,
                    successful_arbitrages = EXCLUDED.successful_arbitrages,
                    total_profit = EXCLUDED.total_profit,
                    total_gas_cost = EXCLUDED.total_gas_cost,
                    uptime_seconds = EXCLUDED.uptime_seconds,
                    last_updated = CURRENT_TIMESTAMP;
            """, (
                metrics.total_arbitrages, metrics.successful_arbitrages,
                metrics.total_profit, metrics.total_gas_cost, metrics.uptime_seconds
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Get latest system metrics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM system_metrics 
                ORDER BY last_updated DESC 
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
        finally:
            cursor.close()
    
    def insert_price_data(self, token_address: str, network: str, 
                         price_usd: float, volume_24h: float = None, 
                         liquidity: float = None) -> bool:
        """Insert price history data for ML training"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO price_history 
                (token_address, network, price_usd, volume_24h, liquidity)
                VALUES (%s, %s, %s, %s, %s);
            """, (token_address, network, price_usd, volume_24h, liquidity))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert price data: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def get_price_history(self, token_address: str, network: str, 
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Get price history for ML training"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM price_history 
                WHERE token_address = %s AND network = %s 
                ORDER BY timestamp DESC 
                LIMIT %s;
            """, (token_address, network, limit))
            
            history = cursor.fetchall()
            return [dict(record) for record in history]
            
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []
        finally:
            cursor.close()
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data to maintain performance"""
        try:
            cursor = self.connection.cursor()
            
            # Clean old opportunities
            cursor.execute("""
                DELETE FROM arbitrage_opportunities 
                WHERE created_at < NOW() - INTERVAL '%s days' 
                AND status IN ('executed', 'failed', 'expired');
            """, (days,))
            
            # Clean old price history (keep more data for ML)
            cursor.execute("""
                DELETE FROM price_history 
                WHERE timestamp < NOW() - INTERVAL '%s days';
            """, (days * 3,))  # Keep 90 days of price data
            
            self.connection.commit()
            logger.info(f"Cleaned up data older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup data: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

# Initialize database manager
def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    db_manager = DatabaseManager()
    if db_manager.connect():
        db_manager.create_tables()
        return db_manager
    else:
        raise ConnectionError("Failed to connect to database")

# Test database connection
def test_database_connection():
    """Test database connection and setup"""
    try:
        db_manager = get_database_manager()
        logger.info("Database connection test successful")
        
        # Test inserting sample data
        sample_opportunity = ArbitrageOpportunity(
            source_network="polygon",
            target_network="base",
            source_pool="0x1234...",
            target_pool="0x5678...",
            profit_potential=0.02,
            required_amount=1000.0,
            execution_cost=15.50,
            net_profit=4.50,
            confidence=0.85
        )
        
        opp_id = db_manager.insert_opportunity(sample_opportunity)
        if opp_id:
            logger.info(f"Sample opportunity inserted with ID: {opp_id}")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_database_connection()