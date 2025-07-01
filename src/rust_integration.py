
"""
Python-Rust FFI Integration for CryptoQuest Arbitrage Bot
Provides secure interface to Rust-based arbitrage calculations
"""

import ctypes
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class RustArbitrageOpportunity:
    source_pool: Dict
    target_pool: Dict
    profit_potential: float
    required_amount: float
    execution_cost: float
    net_profit: float
    confidence: float
    timestamp: int

class RustArbitrageCore:
    """Python wrapper for Rust arbitrage core functionality"""
    
    def __init__(self, polygon_rpc: str, base_rpc: str):
        """Initialize Rust arbitrage core"""
        
        # Load the Rust shared library
        lib_path = self._find_rust_library()
        if not lib_path:
            raise RuntimeError("Rust arbitrage library not found. Please compile with 'cargo build --release'")
        
        self.lib = ctypes.CDLL(lib_path)
        
        # Define function signatures
        self._define_function_signatures()
        
        # Initialize the core
        polygon_rpc_c = ctypes.c_char_p(polygon_rpc.encode('utf-8'))
        base_rpc_c = ctypes.c_char_p(base_rpc.encode('utf-8'))
        
        self.core = self.lib.create_arbitrage_core(polygon_rpc_c, base_rpc_c)
        if not self.core:
            raise RuntimeError("Failed to initialize Rust arbitrage core")
        
        logger.info("Rust arbitrage core initialized successfully")
    
    def _find_rust_library(self) -> Optional[str]:
        """Find the compiled Rust library"""
        
        possible_paths = [
            "target/release/libarbitrage_core.so",  # Linux
            "target/release/libarbitrage_core.dylib",  # macOS
            "target/release/arbitrage_core.dll",  # Windows
            "./libarbitrage_core.so",
            "./libarbitrage_core.dylib",
            "./arbitrage_core.dll"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _define_function_signatures(self):
        """Define C function signatures for FFI"""
        
        # create_arbitrage_core
        self.lib.create_arbitrage_core.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.create_arbitrage_core.restype = ctypes.c_void_p
        
        # validate_opportunity_ffi
        self.lib.validate_opportunity_ffi.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.validate_opportunity_ffi.restype = ctypes.c_bool
        
        # calculate_optimal_amount_ffi
        self.lib.calculate_optimal_amount_ffi.argtypes = [
            ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_double
        ]
        self.lib.calculate_optimal_amount_ffi.restype = ctypes.c_double
        
        # free_arbitrage_core
        self.lib.free_arbitrage_core.argtypes = [ctypes.c_void_p]
        self.lib.free_arbitrage_core.restype = None
    
    def validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate arbitrage opportunity using Rust security checks"""
        
        try:
            # Convert opportunity to JSON
            opportunity_json = json.dumps(opportunity).encode('utf-8')
            opportunity_c = ctypes.c_char_p(opportunity_json)
            
            # Call Rust function
            result = self.lib.validate_opportunity_ffi(self.core, opportunity_c)
            
            logger.debug(f"Opportunity validation result: {result}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return False
    
    def calculate_optimal_amount(self, source_liquidity: int, target_liquidity: int, price_diff: float) -> float:
        """Calculate optimal arbitrage amount using Rust algorithms"""
        
        try:
            result = self.lib.calculate_optimal_amount_ffi(
                self.core,
                ctypes.c_uint64(source_liquidity),
                ctypes.c_uint64(target_liquidity),
                ctypes.c_double(price_diff)
            )
            
            logger.debug(f"Optimal amount calculated: {result}")
            return float(result)
            
        except Exception as e:
            logger.error(f"Error calculating optimal amount: {e}")
            return 0.0
    
    def calculate_price_impact(self, amount: float, liquidity: float) -> float:
        """Calculate price impact for given trade size"""
        
        if liquidity <= 0:
            return 1.0  # 100% impact if no liquidity
        
        return amount / (liquidity + amount)
    
    def validate_security_constraints(self, opportunity: Dict, config: Dict) -> Tuple[bool, str]:
        """Validate opportunity against security constraints"""
        
        # Check minimum profit threshold
        min_profit = config.get('min_profit_threshold', 0.005)
        if opportunity.get('net_profit', 0) < min_profit:
            return False, f"Profit below threshold: {opportunity.get('net_profit', 0)} < {min_profit}"
        
        # Check maximum position size
        max_position = config.get('max_position_size', 1000000)
        if opportunity.get('required_amount', 0) > max_position:
            return False, f"Position too large: {opportunity.get('required_amount', 0)} > {max_position}"
        
        # Check confidence threshold
        min_confidence = config.get('min_confidence', 0.7)
        if opportunity.get('confidence', 0) < min_confidence:
            return False, f"Confidence too low: {opportunity.get('confidence', 0)} < {min_confidence}"
        
        # Check maximum slippage
        max_slippage = config.get('max_slippage', 0.02)
        required_amount = opportunity.get('required_amount', 0)
        source_liquidity = opportunity.get('source_pool', {}).get('liquidity', 0)
        
        if source_liquidity > 0:
            price_impact = self.calculate_price_impact(required_amount, float(source_liquidity))
            if price_impact > max_slippage:
                return False, f"Price impact too high: {price_impact:.4f} > {max_slippage}"
        
        return True, "All security constraints satisfied"
    
    def enhanced_opportunity_validation(self, opportunity: Dict, config: Dict) -> Dict:
        """Enhanced validation combining Rust and Python checks"""
        
        validation_result = {
            'is_valid': False,
            'rust_validation': False,
            'security_validation': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Rust-based validation
            rust_valid = self.validate_opportunity(opportunity)
            validation_result['rust_validation'] = rust_valid
            
            if not rust_valid:
                validation_result['errors'].append("Failed Rust security validation")
            
            # Python security constraints
            security_valid, security_message = self.validate_security_constraints(opportunity, config)
            validation_result['security_validation'] = security_valid
            
            if not security_valid:
                validation_result['errors'].append(security_message)
            
            # Overall validation
            validation_result['is_valid'] = rust_valid and security_valid
            
            # Add warnings for edge cases
            confidence = opportunity.get('confidence', 0)
            if confidence < 0.8:
                validation_result['warnings'].append(f"Low confidence: {confidence:.2f}")
            
            profit_margin = opportunity.get('net_profit', 0) / opportunity.get('execution_cost', 1)
            if profit_margin < 2.0:
                validation_result['warnings'].append(f"Low profit margin: {profit_margin:.2f}x")
            
        except Exception as e:
            logger.error(f"Error in enhanced validation: {e}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def optimize_arbitrage_parameters(self, pools: List[Dict], price_data: Dict) -> Dict:
        """Optimize arbitrage parameters using Rust calculations"""
        
        optimization_result = {
            'optimal_amounts': {},
            'risk_scores': {},
            'execution_order': [],
            'total_profit_potential': 0.0
        }
        
        try:
            for i, source_pool in enumerate(pools):
                for j, target_pool in enumerate(pools[i+1:], i+1):
                    pool_pair = f"{source_pool['address']}-{target_pool['address']}"
                    
                    # Calculate optimal amount using Rust
                    optimal_amount = self.calculate_optimal_amount(
                        source_pool.get('liquidity', 0),
                        target_pool.get('liquidity', 0),
                        abs(source_pool.get('price', 0) - target_pool.get('price', 0))
                    )
                    
                    optimization_result['optimal_amounts'][pool_pair] = optimal_amount
                    
                    # Calculate risk score
                    price_impact = self.calculate_price_impact(
                        optimal_amount, 
                        float(source_pool.get('liquidity', 1))
                    )
                    
                    risk_score = price_impact * 100  # Convert to percentage
                    optimization_result['risk_scores'][pool_pair] = risk_score
                    
                    # Add to execution order if viable
                    if optimal_amount > 1000 and risk_score < 2.0:  # Minimum 1000 CQT, max 2% impact
                        optimization_result['execution_order'].append({
                            'pair': pool_pair,
                            'amount': optimal_amount,
                            'risk': risk_score
                        })
            
            # Sort execution order by risk (lowest first)
            optimization_result['execution_order'].sort(key=lambda x: x['risk'])
            
            # Calculate total profit potential
            optimization_result['total_profit_potential'] = sum(
                item['amount'] * 0.01 for item in optimization_result['execution_order']  # Assume 1% profit
            )
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
        
        return optimization_result
    
    def __del__(self):
        """Cleanup Rust resources"""
        if hasattr(self, 'core') and hasattr(self, 'lib'):
            try:
                self.lib.free_arbitrage_core(self.core)
                logger.debug("Rust arbitrage core cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up Rust core: {e}")

# Utility functions for integration
def compile_rust_library() -> bool:
    """Compile the Rust library if needed"""
    
    try:
        import subprocess
        
        # Check if Cargo is available
        result = subprocess.run(['cargo', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Cargo not found. Please install Rust and Cargo.")
            return False
        
        # Compile the library
        logger.info("Compiling Rust arbitrage library...")
        result = subprocess.run(['cargo', 'build', '--release'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Rust library compiled successfully")
            return True
        else:
            logger.error(f"Rust compilation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error compiling Rust library: {e}")
        return False

def test_rust_integration() -> bool:
    """Test the Rust integration"""
    
    try:
        # Initialize core
        core = RustArbitrageCore(
            "https://polygon-rpc.com",
            "https://mainnet.base.org"
        )
        
        # Test opportunity validation
        test_opportunity = {
            "source_pool": {
                "address": "0xb1e0b26c31a2e8c3eeBd6d5ff0E386A9c073d24F",
                "network": "polygon",
                "price": 10.67,
                "liquidity": 1500000
            },
            "target_pool": {
                "address": "0xd874aeaef376229c8d41d392c9ce272bd41e57d6",
                "network": "base", 
                "price": 0.10,
                "liquidity": 800000
            },
            "profit_potential": 98.0,
            "required_amount": 10000,
            "execution_cost": 0.05,
            "net_profit": 9.8,
            "confidence": 0.95,
            "timestamp": 1640995200
        }
        
        # Test validation
        is_valid = core.validate_opportunity(test_opportunity)
        logger.info(f"Test opportunity validation: {is_valid}")
        
        # Test optimal amount calculation
        optimal_amount = core.calculate_optimal_amount(1500000, 800000, 10.57)
        logger.info(f"Test optimal amount: {optimal_amount}")
        
        return True
        
    except Exception as e:
        logger.error(f"Rust integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the integration
    if compile_rust_library():
        test_rust_integration()
