import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const PositionsTable = ({ positions = [] }) => {
  const [sortField, setSortField] = useState('symbol');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filter, setFilter] = useState('');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredPositions = positions.filter(pos => 
    pos.symbol.toLowerCase().includes(filter.toLowerCase()) ||
    pos.exchange.toLowerCase().includes(filter.toLowerCase())
  );

  const sortedPositions = [...filteredPositions].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];
    const direction = sortDirection === 'asc' ? 1 : -1;
    
    if (typeof aVal === 'number') {
      return (aVal - bVal) * direction;
    }
    return aVal.localeCompare(bVal) * direction;
  });

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  return (
    <div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter positions..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 rounded-lg glass border border-gray-700 bg-transparent w-full md:w-64 focus:border-purple-500 outline-none"
        />
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left border-b border-gray-800">
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('symbol')}>
                <div className="flex items-center gap-1">
                  Symbol <SortIcon field="symbol" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('side')}>
                <div className="flex items-center gap-1">
                  Side <SortIcon field="side" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('entryPrice')}>
                <div className="flex items-center gap-1">
                  Entry <SortIcon field="entryPrice" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('currentPrice')}>
                <div className="flex items-center gap-1">
                  Current <SortIcon field="currentPrice" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('pnl')}>
                <div className="flex items-center gap-1">
                  P&L <SortIcon field="pnl" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('size')}>
                <div className="flex items-center gap-1">
                  Size <SortIcon field="size" />
                </div>
              </th>
              <th className="pb-3 cursor-pointer hover:text-purple-400" onClick={() => handleSort('exchange')}>
                <div className="flex items-center gap-1">
                  Exchange <SortIcon field="exchange" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedPositions.map((position, idx) => (
              <tr key={idx} className="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors">
                <td className="py-3 font-medium">{position.symbol}</td>
                <td className={`py-3 ${position.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                  {position.side}
                </td>
                <td className="py-3">${position.entryPrice?.toLocaleString()}</td>
                <td className="py-3">${position.currentPrice?.toLocaleString()}</td>
                <td className={`py-3 font-medium ${position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {position.pnl >= 0 ? '+' : ''}{position.pnl?.toFixed(2)}%
                </td>
                <td className="py-3">{position.size}</td>
                <td className="py-3 text-gray-400">{position.exchange}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {sortedPositions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No positions found
          </div>
        )}
      </div>
    </div>
  );
};

export default PositionsTable;
