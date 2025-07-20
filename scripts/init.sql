-- Initialize crypto trading database

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchange credentials (encrypted)
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    exchange_name VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    encrypted_secret TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading strategies configuration
CREATE TABLE IF NOT EXISTS strategy_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade history
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(100),
    exchange VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10),
    amount DECIMAL(20, 8),
    price DECIMAL(20, 8),
    fee DECIMAL(20, 8),
    pnl DECIMAL(20, 8),
    order_id VARCHAR(100),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- ML model metadata
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    accuracy DECIMAL(5, 4),
    feature_set JSONB,
    parameters JSONB,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social media signals
CREATE TABLE IF NOT EXISTS social_signals (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    signal_type VARCHAR(50),
    sentiment_score DECIMAL(5, 4),
    confidence DECIMAL(5, 4),
    metadata JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Arbitrage opportunities log
CREATE TABLE IF NOT EXISTS arbitrage_log (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    buy_exchange VARCHAR(50),
    sell_exchange VARCHAR(50),
    buy_price DECIMAL(20, 8),
    sell_price DECIMAL(20, 8),
    spread_percentage DECIMAL(10, 6),
    estimated_profit DECIMAL(20, 8),
    executed BOOLEAN DEFAULT false,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_trades_user_date ON trades(user_id, executed_at);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_performance_user_date ON performance_metrics(user_id, date);
CREATE INDEX idx_social_signals_symbol ON social_signals(symbol, detected_at);
CREATE INDEX idx_arbitrage_symbol ON arbitrage_log(symbol, detected_at);
