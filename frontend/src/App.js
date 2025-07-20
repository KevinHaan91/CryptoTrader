import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import TradingView from './components/TradingView';
import Predictions from './components/Predictions';
import Wallets from './components/Wallets';
import PumpAlerts from './components/PumpAlerts';
import Settings from './components/Settings';
import StrategyPerformance from './components/StrategyPerformance';
import { SocketProvider } from './context/SocketContext';
import { DataProvider } from './context/DataContext';
import './index.css';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');

  return (
    <SocketProvider>
      <DataProvider>
        <Router>
          <div className="flex h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black">
            <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
            
            <div className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-16'}`}>
              <header className="glass h-16 px-6 flex items-center justify-between border-b border-gray-800">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                  <h1 className="text-xl font-bold gradient-text">Crypto Trading AI</h1>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-gray-400">Live Trading</span>
                  </div>
                  <button className="p-2 rounded-lg hover:bg-gray-800 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                  </button>
                </div>
              </header>
              
              <main className="flex-1 overflow-auto p-6">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/trading" element={<TradingView />} />
                  <Route path="/predictions" element={<Predictions />} />
                  <Route path="/wallets" element={<Wallets />} />
                  <Route path="/alerts" element={<PumpAlerts />} />
                  <Route path="/performance" element={<StrategyPerformance />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </main>
            </div>
          </div>
        </Router>
      </DataProvider>
    </SocketProvider>
  );
}

export default App;
