#!/usr/bin/env python3
"""
Quick setup script for Crypto Trading Bot
Helps users configure and start trading
"""

import os
import sys
import json
import getpass
import subprocess
from pathlib import Path

def print_banner():
    print("""
    ╔═══════════════════════════════════════╗
    ║     Crypto Trading AI Bot Setup       ║
    ║         RTX 4080 Optimized            ║
    ╚═══════════════════════════════════════╝
    """)

def check_requirements():
    """Check system requirements"""
    print("\n📋 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False
    print("✅ Python version OK")
    
    # Check GPU
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected")
        else:
            print("⚠️  No NVIDIA GPU detected - will use CPU (slower)")
    except:
        print("⚠️  nvidia-smi not found - GPU features disabled")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True)
        if result.returncode == 0:
            print("✅ Docker installed")
        else:
            print("❌ Docker not found - please install Docker")
            return False
    except:
        print("❌ Docker not found - please install Docker")
        return False
    
    return True

def setup_env_file():
    """Setup .env file with user's API keys"""
    print("\n🔑 Setting up API keys...")
    
    env_path = Path('.env')
    if env_path.exists():
        overwrite = input(".env file exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            return
    
    env_content = []
    
    # Exchange selection
    print("\n📊 Which exchanges do you want to use?")
    print("1. Kraken (your current exchange)")
    print("2. Binance (recommended - lower latency)")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ")
    
    if choice in ['1', '3']:
        print("\n🔐 Kraken API Setup:")
        kraken_key = input("Enter Kraken API Key: ").strip()
        kraken_secret = getpass.getpass("Enter Kraken API Secret: ").strip()
        env_content.append(f"KRAKEN_API_KEY={kraken_key}")
        env_content.append(f"KRAKEN_API_SECRET={kraken_secret}")
    
    if choice in ['2', '3']:
        print("\n🔐 Binance API Setup:")
        binance_key = input("Enter Binance API Key: ").strip()
        binance_secret = getpass.getpass("Enter Binance API Secret: ").strip()
        env_content.append(f"BINANCE_API_KEY={binance_key}")
        env_content.append(f"BINANCE_API_SECRET={binance_secret}")
    
    # Database passwords
    print("\n💾 Database Setup:")
    use_defaults = input("Use default database passwords? (Y/n): ")
    
    if use_defaults.lower() != 'n':
        env_content.extend([
            "INFLUXDB_URL=http://localhost:8086",
            "INFLUXDB_TOKEN=your-influxdb-token",
            "DATABASE_URL=postgresql://postgres:password@localhost/crypto_trading",
            "REDIS_URL=redis://localhost:6379/0"
        ])
    else:
        db_pass = getpass.getpass("Enter PostgreSQL password: ")
        env_content.append(f"DATABASE_URL=postgresql://postgres:{db_pass}@localhost/crypto_trading")
        env_content.append("REDIS_URL=redis://localhost:6379/0")
        env_content.append("INFLUXDB_URL=http://localhost:8086")
        env_content.append("INFLUXDB_TOKEN=your-influxdb-token")
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
    
    print("✅ .env file created successfully")

def select_strategies():
    """Help user select trading strategies"""
    print("\n🎯 Trading Strategy Selection:")
    print("\nAvailable strategies:")
    print("1. Arbitrage (Lowest risk - price differences between exchanges)")
    print("2. Scalping (Fast trades, small profits, requires low latency)")
    print("3. Day Trading (Technical analysis based, moderate risk)")
    print("4. Swing Trading (Multi-day positions, patient approach)")
    print("5. Pump Detection (Higher risk - ML detects unusual activity)")
    
    print("\n📌 Recommended for beginners: Start with Arbitrage only")
    
    strategies = {
        'arbitrage': False,
        'scalping': False,
        'day_trading': False,
        'swing_trading': False,
        'pump_detection': False
    }
    
    choice = input("\nEnable recommended settings? (Y/n): ")
    
    if choice.lower() != 'n':
        strategies['arbitrage'] = True
        print("✅ Arbitrage strategy enabled")
    else:
        selections = input("Enter strategy numbers to enable (comma-separated, e.g., 1,2,3): ")
        for num in selections.split(','):
            num = num.strip()
            if num == '1':
                strategies['arbitrage'] = True
            elif num == '2':
                strategies['scalping'] = True
            elif num == '3':
                strategies['day_trading'] = True
            elif num == '4':
                strategies['swing_trading'] = True
            elif num == '5':
                strategies['pump_detection'] = True
    
    return strategies

def configure_risk_settings():
    """Configure risk management settings"""
    print("\n⚠️  Risk Management Configuration:")
    
    risk_profile = input("\nRisk profile (1=Conservative, 2=Moderate, 3=Aggressive): ")
    
    if risk_profile == '1':
        return {
            'max_position_size': 0.02,  # 2%
            'max_daily_loss': 0.03,     # 3%
            'max_trade_amount': 500
        }
    elif risk_profile == '3':
        return {
            'max_position_size': 0.10,  # 10%
            'max_daily_loss': 0.10,     # 10%
            'max_trade_amount': 5000
        }
    else:  # Default moderate
        return {
            'max_position_size': 0.05,  # 5%
            'max_daily_loss': 0.05,     # 5%
            'max_trade_amount': 1000
        }

def start_services():
    """Start Docker services"""
    print("\n🚀 Starting services...")
    
    try:
        # Start databases
        subprocess.run(['docker-compose', 'up', '-d', 'influxdb', 'postgres', 'redis'], check=True)
        print("✅ Databases started")
        
        # Wait for services
        import time
        print("⏳ Waiting for services to initialize...")
        time.sleep(10)
        
        # Start trading bot
        start_bot = input("\nStart trading bot now? (y/N): ")
        if start_bot.lower() == 'y':
            subprocess.run(['docker-compose', 'up', '-d', 'trading-bot'], check=True)
            print("✅ Trading bot started!")
            print("\n📊 Monitor logs: docker-compose logs -f trading-bot")
            print("📈 Grafana dashboard: http://localhost:3000 (admin/admin)")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting services: {e}")
        return False
    
    return True

def main():
    """Main setup flow"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing requirements and try again")
        return
    
    # Setup environment
    setup_env_file()
    
    # Configure strategies
    strategies = select_strategies()
    
    # Configure risk
    risk_settings = configure_risk_settings()
    
    # Summary
    print("\n📋 Configuration Summary:")
    print(f"Enabled strategies: {[s for s, enabled in strategies.items() if enabled]}")
    print(f"Max position size: {risk_settings['max_position_size']*100}%")
    print(f"Max daily loss: {risk_settings['max_daily_loss']*100}%")
    print(f"Max trade amount: ${risk_settings['max_trade_amount']}")
    
    # Start services
    if start_services():
        print("\n✅ Setup complete!")
        print("\n📚 Next steps:")
        print("1. Monitor initial trades carefully")
        print("2. Check logs for any errors")
        print("3. Adjust settings in config/settings.py as needed")
        print("4. Join our Discord for support")
        print("\n⚠️  Remember: Start small and increase gradually!")
    
if __name__ == "__main__":
    main()
