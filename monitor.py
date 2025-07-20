#!/usr/bin/env python3
"""
Real-time monitoring dashboard for Crypto Trading Bot
Displays positions, P&L, and performance metrics
"""

import asyncio
import curses
import sys
from datetime import datetime
from typing import Dict, List
import json

# Add parent directory to path
sys.path.append('.')

from src.core.exchange_manager import ExchangeManager
from src.core.risk_manager import RiskManager
from config.settings import EXCHANGES

class TradingDashboard:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.exchange_manager = None
        self.risk_manager = RiskManager()
        self.running = True
        
        # Dashboard data
        self.balances = {}
        self.positions = {}
        self.recent_trades = []
        self.performance = {
            'daily_pnl': 0,
            'total_pnl': 0,
            'win_rate': 0,
            'active_strategies': []
        }
        
        # Setup colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Profit
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Loss
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Info
        
    async def initialize(self):
        """Initialize connections"""
        self.exchange_manager = ExchangeManager()
        await self.exchange_manager.initialize()
        
    async def update_data(self):
        """Update dashboard data"""
        while self.running:
            try:
                # Update balances
                for exchange in self.exchange_manager.exchanges:
                    balance = await self.exchange_manager.get_balance(exchange)
                    self.balances[exchange] = balance
                
                # Update positions from risk manager
                self.positions = self.risk_manager.get_risk_metrics()
                
                # Update performance metrics
                # This would normally query the database
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                # Log error but continue
                pass
    
    def draw_header(self):
        """Draw dashboard header"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Title
        title = "🚀 Crypto Trading Bot Dashboard 🚀"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stdscr.addstr(1, width - len(current_time) - 1, current_time)
        
        # Separator
        self.stdscr.addstr(2, 0, "─" * width)
    
    def draw_balances(self, start_row: int) -> int:
        """Draw balance section"""
        row = start_row
        self.stdscr.addstr(row, 0, "💰 BALANCES", curses.A_BOLD)
        row += 1
        
        total_usd = 0
        for exchange, balances in self.balances.items():
            self.stdscr.addstr(row, 2, f"{exchange.upper()}:")
            row += 1
            
            for asset, amount in balances.items():
                if amount > 0.001:  # Hide dust
                    # Estimate USD value (would need price data)
                    usd_value = amount  # Placeholder
                    total_usd += usd_value
                    
                    self.stdscr.addstr(row, 4, f"{asset}: {amount:.4f} (${usd_value:.2f})")
                    row += 1
        
        self.stdscr.addstr(row, 2, f"Total USD Value: ${total_usd:.2f}", 
                          curses.color_pair(1) if total_usd > 0 else curses.color_pair(2))
        row += 2
        
        return row
    
    def draw_positions(self, start_row: int) -> int:
        """Draw open positions"""
        row = start_row
        positions = self.positions.get('position_details', {})
        
        self.stdscr.addstr(row, 0, f"📊 OPEN POSITIONS ({len(positions)})", curses.A_BOLD)
        row += 1
        
        if not positions:
            self.stdscr.addstr(row, 2, "No open positions")
            row += 1
        else:
            # Header
            self.stdscr.addstr(row, 2, "Symbol    Side    Entry      Current    P&L%     Value")
            row += 1
            
            for symbol, pos in positions.items():
                # Get current price (placeholder)
                current_price = pos['avg_price'] * 1.01  # Placeholder
                
                if pos['side'] == 'buy':
                    pnl_pct = (current_price - pos['avg_price']) / pos['avg_price'] * 100
                else:
                    pnl_pct = (pos['avg_price'] - current_price) / pos['avg_price'] * 100
                
                color = curses.color_pair(1) if pnl_pct > 0 else curses.color_pair(2)
                
                line = f"{symbol:<10} {pos['side']:<6} {pos['avg_price']:<10.4f} {current_price:<10.4f} {pnl_pct:>6.2f}% ${pos['value']:>10.2f}"
                self.stdscr.addstr(row, 2, line, color)
                row += 1
        
        row += 1
        return row
    
    def draw_performance(self, start_row: int) -> int:
        """Draw performance metrics"""
        row = start_row
        metrics = self.positions
        
        self.stdscr.addstr(row, 0, "📈 PERFORMANCE", curses.A_BOLD)
        row += 1
        
        # Daily P&L
        daily_pnl = metrics.get('daily_pnl', 0)
        color = curses.color_pair(1) if daily_pnl >= 0 else curses.color_pair(2)
        self.stdscr.addstr(row, 2, f"Daily P&L: ${daily_pnl:.2f}", color)
        row += 1
        
        # Max Drawdown
        max_dd = metrics.get('max_drawdown', 0) * 100
        color = curses.color_pair(3) if max_dd > 5 else curses.color_pair(4)
        self.stdscr.addstr(row, 2, f"Max Drawdown: {max_dd:.2f}%", color)
        row += 1
        
        # Trading Status
        trading_enabled = metrics.get('trading_enabled', True)
        status = "ACTIVE" if trading_enabled else "STOPPED"
        color = curses.color_pair(1) if trading_enabled else curses.color_pair(2)
        self.stdscr.addstr(row, 2, f"Trading Status: {status}", color)
        row += 1
        
        # Risk Metrics
        var_95 = metrics.get('var_95', 0)
        self.stdscr.addstr(row, 2, f"Value at Risk (95%): ${var_95:.2f}")
        row += 1
        
        row += 1
        return row
    
    def draw_recent_trades(self, start_row: int, max_height: int) -> int:
        """Draw recent trades"""
        row = start_row
        self.stdscr.addstr(row, 0, "💹 RECENT TRADES", curses.A_BOLD)
        row += 1
        
        if not self.recent_trades:
            self.stdscr.addstr(row, 2, "No recent trades")
            row += 1
        else:
            # Show last 5 trades
            for trade in self.recent_trades[-5:]:
                if row >= max_height - 2:
                    break
                    
                trade_str = f"{trade['time']} {trade['symbol']} {trade['side']} {trade['amount']} @ {trade['price']}"
                color = curses.color_pair(1) if trade['pnl'] > 0 else curses.color_pair(2)
                self.stdscr.addstr(row, 2, trade_str, color)
                row += 1
        
        return row
    
    def draw_footer(self, height: int):
        """Draw footer with commands"""
        footer = "Commands: [Q]uit | [R]efresh | [P]ause Trading | [S]tats"
        self.stdscr.addstr(height - 1, 0, footer, curses.A_REVERSE)
    
    async def run(self):
        """Main dashboard loop"""
        # Start data updates
        asyncio.create_task(self.update_data())
        
        # Configure screen
        self.stdscr.nodelay(True)
        curses.curs_set(0)  # Hide cursor
        
        while self.running:
            try:
                height, width = self.stdscr.getmaxyx()
                
                # Draw sections
                self.draw_header()
                row = 4
                
                row = self.draw_balances(row)
                row = self.draw_positions(row)
                row = self.draw_performance(row)
                self.draw_recent_trades(row, height - 2)
                
                self.draw_footer(height)
                
                # Refresh screen
                self.stdscr.refresh()
                
                # Handle input
                key = self.stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    self.running = False
                elif key == ord('r') or key == ord('R'):
                    continue  # Force refresh
                elif key == ord('p') or key == ord('P'):
                    # Toggle trading
                    self.risk_manager.trading_enabled = not self.risk_manager.trading_enabled
                
                await asyncio.sleep(0.1)
                
            except curses.error:
                # Terminal too small, just wait
                await asyncio.sleep(1)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.exchange_manager:
            self.exchange_manager.close()

async def run_dashboard(stdscr):
    """Run the dashboard"""
    dashboard = TradingDashboard(stdscr)
    
    try:
        await dashboard.initialize()
        await dashboard.run()
    finally:
        await dashboard.cleanup()

def main():
    """Entry point"""
    try:
        # Check if we can connect
        if not any(EXCHANGES[ex].get('api_key') for ex in EXCHANGES):
            print("❌ No API keys configured. Run setup.py first.")
            return
        
        # Run dashboard
        curses.wrapper(lambda stdscr: asyncio.run(run_dashboard(stdscr)))
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the trading bot is running: docker-compose up -d")

if __name__ == "__main__":
    main()
