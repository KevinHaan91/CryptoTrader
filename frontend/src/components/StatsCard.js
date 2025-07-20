import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const StatsCard = ({ title, value, change, icon: Icon, gradient }) => {
  const isPositive = change >= 0;
  
  return (
    <div className={`glass rounded-xl p-6 border border-gray-800 hover-lift bg-gradient-to-br ${gradient}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {change !== 0 && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
              {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        <div className="p-3 rounded-lg bg-gray-900/50">
          <Icon size={24} className="text-gray-400" />
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
