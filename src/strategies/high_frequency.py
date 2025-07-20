import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from config.settings import STRATEGIES, TRADING
from ..core.exchange_manager import ExchangeManager
from ..core.market_data import MarketDataManager
from ..ml.models import ModelManager

logger = logging.getLogger(__name__)

class ScalpingStrategy:
    """Ultra-low latency scalping strategy"""
    
    def __init__(self, exchange_manager: ExchangeManager, 
                 market_data: MarketDataManager,
                 model_manager: ModelManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.config = STRATEGIES['scalping']
        self.active_positions = {}
        self.entry_times = {}
        
    async def run(self):
        """Main scalping loop"""
        if not self.config['enabled']:
            return
        
        # Subscribe to real-time data
        for symbol in self.config['pairs']:
            await self.market_data.subscribe(f"trade:{symbol}", self.on_trade)
            await self.market_data.subscribe(f"orderbook:{symbol}", self.on_orderbook)
        
        logger.info(f"Scalping strategy started for {self.config['pairs']}")
    
    async def on_trade(self, trade: Dict):
        """React to new trades with minimal latency"""
        symbol = trade['symbol']
        
        # Check if we have an open position
        if symbol in self.active_positions:
            await self.check_exit(symbol, trade['price'])
        else:
            await self.check_entry(symbol, trade)
    
    async def on_orderbook(self, orderbook: Dict):
        """Analyze order book for scalping opportunities"""
        symbol = orderbook['symbol']
        
        # Calculate order book imbalance
        bid_volume = sum(q for _, q in orderbook['bids'][:5])
        ask_volume = sum(q for _, q in orderbook['asks'][:5])
        
        if bid_volume + ask_volume == 0:
            return
        
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        
        # Strong buying pressure
        if imbalance > 0.7 and symbol not in self.active_positions:
            await self.enter_position(symbol, 'buy', orderbook['asks'][0][0])
        
        # Strong selling pressure - exit long positions
        elif imbalance < -0.7 and symbol in self.active_positions:
            if self.active_positions[symbol]['side'] == 'buy':
                await self.exit_position(symbol, orderbook['bids'][0][0])
    
    async def check_entry(self, symbol: str, trade: Dict):
        """Check entry conditions"""
        # Get recent trades
        trades = await self.market_data.redis_client.lrange(f"trades:{symbol}", 0, 20)
        if len(trades) < 10:
            return
        
        # Calculate micro momentum
        prices = [float(t['price']) for t in trades]
        momentum = (prices[0] - prices[-1]) / prices[-1]
        
        # Volume analysis
        volumes = [float(t['amount']) for t in trades]
        avg_volume = np.mean(volumes)
        current_volume = trade['amount']
        
        # Entry conditions
        if (momentum > 0.001 and  # 0.1% momentum
            current_volume > avg_volume * 1.5 and  # Volume spike
            trade['side'] == 'buy'):  # Aggressive buying
            
            # Get ML prediction
            predictions = self.model_manager.get_ensemble_prediction(
                pd.DataFrame(trades), None
            )
            
            if predictions.get('price', {}).get('up', 0) > 0.6:
                await self.enter_position(symbol, 'buy', trade['price'])
    
    async def enter_position(self, symbol: str, side: str, price: float):
        """Enter a scalping position"""
        # Calculate position size
        balance = await self.exchange_manager.get_balance()
        usdt_balance = balance.get('USDT', 0)
        
        position_size = min(
            usdt_balance * TRADING['max_position_size'],
            TRADING['max_trade_amount_usd']
        )
        
        if position_size < TRADING['min_trade_amount_usd']:
            return
        
        # Execute order
        order = await self.exchange_manager.execute_market_order(
            'binance', symbol, side, position_size
        )
        
        if order:
            self.active_positions[symbol] = {
                'side': side,
                'entry_price': price,
                'size': position_size,
                'order_id': order['id']
            }
            self.entry_times[symbol] = datetime.now()
            
            logger.info(f"Scalp entry: {symbol} {side} @ {price}")
    
    async def check_exit(self, symbol: str, current_price: float):
        """Check exit conditions"""
        position = self.active_positions[symbol]
        entry_price = position['entry_price']
        entry_time = self.entry_times[symbol]
        
        # Calculate P&L
        if position['side'] == 'buy':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Exit conditions
        exit_signal = False
        
        # Take profit
        if pnl_pct >= self.config['min_profit_target']:
            exit_signal = True
            logger.info(f"Scalp take profit: {symbol} +{pnl_pct*100:.2f}%")
        
        # Stop loss
        elif pnl_pct <= -self.config['min_profit_target']:
            exit_signal = True
            logger.info(f"Scalp stop loss: {symbol} {pnl_pct*100:.2f}%")
        
        # Time-based exit
        elif (datetime.now() - entry_time).seconds > self.config['max_hold_time']:
            exit_signal = True
            logger.info(f"Scalp time exit: {symbol}")
        
        if exit_signal:
            await self.exit_position(symbol, current_price)
    
    async def exit_position(self, symbol: str, price: float):
        """Exit scalping position"""
        position = self.active_positions[symbol]
        
        # Execute exit order
        exit_side = 'sell' if position['side'] == 'buy' else 'buy'
        order = await self.exchange_manager.execute_market_order(
            'binance', symbol, exit_side, position['size']
        )
        
        if order:
            del self.active_positions[symbol]
            del self.entry_times[symbol]
            logger.info(f"Scalp exit: {symbol} @ {price}")

class ArbitrageStrategy:
    """Cross-exchange arbitrage strategy"""
    
    def __init__(self, exchange_manager: ExchangeManager,
                 market_data: MarketDataManager,
                 model_manager: ModelManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.config = STRATEGIES['arbitrage']
        self.active_arbs = {}
        
    async def run(self):
        """Main arbitrage scanning loop"""
        if not self.config['enabled']:
            return
        
        while True:
            await self.scan_opportunities()
            await asyncio.sleep(self.config['check_interval'])
    
    async def scan_opportunities(self):
        """Scan for arbitrage opportunities across exchanges"""
        # Get common pairs across exchanges
        pairs = await self.get_common_pairs()
        
        for symbol in pairs:
            prices = await self.get_cross_exchange_prices(symbol)
            
            if len(prices) < 2:
                continue
            
            # Find best arbitrage opportunity
            opportunity = self.find_best_opportunity(symbol, prices)
            
            if opportunity and opportunity['net_profit_pct'] > self.config['min_spread']:
                await self.execute_arbitrage(opportunity)
    
    async def get_common_pairs(self) -> List[str]:
        """Get trading pairs available on multiple exchanges"""
        all_pairs = {}
        
        for exchange_name in self.exchange_manager.exchanges:
            pairs = await self.exchange_manager.get_available_pairs(exchange_name)
            for pair in pairs:
                if pair not in all_pairs:
                    all_pairs[pair] = []
                all_pairs[pair].append(exchange_name)
        
        # Return pairs available on at least 2 exchanges
        return [pair for pair, exchanges in all_pairs.items() if len(exchanges) >= 2]
    
    async def get_cross_exchange_prices(self, symbol: str) -> Dict[str, Dict]:
        """Get current prices across all exchanges"""
        prices = {}
        
        tasks = []
        for exchange_name in self.exchange_manager.exchanges:
            task = self.get_exchange_price(exchange_name, symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for exchange_name, result in zip(self.exchange_manager.exchanges.keys(), results):
            if not isinstance(result, Exception) and result:
                prices[exchange_name] = result
        
        return prices
    
    async def get_exchange_price(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """Get price from specific exchange"""
        try:
            orderbook = await self.exchange_manager.get_order_book(exchange_name, symbol, 5)
            
            if orderbook['bids'] and orderbook['asks']:
                return {
                    'bid': orderbook['bids'][0][0],
                    'ask': orderbook['asks'][0][0],
                    'bid_volume': orderbook['bids'][0][1],
                    'ask_volume': orderbook['asks'][0][1]
                }
        except Exception as e:
            logger.debug(f"Failed to get price from {exchange_name}: {e}")
        
        return None
    
    def find_best_opportunity(self, symbol: str, prices: Dict[str, Dict]) -> Optional[Dict]:
        """Find the best arbitrage opportunity"""
        best_opportunity = None
        max_profit = 0
        
        # Check all exchange pairs
        exchanges = list(prices.keys())
        
        for buy_exchange in exchanges:
            for sell_exchange in exchanges:
                if buy_exchange == sell_exchange:
                    continue
                
                buy_price = prices[buy_exchange]['ask']
                sell_price = prices[sell_exchange]['bid']
                
                # Calculate profit
                gross_profit_pct = (sell_price - buy_price) / buy_price
                
                # Estimate fees
                buy_fee = 0.001  # 0.1%
                sell_fee = 0.001
                net_profit_pct = gross_profit_pct - buy_fee - sell_fee
                
                if net_profit_pct > max_profit:
                    max_profit = net_profit_pct
                    best_opportunity = {
                        'symbol': symbol,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'gross_profit_pct': gross_profit_pct,
                        'net_profit_pct': net_profit_pct,
                        'buy_volume': prices[buy_exchange]['ask_volume'],
                        'sell_volume': prices[sell_exchange]['bid_volume']
                    }
        
        return best_opportunity
    
    async def execute_arbitrage(self, opportunity: Dict):
        """Execute arbitrage trade"""
        symbol = opportunity['symbol']
        
        # Check if already executing this arbitrage
        arb_key = f"{symbol}:{opportunity['buy_exchange']}:{opportunity['sell_exchange']}"
        if arb_key in self.active_arbs:
            return
        
        self.active_arbs[arb_key] = opportunity
        
        try:
            # Calculate trade size
            balance = await self.exchange_manager.get_balance(opportunity['buy_exchange'])
            usdt_balance = balance.get('USDT', 0)
            
            max_size = min(
                usdt_balance * 0.3,  # Max 30% of balance per arbitrage
                opportunity['buy_volume'] * opportunity['buy_price'] * 0.5,  # Max 50% of available liquidity
                opportunity['sell_volume'] * opportunity['sell_price'] * 0.5,
                TRADING['max_trade_amount_usd']
            )
            
            if max_size < TRADING['min_trade_amount_usd']:
                logger.debug(f"Arbitrage size too small: {max_size}")
                return
            
            # Execute simultaneously
            buy_task = self.exchange_manager.execute_market_order(
                opportunity['buy_exchange'], symbol, 'buy', max_size
            )
            sell_task = self.exchange_manager.execute_market_order(
                opportunity['sell_exchange'], symbol, 'sell', max_size / opportunity['sell_price']
            )
            
            buy_order, sell_order = await asyncio.gather(buy_task, sell_task)
            
            if buy_order and sell_order:
                logger.info(f"Arbitrage executed: {symbol} "
                          f"{opportunity['buy_exchange']}→{opportunity['sell_exchange']} "
                          f"profit: {opportunity['net_profit_pct']*100:.2f}%")
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
        finally:
            del self.active_arbs[arb_key]

class PumpDetectionStrategy:
    """Detect and trade pump-and-dump schemes"""
    
    def __init__(self, exchange_manager: ExchangeManager,
                 market_data: MarketDataManager,
                 model_manager: ModelManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.config = STRATEGIES['pump_detection']
        self.monitoring_coins = {}
        
    async def run(self):
        """Main pump detection loop"""
        if not self.config['enabled']:
            return
        
        # Monitor volume spikes
        asyncio.create_task(self.monitor_volume_spikes())
        
        # Monitor social signals
        asyncio.create_task(self.monitor_social_signals())
        
        logger.info("Pump detection strategy started")
    
    async def monitor_volume_spikes(self):
        """Monitor for unusual volume spikes"""
        while True:
            try:
                # Get all active trading pairs
                pairs = await self.exchange_manager.get_available_pairs('binance')
                
                for symbol in pairs[:100]:  # Monitor top 100 pairs
                    # Check for volume spike
                    spike_detected = await self.market_data.detect_volume_spike(
                        symbol, self.config['volume_spike_threshold']
                    )
                    
                    if spike_detected and symbol not in self.monitoring_coins:
                        await self.analyze_pump_potential(symbol)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Volume monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def analyze_pump_potential(self, symbol: str):
        """Analyze if volume spike indicates pump"""
        self.monitoring_coins[symbol] = datetime.now()
        
        try:
            # Get recent market data
            trades = await self.market_data.get_recent_trades('binance', symbol, 100)
            
            if not trades:
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Get ML prediction
            predictions = self.model_manager.get_ensemble_prediction(df)
            
            pump_prob = predictions['pump']['probability']
            pump_signal = predictions['pump']['signal']
            
            if pump_prob > 0.7:
                logger.warning(f"PUMP DETECTED: {symbol} "
                             f"probability: {pump_prob:.2f} "
                             f"signal: {pump_signal}")
                
                # Execute trade if confidence is high
                if pump_signal in ['critical', 'high']:
                    await self.enter_pump_trade(symbol, pump_prob)
            
        except Exception as e:
            logger.error(f"Pump analysis error for {symbol}: {e}")
        finally:
            # Stop monitoring after 30 minutes
            if symbol in self.monitoring_coins:
                if (datetime.now() - self.monitoring_coins[symbol]).seconds > 1800:
                    del self.monitoring_coins[symbol]
    
    async def enter_pump_trade(self, symbol: str, confidence: float):
        """Enter a pump trade with strict risk management"""
        try:
            # Very conservative position sizing for pumps
            balance = await self.exchange_manager.get_balance()
            usdt_balance = balance.get('USDT', 0)
            
            # Scale position by confidence
            position_size = min(
                usdt_balance * 0.02 * confidence,  # Max 2% of portfolio
                500  # Max $500 per pump trade
            )
            
            if position_size < 50:
                return
            
            # Set tight stop loss
            current_price = await self.market_data.get_latest_price(symbol)
            stop_loss_price = current_price * 0.95  # 5% stop loss
            
            # Execute entry
            order = await self.exchange_manager.execute_market_order(
                'binance', symbol, 'buy', position_size
            )
            
            if order:
                # Set stop loss immediately
                stop_order = await self.exchange_manager.execute_limit_order(
                    'binance', symbol, 'sell', 
                    position_size / current_price, stop_loss_price
                )
                
                logger.info(f"Pump trade entered: {symbol} "
                          f"size: ${position_size:.2f} "
                          f"stop: {stop_loss_price:.4f}")
                
                # Monitor for exit
                asyncio.create_task(
                    self.monitor_pump_exit(symbol, order, stop_order)
                )
                
        except Exception as e:
            logger.error(f"Pump trade entry failed: {e}")
    
    async def monitor_pump_exit(self, symbol: str, entry_order: Dict, stop_order: Dict):
        """Monitor pump trade for exit signals"""
        entry_price = float(entry_order['price'])
        peak_price = entry_price
        
        for _ in range(300):  # Monitor for 5 minutes max
            try:
                current_price = await self.market_data.get_latest_price(symbol)
                
                if not current_price:
                    continue
                
                # Update peak
                if current_price > peak_price:
                    peak_price = current_price
                
                # Trailing stop logic
                drawdown = (peak_price - current_price) / peak_price
                
                if drawdown > 0.1:  # 10% drawdown from peak
                    # Cancel stop loss and market sell
                    await self.exchange_manager.cancel_order(
                        'binance', stop_order['id'], symbol
                    )
                    
                    await self.exchange_manager.execute_market_order(
                        'binance', symbol, 'sell', entry_order['amount']
                    )
                    
                    profit = (current_price - entry_price) / entry_price
                    logger.info(f"Pump trade exited: {symbol} "
                              f"profit: {profit*100:.2f}%")
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Pump exit monitoring error: {e}")
                break
    
    async def monitor_social_signals(self):
        """Monitor social media for pump signals"""
        # This would integrate with social media APIs
        # For now, it's a placeholder
        pass
