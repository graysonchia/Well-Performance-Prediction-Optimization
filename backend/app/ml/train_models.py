"""
ML Training Script

Train and save machine learning models for well performance prediction.
Run this script periodically to update models with new data.

Usage:
    python -m app.ml.train_models
"""

import asyncio
import pandas as pd
from sqlalchemy import select
from datetime import datetime, timedelta

from app.database import AsyncSessionLocal
from app.models.models import ProductionLog, SensorReading, Well
from app.ml.models import WellPerformanceModel
import pickle
import os


async def train_models():
    """Train ML models on all wells in the database."""
    
    async with AsyncSessionLocal() as db:
        # Get all active wells
        wells_stmt = select(Well)
        result = await db.execute(wells_stmt)
        wells = result.scalars().all()
        
        print(f"Training models for {len(wells)} wells...")
        
        trained_count = 0
        
        for well in wells:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=180)
                
                # Get production history
                prod_stmt = (
                    select(ProductionLog)
                    .where(
                        (ProductionLog.well_id == well.id) &
                        (ProductionLog.log_date >= cutoff_date)
                    )
                    .order_by(ProductionLog.log_date)
                )
                prod_result = await db.execute(prod_stmt)
                production_logs = prod_result.scalars().all()
                
                # Get sensor readings
                sensor_stmt = (
                    select(SensorReading)
                    .where(
                        (SensorReading.well_id == well.id) &
                        (SensorReading.recorded_at >= cutoff_date)
                    )
                    .order_by(SensorReading.recorded_at)
                )
                sensor_result = await db.execute(sensor_stmt)
                sensor_readings = sensor_result.scalars().all()
                
                if len(production_logs) > 5 or len(sensor_readings) > 10:
                    model = WellPerformanceModel()
                    
                    # Train forecaster
                    if len(production_logs) > 5:
                        dates = [log.log_date for log in production_logs]
                        values = [log.oil_bbl for log in production_logs]
                        model.forecaster.fit(dates, values)
                        print(f"  ✓ {well.well_name}: Production forecaster trained")
                    
                    # Train anomaly detector
                    if len(sensor_readings) > 10:
                        sensor_data = pd.DataFrame([
                            {
                                "temperature_c": s.temperature_c,
                                "pressure_psi": s.pressure_psi,
                                "flow_rate_bpd": s.flow_rate_bpd,
                                "vibration_mms": s.vibration_mms,
                            }
                            for s in sensor_readings
                        ])
                        
                        feature_cols = ["temperature_c", "pressure_psi", "flow_rate_bpd", "vibration_mms"]
                        available_cols = [col for col in feature_cols if col in sensor_data.columns]
                        
                        if available_cols:
                            model.anomaly_detector.fit(sensor_data, available_cols)
                            print(f"  ✓ {well.well_name}: Anomaly detector trained")
                    
                    # Save model
                    model_dir = "backend/app/ml/trained_models"
                    os.makedirs(model_dir, exist_ok=True)
                    
                    model_path = f"{model_dir}/well_{well.id}_model.pkl"
                    with open(model_path, "wb") as f:
                        pickle.dump(model, f)
                    
                    trained_count += 1
                    
            except Exception as e:
                print(f"  ✗ {well.well_name}: Error - {str(e)}")
        
        print(f"\n✓ Successfully trained {trained_count}/{len(wells)} models")


if __name__ == "__main__":
    asyncio.run(train_models())
