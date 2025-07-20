# New Listing Detection Strategy

## Overview

The New Listing Detection Strategy is a comprehensive system designed to identify and trade newly listed cryptocurrencies before they experience significant price movements. It monitors multiple sources to find opportunities at different stages of a token's lifecycle.

## Key Features

### 1. **Multi-Stage Opportunity Detection**
- **Presale Monitoring**: Tracks ICO/IDO/IEO opportunities before tokens hit exchanges
- **DEX Monitoring**: Detects new pairs on decentralized exchanges (Uniswap, PancakeSwap)
- **CEX Monitoring**: Tracks new listings on centralized exchanges (MEXC, KuCoin, Gate.io, Binance)

### 2. **Machine Learning Integration**
- **Presale Success Prediction**: ML model to evaluate presale potential
- **DEX Success Prediction**: Analyzes liquidity and contract quality
- **Exit Timing Optimization**: ML-driven exit signals for maximum profit
- **Source Reliability Analysis**: Tracks which information sources are most accurate

### 3. **Comprehensive Source Monitoring**
- **News Aggregation**: Monitors crypto news sites via RSS and web scraping
- **Social Media Tracking**: Twitter, Reddit, Telegram, Discord monitoring
- **Exchange APIs**: Direct monitoring of exchange announcements
- **Blockchain Events**: Web3 integration for DEX pair creation events

### 4. **Risk Management**
- **Position Sizing**: Higher risk opportunities get smaller allocations
- **Confidence Scoring**: ML-based confidence scores for each opportunity
- **Stop Loss/Take Profit**: Automated exit strategies
- **Source Validation**: Cross-references multiple sources to avoid false signals

## Configuration

The strategy is configured in `config/settings.py`:

```python
'new_listing_detection': {
    'enabled': True,
    'monitor_exchanges': ['mexc', 'kucoin', 'gate', 'binance'],
    'monitor_dex': ['uniswap', 'pancakeswap'],
    'max_presale_amount': 1000,  # USD per presale
    'max_listing_amount': 5000,  # USD per new listing
    'confidence_threshold': 0.7,
    'exit_strategy': {
        'take_profit': 2.0,  # 200% gain
        'stop_loss': 0.5,  # 50% loss
        'time_based_exit': 72  # hours
    }
}
```

## Components

### 1. **PresaleMonitor** (`presale_monitor.py`)
- Monitors presale platforms (PinkSale, DxSale, Polkastarter, Seedify)
- Analyzes team, tokenomics, and community metrics
- Provides early entry opportunities with highest risk/reward

### 2. **ExchangeMonitor** (`exchange_monitor.py`)
- Monitors exchange APIs and announcement pages
- Detects both announcements and actual listing events
- Tracks which exchanges list tokens first

### 3. **NewsMonitor** (`news_monitor.py`)
- Aggregates news from crypto news sites
- Monitors social media for early signals
- Performs sentiment analysis on content
- Tracks source reliability over time

### 4. **ListingMLModels** (`listing_ml_models.py`)
- Predicts presale success probability
- Evaluates DEX listing potential
- Optimizes exit timing
- Analyzes information source reliability

## Performance Tracking

The strategy includes comprehensive performance tracking:

- **Sub-strategy Performance**: Tracks presale vs DEX vs CEX performance
- **Source Reliability**: Identifies which sources provide the best signals
- **Win Rate & P&L**: Detailed metrics for each type of opportunity
- **ML Model Performance**: Tracks prediction accuracy over time

Performance can be viewed in the web UI under the "Performance" tab, showing:
- Overall strategy P&L
- Win rate by opportunity type
- Best performing information sources
- Recent trades and active positions

## Usage

1. **Enable the strategy** in `config/settings.py`
2. **Configure API credentials** for social media monitoring (optional but recommended)
3. **Set risk parameters** according to your risk tolerance
4. **Monitor the web UI** for new opportunities and performance

## Safety Features

- **Honeypot Detection**: Checks for scam tokens on DEXs
- **Liquidity Analysis**: Ensures sufficient liquidity before entering
- **Contract Verification**: Checks if contracts are verified
- **Multi-source Validation**: Requires confirmation from multiple sources for high-confidence trades

## Tips for Success

1. **Start Small**: Use minimum position sizes while the ML models learn
2. **Monitor Performance**: Check which sources and exchanges perform best
3. **Adjust Thresholds**: Fine-tune confidence thresholds based on results
4. **Enable Social Monitoring**: Better signals with Twitter/Reddit API access
5. **Regular Updates**: Keep exchange APIs and monitoring tools updated

## Risks

- **High Volatility**: New listings can be extremely volatile
- **Rug Pulls**: Despite safety features, scams are possible
- **Liquidity Issues**: May be difficult to exit large positions
- **Technical Failures**: API rate limits or connection issues

Always use proper risk management and never invest more than you can afford to lose.
