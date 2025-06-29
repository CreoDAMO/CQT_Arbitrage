"""
Machine Learning Predictor for CQT Arbitrage
LSTM-based prediction model for liquidity drain and arbitrage success
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# TensorFlow/Keras imports - with graceful fallback
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TensorFlow not available: {e}")
    TENSORFLOW_AVAILABLE = False
    # Create dummy classes for type hints
    class Sequential: pass
    class load_model: pass
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    confidence: float
    predicted_price: float
    volatility: float
    liquidity_risk: float
    execution_probability: float

class LSTMPredictor:
    """LSTM-based predictor for arbitrage opportunities and liquidity analysis"""
    
    def __init__(self, model_path: str = "models/lstm_model.h5"):
        """Initialize the LSTM predictor"""
        
        self.model_path = model_path
        self.scaler = MinMaxScaler()
        self.model = None
        self.is_trained = False
        
        # Model parameters
        self.sequence_length = 60  # 60 time steps for prediction
        self.features = ['price', 'liquidity', 'volume', 'volatility']
        self.prediction_horizon = 5  # Predict 5 steps ahead
        
        # Training parameters
        self.batch_size = 32
        self.epochs = 100
        self.validation_split = 0.2
        
        # Check if TensorFlow is available
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available - ML predictions will use fallback methods")
            return
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self._load_model()
        
        # Performance tracking
        self.predictions_made = 0
        self.correct_predictions = 0
        self.prediction_accuracy = 0.0
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        
        if not TENSORFLOW_AVAILABLE:
            logger.info("TensorFlow not available - using fallback prediction methods")
            self.is_trained = False
            return
        
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                self.is_trained = True
                logger.info(f"Loaded pre-trained model from {self.model_path}")
            else:
                logger.info("No pre-trained model found, will train new model")
                self._build_model()
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._build_model()
    
    def _build_model(self):
        """Build LSTM neural network architecture"""
        
        self.model = Sequential([
            # First LSTM layer with return sequences
            LSTM(128, return_sequences=True, input_shape=(self.sequence_length, len(self.features))),
            Dropout(0.2),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            
            # Third LSTM layer
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            
            # Dense layers for final prediction
            Dense(50, activation='relu'),
            Dropout(0.1),
            Dense(25, activation='relu'),
            Dense(1, activation='sigmoid')  # Output probability/confidence
        ])
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mse']
        )
        
        logger.info("Built new LSTM model architecture")
    
    def prepare_training_data(self, historical_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare historical data for training"""
        
        if len(historical_data) < self.sequence_length + self.prediction_horizon:
            raise ValueError("Insufficient historical data for training")
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate additional features
        df['volatility'] = df['price'].rolling(window=10).std().fillna(0)
        df['volume'] = df['liquidity'].pct_change().abs().fillna(0)
        df['price_change'] = df['price'].pct_change().fillna(0)
        
        # Select features
        feature_columns = ['price', 'liquidity', 'volume', 'volatility']
        data = df[feature_columns].values
        
        # Normalize data
        data_scaled = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        
        for i in range(self.sequence_length, len(data_scaled) - self.prediction_horizon):
            # Input sequence
            X.append(data_scaled[i-self.sequence_length:i])
            
            # Target: success probability based on price movement
            future_prices = data_scaled[i:i+self.prediction_horizon, 0]  # Price column
            current_price = data_scaled[i-1, 0]
            
            # Calculate success probability (simplified)
            price_movement = abs(future_prices[-1] - current_price)
            volatility = np.std(future_prices)
            
            # Success probability based on predictable movement
            success_prob = min(1.0, max(0.0, (price_movement - volatility) / price_movement))
            y.append(success_prob)
        
        return np.array(X), np.array(y)
    
    def train_model(self, historical_data: List[Dict], save_model: bool = True):
        """Train the LSTM model with historical data"""
        
        try:
            logger.info("Starting model training...")
            
            # Prepare training data
            X, y = self.prepare_training_data(historical_data)
            
            logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
            
            # Setup callbacks
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=15,
                    restore_best_weights=True
                )
            ]
            
            if save_model:
                # Ensure model directory exists
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                
                callbacks.append(
                    ModelCheckpoint(
                        self.model_path,
                        monitor='val_loss',
                        save_best_only=True,
                        verbose=1
                    )
                )
            
            # Train model
            history = self.model.fit(
                X, y,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_split=self.validation_split,
                callbacks=callbacks,
                verbose=1
            )
            
            self.is_trained = True
            
            # Log training results
            final_loss = history.history['loss'][-1]
            final_val_loss = history.history['val_loss'][-1]
            
            logger.info(f"Training completed. Final loss: {final_loss:.4f}, "
                       f"Validation loss: {final_val_loss:.4f}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict_arbitrage_success(self, pool1, pool2, amount: float) -> float:
        """Predict success probability for arbitrage opportunity"""
        
        if not self.is_trained:
            logger.warning("Model not trained, returning default confidence")
            return 0.5
        
        try:
            # Prepare input features
            features = self._prepare_prediction_features(pool1, pool2, amount)
            
            if features is None:
                return 0.5
            
            # Make prediction
            prediction = self.model.predict(features, verbose=0)
            confidence = float(prediction[0][0])
            
            self.predictions_made += 1
            
            logger.debug(f"Predicted arbitrage confidence: {confidence:.3f}")
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return 0.5
    
    def predict_liquidity_drain(self, pool_data: Dict) -> PredictionResult:
        """Predict liquidity drain probability and market conditions"""
        
        if not self.is_trained:
            return PredictionResult(0.5, 0.0, 0.0, 0.5, 0.5)
        
        try:
            # Extract features from pool data
            features = []
            for pool in pool_data.values():
                features.extend([
                    pool.price,
                    pool.liquidity,
                    0.0,  # volume placeholder
                    0.0   # volatility placeholder
                ])
            
            if len(features) < len(self.features):
                # Pad with zeros if insufficient data
                features.extend([0.0] * (len(self.features) - len(features)))
            
            # Reshape for model input
            features_array = np.array(features[:len(self.features)]).reshape(1, 1, -1)
            
            # Make prediction
            prediction = self.model.predict(features_array, verbose=0)
            confidence = float(prediction[0][0])
            
            # Calculate additional metrics
            avg_price = np.mean([pool.price for pool in pool_data.values()])
            total_liquidity = sum(pool.liquidity for pool in pool_data.values())
            
            result = PredictionResult(
                confidence=confidence,
                predicted_price=avg_price,
                volatility=0.1,  # Placeholder
                liquidity_risk=1.0 - confidence,
                execution_probability=confidence
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting liquidity drain: {e}")
            return PredictionResult(0.5, 0.0, 0.0, 0.5, 0.5)
    
    def _prepare_prediction_features(self, pool1, pool2, amount: float) -> Optional[np.ndarray]:
        """Prepare features for prediction from pool data"""
        
        try:
            # Calculate price difference
            price_diff = abs(pool1.price - pool2.price)
            avg_price = (pool1.price + pool2.price) / 2
            price_diff_pct = price_diff / avg_price if avg_price > 0 else 0
            
            # Calculate liquidity metrics
            min_liquidity = min(pool1.liquidity, pool2.liquidity)
            liquidity_ratio = amount / min_liquidity if min_liquidity > 0 else 1
            
            # Create feature vector
            features = [
                avg_price,
                min_liquidity,
                liquidity_ratio,  # Volume proxy
                price_diff_pct    # Volatility proxy
            ]
            
            # Normalize features (simplified)
            features_normalized = np.array(features) / np.max(features)
            
            # Reshape for model input (batch_size, sequence_length, features)
            features_reshaped = features_normalized.reshape(1, 1, len(features))
            
            return features_reshaped
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None
    
    def update_model(self, new_data: List[Dict]):
        """Update model with new data (incremental learning)"""
        
        try:
            if len(new_data) < 10:  # Need minimum data for meaningful update
                return
            
            logger.info(f"Updating model with {len(new_data)} new data points")
            
            # Prepare new training data
            X_new, y_new = self.prepare_training_data(new_data)
            
            # Retrain with lower learning rate for fine-tuning
            self.model.optimizer.learning_rate = 0.0001
            
            # Train for fewer epochs
            self.model.fit(
                X_new, y_new,
                batch_size=min(self.batch_size, len(X_new)),
                epochs=10,
                verbose=0
            )
            
            logger.info("Model updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
    
    def evaluate_model(self, test_data: List[Dict]) -> Dict[str, float]:
        """Evaluate model performance on test data"""
        
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        try:
            # Prepare test data
            X_test, y_test = self.prepare_training_data(test_data)
            
            # Make predictions
            predictions = self.model.predict(X_test, verbose=0)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            
            # Calculate accuracy (predictions within 10% of actual)
            accuracy = np.mean(np.abs(predictions.flatten() - y_test) < 0.1)
            
            metrics = {
                "mse": float(mse),
                "mae": float(mae),
                "accuracy": float(accuracy),
                "predictions_made": self.predictions_made,
                "test_samples": len(y_test)
            }
            
            logger.info(f"Model evaluation: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {"error": str(e)}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance (simplified analysis)"""
        
        if not self.is_trained:
            return {}
        
        # For LSTM, feature importance is complex to calculate
        # Return placeholder importance scores
        importance = {
            "price": 0.35,
            "liquidity": 0.30,
            "volume": 0.20,
            "volatility": 0.15
        }
        
        return importance
    
    def save_model(self, path: Optional[str] = None):
        """Save the trained model"""
        
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        save_path = path or self.model_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save model
            self.model.save(save_path)
            
            # Save scaler
            scaler_path = save_path.replace('.h5', '_scaler.pkl')
            import joblib
            joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"Model saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def get_model_summary(self) -> Dict:
        """Get model summary and statistics"""
        
        summary = {
            "is_trained": self.is_trained,
            "model_path": self.model_path,
            "sequence_length": self.sequence_length,
            "features": self.features,
            "predictions_made": self.predictions_made,
            "prediction_accuracy": self.prediction_accuracy
        }
        
        if self.model:
            summary["total_params"] = self.model.count_params()
            summary["model_layers"] = len(self.model.layers)
        
        return summary

if __name__ == "__main__":
    # Example usage and testing
    predictor = LSTMPredictor()
    
    # Generate sample data for testing
    sample_data = []
    for i in range(100):
        sample_data.append({
            "timestamp": datetime.now() - timedelta(hours=i),
            "price": 1000 + np.random.normal(0, 50),
            "liquidity": 1000000 + np.random.normal(0, 100000),
        })
    
    # Train model
    if len(sample_data) >= predictor.sequence_length + predictor.prediction_horizon:
        predictor.train_model(sample_data)
        
        # Evaluate model
        metrics = predictor.evaluate_model(sample_data[-50:])
        print("Model metrics:", metrics)
        
        # Get model summary
        summary = predictor.get_model_summary()
        print("Model summary:", summary)
