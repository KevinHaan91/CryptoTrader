import asyncio
import logging
import signal
import sys
from datetime import datetime
import schedule

from config.settings import MONITORING, STRATEGIES
from src.core.exchange_manager import ExchangeManager
from src.core.market_data import MarketDataManager
from src.core.risk_manager import RiskManager
from src.ml.models import ModelManager
from src.execution.order_manager import OrderManager
from src.strategies.high_frequency import (
    ScalpingStrategy, ArbitrageStrategy, PumpDetectionStrategy
)
from src.strategies.new_listing_detection import NewListingDetectionStrategy
from src.core.performance_tracker import PerformanceTracker
from api.server import TradingAPI
import threading

# Configure logging
logging.basicConfig(
    level=getattr(logging, MONITORING['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CryptoTradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        self.exchange_manager = None
        self.market_data = None
        self.risk_manager = None
        self.model_manager = None
        self.order_manager = None
        self.performance_tracker = None
        self.strategies = {}
        self.running = False
        self.api_server = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Crypto Trading Bot...")
        
        # Initialize core components
        self.exchange_manager = ExchangeManager()
        await self.exchange_manager.initialize()
        
        self.market_data = MarketDataManager()
        await self.market_data.initialize()
        
        self.risk_manager = RiskManager()
        self.model_manager = ModelManager()
        
        self.order_manager = OrderManager(
            self.exchange_manager, 
            self.risk_manager
        )
        
        # Initialize performance tracker
        self.performance_tracker = PerformanceTracker()
        
        # Initialize strategies
        if STRATEGIES['scalping']['enabled']:
            self.strategies['scalping'] = ScalpingStrategy(
                self.exchange_manager,
                self.market_data,
                self.model_manager
            )
        
        if STRATEGIES['arbitrage']['enabled']:
            self.strategies['arbitrage'] = ArbitrageStrategy(
                self.exchange_manager,
                self.market_data,
                self.model_manager
            )
        
        if STRATEGIES['pump_detection']['enabled']:
            self.strategies['pump_detection'] = PumpDetectionStrategy(
                self.exchange_manager,
                self.market_data,
                self.model_manager
            )
        
        if STRATEGIES.get('new_listing_detection', {}).get('enabled', False):
            self.strategies['new_listing_detection'] = NewListingDetectionStrategy(
                self.exchange_manager,
                self.market_data,
                self.model_manager,
                self.order_manager
            )
        
        # Connect to market data streams
        await self._connect_data_streams()
        
        # Register strategies with performance tracker
        for strategy_id, strategy in self.strategies.items():
            self.performance_tracker.register_strategy(strategy_id, strategy)
        
        # Initialize API server
        self.api_server = TradingAPI(self)
        
        logger.info("Bot initialization complete")
    
    async def _connect_data_streams(self):
        """Connect to real-time market data"""
        # Get all unique symbols from enabled strategies
        symbols = set()
        
        if 'scalping' in self.strategies:
            symbols.update(STRATEGIES['scalping']['pairs'])
        
        # Add more symbols from other strategies as needed
        symbols.update(['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])  # Core pairs
        
        # Connect to Binance WebSocket for low latency
        await self.market_data.connect_binance_stream(list(symbols))
        
        logger.info(f"Connected to market data streams for {len(symbols)} symbols")
    
    async def start(self):
        """Start trading bot"""
        self.running = True
        logger.info("Starting trading strategies...")
        
        # Start all enabled strategies
        tasks = []
        for name, strategy in self.strategies.items():
            logger.info(f"Starting {name} strategy")
            task = asyncio.create_task(strategy.run())
            tasks.append(task)
        
        # Start periodic tasks
        asyncio.create_task(self._periodic_tasks())
        
        # Start monitoring
        asyncio.create_task(self._monitor_performance())
        
        # Start API server in separate thread
        api_thread = threading.Thread(
            target=self.api_server.start,
            kwargs={'host': '0.0.0.0', 'port': 8000},
            daemon=True
        )
        api_thread.start()
        logger.info("API server started on port 8000")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Strategy error: {e}")
    
    async def _periodic_tasks(self):
        """Run periodic maintenance tasks"""
        while self.running:
            try:
                # Update ML models every hour
                if datetime.now().minute == 0:
                    logger.info("Updating ML models...")
                    # await self.model_manager.update_models(training_data)
                
                # Reset daily limits at midnight UTC
                if datetime.now().hour == 0 and datetime.now().minute == 0:
                    self.risk_manager.reset_daily_limits()
                
                # Log portfolio status every 15 minutes
                if datetime.now().minute % 15 == 0:
                    await self._log_portfolio_status()
                
                # Update performance tracker every 5 minutes
                if datetime.now().minute % 5 == 0:
                    await self._update_performance_tracker()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Periodic task error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_performance(self):
        """Monitor trading performance and risk"""
        while self.running:
            try:
                # Get current balance
                balance = await self.exchange_manager.get_balance()
                total_balance = sum(balance.values())
                
                # Update risk manager
                self.risk_manager.update_drawdown(total_balance)
                
                # Check circuit breakers
                risk_metrics = self.risk_manager.get_risk_metrics()
                
                if not risk_metrics['trading_enabled']:
                    logger.warning("Trading disabled by risk manager")
                    # Could send alert here
                
                # Log metrics
                logger.info(f"Portfolio Value: ${total_balance:.2f}, "
                          f"Daily P&L: ${risk_metrics['daily_pnl']:.2f}, "
                          f"Positions: {risk_metrics['open_positions']}")
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _log_portfolio_status(self):
        """Log detailed portfolio status"""
        try:
            # Get balances
            balances = {}
            for exchange in self.exchange_manager.exchanges:
                balance = await self.exchange_manager.get_balance(exchange)
                balances[exchange] = balance
            
            # Get risk metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # Get order stats
            order_stats = self.order_manager.get_order_stats()
            
            logger.info("=== Portfolio Status ===")
            logger.info(f"Balances: {balances}")
            logger.info(f"Risk Metrics: {risk_metrics}")
            logger.info(f"Order Stats: {order_stats}")
            logger.info("=====================")
            
        except Exception as e:
            logger.error(f"Portfolio status error: {e}")
    
    async def _update_performance_tracker(self):
        """Update performance tracking data"""
        try:
            # Get performance from each strategy
            for strategy_id, strategy in self.strategies.items():
                if hasattr(strategy, 'get_strategy_performance'):
                    perf_data = strategy.get_strategy_performance()
                    # Update tracker with strategy-specific data
                    logger.debug(f"Updated performance for {strategy_id}")
            
            # Get overall performance
            overall_perf = self.performance_tracker.get_strategy_performance()
            
            # Log summary
            if overall_perf.get('overall'):
                total_pnl = overall_perf['overall']['total_pnl']
                win_rate = overall_perf['overall']['overall_win_rate']
                logger.info(f"Overall Performance - P&L: ${total_pnl:.2f}, Win Rate: {win_rate*100:.1f}%")
            
        except Exception as e:
            logger.error(f"Performance tracker update error: {e}")
    
    async def stop(self):
        """Gracefully stop trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False
        
        # Cancel all active orders
        active_orders = self.order_manager.get_active_orders()
        for order_id in active_orders:
            await self.order_manager.cancel_order(order_id)
        
        # Close all connections
        self.exchange_manager.close()
        self.market_data.close()
        
        # Save performance data
        self.performance_tracker._save_performance_data()
        
        logger.info("Trading bot stopped")

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    asyncio.create_task(bot.stop())
    sys.exit(0)

# Global bot instance
bot = CryptoTradingBot()

async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        # Initialize bot
        await bot.initialize()
        
        # Start trading
        await bot.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await bot.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
