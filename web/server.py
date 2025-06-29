"""
FastAPI Web Server for CryptoQuest Arbitrage Bot
Provides REST API endpoints and WebSocket connections for real-time monitoring
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket client: {e}")
                disconnected_clients.append(connection)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.disconnect(client)

def create_web_server(pipeline, config: Dict) -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="CryptoQuest Arbitrage Bot",
        description="Real-time monitoring and control interface for cross-chain CQT arbitrage",
        version="1.0.0"
    )
    
    # Configure CORS
    if config.get("cors_enabled", True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory="web"), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Serve the main dashboard page"""
        try:
            with open("web/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(content="""
            <html>
                <head><title>CryptoQuest Arbitrage Bot</title></head>
                <body>
                    <h1>CryptoQuest Arbitrage Bot</h1>
                    <p>Dashboard is loading...</p>
                    <p>API Status: <a href="/api/status">/api/status</a></p>
                </body>
            </html>
            """)
    
    @app.get("/api/status")
    async def get_status():
        """Get current bot status"""
        try:
            if pipeline:
                status = pipeline.get_status()
            else:
                status = {
                    "status": "initializing",
                    "message": "Pipeline not ready",
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "success": True,
                "data": status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/opportunities")
    async def get_opportunities():
        """Get current arbitrage opportunities"""
        try:
            # Mock data for now - will be replaced with real data from pipeline
            opportunities = [
                {
                    "id": "poly_base_1",
                    "source": "Polygon",
                    "target": "Base", 
                    "profit": 0.025,
                    "confidence": 0.85,
                    "amount": 50000,
                    "status": "active"
                },
                {
                    "id": "base_poly_1",
                    "source": "Base",
                    "target": "Polygon",
                    "profit": 0.018,
                    "confidence": 0.72,
                    "amount": 75000,
                    "status": "active"
                }
            ]
            
            return {
                "success": True,
                "data": opportunities,
                "count": len(opportunities),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting opportunities: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/pools")
    async def get_pools():
        """Get current pool status"""
        try:
            # Mock data for now - will be replaced with real data from pipeline
            pools = [
                {
                    "id": "polygon_cqt_weth",
                    "network": "Polygon",
                    "token0": "CQT",
                    "token1": "WETH", 
                    "price": 10.67385,
                    "liquidity": 2500000,
                    "volume_24h": 150000,
                    "status": "active"
                },
                {
                    "id": "polygon_cqt_wmatic",
                    "network": "Polygon",
                    "token0": "CQT",
                    "token1": "WMATIC",
                    "price": 1.79273,
                    "liquidity": 1800000,
                    "volume_24h": 95000,
                    "status": "active"
                }
            ]
            
            return {
                "success": True,
                "data": pools,
                "count": len(pools),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting pools: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/transactions")
    async def get_transactions():
        """Get recent transactions"""
        try:
            # Mock data for now - will be replaced with real data from pipeline
            transactions = [
                {
                    "id": "tx_001",
                    "type": "arbitrage",
                    "network": "Polygon -> Base",
                    "amount": 50000,
                    "profit": 1250.50,
                    "status": "success",
                    "hash": "0x1234...abcd",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "tx_002", 
                    "type": "arbitrage",
                    "network": "Base -> Polygon",
                    "amount": 75000,
                    "profit": 1350.25,
                    "status": "success",
                    "hash": "0x5678...efgh",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            return {
                "success": True,
                "data": transactions,
                "count": len(transactions),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/predictions")
    async def get_predictions():
        """Get ML predictions"""
        try:
            # Mock data for now - will be replaced with real ML predictions
            predictions = {
                "liquidity_risk": 0.25,
                "volatility": 0.45,
                "price_trend": "bullish",
                "execution_probability": 0.78,
                "optimal_timing": 300,  # seconds
                "confidence": 0.82
            }
            
            return {
                "success": True,
                "data": predictions,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/bot/start")
    async def start_bot():
        """Start the arbitrage bot"""
        try:
            # This would trigger the actual bot start
            await websocket_manager.broadcast({
                "type": "bot_status",
                "payload": {"status": "starting", "message": "Bot is starting up..."}
            })
            
            return {
                "success": True,
                "message": "Bot start initiated",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/bot/stop")
    async def stop_bot():
        """Stop the arbitrage bot"""
        try:
            # This would trigger the actual bot stop
            await websocket_manager.broadcast({
                "type": "bot_status", 
                "payload": {"status": "stopping", "message": "Bot is shutting down..."}
            })
            
            return {
                "success": True,
                "message": "Bot stop initiated",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket_manager.connect(websocket)
        
        try:
            # Send initial connection message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "payload": {"status": "connected", "message": "WebSocket connected successfully"}
            }))
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client (e.g., subscription requests)
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    # Handle different message types
                    if data.get("type") == "subscribe":
                        # Client is subscribing to updates
                        await websocket.send_text(json.dumps({
                            "type": "subscription",
                            "payload": {"status": "subscribed", "channels": data.get("channels", [])}
                        }))
                    
                except asyncio.TimeoutError:
                    # Send ping message to keep connection alive
                    await websocket.send_text(json.dumps({"type": "ping"}))
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            websocket_manager.disconnect(websocket)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event"""
        logger.info("CryptoQuest Arbitrage Bot web server starting up...")
        
        # Start background task for periodic updates
        asyncio.create_task(periodic_updates(websocket_manager))
    
    @app.on_event("shutdown") 
    async def shutdown_event():
        """Application shutdown event"""
        logger.info("CryptoQuest Arbitrage Bot web server shutting down...")
    
    async def periodic_updates(ws_manager: WebSocketManager):
        """Send periodic updates to WebSocket clients"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Send price updates
                await ws_manager.broadcast({
                    "type": "price_update",
                    "payload": {
                        "polygon_price": 10.67385 + (asyncio.get_event_loop().time() % 10) * 0.001,
                        "base_price": 10.67890 + (asyncio.get_event_loop().time() % 10) * 0.001,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    return app

# For standalone testing
if __name__ == "__main__":
    app = create_web_server(None, {"host": "0.0.0.0", "port": 5000, "debug": True})
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")