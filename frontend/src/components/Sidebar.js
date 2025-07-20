import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  Brain, 
  Wallet, 
  AlertTriangle, 
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/trading', icon: TrendingUp, label: 'Trading' },
    { path: '/predictions', icon: Brain, label: 'AI Predictions' },
    { path: '/wallets', icon: Wallet, label: 'Wallets' },
    { path: '/alerts', icon: AlertTriangle, label: 'Pump Alerts' },
    { path: '/performance', icon: BarChart3, label: 'Performance' },
    { path: '/settings', icon: Settings, label: 'Settings' }
  ];

  return (
    <div className={`fixed left-0 top-0 h-full glass border-r border-gray-800 transition-all duration-300 ${isOpen ? 'w-64' : 'w-16'}`}>
      <div className="flex flex-col h-full">
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
          {isOpen && <span className="text-lg font-bold gradient-text">Crypto AI</span>}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 rounded-lg hover:bg-gray-800 transition-colors"
          >
            {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>
        
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all hover-lift ${
                      isActive
                        ? 'bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30'
                        : 'hover:bg-gray-800/50'
                    }`
                  }
                >
                  <item.icon size={20} />
                  {isOpen && <span>{item.label}</span>}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="p-4 border-t border-gray-800">
          {isOpen && (
            <div className="text-xs text-gray-500">
              <p>Version 1.0.0</p>
              <p>© 2024 Crypto Trading AI</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
