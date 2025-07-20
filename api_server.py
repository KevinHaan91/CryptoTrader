from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime
import uvicorn
from contextlib import asynccontextmanager

# Import our trading bot modules
from src.core.exchange_manager import ExchangeManager
from src.core.market_data import MarketDataStream
from src.core.risk_manager import RiskManager
from src.strategies.high_frequency import ScalpingStrategy, ArbitrageStrategy, PumpDetector
from src.strategies.technical_trading import DayTradingStrategy, SwingTradingStrategy

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Global instances
exchange_manager = None
market_data = None
risk_manager = None
strategies = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global exchange_manager, market_data, risk_manager, strategies
    
    print("Starting up trading bot API...")
    
    # Initialize components
    exchange_manager = ExchangeManager()
    market_data = MarketDataStream(exchange_manager)
    risk_manager = RiskManager()
    
    # Initialize strategies
    strategies = {
        'scalping': ScalpingStrategy(exchange_manager, risk_manager),
        'arbitrage': ArbitrageStrategy(exchange_manager),
        'pump_detector': PumpDetector(),
        'day_trading': DayTradingStrategy(exchange_manager, risk_manager),
        'swing_trading': SwingTradingStrategy(exchange_manager, risk_manager)
    }
    
    # Start background tasks
    asyncio.create_task(portfolio_update_loop())
    asyncio.create_task(position_update_loop())
    asyncio.create_task(prediction_update_loop())
    
    yield
    
    # Shutdown
    print("Shutting down trading bot API...")
    if market_data:
        await market_data.stop()

app = FastAPI(lifespan=lifespan)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background tasks
async def portfolio_update_loop():
    """Send portfolio updates every 5 seconds"""
    while True:
        try:
            if exchange_manager and exchange_manager.initialized:
                portfolio_data = {
                    "totalBalance": exchange_manager.get_total_balance(),
                    "balanceChange24h": 2.34,  # Calculate from historical data
                    "pnl24h": 356.78,
                    "pnlPercent24h": 2.34,
                    "winRate": risk_manager.get_win_rate() if risk_manager else 68.5
                }
                await manager.broadcast({
                    "event": "portfolio:update",
                    "data": portfolio_data
                })
        except Exception as e:
            print(f"Error in portfolio update loop: {e}")
        await asyncio.sleep(5)

async def position_update_loop():
    """Send position updates every 2 seconds"""
    while True:
        try:
            if exchange_manager and exchange_manager.initialized:
                positions = exchange_manager.get_all_positions()
                await manager.broadcast({
                    "event": "positions:update",
                    "data": positions
                })
        except Exception as e:
            print(f"Error in position update loop: {e}")
        await asyncio.sleep(2)

async def prediction_update_loop():
    """Send AI predictions every 30 seconds"""
    while True:
        try:
            predictions = []
            for name, strategy in strategies.items():
                if hasattr(strategy, 'get_predictions'):
                    preds = strategy.get_predictions()
                    predictions.extend(preds)
            
            await manager.broadcast({
                "event": "predictions:update",
                "data": predictions
            })
        except Exception as e:
            print(f"Error in prediction update loop: {e}")
        await asyncio.sleep(30)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                # Handle subscription requests
                pass
            elif message.get("type") == "command":
                # Handle trading commands
                command = message.get("command")
                if command == "place_order":
                    # Place order logic
                    pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# REST API endpoints
@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    if not exchange_manager or not exchange_manager.initialized:
        return {"error": "Exchange manager not initialized"}
    
    return {
        "totalBalance": exchange_manager.get_total_balance(),
        "balanceChange24h": 2.34,
        "pnl24h": 356.78,
        "pnlPercent24h": 2.34,
        "winRate": risk_manager.get_win_rate() if risk_manager else 68.5
    }

@app.get("/api/positions")
async def get_positions():
    """Get all open positions"""
    if not exchange_manager or not exchange_manager.initialized:
        return []
    
    return exchange_manager.get_all_positions()

@app.get("/api/wallets")
async def get_wallets():
    """Get wallet balances across all exchanges"""
    if not exchange_manager or not exchange_manager.initialized:
        return {}
    
    wallets = {}
    for exchange_name in exchange_manager.exchanges:
        balances = exchange_manager.get_balance(exchange_name)
        wallets[exchange_name] = {
            "totalValue": sum(b['value'] for b in balances),
            "assets": balances,
            "address": "0x..." + exchange_name[:8]  # Mock address
        }
    
    return wallets

@app.post("/api/orders")
async def place_order(order: dict):
    """Place a new order"""
    try:
        exchange = order.get("exchange", "binance")
        symbol = order.get("symbol")
        side = order.get("side")
        order_type = order.get("type", "market")
        amount = order.get("amount")
        price = order.get("price")
        
        result = await exchange_manager.place_order(
            exchange=exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price
        )
        
        # Broadcast trade execution
        await manager.broadcast({
            "event": "trade:executed",
            "data": {
                "id": result.get("id"),
                "symbol": symbol,
                "side": side,
                "price": price or result.get("price"),
                "amount": amount,
                "profit": 0,  # Calculate actual P&L
                "time": datetime.now().isoformat()
            }
        })
        
        return {"success": True, "order": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/predictions")
async def get_predictions():
    """Get AI predictions"""
    predictions = []
    for name, strategy in strategies.items():
        if hasattr(strategy, 'get_predictions'):
            preds = strategy.get_predictions()
            predictions.extend(preds)
    
    return predictions

@app.get("/api/pump-alerts")
async def get_pump_alerts():
    """Get pump detection alerts"""
    if 'pump_detector' in strategies:
        return strategies['pump_detector'].get_recent_alerts()
    return []

@app.get("/api/settings")
async def get_settings():
    """Get current bot settings"""
    return {
        "paperTrading": True,  # Get from config
        "maxPositionSize": 5,
        "stopLossPercent": 2,
        "takeProfitPercent": 5,
        "enabledStrategies": list(strategies.keys()),
        "riskSettings": risk_manager.get_settings() if risk_manager else {}
    }

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update bot settings"""
    # Update configuration
    # This would update the actual bot settings
    return {"success": True, "settings": settings}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "exchange_manager": exchange_manager is not None,
            "market_data": market_data is not None,
            "risk_manager": risk_manager is not None,
            "strategies": len(strategies)
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
