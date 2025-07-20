import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import talib

from config.settings import STRATEGIES, TRADING
from ..core.exchange_manager import ExchangeManager
from ..core.market_data import MarketDataManager
from ..ml.models import ModelManager
from ..execution.order_manager import OrderManager

logger = logging.getLogger(__name__)

class DayTradingStrategy:
    """Day trading strategy with technical indicators"""
    
    def __init__(self, exchange_manager: ExchangeManager,
                 market_data: MarketDataManager,
                 model_manager: ModelManager,
                 order_manager: OrderManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.order_manager = order_manager
        self.config = STRATEGIES.get('day_trading', {})
        self.active_trades = {}
        self.daily_trades = 0
        
    async def run(self):
        """Main day trading loop"""
        if not self.config.get('enabled', False):
            return
            
        symbols = self.config.get('pairs', ['BTC/USDT', 'ETH/USDT'])
        
        while True:
            try:
                for symbol in symbols:
                    await self.analyze_symbol(symbol)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Day trading error: {e}")
                await asyncio.sleep(300)
    
    async def analyze_symbol(self, symbol: str):
        """Analyze symbol for day trading opportunities"""
        try:
            # Get historical data
            klines = await self._get_historical_data(symbol, '15m', 100)
            
            if len(klines) < 50:
                return
            
            # Calculate indicators
            indicators = self.calculate_indicators(klines)
            
            # Get ML predictions
            predictions = self.model_manager.get_ensemble_prediction(klines)
            
            # Check for signals
            signal = self.generate_signal(indicators, predictions)
            
            if signal['action'] != 'hold':
                await self.execute_trade(symbol, signal)
                
        except Exception as e:
            logger.error(f"Symbol analysis error {symbol}: {e}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(close)
        
        # RSI
        rsi = talib.RSI(close, timeperiod=14)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
        
        # Volume indicators
        obv = talib.OBV(close, volume)
        
        # ATR for volatility
        atr = talib.ATR(high, low, close, timeperiod=14)
        
        # Stochastic
        slowk, slowd = talib.STOCH(high, low, close)
        
        return {
            'macd': macd[-1],
            'macd_signal': macd_signal[-1],
            'macd_hist': macd_hist[-1],
            'macd_cross': self._detect_crossover(macd, macd_signal),
            'rsi': rsi[-1],
            'rsi_oversold': rsi[-1] < 30,
            'rsi_overbought': rsi[-1] > 70,
            'bb_position': (close[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]),
            'volume_trend': obv[-1] > obv[-5],
            'atr': atr[-1],
            'stoch_k': slowk[-1],
            'stoch_d': slowd[-1],
            'price_trend': self._calculate_trend(close)
        }
    
    def generate_signal(self, indicators: Dict, predictions: Dict) -> Dict:
        """Generate trading signal from indicators and ML predictions"""
        signal_strength = 0
        reasons = []
        
        # MACD signal
        if indicators['macd_cross'] == 'bullish':
            signal_strength += 2
            reasons.append("MACD bullish crossover")
        elif indicators['macd_cross'] == 'bearish':
            signal_strength -= 2
            reasons.append("MACD bearish crossover")
        
        # RSI signal
        if indicators['rsi_oversold']:
            signal_strength += 1.5
            reasons.append("RSI oversold")
        elif indicators['rsi_overbought']:
            signal_strength -= 1.5
            reasons.append("RSI overbought")
        
        # Bollinger Bands
        if indicators['bb_position'] < 0.2:
            signal_strength += 1
            reasons.append("Price near lower BB")
        elif indicators['bb_position'] > 0.8:
            signal_strength -= 1
            reasons.append("Price near upper BB")
        
        # ML predictions
        ml_signal = predictions.get('price', {})
        if ml_signal.get('up', 0) > 0.7:
            signal_strength += 2
            reasons.append(f"ML bullish: {ml_signal['up']:.2f}")
        elif ml_signal.get('down', 0) > 0.7:
            signal_strength -= 2
            reasons.append(f"ML bearish: {ml_signal['down']:.2f}")
        
        # Volume confirmation
        if indicators['volume_trend']:
            signal_strength *= 1.2
            reasons.append("Volume confirmation")
        
        # Determine action
        if signal_strength >= 3:
            action = 'buy'
        elif signal_strength <= -3:
            action = 'sell'
        else:
            action = 'hold'
        
        return {
            'action': action,
            'strength': abs(signal_strength),
            'reasons': reasons,
            'confidence': min(abs(signal_strength) / 5, 1.0)
        }
    
    async def execute_trade(self, symbol: str, signal: Dict):
        """Execute day trade based on signal"""
        if symbol in self.active_trades:
            # Check exit conditions for existing trade
            await self.check_exit_conditions(symbol, signal)
        else:
            # Check entry conditions
            if signal['confidence'] > 0.6:
                await self.enter_trade(symbol, signal)
    
    async def enter_trade(self, symbol: str, signal: Dict):
        """Enter a new day trade"""
        try:
            # Calculate position size
            balance = await self.exchange_manager.get_balance()
            usdt_balance = balance.get('USDT', 0)
            
            # Day trading uses moderate position sizes
            position_size = min(
                usdt_balance * 0.1 * signal['confidence'],
                TRADING['max_trade_amount_usd']
            )
            
            if position_size < TRADING['min_trade_amount_usd']:
                return
            
            # Place order
            order = await self.order_manager.place_order(
                strategy='day_trading',
                exchange='binance',
                symbol=symbol,
                side=signal['action'],
                amount=position_size
            )
            
            if order:
                current_price = await self.market_data.get_latest_price(symbol)
                
                self.active_trades[symbol] = {
                    'entry_price': current_price,
                    'entry_time': datetime.now(),
                    'side': signal['action'],
                    'size': position_size,
                    'reasons': signal['reasons'],
                    'stop_loss': current_price * 0.98 if signal['action'] == 'buy' else current_price * 1.02,
                    'take_profit': current_price * 1.03 if signal['action'] == 'buy' else current_price * 0.97
                }
                
                self.daily_trades += 1
                logger.info(f"Day trade entered: {symbol} {signal['action']} @ {current_price}")
                
        except Exception as e:
            logger.error(f"Day trade entry error: {e}")
    
    async def check_exit_conditions(self, symbol: str, signal: Dict):
        """Check if we should exit current position"""
        trade = self.active_trades[symbol]
        current_price = await self.market_data.get_latest_price(symbol)
        
        if not current_price:
            return
        
        # Calculate P&L
        if trade['side'] == 'buy':
            pnl_pct = (current_price - trade['entry_price']) / trade['entry_price']
            exit_condition = current_price <= trade['stop_loss'] or current_price >= trade['take_profit']
        else:
            pnl_pct = (trade['entry_price'] - current_price) / trade['entry_price']
            exit_condition = current_price >= trade['stop_loss'] or current_price <= trade['take_profit']
        
        # Check exit conditions
        should_exit = False
        exit_reason = ""
        
        if exit_condition:
            should_exit = True
            exit_reason = "Stop loss" if pnl_pct < 0 else "Take profit"
        elif signal['action'] != 'hold' and signal['action'] != trade['side']:
            should_exit = True
            exit_reason = "Signal reversal"
        elif (datetime.now() - trade['entry_time']).seconds > 14400:  # 4 hours
            should_exit = True
            exit_reason = "Time limit"
        
        if should_exit:
            await self.exit_trade(symbol, exit_reason)
    
    async def exit_trade(self, symbol: str, reason: str):
        """Exit day trade"""
        try:
            trade = self.active_trades[symbol]
            
            # Place exit order
            exit_side = 'sell' if trade['side'] == 'buy' else 'buy'
            order = await self.order_manager.place_order(
                strategy='day_trading',
                exchange='binance',
                symbol=symbol,
                side=exit_side,
                amount=trade['size']
            )
            
            if order:
                del self.active_trades[symbol]
                logger.info(f"Day trade exited: {symbol} - {reason}")
                
        except Exception as e:
            logger.error(f"Day trade exit error: {e}")
    
    def _detect_crossover(self, fast: np.ndarray, slow: np.ndarray) -> str:
        """Detect crossover between two lines"""
        if len(fast) < 2 or len(slow) < 2:
            return 'none'
        
        if fast[-2] <= slow[-2] and fast[-1] > slow[-1]:
            return 'bullish'
        elif fast[-2] >= slow[-2] and fast[-1] < slow[-1]:
            return 'bearish'
        
        return 'none'
    
    def _calculate_trend(self, prices: np.ndarray, period: int = 20) -> str:
        """Calculate price trend"""
        if len(prices) < period:
            return 'neutral'
        
        sma = np.mean(prices[-period:])
        if prices[-1] > sma * 1.02:
            return 'bullish'
        elif prices[-1] < sma * 0.98:
            return 'bearish'
        
        return 'neutral'
    
    async def _get_historical_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical OHLCV data"""
        try:
            exchange = self.exchange_manager.exchanges['binance']
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()


class SwingTradingStrategy:
    """Multi-day swing trading strategy"""
    
    def __init__(self, exchange_manager: ExchangeManager,
                 market_data: MarketDataManager,
                 model_manager: ModelManager,
                 order_manager: OrderManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.order_manager = order_manager
        self.config = STRATEGIES.get('swing_trading', {})
        self.swing_positions = {}
        
    async def run(self):
        """Main swing trading loop"""
        if not self.config.get('enabled', False):
            return
            
        while True:
            try:
                await self.scan_for_swings()
                await self.manage_positions()
                
                # Swing trading checks less frequently
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Swing trading error: {e}")
                await asyncio.sleep(3600)
    
    async def scan_for_swings(self):
        """Scan market for swing trade setups"""
        # Get top volume coins
        symbols = await self.get_high_volume_symbols()
        
        for symbol in symbols[:20]:  # Check top 20
            try:
                setup = await self.analyze_swing_setup(symbol)
                
                if setup['quality'] > 0.7:
                    await self.enter_swing_position(symbol, setup)
                    
            except Exception as e:
                logger.error(f"Swing scan error {symbol}: {e}")
    
    async def analyze_swing_setup(self, symbol: str) -> Dict:
        """Analyze potential swing trade setup"""
        # Get daily data
        daily_data = await self._get_historical_data(symbol, '1d', 100)
        
        if len(daily_data) < 50:
            return {'quality': 0}
        
        # Calculate swing indicators
        setup = {
            'trend': self._identify_trend(daily_data),
            'support_resistance': self._find_support_resistance(daily_data),
            'fibonacci_levels': self._calculate_fibonacci(daily_data),
            'pattern': self._detect_chart_pattern(daily_data),
            'momentum': self._analyze_momentum(daily_data)
        }
        
        # Score setup quality
        quality_score = 0
        
        if setup['trend']['strength'] > 0.6:
            quality_score += 0.3
        
        if setup['support_resistance']['near_support']:
            quality_score += 0.2
        
        if setup['pattern']['type'] != 'none':
            quality_score += 0.3
        
        if setup['momentum']['divergence']:
            quality_score += 0.2
        
        setup['quality'] = quality_score
        
        return setup
    
    def _identify_trend(self, df: pd.DataFrame) -> Dict:
        """Identify market trend using multiple timeframes"""
        close = df['close'].values
        
        # Calculate EMAs
        ema_20 = talib.EMA(close, timeperiod=20)
        ema_50 = talib.EMA(close, timeperiod=50)
        ema_100 = talib.EMA(close, timeperiod=100)
        
        # Determine trend
        if ema_20[-1] > ema_50[-1] > ema_100[-1]:
            trend = 'bullish'
            strength = min((ema_20[-1] - ema_100[-1]) / ema_100[-1] * 10, 1.0)
        elif ema_20[-1] < ema_50[-1] < ema_100[-1]:
            trend = 'bearish'
            strength = min((ema_100[-1] - ema_20[-1]) / ema_100[-1] * 10, 1.0)
        else:
            trend = 'neutral'
            strength = 0.3
        
        return {
            'direction': trend,
            'strength': strength,
            'ema_20': ema_20[-1],
            'ema_50': ema_50[-1],
            'ema_100': ema_100[-1]
        }
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find key support and resistance levels"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Find pivot points
        pivots_high = []
        pivots_low = []
        
        for i in range(2, len(high) - 2):
            if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
                pivots_high.append(high[i])
            if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
                pivots_low.append(low[i])
        
        current_price = close[-1]
        
        # Find nearest levels
        resistance = min([p for p in pivots_high if p > current_price], default=current_price * 1.1)
        support = max([p for p in pivots_low if p < current_price], default=current_price * 0.9)
        
        return {
            'support': support,
            'resistance': resistance,
            'near_support': (current_price - support) / support < 0.02,
            'near_resistance': (resistance - current_price) / current_price < 0.02
        }
    
    def _calculate_fibonacci(self, df: pd.DataFrame) -> Dict:
        """Calculate Fibonacci retracement levels"""
        high = df['high'].values
        low = df['low'].values
        
        # Find recent swing high and low
        recent_high = np.max(high[-20:])
        recent_low = np.min(low[-20:])
        
        diff = recent_high - recent_low
        
        levels = {
            '0.0': recent_high,
            '23.6': recent_high - diff * 0.236,
            '38.2': recent_high - diff * 0.382,
            '50.0': recent_high - diff * 0.5,
            '61.8': recent_high - diff * 0.618,
            '100.0': recent_low
        }
        
        return levels
    
    def _detect_chart_pattern(self, df: pd.DataFrame) -> Dict:
        """Detect chart patterns"""
        close = df['close'].values
        
        # Simple pattern detection
        pattern_type = 'none'
        confidence = 0
        
        # Double bottom
        if len(close) > 30:
            recent_lows = []
            for i in range(10, len(close) - 10):
                if close[i] < close[i-5] and close[i] < close[i+5]:
                    recent_lows.append((i, close[i]))
            
            if len(recent_lows) >= 2:
                low1, low2 = recent_lows[-2], recent_lows[-1]
                if abs(low1[1] - low2[1]) / low1[1] < 0.02:  # Similar lows
                    pattern_type = 'double_bottom'
                    confidence = 0.7
        
        return {
            'type': pattern_type,
            'confidence': confidence
        }
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """Analyze momentum indicators"""
        close = df['close'].values
        
        # RSI
        rsi = talib.RSI(close, timeperiod=14)
        
        # Check for divergence
        price_trend = close[-5] > close[-10]
        rsi_trend = rsi[-5] > rsi[-10]
        
        divergence = price_trend != rsi_trend
        
        return {
            'rsi': rsi[-1],
            'divergence': divergence,
            'momentum_strong': rsi[-1] > 50 and rsi[-1] < 70
        }
    
    async def enter_swing_position(self, symbol: str, setup: Dict):
        """Enter swing position"""
        if symbol in self.swing_positions:
            return
        
        try:
            # Conservative position sizing for swings
            balance = await self.exchange_manager.get_balance()
            usdt_balance = balance.get('USDT', 0)
            
            position_size = min(
                usdt_balance * 0.15,  # 15% per swing trade
                TRADING['max_trade_amount_usd'] * 2  # Allow larger swings
            )
            
            if position_size < TRADING['min_trade_amount_usd'] * 2:
                return
            
            # Determine direction based on setup
            if setup['trend']['direction'] == 'bullish' and setup['support_resistance']['near_support']:
                side = 'buy'
            elif setup['trend']['direction'] == 'bearish' and setup['support_resistance']['near_resistance']:
                side = 'sell'
            else:
                return
            
            # Place order
            order = await self.order_manager.place_order(
                strategy='swing_trading',
                exchange='binance',
                symbol=symbol,
                side=side,
                amount=position_size
            )
            
            if order:
                current_price = await self.market_data.get_latest_price(symbol)
                
                self.swing_positions[symbol] = {
                    'entry_price': current_price,
                    'entry_time': datetime.now(),
                    'side': side,
                    'size': position_size,
                    'setup': setup,
                    'stop_loss': setup['support_resistance']['support'] * 0.98 if side == 'buy' else setup['support_resistance']['resistance'] * 1.02,
                    'take_profit': setup['support_resistance']['resistance'] if side == 'buy' else setup['support_resistance']['support']
                }
                
                logger.info(f"Swing position entered: {symbol} {side} @ {current_price}")
                
        except Exception as e:
            logger.error(f"Swing entry error: {e}")
    
    async def manage_positions(self):
        """Manage open swing positions"""
        for symbol, position in list(self.swing_positions.items()):
            try:
                current_price = await self.market_data.get_latest_price(symbol)
                
                if not current_price:
                    continue
                
                # Calculate P&L
                if position['side'] == 'buy':
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                    should_exit = current_price <= position['stop_loss'] or current_price >= position['take_profit']
                else:
                    pnl_pct = (position['entry_price'] - current_price) / position['entry_price']
                    should_exit = current_price >= position['stop_loss'] or current_price <= position['take_profit']
                
                # Time-based exit (max 2 weeks)
                days_held = (datetime.now() - position['entry_time']).days
                if days_held > 14:
                    should_exit = True
                
                # Trailing stop for profits
                if pnl_pct > 0.05:  # 5% profit
                    new_stop = current_price * 0.97 if position['side'] == 'buy' else current_price * 1.03
                    if position['side'] == 'buy' and new_stop > position['stop_loss']:
                        position['stop_loss'] = new_stop
                    elif position['side'] == 'sell' and new_stop < position['stop_loss']:
                        position['stop_loss'] = new_stop
                
                if should_exit:
                    await self.exit_swing_position(symbol)
                    
            except Exception as e:
                logger.error(f"Position management error {symbol}: {e}")
    
    async def exit_swing_position(self, symbol: str):
        """Exit swing position"""
        try:
            position = self.swing_positions[symbol]
            
            exit_side = 'sell' if position['side'] == 'buy' else 'buy'
            order = await self.order_manager.place_order(
                strategy='swing_trading',
                exchange='binance',
                symbol=symbol,
                side=exit_side,
                amount=position['size']
            )
            
            if order:
                del self.swing_positions[symbol]
                logger.info(f"Swing position exited: {symbol}")
                
        except Exception as e:
            logger.error(f"Swing exit error: {e}")
    
    async def get_high_volume_symbols(self) -> List[str]:
        """Get symbols with high trading volume"""
        try:
            exchange = self.exchange_manager.exchanges['binance']
            tickers = await exchange.fetch_tickers()
            
            # Filter and sort by volume
            usdt_pairs = [
                (symbol, ticker['quoteVolume']) 
                for symbol, ticker in tickers.items() 
                if symbol.endswith('/USDT') and ticker['quoteVolume']
            ]
            
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return [symbol for symbol, _ in usdt_pairs[:50]]
            
        except Exception as e:
            logger.error(f"Failed to get high volume symbols: {e}")
            return []
    
    async def _get_historical_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical OHLCV data"""
        try:
            exchange = self.exchange_manager.exchanges['binance']
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
