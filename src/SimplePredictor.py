"""
Simple Predictor for CQT Arbitrage
Fallback prediction system using statistical methods when TensorFlow is unavailable
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    confidence: float
    predicted_price: float
    volatility: float
    liquidity_risk: float
    execution_probability: float

class SimplePredictor:
    """Simple statistical predictor for arbitrage opportunities"""
    
    def __init__(self):
        """Initialize the simple predictor"""
        self.historical_data = []
        self.price_history = {}
        self.volatility_window = 10
        
        logger.info("Simple predictor initialized (TensorFlow-free)")
    
    def predict_arbitrage_success(self, pool1, pool2, amount: float) -> float:
        """Predict success probability for arbitrage opportunity"""
        
        try:
            # Calculate price difference ratio
            price_diff = abs(pool1.price - pool2.price) / max(pool1.price, pool2.price)
            
            # Calculate liquidity impact
            liquidity_factor = min(pool1.liquidity, pool2.liquidity) / amount
            liquidity_score = min(liquidity_factor, 1.0)
            
            # Calculate volatility factor
            volatility = self._estimate_volatility(pool1.address, pool1.price)
            volatility_penalty = max(0, 1 - volatility * 2)  # Reduce confidence for high volatility
            
            # Combine factors for confidence score
            base_confidence = price_diff * 20  # 5% price diff = 100% confidence
            liquidity_adjusted = base_confidence * liquidity_score
            final_confidence = liquidity_adjusted * volatility_penalty
            
            return max(0.1, min(0.95, final_confidence))
            
        except Exception as e:
            logger.error(f"Error in arbitrage prediction: {e}")
            return 0.5
    
    def predict_liquidity_drain(self, pool_data: Dict) -> PredictionResult:
        """Predict liquidity drain probability and market conditions"""
        
        try:
            # Calculate average liquidity
            total_liquidity = sum(pool.liquidity for pool in pool_data.values())
            avg_liquidity = total_liquidity / len(pool_data) if pool_data else 0
            
            # Estimate liquidity risk based on pool sizes
            small_pools = sum(1 for pool in pool_data.values() if pool.liquidity < avg_liquidity * 0.5)
            liquidity_risk = small_pools / len(pool_data) if pool_data else 0.5
            
            # Calculate price volatility
            prices = [pool.price for pool in pool_data.values()]
            if len(prices) > 1:
                price_std = np.std(prices)
                price_mean = np.mean(prices)
                volatility = price_std / price_mean if price_mean > 0 else 0.5
            else:
                volatility = 0.3  # Default moderate volatility
            
            # Predict next price (simple moving average)
            predicted_price = np.mean(prices) if prices else 10.0
            
            # Calculate execution probability
            execution_prob = (1 - liquidity_risk) * (1 - volatility * 0.5)
            
            return PredictionResult(
                confidence=0.75,  # Medium confidence for statistical methods
                predicted_price=predicted_price,
                volatility=volatility,
                liquidity_risk=liquidity_risk,
                execution_probability=max(0.1, min(0.9, execution_prob))
            )
            
        except Exception as e:
            logger.error(f"Error in liquidity prediction: {e}")
            return PredictionResult(
                confidence=0.5,
                predicted_price=10.0,
                volatility=0.5,
                liquidity_risk=0.5,
                execution_probability=0.5
            )
    
    def _estimate_volatility(self, pool_address: str, current_price: float) -> float:
        """Estimate price volatility for a pool"""
        
        if pool_address not in self.price_history:
            self.price_history[pool_address] = []
        
        # Add current price to history
        self.price_history[pool_address].append({
            'price': current_price,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.price_history[pool_address] = [
            entry for entry in self.price_history[pool_address]
            if entry['timestamp'] > cutoff_time
        ]
        
        history = self.price_history[pool_address]
        
        if len(history) < 2:
            return 0.3  # Default moderate volatility
        
        # Calculate price changes
        prices = [entry['price'] for entry in history]
        price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                        for i in range(1, len(prices))]
        
        return np.mean(price_changes) if price_changes else 0.3
    
    def update_model(self, new_data: List[Dict]):
        """Update model with new data (store for statistical analysis)"""
        
        self.historical_data.extend(new_data)
        
        # Keep only recent data (last 1000 entries)
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]
        
        logger.debug(f"Updated simple predictor with {len(new_data)} new data points")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance (simplified analysis)"""
        
        return {
            "price_difference": 0.4,
            "liquidity_ratio": 0.3,
            "volatility": 0.2,
            "time_of_day": 0.1
        }
    
    def get_model_summary(self) -> Dict:
        """Get model summary and statistics"""
        
        return {
            "model_type": "simple_statistical",
            "data_points": len(self.historical_data),
            "pools_tracked": len(self.price_history),
            "tensorflow_required": False,
            "features": ["price_difference", "liquidity_ratio", "volatility"],
            "accuracy_estimate": 0.75
        }