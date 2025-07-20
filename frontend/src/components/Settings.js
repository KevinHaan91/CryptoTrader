import React, { useState } from 'react';
import { Settings as SettingsIcon, Key, Bot, Bell, Shield, Save } from 'lucide-react';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('api');
  const [settings, setSettings] = useState({
    // API Keys
    binanceApiKey: '',
    binanceApiSecret: '',
    kuCoinApiKey: '',
    kuCoinApiSecret: '',
    
    // Trading Settings
    paperTrading: true,
    maxPositionSize: 5,
    stopLossPercent: 2,
    takeProfitPercent: 5,
    
    // Strategy Settings
    enableScalping: true,
    enableArbitrage: true,
    enableDayTrading: false,
    enableSwingTrading: false,
    enablePumpDetection: true,
    
    // Notifications
    emailNotifications: true,
    pushNotifications: false,
    alertThreshold: 80,
    
    // Risk Management
    maxDailyLoss: 500,
    maxDrawdown: 10,
    positionSizeMethod: 'kelly'
  });

  const handleSave = () => {
    console.log('Saving settings:', settings);
    // API call to save settings
  };

  const tabs = [
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'trading', label: 'Trading', icon: Bot },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'risk', label: 'Risk Management', icon: Shield }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Settings</h2>
        <button
          onClick={handleSave}
          className="px-6 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium flex items-center gap-2 transition-colors"
        >
          <Save size={20} />
          Save Changes
        </button>
      </div>

      <div className="flex gap-6">
        {/* Tabs */}
        <div className="w-64">
          <div className="glass rounded-xl p-4 border border-gray-800">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all mb-2 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30'
                    : 'hover:bg-gray-800/50'
                }`}
              >
                <tab.icon size={20} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="glass rounded-xl p-6 border border-gray-800">
            {activeTab === 'api' && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold mb-4">Exchange API Keys</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Binance API Key</label>
                    <input
                      type="password"
                      value={settings.binanceApiKey}
                      onChange={(e) => setSettings({...settings, binanceApiKey: e.target.value})}
                      placeholder="Enter your Binance API key"
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Binance API Secret</label>
                    <input
                      type="password"
                      value={settings.binanceApiSecret}
                      onChange={(e) => setSettings({...settings, binanceApiSecret: e.target.value})}
                      placeholder="Enter your Binance API secret"
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>
                  
                  <div className="pt-4">
                    <label className="text-sm text-gray-400 mb-2 block">KuCoin API Key</label>
                    <input
                      type="password"
                      value={settings.kuCoinApiKey}
                      onChange={(e) => setSettings({...settings, kuCoinApiKey: e.target.value})}
                      placeholder="Enter your KuCoin API key"
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">KuCoin API Secret</label>
                    <input
                      type="password"
                      value={settings.kuCoinApiSecret}
                      onChange={(e) => setSettings({...settings, kuCoinApiSecret: e.target.value})}
                      placeholder="Enter your KuCoin API secret"
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'trading' && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold mb-4">Trading Configuration</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Paper Trading Mode</p>
                      <p className="text-sm text-gray-400">Test strategies without real money</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.paperTrading}
                        onChange={(e) => setSettings({...settings, paperTrading: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Max Position Size (%)</label>
                    <input
                      type="number"
                      value={settings.maxPositionSize}
                      onChange={(e) => setSettings({...settings, maxPositionSize: e.target.value})}
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-400 mb-2 block">Stop Loss (%)</label>
                      <input
                        type="number"
                        value={settings.stopLossPercent}
                        onChange={(e) => setSettings({...settings, stopLossPercent: e.target.value})}
                        className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-400 mb-2 block">Take Profit (%)</label>
                      <input
                        type="number"
                        value={settings.takeProfitPercent}
                        onChange={(e) => setSettings({...settings, takeProfitPercent: e.target.value})}
                        className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                      />
                    </div>
                  </div>

                  <div className="pt-4">
                    <p className="font-medium mb-3">Active Strategies</p>
                    <div className="space-y-3">
                      {[
                        { key: 'enableScalping', label: 'Scalping' },
                        { key: 'enableArbitrage', label: 'Arbitrage' },
                        { key: 'enableDayTrading', label: 'Day Trading' },
                        { key: 'enableSwingTrading', label: 'Swing Trading' },
                        { key: 'enablePumpDetection', label: 'Pump Detection' }
                      ].map((strategy) => (
                        <label key={strategy.key} className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings[strategy.key]}
                            onChange={(e) => setSettings({...settings, [strategy.key]: e.target.checked})}
                            className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                          />
                          <span>{strategy.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold mb-4">Notification Preferences</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-gray-400">Receive alerts via email</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.emailNotifications}
                        onChange={(e) => setSettings({...settings, emailNotifications: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Push Notifications</p>
                      <p className="text-sm text-gray-400">Mobile app notifications</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.pushNotifications}
                        onChange={(e) => setSettings({...settings, pushNotifications: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Alert Confidence Threshold (%)</label>
                    <input
                      type="number"
                      value={settings.alertThreshold}
                      onChange={(e) => setSettings({...settings, alertThreshold: e.target.value})}
                      min="0"
                      max="100"
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'risk' && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold mb-4">Risk Management</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Max Daily Loss ($)</label>
                    <input
                      type="number"
                      value={settings.maxDailyLoss}
                      onChange={(e) => setSettings({...settings, maxDailyLoss: e.target.value})}
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Max Drawdown (%)</label>
                    <input
                      type="number"
                      value={settings.maxDrawdown}
                      onChange={(e) => setSettings({...settings, maxDrawdown: e.target.value})}
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Position Sizing Method</label>
                    <select
                      value={settings.positionSizeMethod}
                      onChange={(e) => setSettings({...settings, positionSizeMethod: e.target.value})}
                      className="w-full px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
                    >
                      <option value="fixed">Fixed Size</option>
                      <option value="kelly">Kelly Criterion</option>
                      <option value="risk-parity">Risk Parity</option>
                      <option value="volatility-adjusted">Volatility Adjusted</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
