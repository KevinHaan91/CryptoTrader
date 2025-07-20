import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const RecentTrades = ({ trades = [] }) => {
  // Mock data if no trades provided
  const displayTrades = trades.length > 0 ? trades : [
    { id: 1, symbol: 'BTC/USDT', side: 'BUY', price: 98234, amount: 0.1, profit: 234.50, time: '2 min ago' },
    { id: 2, symbol: 'ETH/USDT', side: 'SELL', price: 3234, amount: 0.5, profit: -45.20, time: '15 min ago' },
    { id: 3, symbol: 'SOL/USDT', side: 'BUY', price: 187.5, amount: 10, profit: 125.30, time: '1 hour ago' },
    { id: 4, symbol: 'MATIC/USDT', side: 'SELL', price: 2.15, amount: 500, profit: 78.90, time: '2 hours ago' },
    { id: 5, symbol: 'LINK/USDT', side: 'BUY', price: 32.40, amount: 25, profit: -23.45, time: '3 hours ago' }
  ];

  return (
    <div className="space-y-3">
      {displayTrades.slice(0, 5).map((trade) => (
        <div key={trade.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${trade.side === 'BUY' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
              {trade.side === 'BUY' ? 
                <ArrowUpRight size={16} className="text-green-500" /> : 
                <ArrowDownRight size={16} className="text-red-500" />
              }
            </div>
            <div>
              <p className="font-medium text-sm">{trade.symbol}</p>
              <p className="text-xs text-gray-400">{trade.time}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm">${trade.price.toLocaleString()}</p>
            <p className={`text-xs font-medium ${trade.profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {trade.profit >= 0 ? '+' : ''}${Math.abs(trade.profit).toFixed(2)}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RecentTrades;
