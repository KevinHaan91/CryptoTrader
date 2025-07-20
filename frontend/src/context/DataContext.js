import React, { createContext, useContext, useState, useEffect } from 'react';
import { useSocket } from './SocketContext';
import axios from 'axios';

const DataContext = createContext();

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within DataProvider');
  }
  return context;
};

export const DataProvider = ({ children }) => {
  const { on, emit } = useSocket();
  const [isLoading, setIsLoading] = useState(false);
  
  // Portfolio data
  const [portfolioStats, setPortfolioStats] = useState({
    totalBalance: 15234.50,
    balanceChange24h: 2.34,
    pnl24h: 356.78,
    pnlPercent24h: 2.34,
    winRate: 68.5
  });
  
  // Positions
  const [positions, setPositions] = useState([
    { id: 1, symbol: 'BTC/USDT', side: 'BUY', entryPrice: 98234, currentPrice: 99123, pnl: 2.3, size: 0.5, exchange: 'Binance' },
    { id: 2, symbol: 'ETH/USDT', side: 'SELL', entryPrice: 3234, currentPrice: 3212, pnl: 0.68, size: 2.1, exchange: 'KuCoin' },
    { id: 3, symbol: 'SOL/USDT', side: 'BUY', entryPrice: 187.5, currentPrice: 192.3, pnl: 2.56, size: 50, exchange: 'Bybit' }
  ]);
  
  // Predictions
  const [predictions, setPredictions] = useState([]);
  
  // Pump alerts
  const [pumpAlerts, setPumpAlerts] = useState([]);
  
  // Wallets
  const [wallets, setWallets] = useState({});
  
  // Recent trades
  const [recentTrades, setRecentTrades] = useState([]);
  
  // Chart data
  const [chartData, setChartData] = useState([]);
  
  // Strategy performance
  const [strategyPerformance, setStrategyPerformance] = useState(null);

  // WebSocket listeners
  useEffect(() => {
    if (!on) return;

    const unsubscribePortfolio = on('portfolio:update', (data) => {
      setPortfolioStats(data);
    });

    const unsubscribePositions = on('positions:update', (data) => {
      setPositions(data);
    });

    const unsubscribePredictions = on('predictions:update', (data) => {
      setPredictions(data);
    });

    const unsubscribePumpAlerts = on('pump:alert', (data) => {
      setPumpAlerts(prev => [data, ...prev].slice(0, 20)); // Keep last 20 alerts
    });

    const unsubscribeWallets = on('wallets:update', (data) => {
      setWallets(data);
    });

    const unsubscribeTrades = on('trade:executed', (data) => {
      setRecentTrades(prev => [data, ...prev].slice(0, 50)); // Keep last 50 trades
    });

    const unsubscribeStrategyPerf = on('strategy:performance', (data) => {
      setStrategyPerformance(data);
    });

    return () => {
      unsubscribePortfolio?.();
      unsubscribePositions?.();
      unsubscribePredictions?.();
      unsubscribePumpAlerts?.();
      unsubscribeWallets?.();
      unsubscribeTrades?.();
      unsubscribeStrategyPerf?.();
    };
  }, [on]);

  // API calls
  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
      
      const [portfolioRes, positionsRes, walletsRes, strategyRes] = await Promise.all([
        axios.get(`${baseURL}/portfolio`),
        axios.get(`${baseURL}/positions`),
        axios.get(`${baseURL}/wallets`),
        axios.get(`${baseURL}/strategy-performance`)
      ]);
      
      setPortfolioStats(portfolioRes.data);
      setPositions(positionsRes.data);
      setWallets(walletsRes.data);
      setStrategyPerformance(strategyRes.data);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const fetchStrategyPerformance = async () => {
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
      const response = await axios.get(`${baseURL}/strategy-performance`);
      setStrategyPerformance(response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching strategy performance:', error);
      return null;
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const value = {
    isLoading,
    portfolioStats,
    positions,
    predictions,
    pumpAlerts,
    wallets,
    recentTrades,
    chartData,
    strategyPerformance,
    refreshData: fetchInitialData,
    fetchStrategyPerformance
  };

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  );
};
