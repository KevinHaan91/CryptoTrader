from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingAPI:
    def __init__(self, bot):
        self.bot = bot
        self.app = FastAPI()
        self.websocket_clients = []
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:80"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/portfolio")
        async def get_portfolio():
            """Get portfolio statistics"""
            try:
                balances = await self.bot.exchange_manager.get_balance()
                risk_metrics = self.bot.risk_manager.get_risk_metrics()
                
                total_balance = sum(balances.values())
                
                return {
                    "totalBalance": total_balance,
                    "balanceChange24h": risk_metrics.get('daily_pnl_pct', 0),
                    "pnl24h": risk_metrics.get('daily_pnl', 0),
                    "pnlPercent24h": risk_metrics.get('daily_pnl_pct', 0),
                    "winRate": risk_metrics.get('win_rate', 0) * 100
                }
            except Exception as e:
                logger.error(f"Portfolio API error: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/positions")
        async def get_positions():
            """Get active positions"""
            try:
                positions = self.bot.performance_tracker.get_active_positions()
                
                # Format positions for frontend
                formatted_positions = []
                for pos in positions:
                    current_price = await self.bot.market_data.get_latest_price(pos['symbol'])
                    
                    if current_price:
                        pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
                        
                        formatted_positions.append({
                            "id": pos['id'],
                            "symbol": pos['symbol'],
                            "side": "BUY",  # Adjust based on strategy
                            "entryPrice": pos['entry_price'],
                            "currentPrice": current_price,
                            "pnl": pnl_pct * 100,
                            "size": pos['amount'],
                            "exchange": pos.get('exchange', 'Unknown')
                        })
                
                return formatted_positions
            except Exception as e:
                logger.error(f"Positions API error: {e}")
                return []
        
        @self.app.get("/api/wallets")
        async def get_wallets():
            """Get wallet balances"""
            try:
                wallets = {}
                
                for exchange in self.bot.exchange_manager.exchanges:
                    balance = await self.bot.exchange_manager.get_balance(exchange)
                    wallets[exchange] = balance
                
                return wallets
            except Exception as e:
                logger.error(f"Wallets API error: {e}")
                return {}
        
        @self.app.get("/api/strategy-performance")
        async def get_strategy_performance():
            """Get strategy performance metrics"""
            try:
                performance = self.bot.performance_tracker.get_strategy_performance()
                return performance
            except Exception as e:
                logger.error(f"Strategy performance API error: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/trade-history")
        async def get_trade_history(limit: int = 100):
            """Get recent trade history"""
            try:
                trades = self.bot.performance_tracker.get_trade_history(limit=limit)
                return trades
            except Exception as e:
                logger.error(f"Trade history API error: {e}")
                return []
        
        @self.app.get("/api/predictions")
        async def get_predictions():
            """Get AI predictions"""
            try:
                predictions = []
                
                # Get new listing predictions if available
                if 'new_listing_detection' in self.bot.strategies:
                    strategy = self.bot.strategies['new_listing_detection']
                    
                    # Get presale opportunities
                    if hasattr(strategy, 'presale_monitor'):
                        presales = strategy.presale_monitor.get_active_opportunities()
                        for presale in presales[:5]:  # Top 5
                            predictions.append({
                                "symbol": presale['symbol'],
                                "prediction": "PRESALE",
                                "confidence": presale['score'],
                                "timeframe": f"{presale.get('time_until_start_hours', 0):.1f}h until start",
                                "potentialReturn": presale['score'] * 100  # Estimate
                            })
                    
                    # Get pending exchange listings
                    if hasattr(strategy, 'exchange_monitor'):
                        pending = strategy.exchange_monitor.get_pending_listings()
                        for listing in pending[:5]:
                            predictions.append({
                                "symbol": listing['symbol'],
                                "prediction": f"LISTING on {listing['exchange']}",
                                "confidence": 0.8,
                                "timeframe": f"{listing.get('hours_until_listing', 0):.1f}h",
                                "potentialReturn": 30  # Conservative estimate
                            })
                
                return predictions
            except Exception as e:
                logger.error(f"Predictions API error: {e}")
                return []
        
        @self.app.get("/api/pump-alerts")
        async def get_pump_alerts():
            """Get recent pump alerts"""
            try:
                alerts = []
                
                # Get alerts from pump detection strategy
                if 'pump_detection' in self.bot.strategies:
                    strategy = self.bot.strategies['pump_detection']
                    if hasattr(strategy, 'get_recent_alerts'):
                        recent_alerts = strategy.get_recent_alerts()
                        
                        for alert in recent_alerts:
                            alerts.append({
                                "id": alert.get('id'),
                                "symbol": alert['symbol'],
                                "exchange": alert.get('exchange', 'Unknown'),
                                "priceChange": alert.get('price_change', 0),
                                "volumeIncrease": alert.get('volume_change', 0),
                                "confidence": alert.get('confidence', 0.5),
                                "timestamp": alert.get('timestamp', datetime.now()).isoformat(),
                                "action": alert.get('action', 'MONITOR')
                            })
                
                return alerts
            except Exception as e:
                logger.error(f"Pump alerts API error: {e}")
                return []
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.websocket_clients.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    await self._broadcast_updates()
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.websocket_clients.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_clients:
                    self.websocket_clients.remove(websocket)
    
    async def _broadcast_updates(self):
        """Broadcast updates to all WebSocket clients"""
        if not self.websocket_clients:
            return
        
        try:
            # Get latest data
            portfolio = await self.get_portfolio_data()
            performance = self.bot.performance_tracker.get_strategy_performance()
            
            # Prepare update message
            update = {
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "portfolio": portfolio,
                    "performance": performance.get('overall', {}),
                    "activeStrategies": len(self.bot.strategies)
                }
            }
            
            # Send to all clients
            disconnected = []
            for client in self.websocket_clients:
                try:
                    await client.send_json(update)
                except:
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.websocket_clients.remove(client)
                
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
    
    async def get_portfolio_data(self):
        """Get portfolio data for broadcasting"""
        try:
            balances = await self.bot.exchange_manager.get_balance()
            risk_metrics = self.bot.risk_manager.get_risk_metrics()
            
            return {
                "totalBalance": sum(balances.values()),
                "pnl24h": risk_metrics.get('daily_pnl', 0),
                "positions": risk_metrics.get('open_positions', 0)
            }
        except:
            return {}
    
    def start(self, host="0.0.0.0", port=8000):
        """Start API server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
