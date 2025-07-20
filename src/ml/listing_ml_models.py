import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class ListingMLModels:
    """ML models for new crypto listing predictions"""
    
    def __init__(self):
        self.models_dir = "models/listing_detection"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Initialize models
        self.presale_success_model = None
        self.dex_success_model = None
        self.exit_timing_model = None
        self.source_reliability_model = None
        self.price_prediction_model = None
        
        # Feature scalers
        self.presale_scaler = StandardScaler()
        self.dex_scaler = StandardScaler()
        self.exit_scaler = StandardScaler()
        
        # Load existing models if available
        self.load_models()
        
        # Performance tracking
        self.model_performance = {
            'presale_accuracy': [],
            'dex_accuracy': [],
            'exit_timing_accuracy': [],
            'price_prediction_rmse': []
        }
    
    def predict_presale_success(self, features: Dict) -> float:
        """Predict presale success probability"""
        try:
            # Extract and prepare features
            feature_vector = self._prepare_presale_features(features)
            
            if self.presale_success_model is None:
                # Use rule-based fallback
                return self._presale_heuristic_score(features)
            
            # Scale features
            scaled_features = self.presale_scaler.transform([feature_vector])
            
            # Predict probability
            prob = self.presale_success_model.predict_proba(scaled_features)[0][1]
            
            # Apply confidence adjustment based on data quality
            confidence_factor = self._calculate_confidence_factor(features)
            
            return prob * confidence_factor
            
        except Exception as e:
            logger.error(f"Presale prediction error: {e}")
            return 0.5
    
    def predict_dex_success(self, features: Dict) -> float:
        """Predict DEX listing success probability"""
        try:
            feature_vector = self._prepare_dex_features(features)
            
            if self.dex_success_model is None:
                return self._dex_heuristic_score(features)
            
            scaled_features = self.dex_scaler.transform([feature_vector])
            prob = self.dex_success_model.predict_proba(scaled_features)[0][1]
            
            # Adjust for market conditions
            market_factor = self._get_market_condition_factor()
            
            return prob * market_factor
            
        except Exception as e:
            logger.error(f"DEX prediction error: {e}")
            return 0.5
    
    def predict_exit_timing(self, features: Dict) -> float:
        """Predict probability that now is good time to exit"""
        try:
            feature_vector = self._prepare_exit_features(features)
            
            if self.exit_timing_model is None:
                return self._exit_heuristic_score(features)
            
            scaled_features = self.exit_scaler.transform([feature_vector])
            
            # Predict exit probability
            exit_prob = self.exit_timing_model.predict_proba(scaled_features)[0][1]
            
            # Apply risk adjustment
            risk_factor = self._calculate_risk_factor(features)
            
            return exit_prob * risk_factor
            
        except Exception as e:
            logger.error(f"Exit timing prediction error: {e}")
            return 0.5
    
    def predict_price_movement(self, symbol: str, features: Dict, horizon_hours: int = 24) -> Dict:
        """Predict price movement for given time horizon"""
        try:
            feature_vector = self._prepare_price_features(features)
            
            if self.price_prediction_model is None:
                return {
                    'predicted_change': 0.0,
                    'confidence': 0.5,
                    'predicted_high': features.get('current_price', 0) * 1.1,
                    'predicted_low': features.get('current_price', 0) * 0.9
                }
            
            # Predict price change percentage
            predicted_change = self.price_prediction_model.predict([feature_vector])[0]
            
            # Calculate confidence based on recent model performance
            confidence = self._calculate_prediction_confidence(features)
            
            current_price = features.get('current_price', 0)
            
            return {
                'predicted_change': predicted_change,
                'confidence': confidence,
                'predicted_price': current_price * (1 + predicted_change),
                'predicted_high': current_price * (1 + predicted_change + 0.1),
                'predicted_low': current_price * (1 + predicted_change - 0.1)
            }
            
        except Exception as e:
            logger.error(f"Price prediction error: {e}")
            return {'predicted_change': 0.0, 'confidence': 0.0}
    
    def analyze_source_reliability(self, source_history: List[Dict]) -> float:
        """Analyze historical reliability of information source"""
        if not source_history:
            return 0.5
        
        try:
            # Calculate success metrics
            successful_calls = sum(1 for s in source_history if s.get('outcome', 0) > 0)
            total_calls = len(source_history)
            
            if total_calls < 5:
                return 0.5  # Not enough data
            
            base_reliability = successful_calls / total_calls
            
            # Factor in timing accuracy
            timing_scores = []
            for signal in source_history:
                if 'hours_early' in signal and signal['hours_early'] > 0:
                    # Reward early signals
                    timing_score = min(signal['hours_early'] / 24, 1.0)
                    timing_scores.append(timing_score)
            
            avg_timing = np.mean(timing_scores) if timing_scores else 0.5
            
            # Factor in magnitude of successful calls
            magnitude_scores = []
            for signal in source_history:
                if signal.get('outcome', 0) > 0:
                    # Normalize outcome to 0-1 scale
                    magnitude = min(signal['outcome'] / 100, 1.0)
                    magnitude_scores.append(magnitude)
            
            avg_magnitude = np.mean(magnitude_scores) if magnitude_scores else 0.5
            
            # Weighted reliability score
            reliability = (
                base_reliability * 0.5 +
                avg_timing * 0.3 +
                avg_magnitude * 0.2
            )
            
            return min(max(reliability, 0.1), 0.95)
            
        except Exception as e:
            logger.error(f"Source reliability analysis error: {e}")
            return 0.5
    
    def train_models(self, training_data: Dict):
        """Train all models with new data"""
        try:
            # Train presale model
            if 'presale_data' in training_data and len(training_data['presale_data']) > 50:
                self._train_presale_model(training_data['presale_data'])
            
            # Train DEX model
            if 'dex_data' in training_data and len(training_data['dex_data']) > 50:
                self._train_dex_model(training_data['dex_data'])
            
            # Train exit timing model
            if 'exit_data' in training_data and len(training_data['exit_data']) > 100:
                self._train_exit_model(training_data['exit_data'])
            
            # Train price prediction model
            if 'price_data' in training_data and len(training_data['price_data']) > 200:
                self._train_price_model(training_data['price_data'])
            
            # Save models
            self.save_models()
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
    
    def _train_presale_model(self, data: List[Dict]):
        """Train presale success prediction model"""
        # Prepare training data
        X = []
        y = []
        
        for sample in data:
            features = self._prepare_presale_features(sample)
            label = 1 if sample['roi'] > 2.0 else 0  # Success = 2x or more
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.presale_scaler.fit_transform(X)
        
        # Train ensemble model
        self.presale_success_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.presale_success_model.fit(X_scaled, y)
        
        logger.info(f"Trained presale model with {len(X)} samples")
    
    def _train_dex_model(self, data: List[Dict]):
        """Train DEX success prediction model"""
        X = []
        y = []
        
        for sample in data:
            features = self._prepare_dex_features(sample)
            label = 1 if sample['price_change_24h'] > 0.5 else 0
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        X_scaled = self.dex_scaler.fit_transform(X)
        
        # Use gradient boosting for DEX predictions
        self.dex_success_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.dex_success_model.fit(X_scaled, y)
        
        logger.info(f"Trained DEX model with {len(X)} samples")
    
    def _train_exit_model(self, data: List[Dict]):
        """Train exit timing model"""
        X = []
        y = []
        
        for sample in data:
            features = self._prepare_exit_features(sample)
            # Label: 1 if exiting at this point was profitable
            label = 1 if sample['exit_profit'] > sample['hold_profit'] else 0
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        X_scaled = self.exit_scaler.fit_transform(X)
        
        # Neural network for complex exit patterns
        self.exit_timing_model = MLPClassifier(
            hidden_layer_sizes=(50, 30, 10),
            activation='relu',
            max_iter=500,
            random_state=42
        )
        
        self.exit_timing_model.fit(X_scaled, y)
        
        logger.info(f"Trained exit model with {len(X)} samples")
    
    def _train_price_model(self, data: List[Dict]):
        """Train price prediction model"""
        X = []
        y = []
        
        for sample in data:
            features = self._prepare_price_features(sample)
            # Target: price change percentage
            target = sample['price_change_24h']
            X.append(features)
            y.append(target)
        
        X = np.array(X)
        y = np.array(y)
        
        # Gradient boosting for price predictions
        self.price_prediction_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            random_state=42
        )
        
        self.price_prediction_model.fit(X, y)
        
        logger.info(f"Trained price model with {len(X)} samples")
    
    def _prepare_presale_features(self, data: Dict) -> List[float]:
        """Extract features for presale prediction"""
        return [
            data.get('hard_cap', 1000000),
            data.get('soft_cap', 500000),
            data.get('token_price', 0.01),
            data.get('total_supply', 1000000000),
            data.get('team_score', 0.5),
            data.get('community_size', 1000),
            data.get('social_engagement', 0.5),
            data.get('whitepaper_score', 0.5),
            data.get('audit_score', 0.5),
            data.get('market_cap_at_launch', 1000000),
            data.get('vesting_period_days', 180),
            data.get('team_allocation_pct', 20),
            data.get('liquidity_lock_days', 365),
            data.get('marketing_budget_pct', 10),
            data.get('similar_projects_success_rate', 0.3)
        ]
    
    def _prepare_dex_features(self, data: Dict) -> List[float]:
        """Extract features for DEX listing prediction"""
        return [
            data.get('initial_liquidity', 10000),
            data.get('liquidity_locked', 1),
            data.get('holder_count', 100),
            data.get('contract_verified', 1),
            data.get('honeypot_score', 0),
            data.get('buy_tax', 5),
            data.get('sell_tax', 5),
            data.get('max_wallet_pct', 2),
            data.get('creator_holdings_pct', 10),
            data.get('sniper_bot_activity', 0),
            data.get('social_mentions', 50),
            data.get('unique_traders_1h', 20),
            data.get('volume_1h', 5000),
            data.get('price_impact_2pct', 0.02),
            data.get('market_sentiment_score', 0.5)
        ]
    
    def _prepare_exit_features(self, data: Dict) -> List[float]:
        """Extract features for exit timing prediction"""
        return [
            data.get('pnl_pct', 0),
            data.get('hold_time_hours', 1),
            data.get('volume_ratio', 1.0),
            data.get('rsi', 50),
            data.get('bb_position', 0.5),
            data.get('price_momentum_1h', 0),
            data.get('volume_momentum_1h', 0),
            data.get('buy_sell_ratio', 1.0),
            data.get('whale_activity', 0),
            data.get('social_sentiment_change', 0),
            data.get('market_fear_greed', 50),
            data.get('btc_correlation', 0.5),
            data.get('time_since_ath', 24),
            data.get('distance_from_ath_pct', 10),
            data.get('listing_type_risk', 0.5)
        ]
    
    def _prepare_price_features(self, data: Dict) -> List[float]:
        """Extract features for price prediction"""
        return [
            data.get('current_price', 1.0),
            data.get('volume_24h', 100000),
            data.get('market_cap', 1000000),
            data.get('holder_count', 1000),
            data.get('whale_holdings_pct', 20),
            data.get('social_volume', 100),
            data.get('sentiment_score', 0.5),
            data.get('technical_score', 0.5),
            data.get('momentum_score', 0.5),
            data.get('volatility_30d', 0.5),
            data.get('correlation_btc', 0.5),
            data.get('exchange_netflow', 0),
            data.get('active_addresses', 1000),
            data.get('transaction_count', 5000),
            data.get('news_sentiment', 0.5)
        ]
    
    def _presale_heuristic_score(self, features: Dict) -> float:
        """Rule-based presale scoring when ML model unavailable"""
        score = 0.5
        
        # Positive factors
        if features.get('audit_score', 0) > 0.8:
            score += 0.1
        if features.get('team_score', 0) > 0.7:
            score += 0.1
        if features.get('liquidity_lock_days', 0) > 365:
            score += 0.1
        if features.get('community_size', 0) > 5000:
            score += 0.1
        
        # Negative factors
        if features.get('team_allocation_pct', 100) > 30:
            score -= 0.2
        if features.get('vesting_period_days', 0) < 90:
            score -= 0.1
        
        return min(max(score, 0.1), 0.9)
    
    def _dex_heuristic_score(self, features: Dict) -> float:
        """Rule-based DEX scoring when ML model unavailable"""
        score = 0.5
        
        # Check critical factors
        if features.get('honeypot_score', 1) > 0:
            return 0.1  # Likely scam
        
        if features.get('liquidity_locked', 0) == 0:
            score -= 0.3
        
        if features.get('initial_liquidity', 0) < 5000:
            score -= 0.2
        
        if features.get('buy_tax', 100) > 10 or features.get('sell_tax', 100) > 10:
            score -= 0.3
        
        if features.get('holder_count', 0) > 100:
            score += 0.1
        
        if features.get('unique_traders_1h', 0) > 50:
            score += 0.2
        
        return min(max(score, 0.1), 0.9)
    
    def _exit_heuristic_score(self, features: Dict) -> float:
        """Rule-based exit scoring when ML model unavailable"""
        pnl = features.get('pnl_pct', 0)
        hold_time = features.get('hold_time_hours', 0)
        rsi = features.get('rsi', 50)
        
        # Strong exit signals
        if pnl > 2.0:  # 200% profit
            return 0.9
        
        if pnl < -0.5:  # 50% loss
            return 0.9
        
        if rsi > 80 and pnl > 0.5:  # Overbought with profit
            return 0.8
        
        if hold_time > 72 and pnl < 0.1:  # Stagnant position
            return 0.7
        
        # Hold signals
        if 0.2 < pnl < 0.8 and 40 < rsi < 60:
            return 0.3
        
        return 0.5
    
    def _calculate_confidence_factor(self, features: Dict) -> float:
        """Calculate confidence adjustment based on data quality"""
        confidence = 1.0
        
        # Reduce confidence for missing/suspicious data
        critical_fields = ['team_score', 'audit_score', 'liquidity_lock_days']
        for field in critical_fields:
            if field not in features or features[field] == 0:
                confidence *= 0.8
        
        return confidence
    
    def _get_market_condition_factor(self) -> float:
        """Get current market condition multiplier"""
        # This would integrate with market data
        # For now, return neutral
        return 1.0
    
    def _calculate_risk_factor(self, features: Dict) -> float:
        """Calculate risk-adjusted multiplier for exit decisions"""
        listing_type = features.get('listing_type', 'unknown')
        
        risk_factors = {
            'presale': 1.2,  # Exit earlier for high-risk presales
            'dex': 1.1,      # Moderate risk
            'cex': 0.9       # Can hold longer for CEX listings
        }
        
        return risk_factors.get(listing_type, 1.0)
    
    def _calculate_prediction_confidence(self, features: Dict) -> float:
        """Calculate confidence in price prediction"""
        # Base confidence on data quality and market conditions
        base_confidence = 0.5
        
        # Increase confidence with more data points
        if features.get('volume_24h', 0) > 1000000:
            base_confidence += 0.1
        
        if features.get('holder_count', 0) > 5000:
            base_confidence += 0.1
        
        if features.get('active_addresses', 0) > 1000:
            base_confidence += 0.1
        
        # Decrease confidence in volatile conditions
        if features.get('volatility_30d', 0) > 1.0:
            base_confidence -= 0.2
        
        return min(max(base_confidence, 0.2), 0.8)
    
    def save_models(self):
        """Save all trained models"""
        try:
            if self.presale_success_model:
                joblib.dump(self.presale_success_model, 
                           f"{self.models_dir}/presale_model.pkl")
                joblib.dump(self.presale_scaler,
                           f"{self.models_dir}/presale_scaler.pkl")
            
            if self.dex_success_model:
                joblib.dump(self.dex_success_model,
                           f"{self.models_dir}/dex_model.pkl")
                joblib.dump(self.dex_scaler,
                           f"{self.models_dir}/dex_scaler.pkl")
            
            if self.exit_timing_model:
                joblib.dump(self.exit_timing_model,
                           f"{self.models_dir}/exit_model.pkl")
                joblib.dump(self.exit_scaler,
                           f"{self.models_dir}/exit_scaler.pkl")
            
            if self.price_prediction_model:
                joblib.dump(self.price_prediction_model,
                           f"{self.models_dir}/price_model.pkl")
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load pre-trained models if available"""
        try:
            presale_path = f"{self.models_dir}/presale_model.pkl"
            if os.path.exists(presale_path):
                self.presale_success_model = joblib.load(presale_path)
                self.presale_scaler = joblib.load(f"{self.models_dir}/presale_scaler.pkl")
                logger.info("Loaded presale model")
            
            dex_path = f"{self.models_dir}/dex_model.pkl"
            if os.path.exists(dex_path):
                self.dex_success_model = joblib.load(dex_path)
                self.dex_scaler = joblib.load(f"{self.models_dir}/dex_scaler.pkl")
                logger.info("Loaded DEX model")
            
            exit_path = f"{self.models_dir}/exit_model.pkl"
            if os.path.exists(exit_path):
                self.exit_timing_model = joblib.load(exit_path)
                self.exit_scaler = joblib.load(f"{self.models_dir}/exit_scaler.pkl")
                logger.info("Loaded exit timing model")
            
            price_path = f"{self.models_dir}/price_model.pkl"
            if os.path.exists(price_path):
                self.price_prediction_model = joblib.load(price_path)
                logger.info("Loaded price prediction model")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_model_performance(self) -> Dict:
        """Get current model performance metrics"""
        return {
            'presale_model': {
                'accuracy': np.mean(self.model_performance['presale_accuracy'][-100:])
                if self.model_performance['presale_accuracy'] else 0,
                'samples_processed': len(self.model_performance['presale_accuracy'])
            },
            'dex_model': {
                'accuracy': np.mean(self.model_performance['dex_accuracy'][-100:])
                if self.model_performance['dex_accuracy'] else 0,
                'samples_processed': len(self.model_performance['dex_accuracy'])
            },
            'exit_model': {
                'accuracy': np.mean(self.model_performance['exit_timing_accuracy'][-100:])
                if self.model_performance['exit_timing_accuracy'] else 0,
                'samples_processed': len(self.model_performance['exit_timing_accuracy'])
            },
            'price_model': {
                'rmse': np.mean(self.model_performance['price_prediction_rmse'][-100:])
                if self.model_performance['price_prediction_rmse'] else 0,
                'samples_processed': len(self.model_performance['price_prediction_rmse'])
            }
        }
