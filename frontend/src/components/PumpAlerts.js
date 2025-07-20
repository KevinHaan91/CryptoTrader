import React, { useState } from 'react';
import { AlertTriangle, Zap, TrendingUp, Clock, ExternalLink } from 'lucide-react';
import { useData } from '../context/DataContext';

const PumpAlerts = () => {
  const { pumpAlerts } = useData();
  const [filter, setFilter] = useState('all');

  // Mock pump alerts data
  const allAlerts = pumpAlerts.length > 0 ? pumpAlerts : [
    { id: 1, symbol: 'PEPE', exchange: 'Binance', change: 145, volume: '850M', volumeChange: 2400, confidence: 92, time: new Date(Date.now() - 2 * 60 * 1000), source: 'Twitter', signals: ['Volume Spike', 'Social Buzz', 'Whale Activity'] },
    { id: 2, symbol: 'SHIB', exchange: 'KuCoin', change: 87, volume: '1.2B', volumeChange: 1850, confidence: 78, time: new Date(Date.now() - 15 * 60 * 1000), source: 'Telegram', signals: ['Coordinated Buying', 'Influencer Mentions'] },
    { id: 3, symbol: 'FLOKI', exchange: 'Bybit', change: 234, volume: '450M', volumeChange: 3200, confidence: 95, time: new Date(Date.now() - 30 * 60 * 1000), source: 'Discord', signals: ['Exchange Listing', 'Volume Explosion', 'Price Breakout'] },
    { id: 4, symbol: 'BONK', exchange: 'Binance', change: 65, volume: '320M', volumeChange: 890, confidence: 68, time: new Date(Date.now() - 1 * 60 * 60 * 1000), source: 'Reddit', signals: ['Gradual Accumulation', 'Community Growth'] },
    { id: 5, symbol: 'DOGE', exchange: 'Coinbase', change: 42, volume: '2.5B', volumeChange: 450, confidence: 55, time: new Date(Date.now() - 2 * 60 * 60 * 1000), source: 'Twitter', signals: ['Elon Tweet', 'Market Momentum'] }
  ];

  const filteredAlerts = allAlerts.filter(alert => {
    if (filter === 'high' && alert.confidence < 80) return false;
    if (filter === 'recent' && (Date.now() - alert.time) > 60 * 60 * 1000) return false;
    return true;
  });

  const getTimeAgo = (time) => {
    const minutes = Math.floor((Date.now() - time) / 60000);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return 'from-green-500 to-emerald-500';
    if (confidence >= 80) return 'from-blue-500 to-purple-500';
    if (confidence >= 70) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-pink-500';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Pump Detection Alerts</h2>
        <div className="flex gap-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
          >
            <option value="all">All Alerts</option>
            <option value="high">High Confidence (80%+)</option>
            <option value="recent">Last Hour</option>
          </select>
        </div>
      </div>

      <div className="glass rounded-xl p-6 border border-yellow-700/50 bg-gradient-to-br from-yellow-900/10 to-orange-900/10">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="text-yellow-500" />
          <h3 className="text-lg font-bold text-yellow-500">Pump Detection Active</h3>
        </div>
        <p className="text-sm text-gray-400">
          AI monitoring social media, order books, and on-chain data for potential pump & dump schemes.
          Trade with caution - high volatility expected.
        </p>
      </div>

      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div key={alert.id} className="glass rounded-xl p-6 border border-gray-800 hover-lift">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg bg-gradient-to-br ${getConfidenceColor(alert.confidence)} bg-opacity-20`}>
                  <Zap size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-2xl font-bold">{alert.symbol}</h3>
                    <span className="text-sm text-gray-400">{alert.exchange}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {getTimeAgo(alert.time)}
                    </span>
                    <span>Source: {alert.source}</span>
                  </div>
                </div>
              </div>
              <button className="p-2 rounded-lg hover:bg-gray-800 transition-colors">
                <ExternalLink size={20} />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-400">Price Change</p>
                <p className="text-2xl font-bold text-green-500">+{alert.change}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Volume</p>
                <p className="text-2xl font-bold">${alert.volume}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Volume Change</p>
                <p className="text-2xl font-bold text-blue-500">+{alert.volumeChange}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Confidence</p>
                <p className="text-2xl font-bold">{alert.confidence}%</p>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-400 mb-2">Detection Signals</p>
              <div className="flex flex-wrap gap-2">
                {alert.signals.map((signal, idx) => (
                  <span key={idx} className="px-3 py-1 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/30">
                    {signal}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PumpAlerts;
