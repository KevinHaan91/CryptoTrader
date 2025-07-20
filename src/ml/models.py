from .listing_ml_models import ListingMLModels
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    """Centralized ML model management"""
    
    def __init__(self):
        # Initialize all model types
        self.listing_models = ListingMLModels()
        
        # Other models can be added here
        self.pump_detection_model = None
        self.arbitrage_model = None
        self.technical_model = None
        
        # Model performance tracking
        self.model_metrics = {
            'listing_models': {
                'predictions': [],
                'accuracy': 0.0,
                'last_updated': None
            }
        }
    
    # Listing detection models
    def predict_presale_success(self, features: Dict) -> float:
        """Predict presale success probability"""
        return self.listing_models.predict_presale_success(features)
    
    def predict_dex_success(self, features: Dict) -> float:
        """Predict DEX listing success probability"""
        return self.listing_models.predict_dex_success(features)
    
    def predict_exit_timing(self, features: Dict) -> float:
        """Predict optimal exit timing"""
        return self.listing_models.predict_exit_timing(features)
    
    def predict_price_movement(self, symbol: str, features: Dict, horizon_hours: int = 24) -> Dict:
        """Predict price movement"""
        return self.listing_models.predict_price_movement(symbol, features, horizon_hours)
    
    def analyze_source_reliability(self, source_history: List[Dict]) -> float:
        """Analyze information source reliability"""
        return self.listing_models.analyze_source_reliability(source_history)
    
    def predict_news_impact(self, features: Dict) -> float:
        """Predict impact of news on token price"""
        # Simple heuristic for now
        sentiment = features.get('sentiment', 0)
        source_weight = features.get('source_weight', 0.5)
        mention_count = features.get('mention_count', 0)
        opportunity_keywords = features.get('opportunity_keywords', 0.5)
        
        # Weighted score
        impact = (
            (sentiment + 1) / 2 * 0.3 +  # Normalize sentiment to 0-1
            source_weight * 0.2 +
            min(mention_count / 10, 1.0) * 0.2 +
            opportunity_keywords * 0.3
        )
        
        return min(max(impact, 0.0), 1.0)
    
    # Model training and updates
    def train_models(self, training_data: Dict):
        """Train all models with new data"""
        if 'listing_data' in training_data:
            self.listing_models.train_models(training_data['listing_data'])
        
        # Train other models as needed
        logger.info("Model training completed")
    
    def update_model_performance(self, model_type: str, prediction: float, actual: float):
        """Update model performance metrics"""
        if model_type in self.model_metrics:
            metrics = self.model_metrics[model_type]
            
            # Store prediction vs actual
            metrics['predictions'].append({
                'predicted': prediction,
                'actual': actual,
                'error': abs(prediction - actual)
            })
            
            # Keep last 1000 predictions
            metrics['predictions'] = metrics['predictions'][-1000:]
            
            # Calculate rolling accuracy
            if len(metrics['predictions']) > 10:
                recent = metrics['predictions'][-100:]
                errors = [p['error'] for p in recent]
                metrics['accuracy'] = 1.0 - np.mean(errors)
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics for all models"""
        performance = {
            'listing_models': self.listing_models.get_model_performance(),
            'overall_metrics': self.model_metrics
        }
        
        return performance
    
    # Utility methods
    def save_all_models(self):
        """Save all trained models"""
        self.listing_models.save_models()
        logger.info("All models saved")
    
    def load_all_models(self):
        """Load all saved models"""
        self.listing_models.load_models()
        logger.info("All models loaded")
