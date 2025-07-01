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

if __name__ == "__main__":
    print("Starting CryptoQuest Arbitrage Bot Web Server...")
    print("Database Available:", DATABASE_AVAILABLE)
    uvicorn.run(app, host="0.0.0.0", port=5000)