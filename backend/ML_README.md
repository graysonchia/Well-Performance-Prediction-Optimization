# ML Module Documentation

## Overview

The ML module provides machine learning capabilities for well performance prediction, anomaly detection, and predictive maintenance. It includes:

1. **Production Forecasting** - Linear regression models to forecast future oil production
2. **Anomaly Detection** - Isolation Forest for detecting abnormal sensor readings
3. **Predictive Maintenance** - Health scoring and maintenance predictions based on sensor trends

## Components

### WellPerformanceModel
Main orchestrator class combining all ML models:
```python
from app.ml.models import WellPerformanceModel

model = WellPerformanceModel()
analysis = model.analyze_well(well_data)
```

### ProductionForecaster
Forecasts future production trends:
```python
from app.ml.models import ProductionForecaster

forecaster = ProductionForecaster()
forecaster.fit(dates, production_values)
forecast = forecaster.predict(days_ahead=30)
# Returns: [(date, predicted_oil_bbl), ...]
```

### AnomalyDetector
Detects abnormal sensor readings using Isolation Forest:
```python
from app.ml.models import AnomalyDetector

detector = AnomalyDetector(contamination=0.1)
detector.fit(sensor_dataframe, feature_columns)
is_anomaly, anomaly_score = detector.predict(sensor_reading)
```

### PredictiveMaintenance
Calculates equipment health and maintenance needs:
```python
from app.ml.models import PredictiveMaintenance

maintenance = PredictiveMaintenance()
health_score = maintenance.calculate_health_score(sensor_readings_df)
needs_maint, message = maintenance.needs_maintenance(health_score)
```

## API Endpoints

### 1. Production Forecast
**GET** `/api/v1/predictions/well/{well_id}/forecast`

Query Parameters:
- `days_ahead` (optional, default: 30) - Number of days to forecast

Response:
```json
{
  "well_id": 1,
  "well_name": "Well-01",
  "forecast_days": 30,
  "forecast": [
    {
      "date": "2026-06-24",
      "predicted_oil_bbl": 850.5
    },
    ...
  ]
}
```

### 2. Anomaly Detection
**GET** `/api/v1/predictions/well/{well_id}/anomalies`

Response:
```json
{
  "well_id": 1,
  "well_name": "Well-01",
  "total_readings": 100,
  "anomalies_detected": 3,
  "anomalies": [
    {
      "index": 45,
      "timestamp": "2026-06-20T15:30:00",
      "is_anomaly": true,
      "anomaly_score": 0.85,
      "reading": {
        "temperature_c": 95.2,
        "pressure_psi": 2850,
        ...
      }
    },
    ...
  ]
}
```

### 3. Well Health & Maintenance
**GET** `/api/v1/predictions/well/{well_id}/health`

Response:
```json
{
  "well_id": 1,
  "well_name": "Well-01",
  "health_score": 78.5,
  "status": "OPERATIONAL",
  "message": "HEALTHY: No action needed",
  "last_reading": {...}
}
```

Health Score Interpretation:
- **80-100**: HEALTHY - No action needed
- **60-80**: CAUTION - Monitor closely
- **40-60**: WARNING - Schedule maintenance soon
- **<40**: CRITICAL - Immediate maintenance required

### 4. Comprehensive Well Analysis
**GET** `/api/v1/predictions/well/{well_id}/analysis`

Returns combined forecast, anomalies, and health data in one call.

### 5. Field-Level Analysis
**GET** `/api/v1/predictions/field/{field_name}/analysis`

Returns ML analysis for all wells in a field.

## Training Models

Train or update ML models with the latest data:

```bash
cd backend
python -m app.ml.train_models
```

This script:
- Loads the last 180 days of production and sensor data
- Trains forecasters on wells with sufficient production history
- Trains anomaly detectors on wells with sufficient sensor data
- Saves trained models to `backend/app/ml/trained_models/`

## Data Flow

```
Database (Production Logs, Sensor Readings)
    ↓
WellPerformanceModel
    ├── ProductionForecaster → Future production predictions
    ├── AnomalyDetector → Abnormal sensor readings
    └── PredictiveMaintenance → Equipment health & maintenance needs
    ↓
API Endpoints → Frontend Dashboard
```

## Model Behavior

### Production Forecasting
- Uses linear regression on historical oil production
- Handles cases with insufficient data gracefully
- Returns non-negative predictions only
- Suitable for stable production trends

**Limitations**: Linear models may not capture complex seasonality. Can be upgraded to Prophet for better accuracy.

### Anomaly Detection
- Uses Isolation Forest (unsupervised learning)
- Trained on 80% of historical data
- Contamination parameter set to 0.1 (assumes ~10% anomalies)
- Scores range 0-1, higher = more anomalous

**Use Cases**:
- Pump failures
- Pressure spikes
- Temperature anomalies
- Unexpected flow rate changes

### Predictive Maintenance
- Calculates health score (0-100) based on:
  - Temperature volatility
  - Vibration levels
  - Pressure stability
- Provides actionable maintenance recommendations
- Customizable degradation threshold

## Integration with Frontend

The frontend can display:
1. **Production forecast chart** from `/forecast` endpoint
2. **Anomaly timeline** from `/anomalies` endpoint
3. **Health gauge** from `/health` endpoint
4. **Alerts** when maintenance is needed

## Future Enhancements

1. **Time Series Models**: Replace linear regression with Prophet/ARIMA
2. **Deep Learning**: LSTM for sequence prediction
3. **Clustering**: Group wells by production profile
4. **Feature Engineering**: Add domain-specific features
5. **Model Versioning**: Track model performance over time
6. **Online Learning**: Update models with streaming data
7. **Causal Inference**: Understand impact of operational changes

## Requirements

The ML module requires:
```
scikit-learn>=1.0.0
pandas>=1.3.0
numpy>=1.21.0
```

These are already in your project dependencies.

## Examples

See `analytics/notebooks/ml_models_example.ipynb` for detailed examples and visualizations.
