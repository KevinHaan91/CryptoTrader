# 🚀 Crypto Trading AI - Quick Start Guide

## 5-Minute Setup

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd crypto-trading-ai

# Run the setup wizard
python quick_start.py
```

### 2. Add Exchange API Keys
Edit `.env` file and add your API keys:
```env
# At minimum, add one exchange:
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

### 3. Start Trading Bot
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f trading-bot
```

### 4. Access Dashboard
- 🌐 **Web UI**: http://localhost:3001
- 📊 **Grafana**: http://localhost:3000 (admin/admin)
- 🔌 **API**: http://localhost:8000

## First Day Checklist

- [ ] ✅ Bot running in paper trading mode
- [ ] 👀 Monitor the dashboard for 24 hours
- [ ] 📈 Check AI predictions accuracy
- [ ] 🚨 Review pump detection alerts
- [ ] 💰 Verify paper trading profits
- [ ] ⚙️ Adjust settings based on performance

## Exchange Recommendations

### For US Users (with VPN):
1. **Binance.com** - Best overall
2. **KuCoin** - No KYC under 5 BTC/day
3. **Bybit** - Excellent for futures

### For US Users (without VPN):
1. **Coinbase Pro** - Fully compliant
2. **Kraken** - Good liquidity
3. **Crypto.com** - Many pairs

## Safety First

The bot starts in **PAPER TRADING** mode:
- No real money at risk
- Test all strategies safely
- Monitor for 1-2 weeks before going live

## Quick Commands

```bash
# Stop the bot
docker-compose down

# Update and restart
git pull
docker-compose up -d --build

# View real-time logs
docker-compose logs -f trading-bot

# Access database
docker exec -it trading-postgres psql -U postgres -d crypto_trading

# Clear cache
docker exec -it trading-redis redis-cli FLUSHALL
```

## Troubleshooting

### Bot not starting?
```bash
# Check logs
docker-compose logs trading-bot

# Verify .env file
cat .env | grep API_KEY
```

### No trades executing?
- Check paper trading is enabled
- Verify API keys are correct
- Ensure minimum balance ($100 recommended)

### High CPU usage?
- Disable unused strategies in Settings
- Reduce number of monitored pairs
- Check GPU acceleration is working

## Mobile Access

The web UI is mobile-responsive. Access from your phone:
1. Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Visit: `http://YOUR-IP:3001` from your phone
3. Add to home screen for app-like experience

## Going Live

When ready for real trading:
1. Set `PAPER_TRADING=false` in `.env`
2. Start with small amounts ($100-500)
3. Enable one strategy at a time
4. Monitor closely for first 48 hours

## Support

- 📖 Full docs: See README.md
- 🐛 Issues: Check logs first
- 💡 Tips: Start conservative, scale up slowly

**Remember**: Crypto trading is risky. Never invest more than you can afford to lose!
