#!/usr/bin/env python3
"""
Quick start script for Crypto Trading AI
Sets up the environment and starts the bot in paper trading mode
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════╗
    ║       Crypto Trading AI Setup Wizard      ║
    ╚═══════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if required software is installed"""
    print("\n🔍 Checking requirements...")
    
    requirements = {
        'docker': 'Docker',
        'docker-compose': 'Docker Compose',
        'node': 'Node.js',
        'npm': 'npm'
    }
    
    missing = []
    for cmd, name in requirements.items():
        if shutil.which(cmd) is None:
            missing.append(name)
            print(f"❌ {name} not found")
        else:
            print(f"✅ {name} found")
    
    if missing:
        print(f"\n❗ Please install: {', '.join(missing)}")
        return False
    
    return True

def setup_env():
    """Setup environment variables"""
    print("\n🔧 Setting up environment...")
    
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
        
        print("\n📝 Exchange Setup (You can add these later)")
        print("1. Binance.com (via VPN) - Best liquidity")
        print("2. KuCoin - No KYC required")
        print("3. Bybit - Great for derivatives")
        print("4. Gate.io - Many altcoins")
        
        update_env = input("\nWould you like to add exchange API keys now? (y/n): ")
        if update_env.lower() == 'y':
            add_exchange_keys()
    else:
        print("✅ .env file already exists")

def add_exchange_keys():
    """Interactive exchange API key setup"""
    exchanges = [
        ('BINANCE', 'Binance'),
        ('KUCOIN', 'KuCoin'),
        ('BYBIT', 'Bybit'),
        ('GATE', 'Gate.io')
    ]
    
    env_content = open('.env', 'r').read()
    
    for prefix, name in exchanges:
        print(f"\n{name} Configuration:")
        add = input(f"Add {name} API keys? (y/n): ")
        if add.lower() == 'y':
            api_key = input(f"{name} API Key: ")
            api_secret = input(f"{name} API Secret: ")
            
            env_content = env_content.replace(
                f'{prefix}_API_KEY=your_{prefix.lower()}_api_key_here',
                f'{prefix}_API_KEY={api_key}'
            )
            env_content = env_content.replace(
                f'{prefix}_API_SECRET=your_{prefix.lower()}_api_secret_here',
                f'{prefix}_API_SECRET={api_secret}'
            )
            
            if prefix == 'KUCOIN':
                password = input("KuCoin Trading Password: ")
                env_content = env_content.replace(
                    'KUCOIN_PASSWORD=your_kucoin_trading_password_here',
                    f'KUCOIN_PASSWORD={password}'
                )
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ API keys saved to .env file")

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n📦 Setting up frontend...")
    
    os.chdir('frontend')
    subprocess.run(['npm', 'install'], check=True)
    os.chdir('..')
    
    print("✅ Frontend dependencies installed")

def choose_deployment():
    """Choose deployment method"""
    print("\n🚀 Deployment Options:")
    print("1. Local Docker (Recommended for testing)")
    print("2. Cloud deployment (Railway/Render)")
    print("3. Hybrid (Frontend cloud, backend local)")
    
    choice = input("\nSelect deployment method (1-3): ")
    return choice

def start_local():
    """Start services locally with Docker"""
    print("\n🐳 Starting services with Docker...")
    
    # Start in paper trading mode
    subprocess.run(['docker-compose', 'up', '-d'], check=True)
    
    print("\n✅ Services started!")
    print("\n📊 Access your dashboard:")
    print("- Web UI: http://localhost:3001")
    print("- Grafana: http://localhost:3000 (admin/admin)")
    print("- API: http://localhost:8000")
    
    print("\n💡 Tips:")
    print("- The bot is running in PAPER TRADING mode (no real money)")
    print("- Check logs: docker-compose logs -f trading-bot")
    print("- Stop services: docker-compose down")
    print("- Monitor performance in the web UI")

def deploy_cloud():
    """Deploy to cloud services"""
    print("\n☁️  Cloud Deployment")
    print("\nRecommended free options:")
    print("1. Railway - $5 free credit/month")
    print("2. Render - 750 hours/month free")
    print("3. Fly.io - 3 VMs free")
    
    print("\nSee DEPLOYMENT.md for detailed instructions")
    
    deploy_now = input("\nInstall Railway CLI and deploy now? (y/n): ")
    if deploy_now.lower() == 'y':
        subprocess.run(['npm', 'install', '-g', '@railway/cli'], check=True)
        subprocess.run(['railway', 'login'], check=True)
        subprocess.run(['railway', 'init'], check=True)
        subprocess.run(['railway', 'up'], check=True)

def main():
    print_banner()
    
    if not check_requirements():
        sys.exit(1)
    
    setup_env()
    setup_frontend()
    
    deployment = choose_deployment()
    
    if deployment == '1':
        start_local()
    elif deployment == '2':
        deploy_cloud()
    elif deployment == '3':
        print("\n🔀 Hybrid Deployment")
        print("1. Deploy frontend to Vercel: vercel --prod")
        print("2. Keep backend running locally")
        print("3. Update frontend .env with your local IP")
    
    print("\n🎉 Setup complete!")
    print("\n📚 Next steps:")
    print("1. Add your exchange API keys to .env")
    print("2. Configure your trading strategies in Settings")
    print("3. Start with small amounts in paper trading")
    print("4. Monitor the AI predictions and pump alerts")
    print("5. Gradually enable live trading when comfortable")
    
    print("\n⚠️  Remember:")
    print("- Start with PAPER TRADING enabled")
    print("- Never invest more than you can afford to lose")
    print("- The bot needs 24-48 hours to learn patterns")
    print("- Monitor closely for the first week")
    
    print("\n💬 Support:")
    print("- Check README.md for documentation")
    print("- Logs are in ./logs directory")
    print("- Dashboard shows all activity")

if __name__ == "__main__":
    main()
