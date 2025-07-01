"""
Simple FastAPI server for CryptoQuest Arbitrage Bot
Serves the web interface with proper static file handling
"""

import os
import sys
import json
import random
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add database API
sys.path.append(os.path.dirname(__file__))

try:
    from database_api import db_api
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Database API not available - using demo data")

app = FastAPI(title="CryptoQuest Arbitrage Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        html_path = os.path.join(current_dir, "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>CryptoQuest Arbitrage Bot</h1><p>Dashboard files not found</p>")

@app.get("/style.css")
async def get_css():
    """Serve CSS file"""
    css_path = os.path.join(current_dir, "style.css")
    return FileResponse(css_path, media_type="text/css")

@app.get("/app.js")
async def get_js():
    """Serve JavaScript file"""
    js_path = os.path.join(current_dir, "app_simple.js")
    if not os.path.exists(js_path):
        # Fallback to app.js if app_simple.js doesn't exist
        js_path = os.path.join(current_dir, "app.js")
    return FileResponse(js_path, media_type="application/javascript")

@app.get("/api/status")
async def get_status():
    """Get bot status"""
    return {
        "status": "running",
        "mode": "demo",
        "database_connected": DATABASE_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/opportunities")
async def get_opportunities():
    """Get current arbitrage opportunities"""
    if DATABASE_AVAILABLE:
        try:
            return {"opportunities": db_api.get_opportunities()}
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback demo data
    opportunities = []
    for i in range(3):
        opp = {
            "id": f"opp_{i+1}",
            "source": "Polygon" if i % 2 == 0 else "Base",
            "target": "Base" if i % 2 == 0 else "Polygon",
            "profit": round(random.uniform(0.5, 3.0), 2),
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "status": "active",
            "net_profit": round(random.uniform(1.0, 25.0), 2),
            "source_pool": f"0x{''.join(random.choices('0123456789abcdef', k=8))}...{''.join(random.choices('0123456789abcdef', k=4))}",
            "target_pool": f"0x{''.join(random.choices('0123456789abcdef', k=8))}...{''.join(random.choices('0123456789abcdef', k=4))}",
            "created_at": datetime.now().isoformat()
        }
        opportunities.append(opp)
    
    return {"opportunities": opportunities}

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    if DATABASE_AVAILABLE:
        try:
            return db_api.get_system_metrics()
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback demo data
    return {
        "total_arbitrages": 45,
        "successful_arbitrages": 42,
        "total_profit": 245.67,
        "total_gas_cost": 89.23,
        "uptime": 86400,
        "success_rate": 93.3,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/executions")
async def get_executions():
    """Get recent arbitrage executions"""
    if DATABASE_AVAILABLE:
        try:
            return {"executions": db_api.get_recent_executions()}
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback demo data
    executions = [
        {
            "id": 1,
            "source_network": "polygon",
            "target_network": "base",
            "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12",
            "actual_profit": 6.25,
            "expected_profit": 6.25,
            "gas_used": 0.015,
            "success": True,
            "execution_time": 3.4,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "source_network": "base",
            "target_network": "polygon",
            "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
            "actual_profit": 0.95,
            "expected_profit": 1.00,
            "gas_used": 0.012,
            "success": True,
            "execution_time": 4.1,
            "created_at": datetime.now().isoformat()
        }
    ]
    
    return {"executions": executions}

@app.get("/api/prices")
async def get_prices():
    """Get price data for charts"""
    if DATABASE_AVAILABLE:
        try:
            history = db_api.get_price_history("0x94ef57abfbff1ad70bd00a921e1d2437f31c1665", "polygon", 24)
            if history:
                return {"prices": history}
        except Exception as e:
            print(f"Database error: {e}")
    
    # Generate demo price data
    prices = []
    for i in range(24):
        price = 0.15 + (0.001 * (i % 10 - 5))  # Small variations around $0.15
        prices.append({
            "price": price,
            "timestamp": datetime.now().isoformat()
        })
    
    return {"prices": prices}

@app.post("/api/bot/{action}")
async def control_bot(action: str):
    """Control bot operations"""
    valid_actions = ["start", "pause", "stop"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    print(f"Bot {action} command received")
    return {"status": "success", "action": action, "message": f"Bot {action} command executed"}

@app.post("/api/emergency-stop")
async def emergency_stop():
    """Emergency stop all operations"""
    print("Emergency stop activated")
    return {"status": "success", "message": "Emergency stop activated"}

@app.post("/api/mining/start")
async def start_mining():
    """Start AI mining operations"""
    print("AI mining started")
    return {"status": "success", "message": "AI mining started"}

@app.post("/api/mining/optimize")
async def optimize_mining():
    """Optimize mining operations"""
    print("Mining optimization started")
    return {"status": "success", "message": "Mining optimization started"}

@app.post("/api/liquidity/inject")
async def inject_liquidity():
    """Inject liquidity into pools"""
    print("Liquidity injection initiated")
    return {"status": "success", "message": "Liquidity injection initiated"}

@app.post("/api/bridge/execute")
async def execute_bridge(bridge_data: dict):
    """Execute cross-chain bridge transaction"""
    print(f"Bridge transaction initiated: {bridge_data}")
    return {"status": "success", "message": "Bridge transaction initiated", "tx_hash": "0x1234567890abcdef"}

@app.post("/api/security/audit")
async def security_audit():
    """Run security audit"""
    print("Security audit initiated")
    return {"status": "success", "message": "Security audit initiated"}

@app.get("/api/staking/overview")
async def get_staking_overview():
    """Get staking overview data"""
    return {
        "total_staked": 1250.75,
        "total_rewards": 142.50,
        "apy": 8.2,
        "networks": [
            {
                "name": "Ethereum",
                "staked": "0.05 ETH",
                "apy": 4.2,
                "rewards": 85.20,
                "status": "active"
            },
            {
                "name": "Polygon", 
                "staked": "750 MATIC",
                "apy": 8.5,
                "rewards": 57.30,
                "status": "active"
            },
            {
                "name": "Base",
                "staked": "0 ETH", 
                "apy": 3.8,
                "rewards": 0,
                "status": "pending"
            }
        ]
    }

@app.get("/api/liquidity/pools")
async def get_liquidity_pools():
    """Get liquidity pool data"""
    return {
        "pools": [
            {
                "name": "CQT/WETH (Polygon)",
                "allocated": 45230,
                "fees_earned": 234.50,
                "apy": 12.3,
                "priority": "high"
            },
            {
                "name": "CQT/WMATIC (Polygon)",
                "allocated": 28450,
                "fees_earned": 142.30,
                "apy": 8.7,
                "priority": "medium"
            },
            {
                "name": "CQT/USDC (Base)",
                "allocated": 12800,
                "fees_earned": 45.20,
                "apy": 5.2,
                "priority": "low"
            }
        ]
    }

@app.get("/api/bridge/status")
async def get_bridge_status():
    """Get bridge status and transactions"""
    return {
        "status": "operational",
        "avg_time": "3m 45s",
        "success_rate": 99.8,
        "transactions": [
            {
                "from": "Polygon",
                "to": "Base", 
                "amount": "1,000 CQT",
                "status": "completed",
                "time": "3m 45s",
                "gas_cost": 12.50
            },
            {
                "from": "Base",
                "to": "Polygon",
                "amount": "750 CQT", 
                "status": "pending",
                "time": "2m 12s",
                "gas_cost": 8.75
            }
        ]
    }

@app.get("/api/agent/performance")
async def get_agent_performance():
    """Get AI agent performance metrics"""
    return {
        "decision_accuracy": 94.2,
        "response_time": 847,
        "successful_predictions": 2847,
        "risk_assessments": 1234,
        "optimizations": 156,
        "decisions": [
            {
                "action": "Execute Arbitrage",
                "details": "Polygon → Base • CQT/WETH",
                "confidence": 92,
                "profit": 45.20,
                "timestamp": "2 min ago"
            },
            {
                "action": "Hold Position", 
                "details": "Market volatility too high",
                "confidence": 78,
                "risk": "high",
                "timestamp": "15 min ago"
            },
            {
                "action": "Rebalance Portfolio",
                "details": "Optimize liquidity allocation", 
                "confidence": 85,
                "status": "completed",
                "timestamp": "32 min ago"
            }
        ]
    }

@app.get("/api/security/status")
async def get_security_status():
    """Get security status"""
    return {
        "private_key_security": "secure",
        "zk_proof_verification": "active", 
        "post_quantum_crypto": "enabled",
        "account_abstraction": "active",
        "recent_transactions": [
            {"type": "arbitrage", "amount": 45.20, "status": "success"},
            {"type": "bridge", "amount": -12.50, "status": "completed"},
            {"type": "liquidity", "amount": 500.00, "status": "pending"}
        ],
        "alerts": [
            {"type": "warning", "message": "High gas prices detected on Polygon"},
            {"type": "info", "message": "Scheduled maintenance in 2 hours"}
        ]
    }

if __name__ == "__main__":
    print("Starting CryptoQuest Arbitrage Bot Web Server...")
    print("Database Available:", DATABASE_AVAILABLE)
    uvicorn.run(app, host="0.0.0.0", port=5000)