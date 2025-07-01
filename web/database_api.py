"""
Database API for CryptoQuest Arbitrage Bot Web Interface
Provides database integration endpoints for the web dashboard
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add parent directory to path for database imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from database_schema import DatabaseManager, ArbitrageOpportunity, SystemMetrics
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class DatabaseAPI:
    """Database API wrapper for web interface"""
    
    def __init__(self):
        self.db_manager = None
        if DATABASE_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                if self.db_manager.connect():
                    self.db_manager.create_tables()
                    logger.info("Database API initialized successfully")
                else:
                    self.db_manager = None
            except Exception as e:
                logger.error(f"Failed to initialize database API: {e}")
                self.db_manager = None
    
    def get_opportunities(self) -> List[Dict[str, Any]]:
        """Get active arbitrage opportunities"""
        if not self.db_manager:
            # Return demo data if database not available
            return self._get_demo_opportunities()
        
        try:
            opportunities = self.db_manager.get_active_opportunities()
            # Convert to format expected by frontend
            formatted_opportunities = []
            for opp in opportunities:
                formatted_opportunities.append({
                    'id': str(opp['id']),
                    'source': opp['source_network'].title(),
                    'target': opp['target_network'].title(),
                    'source_pool': opp['source_pool'],
                    'target_pool': opp['target_pool'],
                    'profit': float(opp['profit_potential']),
                    'net_profit': float(opp['net_profit']),
                    'confidence': float(opp['confidence']),
                    'status': opp['status'],
                    'created_at': opp['created_at'].isoformat() if opp['created_at'] else None
                })
            return formatted_opportunities
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            return self._get_demo_opportunities()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        if not self.db_manager:
            return self._get_demo_metrics()
        
        try:
            metrics = self.db_manager.get_system_metrics()
            if metrics:
                return {
                    'total_arbitrages': metrics['total_arbitrages'],
                    'successful_arbitrages': metrics['successful_arbitrages'],
                    'total_profit': float(metrics['total_profit']),
                    'total_gas_cost': float(metrics['total_gas_cost']),
                    'uptime': metrics['uptime_seconds'],
                    'last_updated': metrics['last_updated'].isoformat() if metrics['last_updated'] else None
                }
            else:
                return self._get_demo_metrics()
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return self._get_demo_metrics()
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent arbitrage executions"""
        if not self.db_manager:
            return self._get_demo_executions()
        
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT ae.*, ao.source_network, ao.target_network, ao.net_profit as expected_profit
                FROM arbitrage_executions ae
                LEFT JOIN arbitrage_opportunities ao ON ae.opportunity_id = ao.id
                ORDER BY ae.created_at DESC
                LIMIT %s;
            """, (limit,))
            
            executions = cursor.fetchall()
            formatted_executions = []
            
            for exec_data in executions:
                formatted_executions.append({
                    'id': exec_data['id'],
                    'source_network': exec_data['source_network'],
                    'target_network': exec_data['target_network'],
                    'transaction_hash': exec_data['transaction_hash'],
                    'actual_profit': float(exec_data['actual_profit']) if exec_data['actual_profit'] else 0,
                    'expected_profit': float(exec_data['expected_profit']) if exec_data['expected_profit'] else 0,
                    'gas_used': float(exec_data['gas_used']) if exec_data['gas_used'] else 0,
                    'success': exec_data['success'],
                    'execution_time': float(exec_data['execution_time']) if exec_data['execution_time'] else 0,
                    'created_at': exec_data['created_at'].isoformat() if exec_data['created_at'] else None
                })
            
            cursor.close()
            return formatted_executions
            
        except Exception as e:
            logger.error(f"Failed to get executions: {e}")
            return self._get_demo_executions()
    
    def get_price_history(self, token_address: str, network: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get price history for charts"""
        if not self.db_manager:
            return self._get_demo_price_history(hours)
        
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT price_usd, timestamp
                FROM price_history
                WHERE token_address = %s AND network = %s 
                  AND timestamp > NOW() - INTERVAL '%s hours'
                ORDER BY timestamp ASC;
            """, (token_address, network, hours))
            
            history = cursor.fetchall()
            formatted_history = []
            
            for record in history:
                formatted_history.append({
                    'price': float(record['price_usd']),
                    'timestamp': record['timestamp'].isoformat()
                })
            
            cursor.close()
            return formatted_history
            
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return self._get_demo_price_history(hours)
    
    def add_sample_data(self):
        """Add sample data for demonstration"""
        if not self.db_manager:
            return False
        
        try:
            # Add sample opportunities
            sample_opportunities = [
                ArbitrageOpportunity(
                    source_network="polygon",
                    target_network="base",
                    source_pool="0x1234567890abcdef1234567890abcdef12345678",
                    target_pool="0xabcdef1234567890abcdef1234567890abcdef12",
                    profit_potential=0.025,
                    required_amount=1000.0,
                    execution_cost=18.75,
                    net_profit=6.25,
                    confidence=0.92
                ),
                ArbitrageOpportunity(
                    source_network="base",
                    target_network="polygon",
                    source_pool="0x9876543210fedcba9876543210fedcba98765432",
                    target_pool="0xfedcba9876543210fedcba9876543210fedcba98",
                    profit_potential=0.018,
                    required_amount=750.0,
                    execution_cost=12.50,
                    net_profit=1.00,
                    confidence=0.78
                )
            ]
            
            for opp in sample_opportunities:
                self.db_manager.insert_opportunity(opp)
            
            # Add sample metrics
            sample_metrics = SystemMetrics(
                total_arbitrages=45,
                successful_arbitrages=42,
                total_profit=245.67,
                total_gas_cost=89.23,
                uptime_seconds=86400  # 24 hours
            )
            
            self.db_manager.update_system_metrics(sample_metrics)
            
            logger.info("Sample data added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add sample data: {e}")
            return False
    
    def _get_demo_opportunities(self) -> List[Dict[str, Any]]:
        """Generate demo opportunities for display"""
        return [
            {
                'id': '1',
                'source': 'Polygon',
                'target': 'Base',
                'source_pool': '0x1234...5678',
                'target_pool': '0xabcd...ef12',
                'profit': 0.025,
                'net_profit': 6.25,
                'confidence': 0.92,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': '2',
                'source': 'Base',
                'target': 'Polygon',
                'source_pool': '0x9876...5432',
                'target_pool': '0xfedc...ba98',
                'profit': 0.018,
                'net_profit': 1.00,
                'confidence': 0.78,
                'status': 'pending',
                'created_at': (datetime.now() - timedelta(minutes=5)).isoformat()
            }
        ]
    
    def _get_demo_metrics(self) -> Dict[str, Any]:
        """Generate demo metrics"""
        return {
            'total_arbitrages': 45,
            'successful_arbitrages': 42,
            'total_profit': 245.67,
            'total_gas_cost': 89.23,
            'uptime': 86400,
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_demo_executions(self) -> List[Dict[str, Any]]:
        """Generate demo executions"""
        return [
            {
                'id': 1,
                'source_network': 'polygon',
                'target_network': 'base',
                'transaction_hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12',
                'actual_profit': 6.25,
                'expected_profit': 6.25,
                'gas_used': 0.015,
                'success': True,
                'execution_time': 3.4,
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                'id': 2,
                'source_network': 'base',
                'target_network': 'polygon',
                'transaction_hash': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab',
                'actual_profit': 0.95,
                'expected_profit': 1.00,
                'gas_used': 0.012,
                'success': True,
                'execution_time': 4.1,
                'created_at': (datetime.now() - timedelta(hours=4)).isoformat()
            }
        ]
    
    def _get_demo_price_history(self, hours: int) -> List[Dict[str, Any]]:
        """Generate demo price history"""
        history = []
        now = datetime.now()
        
        # Generate hourly price points
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i)
            # Simulate price movement around $0.15
            price = 0.15 + (0.001 * (i % 10 - 5))  # Small variations
            
            history.append({
                'price': price,
                'timestamp': timestamp.isoformat()
            })
        
        return history

# Global database API instance
db_api = DatabaseAPI()

# Initialize with sample data on startup
if DATABASE_AVAILABLE and db_api.db_manager:
    db_api.add_sample_data()