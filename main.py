#!/usr/bin/env python3
"""
CryptoQuest Arbitrage Trading Bot
Main entry point for the sophisticated cross-chain CQT arbitrage system

Features:
- Cross-chain arbitrage between Polygon and Base networks
- ZK-proof verification and post-quantum cryptography
- ML-based predictions using LSTM models
- ERC-4337 account abstraction with Paymaster integration
- Real-time monitoring and web dashboard
- Agent Kit integration for automated decision making
"""

import os
import sys
import json
import logging
import asyncio
import signal
import argparse
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from CryptoQuestPipeline import CryptoQuestPipeline
try:
    from MLPredictor import LSTMPredictor
except ImportError:
    from SimplePredictor import SimplePredictor as LSTMPredictor
from CrossChainManager import CrossChainManager
from AgentKitIntegration import AgentKitClient
from web.server import create_web_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CryptoQuestArbitrageBot:
    """Main arbitrage bot controller"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the arbitrage bot"""
        
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        self.pipeline = None
        self.web_server = None
        
        # Component initialization flags
        self.components_initialized = False
        self.shutdown_initiated = False
        
        logger.info("CryptoQuest Arbitrage Bot initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        
        return {
            "networks": {
                "polygon": {
                    "rpc_url": "https://polygon-rpc.com",
                    "chain_id": 137,
                    "cqt_address": "0x94ef57abfbff1ad70bd00a921e1d2437f31c1665"
                },
                "base": {
                    "rpc_url": "https://mainnet.base.org",
                    "chain_id": 8453,
                    "cqt_address": "0x9d1075b41cd80ab08179f36bc17a7ff8708748ba"
                }
            },
            "pools": [
                {
                    "address": "0xb1e0b26c31a2e8c3eeBd6d5ff0E386A9c073d24F",
                    "network": "polygon",
                    "token0": "CQT",
                    "token1": "WETH",
                    "fee_tier": 3000
                },
                {
                    "address": "0x0b3cd8a65c5C3C4D6b5a7e8b2f8d9E9c2B8A5D3F",
                    "network": "polygon",
                    "token0": "CQT",
                    "token1": "WMATIC",
                    "fee_tier": 3000
                }
            ],
            "arbitrage": {
                "min_profit_threshold": 0.005,  # 0.5%
                "max_position_size": 1000000,   # 1M CQT
                "monitoring_interval": 30,      # 30 seconds
                "risk_tolerance": 0.02,         # 2%
                "gas_limit_multiplier": 1.2     # 20% buffer
            },
            "ml": {
                "model_path": "models/lstm_model.h5",
                "retrain_interval": 3600,       # 1 hour
                "prediction_confidence_threshold": 0.7
            },
            "web": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "agent_kit": {
                "enabled": True,
                "project_id": "eb262ee5-9b74-4fa6-8891-0ae680cfea10"
            }
        }
    
    async def initialize_components(self):
        """Initialize all bot components"""
        
        if self.components_initialized:
            return
        
        try:
            logger.info("Initializing bot components...")
            
            # Initialize main pipeline
            self.pipeline = CryptoQuestPipeline(self.config_path)
            
            # Create web server
            self.web_server = create_web_server(self.pipeline, self.config["web"])
            
            # Verify environment variables
            self._verify_environment()
            
            # Test network connections
            await self._test_network_connections()
            
            # Initialize ML model
            await self._initialize_ml_model()
            
            self.components_initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _verify_environment(self):
        """Verify required environment variables"""
        
        required_vars = [
            "PRIVATE_KEY",
            "POLYGON_RPC_URL",
            "BASE_RPC_URL"
        ]
        
        optional_vars = [
            "CDP_API_KEY",
            "CDP_PROJECT_ID",
            "REDIS_HOST",
            "REDIS_PORT"
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            raise ValueError(f"Missing required environment variables: {missing_required}")
        
        if missing_optional:
            logger.warning(f"Missing optional environment variables: {missing_optional}")
            logger.warning("Some features may be limited")
        
        # Validate private key format
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key.startswith("0x") and len(private_key) != 66:
            logger.warning("Private key format may be incorrect")
        
        logger.info("Environment verification completed")
    
    async def _test_network_connections(self):
        """Test connections to blockchain networks"""
        
        try:
            # Test Polygon connection
            polygon_rpc = os.getenv("POLYGON_RPC_URL", self.config["networks"]["polygon"]["rpc_url"])
            from web3 import Web3
            
            w3_polygon = Web3(Web3.HTTPProvider(polygon_rpc))
            if not w3_polygon.isConnected():
                raise ConnectionError("Failed to connect to Polygon network")
            
            polygon_block = w3_polygon.eth.block_number
            logger.info(f"Polygon connection successful (block: {polygon_block})")
            
            # Test Base connection
            base_rpc = os.getenv("BASE_RPC_URL", self.config["networks"]["base"]["rpc_url"])
            w3_base = Web3(Web3.HTTPProvider(base_rpc))
            if not w3_base.isConnected():
                raise ConnectionError("Failed to connect to Base network")
            
            base_block = w3_base.eth.block_number
            logger.info(f"Base connection successful (block: {base_block})")
            
            # Test account balances
            account_address = self.pipeline.account.address
            
            polygon_balance = w3_polygon.eth.get_balance(account_address)
            base_balance = w3_base.eth.get_balance(account_address)
            
            logger.info(f"Account balances - Polygon: {w3_polygon.fromWei(polygon_balance, 'ether'):.4f} MATIC, "
                       f"Base: {w3_base.fromWei(base_balance, 'ether'):.4f} ETH")
            
            # Warn if balances are low
            min_balance_wei = w3_polygon.toWei(0.01, 'ether')  # 0.01 ETH minimum
            
            if polygon_balance < min_balance_wei:
                logger.warning("Low MATIC balance on Polygon - may not be sufficient for gas fees")
            
            if base_balance < min_balance_wei:
                logger.warning("Low ETH balance on Base - may not be sufficient for gas fees")
            
        except Exception as e:
            logger.error(f"Network connection test failed: {e}")
            raise
    
    async def _initialize_ml_model(self):
        """Initialize and load ML model"""
        
        try:
            model_path = self.config["ml"]["model_path"]
            
            # Create models directory if it doesn't exist
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Initialize predictor
            predictor = LSTMPredictor(model_path)
            
            if not predictor.is_trained:
                logger.warning("ML model not found or not trained")
                logger.info("Bot will use fallback prediction methods")
            else:
                logger.info("ML model loaded successfully")
                
                # Test prediction
                summary = predictor.get_model_summary()
                logger.info(f"Model summary: {summary}")
            
        except Exception as e:
            logger.error(f"ML model initialization failed: {e}")
            logger.warning("Continuing without ML predictions")
    
    async def start(self):
        """Start the arbitrage bot"""
        
        if self.running:
            logger.warning("Bot is already running")
            return
        
        try:
            logger.info("Starting CryptoQuest Arbitrage Bot...")
            
            # Initialize components if not already done
            await self.initialize_components()
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start web server
            if self.web_server:
                web_task = asyncio.create_task(self._start_web_server())
            
            # Start main pipeline
            pipeline_task = asyncio.create_task(self.pipeline.start())
            
            self.running = True
            logger.info("✅ CryptoQuest Arbitrage Bot started successfully!")
            logger.info(f"📊 Web dashboard available at http://{self.config['web']['host']}:{self.config['web']['port']}")
            logger.info("🤖 Monitoring for arbitrage opportunities...")
            
            # Wait for tasks to complete or be cancelled
            if self.web_server:
                await asyncio.gather(web_task, pipeline_task, return_exceptions=True)
            else:
                await pipeline_task
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the arbitrage bot"""
        
        if self.shutdown_initiated:
            return
        
        self.shutdown_initiated = True
        logger.info("Stopping CryptoQuest Arbitrage Bot...")
        
        try:
            # Stop pipeline
            if self.pipeline:
                self.pipeline.stop()
                logger.info("Pipeline stopped")
            
            # Stop web server
            if self.web_server:
                # Web server shutdown is handled by the framework
                logger.info("Web server stopping...")
            
            self.running = False
            logger.info("✅ CryptoQuest Arbitrage Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _start_web_server(self):
        """Start the web server"""
        
        try:
            import uvicorn
            
            config = uvicorn.Config(
                self.web_server,
                host=self.config["web"]["host"],
                port=self.config["web"]["port"],
                log_level="info" if not self.config["web"]["debug"] else "debug",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except ImportError:
            logger.error("uvicorn not installed. Please install with: pip install uvicorn")
            logger.info("Starting simple HTTP server instead...")
            await self._start_simple_server()
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    async def _start_simple_server(self):
        """Start a simple HTTP server as fallback"""
        
        import http.server
        import socketserver
        import threading
        
        try:
            handler = http.server.SimpleHTTPRequestHandler
            
            class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
                allow_reuse_address = True
            
            # Change to web directory
            web_dir = os.path.join(os.path.dirname(__file__), 'web')
            os.chdir(web_dir)
            
            with ThreadedTCPServer(("", self.config["web"]["port"]), handler) as httpd:
                logger.info(f"Simple HTTP server started on port {self.config['web']['port']}")
                
                # Run server in thread
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                
                # Keep alive
                while self.running and not self.shutdown_initiated:
                    await asyncio.sleep(1)
                
                httpd.shutdown()
                
        except Exception as e:
            logger.error(f"Failed to start simple server: {e}")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        
        status = {
            "running": self.running,
            "components_initialized": self.components_initialized,
            "config_loaded": bool(self.config),
            "pipeline_status": None,
            "uptime": None
        }
        
        if self.pipeline:
            status["pipeline_status"] = self.pipeline.get_status()
        
        return status

def create_argument_parser():
    """Create command line argument parser"""
    
    parser = argparse.ArgumentParser(
        description="CryptoQuest Arbitrage Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start with default config
  python main.py --config custom.json  # Use custom config file
  python main.py --test-only        # Test connections only
  python main.py --web-only         # Start web interface only
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Test connections and exit"
    )
    
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Start web interface only (no trading)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="CryptoQuest Arbitrage Bot v1.0.0"
    )
    
    return parser

async def main():
    """Main entry point"""
    
    # Print banner
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          🚀 CryptoQuest Arbitrage Trading Bot 🚀          ║
    ║                                                           ║
    ║  Cross-chain CQT arbitrage with ZK-proofs & ML           ║
    ║  Polygon ↔ Base • ERC-4337 • Agent Kit • LSTM            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create bot instance
    bot = CryptoQuestArbitrageBot(args.config)
    
    try:
        if args.test_only:
            logger.info("Running connection tests...")
            await bot.initialize_components()
            logger.info("✅ All tests passed!")
            return
        
        if args.web_only:
            logger.info("Starting web interface only...")
            bot.config["arbitrage"]["enabled"] = False
        
        # Start the bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Ensure clean shutdown
        await bot.stop()

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            sys.exit(1)
        
        # Check required packages
        try:
            import web3
            import redis
            import tensorflow
        except ImportError as e:
            print(f"❌ Missing required package: {e}")
            print("Please install requirements: pip install web3 redis tensorflow")
            sys.exit(1)
        
        # Run main
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
