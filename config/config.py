import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Trading Mode
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    # Exchange Configuration
    EXCHANGES = {
        'binance': {
            'api_key': os.getenv('BINANCE_API_KEY'),
            'api_secret': os.getenv('BINANCE_API_SECRET'),
            'testnet': PAPER_TRADING,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True
            }
        },
        'kucoin': {
            'api_key': os.getenv('KUCOIN_API_KEY'),
            'api_secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_PASSWORD'),
            'sandbox': PAPER_TRADING
        },
        'bybit': {
            'api_key': os.getenv('BYBIT_API_KEY'),
            'api_secret': os.getenv('BYBIT_API_SECRET'),
            'testnet': PAPER_TRADING
        },
        'gate': {
            'api_key': os.getenv('GATE_API_KEY'),
            'api_secret': os.getenv('GATE_API_SECRET')
        }
    }
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/crypto_trading')
    INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'your-influxdb-token')
    INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'crypto-trading')
    INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'market-data')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Trading Configuration
    TRADING = {
        'max_position_size_percent': float(os.getenv('MAX_POSITION_SIZE', '5')),
        'stop_loss_percent': float(os.getenv('STOP_LOSS_PERCENT', '2')),
        'take_profit_percent': float(os.getenv('TAKE_PROFIT_PERCENT', '5')),
        'max_positions': int(os.getenv('MAX_POSITIONS', '10')),
        'min_order_size_usdt': float(os.getenv('MIN_ORDER_SIZE', '10')),
    }
    
    # Risk Management
    RISK_MANAGEMENT = {
        'max_daily_loss_usd': float(os.getenv('MAX_DAILY_LOSS', '500')),
        'max_drawdown_percent': float(os.getenv('MAX_DRAWDOWN', '10')),
        'position_sizing_method': os.getenv('POSITION_SIZING', 'kelly'),  # kelly, fixed, risk_parity
        'kelly_fraction': float(os.getenv('KELLY_FRACTION', '0.25')),  # Conservative Kelly
    }
    
    # Strategy Configuration
    STRATEGIES = {
        'scalping': {
            'enabled': os.getenv('ENABLE_SCALPING', 'true').lower() == 'true',
            'timeframe': '1m',
            'min_profit_percent': 0.3,
            'max_hold_time_minutes': 15
        },
        'arbitrage': {
            'enabled': os.getenv('ENABLE_ARBITRAGE', 'true').lower() == 'true',
            'min_spread_percent': 0.5,
            'max_execution_time_seconds': 30
        },
        'day_trading': {
            'enabled': os.getenv('ENABLE_DAY_TRADING', 'false').lower() == 'true',
            'timeframe': '15m',
            'indicators': ['RSI', 'MACD', 'BB']
        },
        'swing_trading': {
            'enabled': os.getenv('ENABLE_SWING_TRADING', 'false').lower() == 'true',
            'timeframe': '4h',
            'max_hold_days': 7
        },
        'pump_detection': {
            'enabled': os.getenv('ENABLE_PUMP_DETECTION', 'true').lower() == 'true',
            'confidence_threshold': 80,
            'social_sources': ['twitter', 'telegram', 'discord']
        }
    }
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # Social Media APIs (for pump detection)
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    
    # Notification Configuration
    NOTIFICATIONS = {
        'telegram': {
            'enabled': os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true',
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID')
        },
        'email': {
            'enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'to_address': os.getenv('EMAIL_TO')
        }
    }
    
    # ML Model Configuration
    ML_MODELS = {
        'update_frequency_hours': int(os.getenv('MODEL_UPDATE_HOURS', '24')),
        'training_data_days': int(os.getenv('TRAINING_DATA_DAYS', '730')),  # 2 years
        'use_gpu': os.getenv('USE_GPU', 'true').lower() == 'true',
        'model_storage_path': os.getenv('MODEL_PATH', './models')
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/crypto_trading.log')
    
    # Security
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

# Create a global config instance
config = Config()
