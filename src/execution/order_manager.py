import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from enum import Enum

from ..core.exchange_manager import ExchangeManager
from ..core.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderManager:
    """Manages order execution and tracking"""
    
    def __init__(self, exchange_manager: ExchangeManager, risk_manager: RiskManager):
        self.exchange_manager = exchange_manager
        self.risk_manager = risk_manager
        self.active_orders = {}
        self.order_history = []
        
    async def place_order(self, strategy: str, exchange: str, symbol: str, 
                         side: str, amount: float, order_type: str = 'market',
                         price: Optional[float] = None) -> Optional[Dict]:
        """Place order with risk checks"""
        
        # Get current price if not provided
        if not price and order_type == 'market':
            price = await self.exchange_manager.market_data.get_latest_price(symbol)
        
        if not price:
            logger.error(f"Cannot get price for {symbol}")
            return None
        
        # Get balance
        balance = await self.exchange_manager.get_balance(exchange)
        
        # Risk checks
        risk_check = await self.risk_manager.check_pre_trade(
            symbol, side, amount, price, balance
        )
        
        if not risk_check['approved']:
            logger.warning(f"Order rejected by risk manager: {risk_check['reason']}")
            return None
        
        # Use recommended size if available
        if risk_check.get('recommended_size'):
            amount = min(amount, risk_check['recommended_size'])
        
        # Execute order
        try:
            if order_type == 'market':
                order = await self.exchange_manager.execute_market_order(
                    exchange, symbol, side, amount
                )
            else:
                order = await self.exchange_manager.execute_limit_order(
                    exchange, symbol, side, amount, price
                )
            
            if order:
                # Track order
                self.active_orders[order['id']] = {
                    'strategy': strategy,
                    'exchange': exchange,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': OrderStatus.PENDING,
                    'timestamp': datetime.now(),
                    'order_data': order
                }
                
                # Update risk manager
                self.risk_manager.update_position(
                    symbol, side, amount, price, order['id']
                )
                
                # Start monitoring
                asyncio.create_task(self.monitor_order(order['id']))
                
                logger.info(f"Order placed: {symbol} {side} {amount} @ {price} [{strategy}]")
                
            return order
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order"""
        if order_id not in self.active_orders:
            return False
        
        order_info = self.active_orders[order_id]
        
        try:
            success = await self.exchange_manager.cancel_order(
                order_info['exchange'],
                order_id,
                order_info['symbol']
            )
            
            if success:
                order_info['status'] = OrderStatus.CANCELLED
                self.order_history.append(order_info)
                del self.active_orders[order_id]
                
            return success
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return False
    
    async def monitor_order(self, order_id: str):
        """Monitor order status"""
        max_checks = 60  # Check for 1 minute max
        
        for _ in range(max_checks):
            if order_id not in self.active_orders:
                break
            
            order_info = self.active_orders[order_id]
            
            try:
                # Check order status
                exchange = self.exchange_manager.exchanges[order_info['exchange']]
                order_status = await exchange.fetch_order(order_id, order_info['symbol'])
                
                if order_status['status'] == 'closed':
                    order_info['status'] = OrderStatus.FILLED
                    order_info['filled_amount'] = order_status['filled']
                    order_info['filled_price'] = order_status['average']
                    
                    # Move to history
                    self.order_history.append(order_info)
                    del self.active_orders[order_id]
                    
                    logger.info(f"Order filled: {order_id}")
                    break
                    
                elif order_status['status'] == 'canceled':
                    order_info['status'] = OrderStatus.CANCELLED
                    self.order_history.append(order_info)
                    del self.active_orders[order_id]
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Order monitoring error: {e}")
                await asyncio.sleep(5)
    
    def get_active_orders(self) -> Dict:
        """Get all active orders"""
        return self.active_orders
    
    def get_order_stats(self) -> Dict:
        """Get order execution statistics"""
        total_orders = len(self.order_history)
        
        if total_orders == 0:
            return {
                'total_orders': 0,
                'filled_orders': 0,
                'cancelled_orders': 0,
                'fill_rate': 0,
                'avg_execution_time': 0
            }
        
        filled = sum(1 for o in self.order_history if o['status'] == OrderStatus.FILLED)
        cancelled = sum(1 for o in self.order_history if o['status'] == OrderStatus.CANCELLED)
        
        execution_times = []
        for order in self.order_history:
            if order['status'] == OrderStatus.FILLED and 'filled_time' in order:
                exec_time = (order['filled_time'] - order['timestamp']).seconds
                execution_times.append(exec_time)
        
        return {
            'total_orders': total_orders,
            'filled_orders': filled,
            'cancelled_orders': cancelled,
            'fill_rate': filled / total_orders,
            'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0
        }
