import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Track and analyze performance of all trading strategies"""
    
    def __init__(self, data_file: str = "data/performance_history.json"):
        self.data_file = data_file
        self.strategies = {}
        self.performance_history = defaultdict(list)
        self.active_trades = defaultdict(list)
        self.completed_trades = defaultdict(list)
        
        # Load historical data
        self._load_performance_data()
        
        # Initialize strategy tracking
        self.strategy_metrics = {
            'new_listing_detection': {
                'name': 'New Listing Detection',
                'enabled': True,
                'sub_strategies': ['presale', 'dex', 'cex'],
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'best_trade': None,
                'worst_trade': None,
                'active_positions': 0,
                'total_trades': 0
            },
            'pump_detection': {
                'name': 'Pump Detection',
                'enabled': True,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'active_positions': 0,
                'total_trades': 0
            },
            'arbitrage': {
                'name': 'Arbitrage',
                'enabled': True,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'active_positions': 0,
                'total_trades': 0
            },
            'day_trading': {
                'name': 'Day Trading',
                'enabled': True,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'active_positions': 0,
                'total_trades': 0
            },
            'swing_trading': {
                'name': 'Swing Trading',
                'enabled': True,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'active_positions': 0,
                'total_trades': 0
            }
        }
        
        # Performance analysis
        self.analysis_cache = {}
        self.last_analysis_update = None
        
    def register_strategy(self, strategy_id: str, strategy_instance):
        """Register a strategy for tracking"""
        self.strategies[strategy_id] = strategy_instance
        logger.info(f"Registered strategy: {strategy_id}")
    
    def record_trade_entry(self, strategy_id: str, trade: Dict):
        """Record a new trade entry"""
        trade_record = {
            'id': f"{strategy_id}_{trade['symbol']}_{datetime.now().timestamp()}",
            'strategy': strategy_id,
            'symbol': trade['symbol'],
            'entry_time': trade.get('entry_time', datetime.now()).isoformat(),
            'entry_price': trade['entry_price'],
            'amount': trade.get('amount', 0),
            'position_size_usd': trade.get('amount', 0) * trade['entry_price'],
            'type': trade.get('type', 'spot'),
            'confidence': trade.get('confidence', 0.5),
            'metadata': trade.get('metadata', {})
        }
        
        self.active_trades[strategy_id].append(trade_record)
        
        # Update strategy metrics
        if strategy_id in self.strategy_metrics:
            self.strategy_metrics[strategy_id]['active_positions'] += 1
        
        logger.info(f"Trade entry recorded: {trade_record['id']}")
        
        return trade_record['id']
    
    def record_trade_exit(self, strategy_id: str, trade_id: str, exit_data: Dict):
        """Record trade exit and calculate performance"""
        # Find the active trade
        active_trade = None
        for i, trade in enumerate(self.active_trades[strategy_id]):
            if trade['id'] == trade_id:
                active_trade = trade
                self.active_trades[strategy_id].pop(i)
                break
        
        if not active_trade:
            logger.error(f"Trade not found: {trade_id}")
            return
        
        # Calculate performance
        entry_price = active_trade['entry_price']
        exit_price = exit_data['exit_price']
        amount = active_trade['amount']
        
        pnl_pct = (exit_price - entry_price) / entry_price
        pnl_usd = amount * (exit_price - entry_price)
        
        # Create completed trade record
        completed_trade = {
            **active_trade,
            'exit_time': exit_data.get('exit_time', datetime.now()).isoformat(),
            'exit_price': exit_price,
            'exit_reason': exit_data.get('reason', 'manual'),
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_usd,
            'hold_time_hours': self._calculate_hold_time(
                active_trade['entry_time'], 
                exit_data.get('exit_time', datetime.now())
            ),
            'success': pnl_pct > 0
        }
        
        self.completed_trades[strategy_id].append(completed_trade)
        
        # Update strategy metrics
        self._update_strategy_metrics(strategy_id, completed_trade)
        
        # Save data
        self._save_performance_data()
        
        logger.info(
            f"Trade exit recorded: {trade_id} - "
            f"P&L: {pnl_pct*100:.2f}% (${pnl_usd:.2f})"
        )
        
        return completed_trade
    
    def _update_strategy_metrics(self, strategy_id: str, completed_trade: Dict):
        """Update strategy performance metrics"""
        if strategy_id not in self.strategy_metrics:
            return
        
        metrics = self.strategy_metrics[strategy_id]
        
        # Update P&L
        metrics['total_pnl'] += completed_trade['pnl_usd']
        
        # Update trade count
        metrics['total_trades'] += 1
        metrics['active_positions'] = max(0, metrics['active_positions'] - 1)
        
        # Update win rate
        all_trades = self.completed_trades[strategy_id]
        if all_trades:
            winning_trades = sum(1 for t in all_trades if t['success'])
            metrics['win_rate'] = winning_trades / len(all_trades)
            
            # Average return
            returns = [t['pnl_pct'] for t in all_trades]
            metrics['avg_return'] = np.mean(returns)
            
            # Best/worst trades
            if not metrics['best_trade'] or completed_trade['pnl_pct'] > metrics['best_trade']['pnl_pct']:
                metrics['best_trade'] = {
                    'symbol': completed_trade['symbol'],
                    'pnl_pct': completed_trade['pnl_pct'],
                    'pnl_usd': completed_trade['pnl_usd']
                }
            
            if not metrics['worst_trade'] or completed_trade['pnl_pct'] < metrics['worst_trade']['pnl_pct']:
                metrics['worst_trade'] = {
                    'symbol': completed_trade['symbol'],
                    'pnl_pct': completed_trade['pnl_pct'],
                    'pnl_usd': completed_trade['pnl_usd']
                }
    
    def get_strategy_performance(self, strategy_id: Optional[str] = None) -> Dict:
        """Get performance metrics for strategies"""
        if strategy_id:
            return self._get_single_strategy_performance(strategy_id)
        
        # Return all strategies
        performance = {}
        
        for sid, metrics in self.strategy_metrics.items():
            performance[sid] = self._get_single_strategy_performance(sid)
        
        # Add overall metrics
        performance['overall'] = self._calculate_overall_performance()
        
        return performance
    
    def _get_single_strategy_performance(self, strategy_id: str) -> Dict:
        """Get performance for a single strategy"""
        if strategy_id not in self.strategy_metrics:
            return {}
        
        metrics = self.strategy_metrics[strategy_id].copy()
        
        # Add time-based performance
        metrics['performance_24h'] = self._calculate_period_performance(
            strategy_id, hours=24
        )
        metrics['performance_7d'] = self._calculate_period_performance(
            strategy_id, days=7
        )
        metrics['performance_30d'] = self._calculate_period_performance(
            strategy_id, days=30
        )
        
        # Add trade distribution for new listing detection
        if strategy_id == 'new_listing_detection' and strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            if hasattr(strategy, 'get_strategy_performance'):
                detailed_perf = strategy.get_strategy_performance()
                metrics['sub_strategy_performance'] = detailed_perf.get('performance_by_type', {})
                metrics['best_sources'] = detailed_perf.get('best_sources', {})
        
        return metrics
    
    def _calculate_period_performance(self, strategy_id: str, hours: int = 0, days: int = 0) -> Dict:
        """Calculate performance for a specific time period"""
        cutoff = datetime.now() - timedelta(hours=hours, days=days)
        
        # Get trades in period
        period_trades = [
            t for t in self.completed_trades[strategy_id]
            if datetime.fromisoformat(t['exit_time']) > cutoff
        ]
        
        if not period_trades:
            return {
                'pnl': 0,
                'trades': 0,
                'win_rate': 0,
                'avg_return': 0
            }
        
        # Calculate metrics
        total_pnl = sum(t['pnl_usd'] for t in period_trades)
        winning_trades = sum(1 for t in period_trades if t['success'])
        
        return {
            'pnl': total_pnl,
            'trades': len(period_trades),
            'win_rate': winning_trades / len(period_trades),
            'avg_return': np.mean([t['pnl_pct'] for t in period_trades])
        }
    
    def _calculate_overall_performance(self) -> Dict:
        """Calculate overall performance across all strategies"""
        total_pnl = 0
        total_trades = 0
        all_returns = []
        active_positions = 0
        
        for strategy_id, metrics in self.strategy_metrics.items():
            if metrics['enabled']:
                total_pnl += metrics['total_pnl']
                total_trades += metrics['total_trades']
                active_positions += metrics['active_positions']
                
                # Collect all returns
                strategy_trades = self.completed_trades.get(strategy_id, [])
                all_returns.extend([t['pnl_pct'] for t in strategy_trades])
        
        win_rate = 0
        avg_return = 0
        
        if all_returns:
            winning_returns = sum(1 for r in all_returns if r > 0)
            win_rate = winning_returns / len(all_returns)
            avg_return = np.mean(all_returns)
        
        # Calculate Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(all_returns)
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'active_positions': active_positions,
            'overall_win_rate': win_rate,
            'overall_avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'best_strategy': self._get_best_performing_strategy(),
            'worst_strategy': self._get_worst_performing_strategy()
        }
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        # Annualized returns and volatility
        avg_return = np.mean(returns) * 365  # Daily to annual
        volatility = np.std(returns) * np.sqrt(365)
        
        if volatility == 0:
            return 0.0
        
        return (avg_return - risk_free_rate) / volatility
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        # Create cumulative P&L series
        all_trades = []
        for trades in self.completed_trades.values():
            all_trades.extend(trades)
        
        if not all_trades:
            return 0.0
        
        # Sort by exit time
        all_trades.sort(key=lambda t: t['exit_time'])
        
        # Calculate cumulative P&L
        cumulative_pnl = []
        current_pnl = 0
        
        for trade in all_trades:
            current_pnl += trade['pnl_usd']
            cumulative_pnl.append(current_pnl)
        
        if not cumulative_pnl:
            return 0.0
        
        # Calculate drawdown
        peak = cumulative_pnl[0]
        max_drawdown = 0
        
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            
            drawdown = (peak - pnl) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _get_best_performing_strategy(self) -> Dict:
        """Get the best performing strategy"""
        best_strategy = None
        best_pnl = float('-inf')
        
        for strategy_id, metrics in self.strategy_metrics.items():
            if metrics['enabled'] and metrics['total_pnl'] > best_pnl:
                best_pnl = metrics['total_pnl']
                best_strategy = {
                    'id': strategy_id,
                    'name': metrics['name'],
                    'pnl': metrics['total_pnl'],
                    'win_rate': metrics['win_rate']
                }
        
        return best_strategy
    
    def _get_worst_performing_strategy(self) -> Dict:
        """Get the worst performing strategy"""
        worst_strategy = None
        worst_pnl = float('inf')
        
        for strategy_id, metrics in self.strategy_metrics.items():
            if metrics['enabled'] and metrics['total_trades'] > 0:
                if metrics['total_pnl'] < worst_pnl:
                    worst_pnl = metrics['total_pnl']
                    worst_strategy = {
                        'id': strategy_id,
                        'name': metrics['name'],
                        'pnl': metrics['total_pnl'],
                        'win_rate': metrics['win_rate']
                    }
        
        return worst_strategy
    
    def get_trade_history(self, strategy_id: Optional[str] = None, 
                         limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        trades = []
        
        if strategy_id:
            trades = self.completed_trades.get(strategy_id, [])[-limit:]
        else:
            # Get all trades
            all_trades = []
            for strategy_trades in self.completed_trades.values():
                all_trades.extend(strategy_trades)
            
            # Sort by exit time and limit
            all_trades.sort(key=lambda t: t['exit_time'], reverse=True)
            trades = all_trades[:limit]
        
        return trades
    
    def get_active_positions(self, strategy_id: Optional[str] = None) -> List[Dict]:
        """Get current active positions"""
        if strategy_id:
            return self.active_trades.get(strategy_id, [])
        
        # Return all active trades
        all_active = []
        for trades in self.active_trades.values():
            all_active.extend(trades)
        
        return all_active
    
    def analyze_performance_trends(self) -> Dict:
        """Analyze performance trends and patterns"""
        # Cache analysis for efficiency
        if (self.last_analysis_update and 
            datetime.now() - self.last_analysis_update < timedelta(hours=1)):
            return self.analysis_cache
        
        analysis = {
            'daily_performance': self._analyze_daily_performance(),
            'hourly_patterns': self._analyze_hourly_patterns(),
            'strategy_correlations': self._analyze_strategy_correlations(),
            'market_condition_performance': self._analyze_market_conditions(),
            'recommendations': self._generate_recommendations()
        }
        
        self.analysis_cache = analysis
        self.last_analysis_update = datetime.now()
        
        return analysis
    
    def _analyze_daily_performance(self) -> Dict:
        """Analyze daily performance patterns"""
        daily_pnl = defaultdict(float)
        daily_trades = defaultdict(int)
        
        for trades in self.completed_trades.values():
            for trade in trades:
                date = datetime.fromisoformat(trade['exit_time']).date()
                daily_pnl[date] += trade['pnl_usd']
                daily_trades[date] += 1
        
        # Last 30 days
        last_30_days = sorted(daily_pnl.keys())[-30:]
        
        return {
            'daily_pnl': {str(date): daily_pnl[date] for date in last_30_days},
            'daily_trades': {str(date): daily_trades[date] for date in last_30_days},
            'best_day': max(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None,
            'worst_day': min(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None
        }
    
    def _analyze_hourly_patterns(self) -> Dict:
        """Analyze performance by hour of day"""
        hourly_stats = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'win_rate': 0})
        
        for trades in self.completed_trades.values():
            for trade in trades:
                hour = datetime.fromisoformat(trade['exit_time']).hour
                hourly_stats[hour]['trades'] += 1
                hourly_stats[hour]['pnl'] += trade['pnl_usd']
                if trade['success']:
                    hourly_stats[hour]['win_rate'] += 1
        
        # Calculate win rates
        for hour, stats in hourly_stats.items():
            if stats['trades'] > 0:
                stats['win_rate'] = stats['win_rate'] / stats['trades']
        
        return dict(hourly_stats)
    
    def _analyze_strategy_correlations(self) -> Dict:
        """Analyze correlations between strategies"""
        # Placeholder for correlation analysis
        return {
            'correlation_matrix': {},
            'diversification_score': 0.7
        }
    
    def _analyze_market_conditions(self) -> Dict:
        """Analyze performance under different market conditions"""
        # Placeholder for market condition analysis
        return {
            'bull_market_performance': {'pnl': 0, 'win_rate': 0},
            'bear_market_performance': {'pnl': 0, 'win_rate': 0},
            'sideways_market_performance': {'pnl': 0, 'win_rate': 0}
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance-based recommendations"""
        recommendations = []
        
        # Check strategy performance
        for strategy_id, metrics in self.strategy_metrics.items():
            if metrics['enabled'] and metrics['total_trades'] > 10:
                if metrics['win_rate'] < 0.3:
                    recommendations.append(
                        f"Consider disabling {metrics['name']} - "
                        f"Win rate: {metrics['win_rate']*100:.1f}%"
                    )
                elif metrics['win_rate'] > 0.7:
                    recommendations.append(
                        f"Strong performance from {metrics['name']} - "
                        f"Consider increasing allocation"
                    )
        
        # Check overall metrics
        overall = self._calculate_overall_performance()
        
        if overall['max_drawdown'] > 0.2:
            recommendations.append(
                "High drawdown detected - Consider implementing tighter risk controls"
            )
        
        if overall['sharpe_ratio'] < 0.5:
            recommendations.append(
                "Low risk-adjusted returns - Review strategy parameters"
            )
        
        return recommendations
    
    def _calculate_hold_time(self, entry_time: str, exit_time) -> float:
        """Calculate hold time in hours"""
        entry = datetime.fromisoformat(entry_time)
        exit = exit_time if isinstance(exit_time, datetime) else datetime.fromisoformat(exit_time)
        
        return (exit - entry).total_seconds() / 3600
    
    def _save_performance_data(self):
        """Save performance data to file"""
        try:
            data = {
                'strategy_metrics': self.strategy_metrics,
                'completed_trades': {
                    k: v for k, v in self.completed_trades.items()
                },
                'performance_history': dict(self.performance_history),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    def _load_performance_data(self):
        """Load historical performance data"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            # Restore data
            self.strategy_metrics.update(data.get('strategy_metrics', {}))
            
            # Convert lists back to defaultdict
            for strategy_id, trades in data.get('completed_trades', {}).items():
                self.completed_trades[strategy_id] = trades
            
            for key, values in data.get('performance_history', {}).items():
                self.performance_history[key] = values
                
            logger.info("Performance data loaded successfully")
            
        except FileNotFoundError:
            logger.info("No historical performance data found")
        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
    
    def export_performance_report(self, format: str = 'json') -> str:
        """Export comprehensive performance report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'overall_performance': self._calculate_overall_performance(),
            'strategy_performance': self.get_strategy_performance(),
            'trade_history': self.get_trade_history(limit=1000),
            'analysis': self.analyze_performance_trends()
        }
        
        if format == 'json':
            return json.dumps(report, indent=2)
        
        # Add other formats as needed
        return json.dumps(report, indent=2)
