import os
from dotenv import load_dotenv

load_dotenv()

# Exchange Configuration
EXCHANGES = {
    'kraken': {
        'api_key': os.getenv('KRAKEN_API_KEY'),
        'api_secret': os.getenv('KRAKEN_API_SECRET'),
        'rate_limit': 10,
        'testnet': False
    },
    'binance': {
        'api_key': os.getenv('BINANCE_API_KEY'),
        'api_secret': os.getenv('BINANCE_API_SECRET'),
        'rate_limit': 1200,
        'testnet': False
    },
    'coinbase': {
        'api_key': os.getenv('COINBASE_API_KEY'),
        'api_secret': os.getenv('COINBASE_API_SECRET'),
        'passphrase': os.getenv('COINBASE_PASSPHRASE'),
        'rate_limit': 10,
        'testnet': False
    }
}

# Trading Configuration
TRADING = {
    'max_position_size': 0.05,  # 5% of portfolio per position
    'max_open_positions': 10,
    'min_trade_amount_usd': 50,
    'max_trade_amount_usd': 5000,
    'stop_loss_percent': 0.02,  # 2%
    'take_profit_percent': 0.05,  # 5%
    'enable_leverage': False,
    'max_leverage': 3,
    'risk_per_trade': 0.01  # 1% of portfolio
}

# Strategy Configuration
STRATEGIES = {
    'scalping': {
        'enabled': True,
        'timeframe': '1m',
        'indicators': ['ema_5', 'ema_13', 'rsi_5', 'volume_delta'],
        'min_profit_target': 0.002,  # 0.2%
        'max_hold_time': 300,  # 5 minutes
        'pairs': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    },
    'arbitrage': {
        'enabled': True,
        'min_spread': 0.005,  # 0.5%
        'max_execution_time': 30,  # seconds
        'check_interval': 1  # seconds
    },
    'pump_detection': {
        'enabled': True,
        'volume_spike_threshold': 3.0,  # 300% normal volume
        'price_spike_threshold': 0.05,  # 5% in 5 minutes
        'social_sentiment_weight': 0.3
    },
    'day_trading': {
        'enabled': True,
        'timeframe': '15m',
        'indicators': ['macd', 'rsi', 'bollinger', 'volume'],
        'confirmation_candles': 2
    },
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
        },
        'social_monitoring': {
            'twitter': True,
            'reddit': True,
            'telegram': True,
            'news_sites': True
        }
    }
}

# Machine Learning Configuration
ML_CONFIG = {
    'use_gpu': True,
    'gpu_device': 0,  # RTX 4080
    'batch_size': 256,
    'model_update_interval': 3600,  # 1 hour
    'feature_window': 100,
    'prediction_horizon': 5,
    'models': {
        'xgboost': {'enabled': True, 'gpu_hist': True},
        'lstm': {'enabled': True, 'layers': 3, 'units': 128},
        'transformer': {'enabled': True, 'heads': 8, 'layers': 4}
    }
}

# Database Configuration
DATABASE = {
    'influxdb': {
        'url': os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        'token': os.getenv('INFLUXDB_TOKEN'),
        'org': 'crypto-trading',
        'bucket': 'market-data'
    },
    'postgresql': {
        'url': os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/crypto_trading')
    },
    'redis': {
        'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    }
}

# WebSocket Configuration
WEBSOCKET = {
    'reconnect_interval': 5,
    'heartbeat_interval': 30,
    'max_reconnect_attempts': 10,
    'connection_timeout': 10
}

# Risk Management
RISK_MANAGEMENT = {
    'max_daily_loss': 0.05,  # 5%
    'max_drawdown': 0.10,  # 10%
    'correlation_limit': 0.7,
    'var_confidence': 0.95,
    'circuit_breaker_threshold': 0.03  # 3% loss triggers pause
}

# Monitoring Configuration
MONITORING = {
    'prometheus_port': 9090,
    'metrics_interval': 10,
    'alert_channels': ['email', 'telegram'],
    'log_level': 'INFO'
}
