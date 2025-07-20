import React, { useState } from 'react';
import { Brain, TrendingUp, TrendingDown, Clock, Target } from 'lucide-react';
import { useData } from '../context/DataContext';

const Predictions = () => {
  const { predictions } = useData();
  const [selectedTimeframe, setSelectedTimeframe] = useState('all');
  const [selectedConfidence, setSelectedConfidence] = useState('all');

  // Mock predictions data
  const allPredictions = predictions.length > 0 ? predictions : [
    { id: 1, symbol: 'BTC/USDT', prediction: 'BULLISH', confidence: 87, target: 105000, currentPrice: 99234, timeframe: '4H', aiModel: 'XGBoost', signals: ['RSI Divergence', 'Volume Spike', 'Support Bounce'] },
    { id: 2, symbol: 'ETH/USDT', prediction: 'BEARISH', confidence: 72, target: 2950, currentPrice: 3234, timeframe: '1D', aiModel: 'LSTM', signals: ['Resistance Test', 'Declining Volume'] },
    { id: 3, symbol: 'SOL/USDT', prediction: 'BULLISH', confidence: 91, target: 210, currentPrice: 187.5, timeframe: '1H', aiModel: 'Ensemble', signals: ['Breakout Pattern', 'Momentum Surge', 'Whale Accumulation'] },
    { id: 4, symbol: 'LINK/USDT', prediction: 'BULLISH', confidence: 84, target: 45.2, currentPrice: 32.4, timeframe: '4H', aiModel: 'Random Forest', signals: ['Golden Cross', 'Bullish Flag'] },
    { id: 5, symbol: 'AVAX/USDT', prediction: 'BEARISH', confidence: 69, target: 38.5, currentPrice: 42.1, timeframe: '1D', aiModel: 'Neural Network', signals: ['Head & Shoulders', 'Volume Decline'] }
  ];

  const filteredPredictions = allPredictions.filter(pred => {
    if (selectedTimeframe !== 'all' && pred.timeframe !== selectedTimeframe) return false;
    if (selectedConfidence !== 'all') {
      const conf = parseInt(selectedConfidence);
      if (pred.confidence < conf) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">AI Predictions</h2>
        <div className="flex gap-4">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
          >
            <option value="all">All Timeframes</option>
            <option value="1H">1 Hour</option>
            <option value="4H">4 Hours</option>
            <option value="1D">1 Day</option>
          </select>
          <select
            value={selectedConfidence}
            onChange={(e) => setSelectedConfidence(e.target.value)}
            className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
          >
            <option value="all">All Confidence</option>
            <option value="70">70%+</option>
            <option value="80">80%+</option>
            <option value="90">90%+</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredPredictions.map((pred) => (
          <div key={pred.id} className="glass rounded-xl p-6 border border-gray-800 hover-lift">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold mb-1">{pred.symbol}</h3>
                <div className="flex items-center gap-3 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <Clock size={14} />
                    {pred.timeframe}
                  </span>
                  <span className="flex items-center gap-1">
                    <Brain size={14} />
                    {pred.aiModel}
                  </span>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-lg font-bold flex items-center gap-2 ${
                pred.prediction === 'BULLISH' 
                  ? 'bg-green-500/20 text-green-500' 
                  : 'bg-red-500/20 text-red-500'
              }`}>
                {pred.prediction === 'BULLISH' ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                {pred.prediction}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-400">Current Price</p>
                <p className="text-lg font-semibold">${pred.currentPrice.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Target Price</p>
                <p className="text-lg font-semibold flex items-center gap-1">
                  <Target size={16} />
                  ${pred.target.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Confidence</span>
                <span className="text-sm font-bold">{pred.confidence}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all ${
                    pred.confidence >= 90 ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
                    pred.confidence >= 80 ? 'bg-gradient-to-r from-blue-500 to-purple-500' :
                    pred.confidence >= 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                    'bg-gradient-to-r from-red-500 to-pink-500'
                  }`}
                  style={{ width: `${pred.confidence}%` }}
                />
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-400 mb-2">AI Signals</p>
              <div className="flex flex-wrap gap-2">
                {pred.signals.map((signal, idx) => (
                  <span key={idx} className="px-3 py-1 rounded-full text-xs bg-purple-500/20 text-purple-400 border border-purple-500/30">
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

export default Predictions;
