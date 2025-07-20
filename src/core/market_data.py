import asyncio
import websockets
import json
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import redis.asyncio as redis

from config.settings import DATABASE, WEBSOCKET

logger = logging.getLogger(__name__)

class MarketDataManager:
    """High-performance market data collection and distribution"""
    
    def __init__(self):
        self.influx_client = None
        self.write_api = None
        self.redis_client = None
        self.websocket_handlers = {}
        self.data_subscribers: Dict[str, List[Callable]] = {}
        self.orderbook_cache = {}
        self.trade_cache = {}
        
    async def initialize(self):
        """Initialize database connections"""
        # InfluxDB for time series data
        self.influx_client = InfluxDBClient(
            url=DATABASE['influxdb']['url'],
            token=DATABASE['influxdb']['token'],
            org=DATABASE['influxdb']['org']
        )
        self.write_api = self.influx_client.write_api(write_options=ASYNCHRONOUS)
        
        # Redis for real-time caching
        self.redis_client = await redis.from_url(DATABASE['redis']['url'])
        
        logger.info("Market data manager initialized")
    
    async def connect_binance_stream(self, symbols: List[str]):
        """Connect to Binance WebSocket streams for ultra-low latency"""
        streams = []
        for symbol in symbols:
            symbol_lower = symbol.replace('/', '').lower()
            streams.extend([
                f"{symbol_lower}@trade",
                f"{symbol_lower}@depth20@100ms",
                f"{symbol_lower}@ticker"
            ])
        
        url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        async def handle_message():
            async with websockets.connect(url) as websocket:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await self._process_binance_message(data)
                    except Exception as e:
                        logger.error(f"Binance WebSocket error: {e}")
                        await asyncio.sleep(WEBSOCKET['reconnect_interval'])
                        break
        
        asyncio.create_task(handle_message())
    
    async def _process_binance_message(self, data: Dict):
        """Process incoming market data with minimal latency"""
        if 'stream' not in data:
            return
        
        stream_type = data['stream'].split('@')[-1]
        symbol = data['data']['s'] if 's' in data['data'] else None
        
        if not symbol:
            return
        
        # Convert to standard format
        symbol = self._normalize_symbol(symbol)
        
        if stream_type == 'trade':
            await self._process_trade(symbol, data['data'])
        elif stream_type.startswith('depth'):
            await self._process_orderbook(symbol, data['data'])
        elif stream_type == 'ticker':
            await self._process_ticker(symbol, data['data'])
    
    async def _process_trade(self, symbol: str, trade_data: Dict):
        """Process trade data"""
        trade = {
            'symbol': symbol,
            'price': float(trade_data['p']),
            'amount': float(trade_data['q']),
            'side': 'buy' if trade_data['m'] else 'sell',
            'timestamp': trade_data['T']
        }
        
        # Cache in Redis for immediate access
        await self.redis_client.lpush(f"trades:{symbol}", json.dumps(trade))
        await self.redis_client.ltrim(f"trades:{symbol}", 0, 999)  # Keep last 1000
        
        # Store in InfluxDB
        point = Point("trades") \
            .tag("symbol", symbol) \
            .tag("side", trade['side']) \
            .field("price", trade['price']) \
            .field("amount", trade['amount']) \
            .time(trade['timestamp'], write_precision='ms')
        
        self.write_api.write(DATABASE['influxdb']['bucket'], record=point)
        
        # Notify subscribers
        await self._notify_subscribers(f"trade:{symbol}", trade)
    
    async def _process_orderbook(self, symbol: str, orderbook_data: Dict):
        """Process order book updates"""
        orderbook = {
            'symbol': symbol,
            'bids': [(float(p), float(q)) for p, q in orderbook_data['bids']],
            'asks': [(float(p), float(q)) for p, q in orderbook_data['asks']],
            'timestamp': orderbook_data['T'] if 'T' in orderbook_data else datetime.now().timestamp() * 1000
        }
        
        # Update cache
        self.orderbook_cache[symbol] = orderbook
        await self.redis_client.set(f"orderbook:{symbol}", json.dumps(orderbook), ex=60)
        
        # Calculate metrics
        best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
        best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
        spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0
        
        # Store metrics
        point = Point("orderbook_metrics") \
            .tag("symbol", symbol) \
            .field("best_bid", best_bid) \
            .field("best_ask", best_ask) \
            .field("spread", spread) \
            .field("bid_depth", sum(q for _, q in orderbook['bids'][:10])) \
            .field("ask_depth", sum(q for _, q in orderbook['asks'][:10]))
        
        self.write_api.write(DATABASE['influxdb']['bucket'], record=point)
        
        # Notify subscribers
        await self._notify_subscribers(f"orderbook:{symbol}", orderbook)
    
    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to market data updates"""
        if channel not in self.data_subscribers:
            self.data_subscribers[channel] = []
        self.data_subscribers[channel].append(callback)
    
    async def _notify_subscribers(self, channel: str, data: Dict):
        """Notify all subscribers of new data"""
        if channel in self.data_subscribers:
            tasks = [callback(data) for callback in self.data_subscribers[channel]]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format across exchanges"""
        # Binance format: BTCUSDT -> BTC/USDT
        if '/' not in symbol:
            # Common patterns
            for quote in ['USDT', 'BUSD', 'BTC', 'ETH', 'BNB']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    return f"{base}/{quote}"
        return symbol
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from cache"""
        try:
            price_data = await self.redis_client.get(f"price:{symbol}")
            if price_data:
                return float(price_data)
            return None
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    async def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """Get current order book from cache"""
        try:
            orderbook_data = await self.redis_client.get(f"orderbook:{symbol}")
            if orderbook_data:
                return json.loads(orderbook_data)
            return self.orderbook_cache.get(symbol)
        except Exception as e:
            logger.error(f"Error getting orderbook: {e}")
            return None
    
    async def get_volume_profile(self, symbol: str, timeframe: str = '1h') -> pd.DataFrame:
        """Get volume profile for analysis"""
        query = f'''
        from(bucket: "{DATABASE['influxdb']['bucket']}")
        |> range(start: -{timeframe})
        |> filter(fn: (r) => r["_measurement"] == "trades")
        |> filter(fn: (r) => r["symbol"] == "{symbol}")
        |> group(columns: ["_time"])
        |> sum(column: "amount")
        '''
        
        result = self.influx_client.query_api().query_data_frame(query)
        return result
    
    async def calculate_vwap(self, symbol: str, period: int = 20) -> float:
        """Calculate Volume Weighted Average Price"""
        trades = await self.redis_client.lrange(f"trades:{symbol}", 0, period-1)
        if not trades:
            return 0
        
        total_value = 0
        total_volume = 0
        
        for trade_json in trades:
            trade = json.loads(trade_json)
            total_value += trade['price'] * trade['amount']
            total_volume += trade['amount']
        
        return total_value / total_volume if total_volume > 0 else 0
    
    async def detect_volume_spike(self, symbol: str, threshold: float = 3.0) -> bool:
        """Detect abnormal volume spikes"""
        current_volume = await self.get_volume_profile(symbol, '5m')
        historical_volume = await self.get_volume_profile(symbol, '1h')
        
        if current_volume.empty or historical_volume.empty:
            return False
        
        avg_volume = historical_volume['_value'].mean()
        current_vol = current_volume['_value'].sum()
        
        return current_vol > avg_volume * threshold
    
    def close(self):
        """Close all connections"""
        if self.influx_client:
            self.influx_client.close()
        if self.redis_client:
            asyncio.create_task(self.redis_client.close())
