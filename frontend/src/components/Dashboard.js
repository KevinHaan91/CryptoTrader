import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react';
import StatsCard from './StatsCard';
import PositionsTable from './PositionsTable';
import ProfitChart from './ProfitChart';
import RecentTrades from './RecentTrades';
import { useData } from '../context/DataContext';

const Dashboard = () => {
  const { portfolioStats, positions, recentTrades, isLoading } = useData();
  const [timeframe, setTimeframe] = useState('24h');

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex items-center gap-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent focus:border-purple-500 outline-none"
          >
            <option value="1h">1 Hour</option>
            <option value="24h">24 Hours</option>
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
          </select>
          <button className="p-2 rounded-lg glass hover:bg-gray-800 transition-colors">
            <RefreshCw size={20} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Balance"
          value={`$${portfolioStats?.totalBalance?.toLocaleString() || '0'}`}
          change={portfolioStats?.balanceChange24h || 0}
          icon={DollarSign}
          gradient="from-green-600/20 to-emerald-600/20"
        />
        <StatsCard
          title="24h P&L"
          value={`$${portfolioStats?.pnl24h?.toLocaleString() || '0'}`}
          change={portfolioStats?.pnlPercent24h || 0}
          icon={portfolioStats?.pnl24h >= 0 ? TrendingUp : TrendingDown}
          gradient={portfolioStats?.pnl24h >= 0 ? "from-green-600/20 to-emerald-600/20" : "from-red-600/20 to-orange-600/20"}
        />
        <StatsCard
          title="Active Positions"
          value={positions?.length || 0}
          change={0}
          icon={Activity}
          gradient="from-blue-600/20 to-purple-600/20"
        />
        <StatsCard
          title="Win Rate"
          value={`${portfolioStats?.winRate || 0}%`}
          change={0}
          icon={Activity}
          gradient="from-purple-600/20 to-pink-600/20"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profit Chart - 2 columns */}
        <div className="lg:col-span-2">
          <div className="glass rounded-xl p-6 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Portfolio Performance</h3>
            <ProfitChart timeframe={timeframe} />
          </div>
        </div>

        {/* Recent Trades - 1 column */}
        <div className="glass rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold mb-4">Recent Trades</h3>
          <RecentTrades trades={recentTrades} />
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

export default Dashboard;
