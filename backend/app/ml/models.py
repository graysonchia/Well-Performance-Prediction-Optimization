"""
ML models for well performance prediction, forecasting, and anomaly detection.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from typing import Optional, Tuple


class ProductionForecaster:
    """
    Forecasts future production using linear regression on historical trends.
    Can be upgraded to Prophet for more advanced time-series forecasting.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, dates: list, production_values: list) -> None:
        """Train the forecaster on historical production data."""
        if len(dates) < 2:
            self.is_fitted = False
            return
            
        # Convert dates to days since start
        X = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
        y = np.array(production_values)
        
        self.model.fit(X, y)
        self.start_date = dates[0]
        self.is_fitted = True
        
    def predict(self, days_ahead: int = 30) -> list[Tuple[datetime, float]]:
        """Forecast production for the next N days."""
        if not self.is_fitted:
            return []
        
        future_days = np.arange(0, days_ahead).reshape(-1, 1)
        predictions = self.model.predict(future_days)
        
        # Ensure non-negative predictions
        predictions = np.maximum(predictions, 0)
        
        result = []
        for i, pred in enumerate(predictions):
            forecast_date = self.start_date + timedelta(days=i)
            result.append((forecast_date, float(pred)))
            
        return result


class AnomalyDetector:
    """
    Detects anomalies in sensor readings using Isolation Forest.
    Identifies abnormal equipment behavior, potential failures.
    """
    
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_columns = None
        
    def fit(self, sensor_data: pd.DataFrame, features: list[str]) -> None:
        """Train the anomaly detector on historical sensor data."""
        if len(sensor_data) < 10:
            self.is_fitted = False
            return
            
        self.feature_columns = features
        X = sensor_data[features].fillna(sensor_data[features].mean())
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        
    def predict(self, sensor_reading: dict) -> Tuple[bool, float]:
        """
        Detect if a sensor reading is anomalous.
        Returns (is_anomaly, anomaly_score)
        """
        if not self.is_fitted or not self.feature_columns:
            return False, 0.0
            
        # Create feature vector
        values = np.array([sensor_reading.get(col, 0) for col in self.feature_columns]).reshape(1, -1)
        values_scaled = self.scaler.transform(values)
        
        prediction = self.model.predict(values_scaled)[0]
        score = abs(self.model.score_samples(values_scaled)[0])
        
        is_anomaly = prediction == -1
        return is_anomaly, float(score)


class PredictiveMaintenance:
    """
    Predicts maintenance needs based on sensor trends and equipment degradation.
    """
    
    def __init__(self, degradation_threshold: float = 0.7):
        self.degradation_threshold = degradation_threshold
        
    def calculate_health_score(self, sensor_readings: pd.DataFrame) -> float:
        """
        Calculate equipment health score (0-100, where 100 is healthy).
        Based on temperature, pressure, vibration trends.
        """
        if len(sensor_readings) == 0:
            return 100.0
            
        health_score = 100.0
        
        # Check temperature trend (should be stable)
        if 'temperature_c' in sensor_readings.columns:
            temps = sensor_readings['temperature_c'].dropna()
            if len(temps) > 1:
                temp_volatility = temps.std() / (temps.mean() + 1)
                health_score -= min(temp_volatility * 20, 30)
        
        # Check vibration (higher = worse)
        if 'vibration_mms' in sensor_readings.columns:
            vibrations = sensor_readings['vibration_mms'].dropna()
            if len(vibrations) > 0:
                max_vibration = vibrations.max()
                health_score -= min(max_vibration / 10, 40)
        
        # Check pressure stability
        if 'pressure_psi' in sensor_readings.columns:
            pressures = sensor_readings['pressure_psi'].dropna()
            if len(pressures) > 1:
                pressure_volatility = pressures.std() / (pressures.mean() + 1)
                health_score -= min(pressure_volatility * 15, 25)
        
        return max(health_score, 0.0)
    
    def needs_maintenance(self, health_score: float) -> Tuple[bool, str]:
        """Determine if maintenance is needed."""
        if health_score < 40:
            return True, "CRITICAL: Immediate maintenance required"
        elif health_score < 60:
            return True, "WARNING: Schedule maintenance soon"
        elif health_score < self.degradation_threshold * 100:
            return False, "CAUTION: Monitor closely"
        else:
            return False, "HEALTHY: No action needed"


class WellPerformanceModel:
    """
    Comprehensive well performance model combining forecasting, anomaly detection,
    and predictive maintenance.
    """
    
    def __init__(self):
        self.forecaster = ProductionForecaster()
        self.anomaly_detector = AnomalyDetector(contamination=0.1)
        self.maintenance = PredictiveMaintenance()
        
    def analyze_well(self, well_data: dict) -> dict:
        """
        Comprehensive analysis of a well's performance.
        """
        analysis = {
            "well_id": well_data.get("well_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "forecast": [],
            "anomalies": [],
            "health_score": 0.0,
            "maintenance_status": "UNKNOWN",
            "maintenance_message": "",
        }
        
        # Production forecasting
        if "production_history" in well_data and len(well_data["production_history"]) > 0:
            hist = well_data["production_history"]
            dates = [pd.to_datetime(h["date"]) for h in hist]
            values = [h["oil_bbl"] for h in hist]
            
            self.forecaster.fit(dates, values)
            analysis["forecast"] = [
                {"date": d.isoformat(), "predicted_oil_bbl": v}
                for d, v in self.forecaster.predict(days_ahead=30)
            ]
        
        # Sensor anomaly detection
        if "sensor_readings" in well_data and len(well_data["sensor_readings"]) > 0:
            sensor_df = pd.DataFrame(well_data["sensor_readings"])
            
            # Fit detector on historical data
            feature_cols = ["temperature_c", "pressure_psi", "flow_rate_bpd", "vibration_mms"]
            available_cols = [col for col in feature_cols if col in sensor_df.columns]
            
            if len(available_cols) > 0:
                self.anomaly_detector.fit(sensor_df, available_cols)
                
                # Check latest reading
                latest = well_data["sensor_readings"][-1]
                is_anomaly, score = self.anomaly_detector.predict(latest)
                
                if is_anomaly:
                    analysis["anomalies"].append({
                        "type": "sensor_anomaly",
                        "severity": min(score * 100, 100),
                        "reading": latest
                    })
        
        # Predictive maintenance
        if "sensor_readings" in well_data and len(well_data["sensor_readings"]) > 0:
            sensor_df = pd.DataFrame(well_data["sensor_readings"])
            health_score = self.maintenance.calculate_health_score(sensor_df)
            needs_maint, msg = self.maintenance.needs_maintenance(health_score)
            
            analysis["health_score"] = health_score
            analysis["maintenance_status"] = "MAINTENANCE_REQUIRED" if needs_maint else "OPERATIONAL"
            analysis["maintenance_message"] = msg
        
        return analysis
