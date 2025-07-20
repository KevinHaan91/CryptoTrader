# Crypto Trading AI Bot

An advanced automated cryptocurrency trading system that leverages machine learning, real-time market analysis, and multiple trading strategies to execute trades with minimal latency. Optimized for NVIDIA RTX 4080 GPU acceleration.

## Features

### Trading Strategies
- **Scalping**: Ultra-low latency trading with sub-second execution
- **Arbitrage**: Cross-exchange price discrepancy exploitation
- **Pump Detection**: ML-based pump-and-dump scheme detection
- **Day Trading**: Technical indicator-based intraday trading
- **Swing Trading**: Multi-day position trading
- **ICO/IDO Analysis**: (Coming soon)

### Technical Features
- GPU-accelerated ML models (XGBoost, LSTM, Transformers)
- Real-time WebSocket market data streaming
- Sub-100ms order execution
- Advanced risk management with circuit breakers
- Multi-exchange support (Kraken, Binance, Coinbase)
- Automated fund transfers for arbitrage
- Portfolio correlation analysis
- Kelly Criterion position sizing

## System Requirements

- **GPU**: NVIDIA RTX 4080 or better (CUDA 12.2+)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 100GB SSD for databases
- **OS**: Ubuntu 22.04 or Windows with WSL2
- **Network**: Low-latency internet connection

## Quick Start

### 1. Transfer Your Crypto from Kraken

**Option A: Keep funds on Kraken (Simplest)**
- The bot can trade directly on Kraken using their API
- No transfers needed, just API setup

**Option B: Transfer to Binance (Recommended for better latency)**
1. Create a Binance account if you don't have one
2. In Kraken: Go to Funding → Withdraw
3. Select your cryptocurrency and enter your Binance deposit address
4. In Binance: Go to Wallet → Deposit to get addresses
5. Wait for confirmation (varies by crypto: BTC ~30min, ETH ~5min)

### 2. API Key Setup

**Kraken API:**
1. Log into Kraken
2. Go to Settings → API
3. Create new key with permissions:
   - Query Funds
   - Query Open/Closed Orders
   - Create/Modify Orders
   - Cancel/Close Orders
4. Save the API Key and Private Key

**Binance API (Recommended):**
1. Log into Binance
2. Go to Account → API Management
3. Create API with permissions:
   - Enable Reading
   - Enable Spot Trading
   - Restrict to your IP (optional but recommended)
4. Save the API Key and Secret Key

### 3. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd crypto-trading-ai

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

### 4. Docker Setup (Easiest)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop services
docker-compose down
```

### 5. Manual Setup (Advanced)

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3-pip

# Install CUDA drivers for RTX 4080
# Follow NVIDIA's guide: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

# Install dependencies
pip install -r requirements.txt

# Install and start databases
docker run -d --name influxdb -p 8086:8086 influxdb:2.7-alpine
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Initialize database
psql -h localhost -U postgres -f scripts/init.sql

# Run the bot
python main.py
```

## Configuration

Edit `config/settings.py` to customize:

```python
# Enable/disable strategies
STRATEGIES = {
    'scalping': {
        'enabled': True,  # Fast trades, small profits
        'pairs': ['BTC/USDT', 'ETH/USDT']
    },
    'arbitrage': {
        'enabled': True,  # Risk-free profit between exchanges
        'min_spread': 0.005  # 0.5% minimum
    },
    'pump_detection': {
        'enabled': False,  # Higher risk, disable initially
    }
}

# Risk settings
TRADING = {
    'max_position_size': 0.05,  # 5% of portfolio per trade
    'stop_loss_percent': 0.02,  # 2% stop loss
    'risk_per_trade': 0.01  # 1% risk per trade
}
```

## Strategy Overview

### For Beginners
Start with these conservative settings:
- Enable only **Arbitrage** (lowest risk)
- Set `max_position_size` to 0.02 (2%)
- Set `max_trade_amount_usd` to 500

### For Intermediate
- Enable **Scalping** and **Day Trading**
- Increase position sizes gradually
- Monitor performance daily

### For Advanced
- Enable all strategies including **Pump Detection**
- Optimize ML models with your data
- Customize technical indicators

## Monitoring

### Grafana Dashboard
Access at `http://localhost:3000` (admin/admin)
- Real-time P&L tracking
- Position monitoring
- Risk metrics
- Strategy performance

### Logs
```bash
# View live logs
docker-compose logs -f trading-bot

# View specific strategy
docker-compose logs -f trading-bot | grep scalping
```

### Performance Metrics
The bot tracks:
- Win rate per strategy
- Sharpe ratio
- Maximum drawdown
- Daily/weekly/monthly returns

## Safety Features

1. **Circuit Breakers**: Auto-stops trading on 3% loss
2. **Position Limits**: Max 10 concurrent positions
3. **Daily Loss Limit**: 5% maximum daily loss
4. **Correlation Checks**: Prevents concentrated risk
5. **Order Validation**: Pre-trade risk checks

## Troubleshooting

### "GPU not available"
```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch GPU
python -c "import torch; print(torch.cuda.is_available())"
```

### "Exchange connection failed"
- Verify API keys in `.env`
- Check IP whitelist on exchange
- Ensure 2FA is not required for API

### "Insufficient balance"
- Minimum trade sizes: $50 on most exchanges
- Check available balance: `docker-compose exec trading-bot python -c "..."`

## Advanced Features

### Custom ML Models
Place trained models in `models/` directory:
```python
# Train your own pump detector
python scripts/train_pump_detector.py --data historical_pumps.csv
```

### Strategy Development
Create new strategies in `src/strategies/`:
```python
class MyStrategy(BaseStrategy):
    async def analyze(self, symbol: str):
        # Your logic here
        pass
```

### Backtesting
```bash
python scripts/backtest.py --strategy scalping --start 2024-01-01 --end 2024-12-31
```

## Security

1. **Never share your API keys**
2. Use read-only keys for testing
3. Enable IP whitelist on exchanges
4. Use separate API keys per strategy
5. Store keys encrypted in production

## Support

- Issues: Create GitHub issue
- Documentation: See `/docs` folder
- Community: Join our Discord

## Disclaimer

Cryptocurrency trading carries significant risk. This software is for educational purposes. Always:
- Start with small amounts
- Test thoroughly before live trading
- Never invest more than you can lose
- Understand each strategy's risks
- Monitor actively during initial use

## License

See LICENSE file
