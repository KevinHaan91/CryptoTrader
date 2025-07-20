import React, { useState } from 'react';
import { TrendingUp, ChevronDown, BarChart3, Maximize2 } from 'lucide-react';
import PositionsTable from './PositionsTable';
import { useData } from '../context/DataContext';

const TradingView = () => {
  const { positions } = useData();
  const [selectedPair, setSelectedPair] = useState('BTC/USDT');
  const [selectedExchange, setSelectedExchange] = useState('Binance');
  const [selectedStrategy, setSelectedStrategy] = useState('all');
  const [orderType, setOrderType] = useState('market');
  const [orderSide, setOrderSide] = useState('buy');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');

  const pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'LINK/USDT', 'AVAX/USDT', 'MATIC/USDT'];
  const exchanges = ['Binance', 'KuCoin', 'Bybit', 'Gate.io'];
  const strategies = [
    { value: 'all', label: 'All Strategies' },
    { value: 'scalping', label: 'Scalping' },
    { value: 'arbitrage', label: 'Arbitrage' },
    { value: 'daytrading', label: 'Day Trading' },
    { value: 'swing', label: 'Swing Trading' }
  ];

  const handlePlaceOrder = () => {
    console.log('Placing order:', { selectedPair, selectedExchange, orderType, orderSide, amount, price });
    // API call to place order
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Trading Terminal</h2>
        <div className="flex gap-4">
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
          >
            {strategies.map(strategy => (
              <option key={strategy.value} value={strategy.value}>{strategy.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trading Chart - Takes 2 columns */}
        <div className="lg:col-span-2 glass rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <select
                value={selectedPair}
                onChange={(e) => setSelectedPair(e.target.value)}
                className="px-3 py-1.5 rounded-lg glass border border-gray-700 bg-transparent"
              >
                {pairs.map(pair => (
                  <option key={pair} value={pair}>{pair}</option>
                ))}
              </select>
              <select
                value={selectedExchange}
                onChange={(e) => setSelectedExchange(e.target.value)}
                className="px-3 py-1.5 rounded-lg glass border border-gray-700 bg-transparent"
              >
                {exchanges.map(exchange => (
                  <option key={exchange} value={exchange}>{exchange}</option>
                ))}
              </select>
            </div>
            <button className="p-2 rounded-lg hover:bg-gray-800 transition-colors">
              <Maximize2 size={20} />
            </button>
          </div>

          {/* Chart placeholder */}
          <div className="h-96 rounded-lg bg-gray-900/50 flex items-center justify-center">
            <div className="text-center">
              <BarChart3 size={48} className="mx-auto mb-4 text-gray-600" />
              <p className="text-gray-500">TradingView Chart Integration</p>
              <p className="text-sm text-gray-600 mt-2">Real-time charts will be displayed here</p>
            </div>
          </div>
        </div>

        {/* Order Form - Takes 1 column */}
        <div className="glass rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-bold mb-4">Place Order</h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setOrderSide('buy')}
                className={`py-2 rounded-lg font-medium transition-colors ${
                  orderSide === 'buy' 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Buy
              </button>
              <button
                onClick={() => setOrderSide('sell')}
                className={`py-2 rounded-lg font-medium transition-colors ${
                  orderSide === 'sell' 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Sell
              </button>
            </div>

            <div>
              <label className="text-sm text-gray-400 mb-1 block">Order Type</label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value)}
                className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
              >
                <option value="market">Market</option>
                <option value="limit">Limit</option>
                <option value="stop">Stop Loss</option>
                <option value="take-profit">Take Profit</option>
              </select>
            </div>

            <div>
              <label className="text-sm text-gray-400 mb-1 block">Amount</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
              />
            </div>

            {orderType !== 'market' && (
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Price</label>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                />
              </div>
            )}

            <div className="pt-2">
              <button
                onClick={handlePlaceOrder}
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  orderSide === 'buy'
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700'
                    : 'bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700'
                } text-white`}
              >
                {orderSide === 'buy' ? 'Buy' : 'Sell'} {selectedPair.split('/')[0]}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Active Positions */}
      <div className="glass rounded-xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-4">Active Positions</h3>
        <PositionsTable positions={positions} />
      </div>
    </div>
  );
};

export default TradingView;
