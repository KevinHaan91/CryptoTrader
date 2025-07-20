import ccxt
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from config.settings import EXCHANGES, TRADING
from .market_data import MarketDataManager
from ..execution.order_manager import OrderManager

logger = logging.getLogger(__name__)

class ExchangeManager:
    """Manages connections to multiple cryptocurrency exchanges with low-latency execution"""
    
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.websocket_connections = {}
        self.order_manager = OrderManager()
        self.market_data = MarketDataManager()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    async def initialize(self):
        """Initialize all configured exchanges"""
        for name, config in EXCHANGES.items():
            if config['api_key'] and config['api_secret']:
                try:
                    exchange_class = getattr(ccxt, name)
                    exchange = exchange_class({
                        'apiKey': config['api_key'],
                        'secret': config['api_secret'],
                        'enableRateLimit': True,
                        'rateLimit': config['rate_limit'],
                        'options': {
                            'defaultType': 'spot',
                            'adjustForTimeDifference': True,
                            'recvWindow': 60000
                        }
                    })
                    
                    if name == 'coinbase' and config.get('passphrase'):
                        exchange.password = config['passphrase']
                    
                    # Test connection
                    await exchange.load_markets()
                    self.exchanges[name] = exchange
                    logger.info(f"Successfully connected to {name}")
                    
                    # Initialize WebSocket for real-time data
                    await self._init_websocket(name, exchange)
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {name}: {e}")
    
    async def _init_websocket(self, exchange_name: str, exchange: ccxt.Exchange):
        """Initialize WebSocket connections for real-time data"""
        if hasattr(exchange, 'watch_order_book'):
            self.websocket_connections[exchange_name] = exchange
            logger.info(f"WebSocket enabled for {exchange_name}")
    
    async def get_balance(self, exchange_name: str = 'kraken') -> Dict[str, float]:
        """Get current balance from specified exchange"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"Exchange {exchange_name} not initialized")
            
            balance = await exchange.fetch_balance()
            return {
                currency: info['free'] 
                for currency, info in balance.items() 
                if info['free'] > 0
            }
        except Exception as e:
            logger.error(f"Error fetching balance from {exchange_name}: {e}")
            return {}
    
    async def transfer_funds(self, from_exchange: str, to_exchange: str, 
                           currency: str, amount: float) -> bool:
        """Transfer funds between exchanges for arbitrage"""
        try:
            # Get withdrawal address from destination exchange
            to_ex = self.exchanges[to_exchange]
            deposit_address = await to_ex.fetch_deposit_address(currency)
            
            # Withdraw from source exchange
            from_ex = self.exchanges[from_exchange]
            withdrawal = await from_ex.withdraw(
                currency, amount, deposit_address['address'],
                tag=deposit_address.get('tag'), 
                params={'network': deposit_address.get('network')}
            )
            
            logger.info(f"Transferred {amount} {currency} from {from_exchange} to {to_exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False
    
    async def execute_market_order(self, exchange_name: str, symbol: str, 
                                 side: str, amount: float) -> Optional[Dict]:
        """Execute market order with ultra-low latency"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Pre-calculate order parameters for speed
            if side == 'buy':
                # For buy orders, amount is in quote currency (USDT)
                ticker = await exchange.fetch_ticker(symbol)
                base_amount = amount / ticker['last']
            else:
                base_amount = amount
            
            # Execute order
            order = await exchange.create_market_order(
                symbol, side, base_amount
            )
            
            # Log execution time
            execution_time = datetime.now().timestamp() - order['timestamp'] / 1000
            logger.info(f"Order executed in {execution_time*1000:.2f}ms")
            
            return order
            
        except Exception as e:
            logger.error(f"Market order failed: {e}")
            return None
    
    async def execute_limit_order(self, exchange_name: str, symbol: str,
                                side: str, amount: float, price: float) -> Optional[Dict]:
        """Execute limit order"""
        try:
            exchange = self.exchanges[exchange_name]
            order = await exchange.create_limit_order(symbol, side, amount, price)
            return order
        except Exception as e:
            logger.error(f"Limit order failed: {e}")
            return None
    
    async def cancel_order(self, exchange_name: str, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            exchange = self.exchanges[exchange_name]
            await exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
    
    async def get_order_book(self, exchange_name: str, symbol: str, limit: int = 20) -> Dict:
        """Get order book with specified depth"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Use WebSocket if available for lower latency
            if exchange_name in self.websocket_connections:
                ws_exchange = self.websocket_connections[exchange_name]
                return await ws_exchange.watch_order_book(symbol, limit)
            else:
                return await exchange.fetch_order_book(symbol, limit)
                
        except Exception as e:
            logger.error(f"Failed to get order book: {e}")
            return {'bids': [], 'asks': []}
    
    async def get_recent_trades(self, exchange_name: str, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for a symbol"""
        try:
            exchange = self.exchanges[exchange_name]
            trades = await exchange.fetch_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return []
    
    async def calculate_fees(self, exchange_name: str, symbol: str, 
                           side: str, amount: float, price: float) -> float:
        """Calculate trading fees for an order"""
        try:
            exchange = self.exchanges[exchange_name]
            market = exchange.market(symbol)
            
            # Get fee structure
            if side == 'buy':
                fee_rate = market.get('taker', 0.001)  # Default 0.1%
            else:
                fee_rate = market.get('maker', 0.001)
            
            return amount * price * fee_rate
            
        except Exception as e:
            logger.error(f"Fee calculation failed: {e}")
            return amount * price * 0.001  # Default to 0.1%
    
    async def get_available_pairs(self, exchange_name: str) -> List[str]:
        """Get all available trading pairs on an exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            markets = exchange.markets
            return [
                symbol for symbol, market in markets.items()
                if market['active'] and market['type'] == 'spot'
            ]
        except Exception as e:
            logger.error(f"Failed to get pairs: {e}")
            return []
    
    def close(self):
        """Close all exchange connections"""
        for name, exchange in self.exchanges.items():
            if hasattr(exchange, 'close'):
                exchange.close()
        self.executor.shutdown(wait=True)
        logger.info("All exchange connections closed")
