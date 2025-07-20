import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { useData } from '../context/DataContext';

const ProfitChart = ({ timeframe }) => {
  const { chartData } = useData();
  const [data, setData] = useState([]);

  useEffect(() => {
    // Mock data - replace with real data from API
    const generateData = () => {
      const points = timeframe === '1h' ? 12 : timeframe === '24h' ? 24 : timeframe === '7d' ? 7 : 30;
      const baseValue = 10000;
      let currentValue = baseValue;
      
      return Array.from({ length: points }, (_, i) => {
        currentValue += (Math.random() - 0.45) * 200;
        return {
          time: timeframe === '1h' ? `${i * 5}m` : 
                timeframe === '24h' ? `${i}h` : 
                timeframe === '7d' ? `Day ${i + 1}` : 
                `${i + 1}`,
          value: Math.max(0, currentValue),
          profit: currentValue - baseValue
        };
      });
    };
    
    setData(generateData());
  }, [timeframe]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass p-4 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-lg font-semibold">${payload[0].value.toLocaleString()}</p>
          <p className={`text-sm ${payload[0].payload.profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {payload[0].payload.profit >= 0 ? '+' : ''}{payload[0].payload.profit.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="time" stroke="#6b7280" />
          <YAxis stroke="#6b7280" />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#8b5cf6"
            fillOpacity={1}
            fill="url(#colorValue)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ProfitChart;
