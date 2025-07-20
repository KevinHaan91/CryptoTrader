import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from config.settings import RISK_MANAGEMENT, TRADING

logger = logging.getLogger(__name__)

class RiskManager:
    """Portfolio risk management and position sizing"""
    
    def __init__(self):
        self.positions = {}
        self.daily_pnl = 0
        self.max_drawdown = 0
        self.peak_balance = 0
        self.trading_enabled = True
        self.position_correlations = {}
        
    async def check_pre_trade(self, symbol: str, side: str, 
                            amount: float, price: float, 
                            balance: Dict[str, float]) -> Dict:
        """Pre-trade risk checks"""
        
        # Circuit breaker check
        if not self.trading_enabled:
            return {'approved': False, 'reason': 'Trading disabled by circuit breaker'}
        
        # Daily loss limit check
        if self.daily_pnl < -RISK_MANAGEMENT['max_daily_loss'] * self.peak_balance:
            self.trading_enabled = False
            return {'approved': False, 'reason': 'Daily loss limit reached'}
        
        # Position size checks
        position_value = amount * price
        total_balance = sum(balance.values())
        
        # Max position size
        if position_value > total_balance * TRADING['max_position_size']:
            return {'approved': False, 'reason': 'Position too large'}
        
        # Min position size
        if position_value < TRADING['min_trade_amount_usd']:
            return {'approved': False, 'reason': 'Position too small'}
        
        # Max open positions
        if len(self.positions) >= TRADING['max_open_positions']:
            return {'approved': False, 'reason': 'Too many open positions'}
        
        # Correlation check
        correlation_risk = await self.check_correlation_risk(symbol)
        if correlation_risk > RISK_MANAGEMENT['correlation_limit']:
            return {'approved': False, 'reason': 'High correlation with existing positions'}
        
        # Calculate position size based on risk
        recommended_size = self.calculate_position_size(
            balance=total_balance,
            price=price,
            stop_loss_pct=TRADING['stop_loss_percent']
        )
        
        return {
            'approved': True,
            'recommended_size': recommended_size,
            'risk_score': self.calculate_risk_score(symbol, amount * price, total_balance)
        }
    
    def calculate_position_size(self, balance: float, price: float, 
                              stop_loss_pct: float) -> float:
        """Kelly Criterion-based position sizing"""
        
        # Get historical win rate and profit ratio
        win_rate = self.get_historical_win_rate()
        avg_win = self.get_average_win()
        avg_loss = self.get_average_loss()
        
        if avg_loss == 0 or win_rate == 0:
            # Default conservative sizing
            return balance * TRADING['risk_per_trade'] / stop_loss_pct
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = profit/loss ratio
        profit_ratio = avg_win / abs(avg_loss)
        kelly_fraction = (win_rate * profit_ratio - (1 - win_rate)) / profit_ratio
        
        # Use fractional Kelly for safety (25% of full Kelly)
        kelly_fraction = max(0, min(kelly_fraction * 0.25, 0.25))
        
        position_value = balance * kelly_fraction
        position_size = position_value / price
        
        return position_size
    
    async def check_correlation_risk(self, symbol: str) -> float:
        """Check correlation with existing positions"""
        if not self.positions:
            return 0.0
        
        # Get correlation data from cache or calculate
        max_correlation = 0.0
        
        for existing_symbol in self.positions:
            correlation = self.position_correlations.get(
                f"{symbol}:{existing_symbol}", 0.5  # Default moderate correlation
            )
            max_correlation = max(max_correlation, abs(correlation))
        
        return max_correlation
    
    def calculate_risk_score(self, symbol: str, position_value: float, 
                           total_balance: float) -> float:
        """Calculate overall risk score for position"""
        
        # Position size risk (0-1)
        size_risk = position_value / (total_balance * TRADING['max_position_size'])
        
        # Concentration risk (0-1)
        total_exposure = sum(pos['value'] for pos in self.positions.values())
        concentration_risk = (total_exposure + position_value) / total_balance
        
        # Volatility risk (0-1) - would need historical data
        volatility_risk = 0.5  # Placeholder
        
        # Weighted risk score
        risk_score = (
            size_risk * 0.3 +
            concentration_risk * 0.4 +
            volatility_risk * 0.3
        )
        
        return min(1.0, risk_score)
    
    def update_position(self, symbol: str, side: str, amount: float, 
                       price: float, order_id: str):
        """Update position tracking"""
        
        if symbol in self.positions:
            # Update existing position (averaging)
            pos = self.positions[symbol]
            total_amount = pos['amount'] + amount
            avg_price = (pos['amount'] * pos['avg_price'] + amount * price) / total_amount
            
            self.positions[symbol] = {
                'side': side,
                'amount': total_amount,
                'avg_price': avg_price,
                'value': total_amount * price,
                'entry_time': pos['entry_time'],
                'orders': pos['orders'] + [order_id]
            }
        else:
            # New position
            self.positions[symbol] = {
                'side': side,
                'amount': amount,
                'avg_price': price,
                'value': amount * price,
                'entry_time': datetime.now(),
                'orders': [order_id]
            }
    
    def close_position(self, symbol: str, exit_price: float) -> float:
        """Close position and calculate P&L"""
        
        if symbol not in self.positions:
            return 0.0
        
        pos = self.positions[symbol]
        
        # Calculate P&L
        if pos['side'] == 'buy':
            pnl = (exit_price - pos['avg_price']) * pos['amount']
        else:
            pnl = (pos['avg_price'] - exit_price) * pos['amount']
        
        # Update daily P&L
        self.daily_pnl += pnl
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Position closed: {symbol} P&L: ${pnl:.2f}")
        
        return pnl
    
    def calculate_portfolio_var(self, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk for current portfolio"""
        
        if not self.positions:
            return 0.0
        
        # Simple VaR calculation - would need historical returns
        portfolio_value = sum(pos['value'] for pos in self.positions.values())
        
        # Assume normal distribution with 2% daily volatility
        daily_volatility = 0.02
        z_score = 1.645 if confidence_level == 0.95 else 2.326
        
        var = portfolio_value * daily_volatility * z_score
        
        return var
    
    def update_drawdown(self, current_balance: float):
        """Update maximum drawdown tracking"""
        
        # Update peak
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Calculate drawdown
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - current_balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, drawdown)
            
            # Circuit breaker check
            if drawdown > RISK_MANAGEMENT['max_drawdown']:
                self.trading_enabled = False
                logger.warning(f"Max drawdown reached: {drawdown:.2%}")
            elif drawdown > RISK_MANAGEMENT['circuit_breaker_threshold']:
                self.trading_enabled = False
                logger.warning(f"Circuit breaker triggered: {drawdown:.2%}")
    
    def reset_daily_limits(self):
        """Reset daily risk limits (call at start of trading day)"""
        self.daily_pnl = 0
        self.trading_enabled = True
        logger.info("Daily risk limits reset")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        total_exposure = sum(pos['value'] for pos in self.positions.values())
        
        return {
            'open_positions': len(self.positions),
            'total_exposure': total_exposure,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'current_drawdown': (self.peak_balance - total_exposure) / self.peak_balance if self.peak_balance > 0 else 0,
            'trading_enabled': self.trading_enabled,
            'var_95': self.calculate_portfolio_var(0.95),
            'position_details': self.positions
        }
    
    def get_historical_win_rate(self) -> float:
        """Get win rate from historical trades"""
        # This would query historical trade database
        # For now, return conservative estimate
        return 0.55
    
    def get_average_win(self) -> float:
        """Get average winning trade size"""
        # This would query historical trade database
        # For now, return conservative estimate
        return 100.0
    
    def get_average_loss(self) -> float:
        """Get average losing trade size"""
        # This would query historical trade database
        # For now, return conservative estimate
        return -80.0
