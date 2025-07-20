import React, { useState } from 'react';
import { Wallet, ExternalLink, Copy, Check } from 'lucide-react';
import { useData } from '../context/DataContext';

const Wallets = () => {
  const { wallets } = useData();
  const [copiedAddress, setCopiedAddress] = useState(null);

  // Mock wallet data
  const walletData = Object.keys(wallets).length > 0 ? wallets : {
    'Binance': {
      totalValue: 25234.50,
      assets: [
        { symbol: 'BTC', balance: 0.5234, value: 51234.50, price: 97892 },
        { symbol: 'ETH', balance: 2.145, value: 6945.30, price: 3238 },
        { symbol: 'USDT', balance: 10000, value: 10000, price: 1 }
      ],
      address: '0x742d35Cc6634C0532925a3b844Bc9e7595f2bd8e'
    },
    'KuCoin': {
      totalValue: 8500.00,
      assets: [
        { symbol: 'SOL', balance: 50.23, value: 9419.13, price: 187.5 },
        { symbol: 'AVAX', balance: 125.5, value: 5282.55, price: 42.1 },
        { symbol: 'USDT', balance: 5000, value: 5000, price: 1 }
      ],
      address: '0x123456789abcdef123456789abcdef123456789a'
    },
    'Bybit': {
      totalValue: 12450.00,
      assets: [
        { symbol: 'BTC', balance: 0.125, value: 12236.50, price: 97892 },
        { symbol: 'ETH', balance: 1.5, value: 4857.00, price: 3238 },
        { symbol: 'USDT', balance: 8500, value: 8500, price: 1 }
      ],
      address: '0xabcdef123456789abcdef123456789abcdef1234'
    }
  };

  const copyAddress = (exchange, address) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(exchange);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  const totalPortfolioValue = Object.values(walletData).reduce((sum, wallet) => sum + wallet.totalValue, 0);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Wallets</h2>
        <div className="text-right">
          <p className="text-sm text-gray-400">Total Portfolio Value</p>
          <p className="text-2xl font-bold gradient-text">${totalPortfolioValue.toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {Object.entries(walletData).map(([exchange, wallet]) => (
          <div key={exchange} className="glass rounded-xl p-6 border border-gray-800 hover-lift">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-blue-600/20">
                  <Wallet size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold">{exchange}</h3>
                  <p className="text-sm text-gray-400">Exchange Wallet</p>
                </div>
              </div>
              <ExternalLink size={20} className="text-gray-400 cursor-pointer hover:text-purple-400" />
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-400 mb-1">Total Value</p>
              <p className="text-2xl font-bold">${wallet.totalValue.toLocaleString()}</p>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-400 mb-2">Wallet Address</p>
              <div className="flex items-center gap-2">
                <code className="text-xs bg-gray-800 px-2 py-1 rounded flex-1 overflow-hidden">
                  {wallet.address.slice(0, 16)}...{wallet.address.slice(-8)}
                </code>
                <button
                  onClick={() => copyAddress(exchange, wallet.address)}
                  className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                >
                  {copiedAddress === exchange ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm text-gray-400 mb-2">Assets</p>
              {wallet.assets.map((asset) => (
                <div key={asset.symbol} className="flex items-center justify-between py-2 border-b border-gray-800/50">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{asset.symbol}</span>
                    <span className="text-sm text-gray-400">{asset.balance}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">${asset.value.toLocaleString()}</p>
                    <p className="text-xs text-gray-400">${asset.price.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Wallets;
