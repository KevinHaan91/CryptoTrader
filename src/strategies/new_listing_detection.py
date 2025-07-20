import asyncio
import logging
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import aiohttp
import json
from dataclasses import dataclass

from config.settings import STRATEGIES, TRADING
from ..core.exchange_manager import ExchangeManager
from ..core.market_data import MarketDataManager
from ..ml.models import ModelManager
from ..execution.order_manager import OrderManager
from .presale_monitor import PresaleMonitor
from .exchange_monitor import ExchangeMonitor
from .news_monitor import NewsMonitor

logger = logging.getLogger(__name__)

@dataclass
class SourceAlert:
    source: str
    timestamp: datetime
    token_symbol: str
    confidence: float
    alert_type: str  # 'presale', 'dex_listing', 'cex_listing', 'pump_signal'
    source_reliability: float

@dataclass
class ListingOpportunity:
    token_symbol: str
    token_address: Optional[str]
    discovery_time: datetime
    opportunity_type: str
    confidence_score: float
    sources: List[SourceAlert]
    ml_prediction: Dict

class SourceAnalyzer:
    """ML-driven analysis of news sources and forums for crypto opportunities"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.source_performance = {}
        self.source_reliability = {}
        
        # Initialize source tracking
        self.monitored_sources = {
            'twitter_accounts': [
                '@tier10k', '@gainzxbt', '@cryptobullet1', '@altcoindaily',
                '@binance', '@mexc_global', '@kucoincom', '@gate_io'
            ],
            'telegram_channels': [
                'cryptogemhunters', 'pumpdiscovery', 'lowcapgems',
                'binancekillaz', 'mexcglobal', 'kucoin_en'
            ],
            'discord_servers': [
                'DegenChat', 'CryptoLaunch', 'AltcoinDaily', 'KuCoin'
            ],
            'websites': [
                'coinlaunch.space', 'listingspy.net', 'cryptocurrencyalerting.com',
                'icobench.com', 'cryptorank.io'
            ]
        }
        
    async def analyze_source_performance(self) -> Dict[str, float]:
        """Analyze historical performance of each source"""
        performance_scores = {}
        
        for source_type, sources in self.monitored_sources.items():
            for source in sources:
                # Get historical alerts from this source
                alerts = await self._get_source_history(source)
                
                if len(alerts) < 5:  # Need minimum data
                    performance_scores[source] = 0.5
                    continue
                
                # Calculate success metrics
                success_rate = await self._calculate_success_rate(alerts)
                timing_score = await self._calculate_timing_score(alerts)
                accuracy_score = await self._calculate_accuracy_score(alerts)
                
                # Weighted performance score
                performance_scores[source] = (
                    success_rate * 0.4 +
                    timing_score * 0.35 +
                    accuracy_score * 0.25
                )
        
        self.source_reliability = performance_scores
        return performance_scores
    
    async def _get_source_history(self, source: str) -> List[SourceAlert]:
        """Retrieve historical alerts from a specific source"""
        # This would connect to your database of tracked alerts
        # For now, return empty list
        return []
    
    async def _calculate_success_rate(self, alerts: List[SourceAlert]) -> float:
        """Calculate what percentage of alerts led to profitable opportunities"""
        if not alerts:
            return 0.5
        
        successful = 0
        for alert in alerts:
            # Check if token pumped within reasonable timeframe
            success = await self._check_token_performance(
                alert.token_symbol, 
                alert.timestamp
            )
            if success:
                successful += 1
        
        return successful / len(alerts)
    
    async def _calculate_timing_score(self, alerts: List[SourceAlert]) -> float:
        """How early does this source provide alerts relative to price movements"""
        timing_scores = []
        
        for alert in alerts:
            hours_before_pump = await self._get_hours_before_pump(
                alert.token_symbol, 
                alert.timestamp
            )
            
            if hours_before_pump > 0:
                # Score based on how early the alert was
                score = min(hours_before_pump / 24, 1.0)  # Max 24 hours
                timing_scores.append(score)
        
        return np.mean(timing_scores) if timing_scores else 0.5
    
    async def _calculate_accuracy_score(self, alerts: List[SourceAlert]) -> float:
        """How accurate are the predictions/confidence scores"""
        return 0.5  # Placeholder implementation
    
    async def _check_token_performance(self, symbol: str, alert_time: datetime) -> bool:
        """Check if token had significant price movement after alert"""
        # Placeholder - would check historical price data
        return False
    
    async def _get_hours_before_pump(self, symbol: str, alert_time: datetime) -> float:
        """Get how many hours before pump the alert was issued"""
        # Placeholder - would analyze price data
        return 0.0

class NewListingDetectionStrategy:
    """Comprehensive new listing detection and trading strategy"""
    
    def __init__(self, exchange_manager: ExchangeManager,
                 market_data: MarketDataManager,
                 model_manager: ModelManager,
                 order_manager: OrderManager):
        self.exchange_manager = exchange_manager
        self.market_data = market_data
        self.model_manager = model_manager
        self.order_manager = order_manager
        self.config = STRATEGIES.get('new_listing_detection', {})
        
        self.source_analyzer = SourceAnalyzer(model_manager)
        self.active_positions = {}
        self.monitored_tokens = {}
        self.strategy_performance = {
            'presale_trades': [],
            'dex_trades': [],
            'cex_trades': [],
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_hold_time': 0.0
        }
        
        # Initialize sub-monitors
        self.presale_monitor = None
        self.exchange_monitor = None
        self.news_monitor = None
        self.dex_monitor = None
        
    async def run(self):
        """Main strategy loop"""
        if not self.config.get('enabled', False):
            return
        
        # Initialize sub-monitors
        await self._initialize_monitors()
        
        # Update source reliability scores every 6 hours
        asyncio.create_task(self._update_source_scores())
        
        # Monitor different opportunity types
        asyncio.create_task(self._monitor_presales())
        asyncio.create_task(self._monitor_dex_listings())
        asyncio.create_task(self._monitor_cex_announcements())
        asyncio.create_task(self._monitor_social_signals())
        
        # Manage existing positions
        asyncio.create_task(self._manage_positions())
        
        logger.info("New listing detection strategy started")
    
    async def _initialize_monitors(self):
        """Initialize all sub-monitors"""
        try:
            # Initialize presale monitor
            self.presale_monitor = PresaleMonitor(self.model_manager.listing_models)
            
            # Initialize exchange monitor
            exchange_credentials = {}
            # Add exchange credentials if available
            self.exchange_monitor = ExchangeMonitor(exchange_credentials)
            
            # Initialize news monitor
            social_credentials = {
                'twitter': {
                    'bearer_token': os.getenv('TWITTER_BEARER_TOKEN')
                },
                'reddit': {
                    'client_id': os.getenv('REDDIT_CLIENT_ID'),
                    'client_secret': os.getenv('REDDIT_CLIENT_SECRET')
                }
            }
            self.news_monitor = NewsMonitor(social_credentials, self.model_manager.listing_models)
            
            logger.info("All monitors initialized successfully")
            
        except Exception as e:
            logger.error(f"Monitor initialization error: {e}")
    
    async def _update_source_scores(self):
        """Periodically update source reliability scores"""
        while True:
            try:
                await self.source_analyzer.analyze_source_performance()
                logger.info("Updated source reliability scores")
                await asyncio.sleep(21600)  # 6 hours
            except Exception as e:
                logger.error(f"Source score update error: {e}")
                await asyncio.sleep(3600)
    
    async def _monitor_presales(self):
        """Monitor ICO/IDO/IEO presales"""
        while True:
            try:
                # Check CoinLaunch API
                presales = await self._fetch_presales()
                
                for presale in presales:
                    if await self._evaluate_presale(presale):
                        await self._enter_presale_position(presale)
                
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Presale monitoring error: {e}")
                await asyncio.sleep(1800)
    
    async def _monitor_dex_listings(self):
        """Monitor DEX new listings via blockchain events"""
        while True:
            try:
                # Monitor Uniswap new pair events
                new_pairs = await self._get_new_uniswap_pairs()
                
                for pair in new_pairs:
                    opportunity = await self._analyze_dex_opportunity(pair)
                    if opportunity and opportunity.confidence_score > 0.7:
                        await self._enter_dex_position(opportunity)
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"DEX monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_cex_announcements(self):
        """Monitor centralized exchange listing announcements"""
        while True:
            try:
                # Check exchange APIs and announcement pages
                announcements = await self._fetch_cex_announcements()
                
                for announcement in announcements:
                    if announcement['exchange'] in ['mexc', 'kucoin', 'gate']:
                        await self._handle_early_cex_listing(announcement)
                    elif announcement['exchange'] in ['binance', 'coinbase']:
                        await self._handle_major_cex_announcement(announcement)
                
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"CEX monitoring error: {e}")
                await asyncio.sleep(600)
    
    async def _monitor_social_signals(self):
        """Monitor Twitter, Telegram, Discord for early signals"""
        while True:
            try:
                # This would integrate with social media APIs
                signals = await self._fetch_social_signals()
                
                for signal in signals:
                    # Weight by source reliability
                    reliability = self.source_analyzer.source_reliability.get(
                        signal.source, 0.5
                    )
                    
                    weighted_confidence = signal.confidence * reliability
                    
                    if weighted_confidence > 0.8:
                        await self._investigate_social_signal(signal)
                
                await asyncio.sleep(120)  # 2 minutes
                
            except Exception as e:
                logger.error(f"Social monitoring error: {e}")
                await asyncio.sleep(120)
    
    async def _fetch_presales(self) -> List[Dict]:
        """Fetch current presales from various sources"""
        presales = []
        
        try:
            # CoinLaunch API
            async with aiohttp.ClientSession() as session:
                async with session.get('https://coinlaunch.space/api/presales') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        presales.extend(data.get('presales', []))
        except Exception as e:
            logger.error(f"Error fetching presales: {e}")
        
        return presales
    
    async def _evaluate_presale(self, presale: Dict) -> bool:
        """Evaluate if presale is worth investing in"""
        # Get ML prediction
        features = self._extract_presale_features(presale)
        prediction = self.model_manager.predict_presale_success(features)
        
        # Check team, tokenomics, market conditions
        team_score = await self._analyze_team(presale.get('team', {}))
        tokenomics_score = self._analyze_tokenomics(presale.get('tokenomics', {}))
        market_score = await self._analyze_market_conditions()
        
        total_score = (
            prediction * 0.4 +
            team_score * 0.3 +
            tokenomics_score * 0.2 +
            market_score * 0.1
        )
        
        return total_score > 0.75
    
    async def _enter_presale_position(self, presale: Dict):
        """Enter presale position"""
        try:
            # Calculate position size (higher risk = smaller size)
            balance = await self.exchange_manager.get_balance()
            usdt_balance = balance.get('USDT', 0)
            
            # Presales are high risk - max 2% of portfolio
            position_size = min(
                usdt_balance * 0.02,
                self.config.get('max_presale_amount', 1000)
            )
            
            if position_size < 100:
                return
            
            # Record the presale entry
            entry = {
                'type': 'presale',
                'symbol': presale['symbol'],
                'entry_time': datetime.now(),
                'entry_price': presale['price'],
                'amount': position_size,
                'expected_listing': presale.get('listing_date'),
                'confidence': presale.get('ml_score', 0.5)
            }
            
            self.active_positions[presale['symbol']] = entry
            self.strategy_performance['presale_trades'].append(entry)
            
            logger.info(f"Entered presale position: {presale['symbol']} ${position_size}")
            
        except Exception as e:
            logger.error(f"Presale entry error: {e}")
    
    async def _get_new_uniswap_pairs(self) -> List[Dict]:
        """Get newly created Uniswap pairs"""
        # This would use Web3 to monitor PairCreated events
        # For now, return placeholder
        return []
    
    async def _analyze_dex_opportunity(self, pair: Dict) -> Optional[ListingOpportunity]:
        """Analyze new DEX pair for trading opportunity"""
        try:
            # Get token info
            token_address = pair['token_address']
            
            # Analyze contract
            contract_score = await self._analyze_contract(token_address)
            
            # Check liquidity
            liquidity_score = await self._analyze_initial_liquidity(pair)
            
            # ML prediction
            features = self._extract_dex_features(pair)
            ml_prediction = self.model_manager.predict_dex_success(features)
            
            confidence = (
                contract_score * 0.3 +
                liquidity_score * 0.3 +
                ml_prediction * 0.4
            )
            
            if confidence > 0.6:
                return ListingOpportunity(
                    token_symbol=pair['symbol'],
                    token_address=token_address,
                    discovery_time=datetime.now(),
                    opportunity_type='dex_listing',
                    confidence_score=confidence,
                    sources=[],
                    ml_prediction={'success_probability': ml_prediction}
                )
        
        except Exception as e:
            logger.error(f"DEX analysis error: {e}")
        
        return None
    
    async def _manage_positions(self):
        """Manage existing positions using ML exit signals"""
        while True:
            try:
                for symbol, position in list(self.active_positions.items()):
                    current_price = await self.market_data.get_latest_price(symbol)
                    
                    if not current_price:
                        continue
                    
                    # Get ML exit signal
                    exit_signal = await self._get_ml_exit_signal(symbol, position)
                    
                    if exit_signal['should_exit']:
                        await self._exit_position(symbol, exit_signal['reason'])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Position management error: {e}")
                await asyncio.sleep(60)
    
    async def _get_ml_exit_signal(self, symbol: str, position: Dict) -> Dict:
        """Get ML-driven exit signal"""
        try:
            # Get current market data
            current_price = await self.market_data.get_latest_price(symbol)
            
            if not current_price:
                return {'should_exit': False, 'reason': 'no_price_data'}
            
            # Calculate current P&L
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Get technical indicators
            technical_data = await self._get_technical_indicators(symbol)
            
            # ML prediction for exit timing
            features = {
                'pnl_pct': pnl_pct,
                'hold_time_hours': (datetime.now() - position['entry_time']).total_seconds() / 3600,
                'volume_ratio': technical_data.get('volume_ratio', 1.0),
                'rsi': technical_data.get('rsi', 50),
                'bb_position': technical_data.get('bb_position', 0.5)
            }
            
            exit_prob = self.model_manager.predict_exit_timing(features)
            
            # Exit conditions
            if exit_prob > 0.8:
                return {'should_exit': True, 'reason': 'ml_signal'}
            elif pnl_pct > 2.0:  # 200% gain
                return {'should_exit': True, 'reason': 'take_profit'}
            elif pnl_pct < -0.5:  # 50% loss
                return {'should_exit': True, 'reason': 'stop_loss'}
            
            return {'should_exit': False, 'reason': 'hold'}
            
        except Exception as e:
            logger.error(f"ML exit signal error: {e}")
            return {'should_exit': False, 'reason': 'error'}
    
    async def _exit_position(self, symbol: str, reason: str):
        """Exit position and update performance tracking"""
        try:
            position = self.active_positions[symbol]
            current_price = await self.market_data.get_latest_price(symbol)
            
            if not current_price:
                return
            
            # Calculate final P&L
            pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            pnl_usd = position['amount'] * pnl_pct
            
            # Update position record
            position.update({
                'exit_time': datetime.now(),
                'exit_price': current_price,
                'exit_reason': reason,
                'pnl_pct': pnl_pct,
                'pnl_usd': pnl_usd,
                'hold_time_hours': (datetime.now() - position['entry_time']).total_seconds() / 3600
            })
            
            # Update strategy performance
            self.strategy_performance['total_pnl'] += pnl_usd
            
            # Update trade list
            trade_type = position['type']
            if trade_type in self.strategy_performance:
                self.strategy_performance[f'{trade_type}_trades'].append(position)
            
            # Calculate win rate
            all_trades = (
                self.strategy_performance['presale_trades'] +
                self.strategy_performance['dex_trades'] +
                self.strategy_performance['cex_trades']
            )
            
            winning_trades = [t for t in all_trades if t.get('pnl_pct', 0) > 0]
            self.strategy_performance['win_rate'] = len(winning_trades) / len(all_trades) if all_trades else 0
            
            del self.active_positions[symbol]
            
            logger.info(f"Exited {symbol}: {pnl_pct*100:.1f}% P&L, reason: {reason}")
            
        except Exception as e:
            logger.error(f"Exit position error: {e}")
    
    def get_strategy_performance(self) -> Dict:
        """Return current strategy performance metrics"""
        return {
            'strategy_name': 'New Listing Detection',
            'total_pnl_usd': self.strategy_performance['total_pnl'],
            'win_rate': self.strategy_performance['win_rate'],
            'total_trades': len(self.strategy_performance['presale_trades']) + 
                           len(self.strategy_performance['dex_trades']) + 
                           len(self.strategy_performance['cex_trades']),
            'active_positions': len(self.active_positions),
            'performance_by_type': {
                'presale': self._calculate_type_performance('presale_trades'),
                'dex': self._calculate_type_performance('dex_trades'),
                'cex': self._calculate_type_performance('cex_trades')
            },
            'best_sources': dict(sorted(
                self.source_analyzer.source_reliability.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }
    
    def _calculate_type_performance(self, trade_type: str) -> Dict:
        """Calculate performance for specific trade type"""
        trades = self.strategy_performance[trade_type]
        
        if not trades:
            return {'pnl': 0, 'win_rate': 0, 'avg_return': 0}
        
        completed_trades = [t for t in trades if 'pnl_pct' in t]
        
        if not completed_trades:
            return {'pnl': 0, 'win_rate': 0, 'avg_return': 0}
        
        total_pnl = sum(t['pnl_usd'] for t in completed_trades)
        winning_trades = [t for t in completed_trades if t['pnl_pct'] > 0]
        avg_return = np.mean([t['pnl_pct'] for t in completed_trades])
        
        return {
            'pnl': total_pnl,
            'win_rate': len(winning_trades) / len(completed_trades),
            'avg_return': avg_return,
            'trade_count': len(completed_trades)
        }
    
    # Placeholder methods for additional functionality
    async def _fetch_cex_announcements(self) -> List[Dict]:
        return []
    
    async def _fetch_social_signals(self) -> List[SourceAlert]:
        return []
    
    async def _analyze_team(self, team: Dict) -> float:
        return 0.5
    
    def _analyze_tokenomics(self, tokenomics: Dict) -> float:
        return 0.5
    
    async def _analyze_market_conditions(self) -> float:
        return 0.5
    
    def _extract_presale_features(self, presale: Dict) -> Dict:
        return {}
    
    def _extract_dex_features(self, pair: Dict) -> Dict:
        return {}
    
    async def _analyze_contract(self, token_address: str) -> float:
        return 0.5
    
    async def _analyze_initial_liquidity(self, pair: Dict) -> float:
        return 0.5
    
    async def _get_technical_indicators(self, symbol: str) -> Dict:
        return {'volume_ratio': 1.0, 'rsi': 50, 'bb_position': 0.5}
    
    async def _handle_early_cex_listing(self, announcement: Dict):
        pass
    
    async def _handle_major_cex_announcement(self, announcement: Dict):
        pass
    
    async def _investigate_social_signal(self, signal: SourceAlert):
        pass
    
    async def _enter_dex_position(self, opportunity: ListingOpportunity):
        pass
