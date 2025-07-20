import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { useData } from '../context/DataContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function StrategyPerformance() {
  const { strategyPerformance, fetchStrategyPerformance } = useData();
  const [selectedStrategy, setSelectedStrategy] = useState('overall');
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchStrategyPerformance();
      setLoading(false);
    };
    
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    
    return () => clearInterval(interval);
  }, []);

  const getStrategyData = () => {
    if (!strategyPerformance) return null;
    
    if (selectedStrategy === 'overall') {
      return strategyPerformance.overall;
    }
    
    return strategyPerformance[selectedStrategy];
  };

  const getPnLChartData = () => {
    const data = getStrategyData();
    if (!data || !data.performance_24h) return null;

    const timeData = {
      '24h': data.performance_24h,
      '7d': data.performance_7d,
      '30d': data.performance_30d
    };

    const selectedData = timeData[timeRange] || data.performance_7d;
    
    return {
      labels: ['P&L'],
      datasets: [{
        label: 'Profit/Loss (USD)',
        data: [selectedData.pnl],
        backgroundColor: selectedData.pnl >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)',
        borderColor: selectedData.pnl >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
        borderWidth: 2
      }]
    };
  };

  const getWinRateChart = () => {
    const data = getStrategyData();
    if (!data) return null;

    const winRate = data.win_rate || data.overall_win_rate || 0;
    
    return {
      labels: ['Wins', 'Losses'],
      datasets: [{
        data: [winRate * 100, (1 - winRate) * 100],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(239, 68, 68)'
        ],
        borderWidth: 2
      }]
    };
  };

  const getStrategyComparisonChart = () => {
    if (!strategyPerformance) return null;

    const strategies = Object.keys(strategyPerformance).filter(key => key !== 'overall');
    const pnlData = strategies.map(strategy => 
      strategyPerformance[strategy]?.total_pnl || 0
    );
    
    return {
      labels: strategies.map(s => strategyPerformance[s]?.name || s),
      datasets: [{
        label: 'Total P&L by Strategy',
        data: pnlData,
        backgroundColor: pnlData.map(pnl => 
          pnl >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'
        ),
        borderColor: pnlData.map(pnl => 
          pnl >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
        ),
        borderWidth: 2
      }]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#374151',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(55, 65, 81, 0.3)'
        },
        ticks: {
          color: '#9CA3AF'
        }
      },
      y: {
        grid: {
          color: 'rgba(55, 65, 81, 0.3)'
        },
        ticks: {
          color: '#9CA3AF'
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const currentData = getStrategyData();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold gradient-text">Strategy Performance</h1>
        
        <div className="flex gap-4">
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="glass px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 transition-colors"
          >
            <option value="overall">All Strategies</option>
            {strategyPerformance && Object.keys(strategyPerformance)
              .filter(key => key !== 'overall')
              .map(strategy => (
                <option key={strategy} value={strategy}>
                  {strategyPerformance[strategy]?.name || strategy}
                </option>
              ))
            }
          </select>
          
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="glass px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 transition-colors"
          >
            <option value="24h">24 Hours</option>
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-darker p-6 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm">Total P&L</p>
              <p className={`text-2xl font-bold mt-1 ${
                currentData?.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                ${currentData?.total_pnl?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${
              currentData?.total_pnl >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'
            }`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d={currentData?.total_pnl >= 0 
                    ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    : "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
                  } 
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="glass-darker p-6 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm">Win Rate</p>
              <p className="text-2xl font-bold text-purple-500 mt-1">
                {((currentData?.win_rate || currentData?.overall_win_rate || 0) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/20">
              <svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="glass-darker p-6 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm">Total Trades</p>
              <p className="text-2xl font-bold text-blue-500 mt-1">
                {currentData?.total_trades || 0}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/20">
              <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="glass-darker p-6 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm">Active Positions</p>
              <p className="text-2xl font-bold text-yellow-500 mt-1">
                {currentData?.active_positions || 0}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-yellow-500/20">
              <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">P&L Over Time</h3>
          <div className="h-64">
            {getPnLChartData() && (
              <Bar data={getPnLChartData()} options={chartOptions} />
            )}
          </div>
        </div>

        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">Win Rate Distribution</h3>
          <div className="h-64">
            {getWinRateChart() && (
              <Doughnut 
                data={getWinRateChart()} 
                options={{
                  ...chartOptions,
                  plugins: {
                    ...chartOptions.plugins,
                    legend: {
                      display: true,
                      position: 'right',
                      labels: {
                        color: '#9CA3AF'
                      }
                    }
                  }
                }} 
              />
            )}
          </div>
        </div>
      </div>

      {/* Strategy Comparison */}
      {selectedStrategy === 'overall' && (
        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">Strategy Comparison</h3>
          <div className="h-64">
            {getStrategyComparisonChart() && (
              <Bar data={getStrategyComparisonChart()} options={chartOptions} />
            )}
          </div>
        </div>
      )}

      {/* New Listing Detection Details */}
      {selectedStrategy === 'new_listing_detection' && currentData?.sub_strategy_performance && (
        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">Sub-Strategy Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(currentData.sub_strategy_performance).map(([type, perf]) => (
              <div key={type} className="glass p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-400 uppercase">{type}</h4>
                <p className={`text-xl font-bold mt-1 ${
                  perf.pnl >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  ${perf.pnl?.toFixed(2) || '0.00'}
                </p>
                <div className="flex justify-between text-sm text-gray-400 mt-2">
                  <span>Win Rate: {(perf.win_rate * 100).toFixed(1)}%</span>
                  <span>{perf.trade_count} trades</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Sources */}
      {selectedStrategy === 'new_listing_detection' && currentData?.best_sources && (
        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">Top Information Sources</h3>
          <div className="space-y-2">
            {Object.entries(currentData.best_sources).slice(0, 10).map(([source, score], index) => (
              <div key={source} className="flex items-center justify-between p-3 glass rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-400">#{index + 1}</span>
                  <span className="font-medium">{source}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-400">{(score * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Metrics */}
      {currentData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {currentData.best_trade && (
            <div className="glass-darker p-6 rounded-xl">
              <h3 className="text-lg font-semibold mb-4">Best Trade</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Symbol</span>
                  <span className="font-medium">{currentData.best_trade.symbol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Return</span>
                  <span className="font-medium text-green-500">
                    +{(currentData.best_trade.pnl_pct * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Profit</span>
                  <span className="font-medium text-green-500">
                    ${currentData.best_trade.pnl_usd.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {currentData.worst_trade && (
            <div className="glass-darker p-6 rounded-xl">
              <h3 className="text-lg font-semibold mb-4">Worst Trade</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Symbol</span>
                  <span className="font-medium">{currentData.worst_trade.symbol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Return</span>
                  <span className="font-medium text-red-500">
                    {(currentData.worst_trade.pnl_pct * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Loss</span>
                  <span className="font-medium text-red-500">
                    ${currentData.worst_trade.pnl_usd.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Overall Statistics */}
      {selectedStrategy === 'overall' && currentData && (
        <div className="glass-darker p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4">Overall Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-gray-400 text-sm">Sharpe Ratio</p>
              <p className="text-xl font-bold text-purple-500">
                {currentData.sharpe_ratio?.toFixed(2) || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Max Drawdown</p>
              <p className="text-xl font-bold text-red-500">
                {currentData.max_drawdown ? `${(currentData.max_drawdown * 100).toFixed(1)}%` : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Best Strategy</p>
              <p className="text-lg font-bold text-green-500">
                {currentData.best_strategy?.name || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Worst Strategy</p>
              <p className="text-lg font-bold text-red-500">
                {currentData.worst_strategy?.name || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyPerformance;
