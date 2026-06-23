"""
ML Predictions API endpoints for production forecasting, anomaly detection,
and predictive maintenance.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.models import ProductionLog, SensorReading, Well
from app.ml.models import WellPerformanceModel


router = APIRouter(prefix="/predictions", tags=["ml-predictions"])

# Initialize ML model
well_model = WellPerformanceModel()


async def get_well_data(well_id: int, db: AsyncSession, days_back: int = 90):
    """Fetch well data for ML analysis."""
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get production history
    prod_stmt = (
        select(ProductionLog)
        .where(
            (ProductionLog.well_id == well_id) &
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
            (SensorReading.well_id == well_id) &
            (SensorReading.recorded_at >= cutoff_date)
        )
        .order_by(SensorReading.recorded_at)
    )
    sensor_result = await db.execute(sensor_stmt)
    sensor_readings = sensor_result.scalars().all()
    
    return {
        "well_id": well_id,
        "production_history": [
            {
                "date": log.log_date.isoformat(),
                "oil_bbl": log.oil_bbl,
                "gas_mcf": log.gas_mcf,
                "water_bbl": log.water_bbl,
            }
            for log in production_logs
        ],
        "sensor_readings": [
            {
                "timestamp": sensor.recorded_at.isoformat(),
                "temperature_c": sensor.temperature_c,
                "pressure_psi": sensor.pressure_psi,
                "flow_rate_bpd": sensor.flow_rate_bpd,
                "vibration_mms": sensor.vibration_mms,
            }
            for sensor in sensor_readings
        ],
    }


@router.get("/well/{well_id}/forecast")
async def forecast_production(
    well_id: int,
    days_ahead: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Forecast production for a well.
    
    - **well_id**: ID of the well to forecast
    - **days_ahead**: Number of days to forecast (default: 30)
    """
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    well_data = await get_well_data(well_id, db)
    
    if not well_data["production_history"]:
        raise HTTPException(
            status_code=400,
            detail="Insufficient production history for forecasting"
        )
    
    # Prepare data for forecaster
    hist = well_data["production_history"]
    dates = [datetime.fromisoformat(h["date"]) for h in hist]
    values = [h["oil_bbl"] for h in hist]
    
    well_model.forecaster.fit(dates, values)
    forecast = well_model.forecaster.predict(days_ahead=days_ahead)
    
    return {
        "well_id": well_id,
        "well_name": well.well_name,
        "forecast_days": days_ahead,
        "forecast": [
            {"date": d.isoformat(), "predicted_oil_bbl": v}
            for d, v in forecast
        ]
    }


@router.get("/well/{well_id}/anomalies")
async def detect_anomalies(
    well_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in sensor readings for a well.
    
    - **well_id**: ID of the well to analyze
    """
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    well_data = await get_well_data(well_id, db)
    
    if not well_data["sensor_readings"]:
        raise HTTPException(
            status_code=400,
            detail="No sensor data available for anomaly detection"
        )
    
    # Fit anomaly detector on 80% of data
    import pandas as pd
    sensor_df = pd.DataFrame(well_data["sensor_readings"])
    
    if len(sensor_df) > 10:
        train_size = int(len(sensor_df) * 0.8)
        train_data = sensor_df.iloc[:train_size]
        
        feature_cols = ["temperature_c", "pressure_psi", "flow_rate_bpd", "vibration_mms"]
        available_cols = [col for col in feature_cols if col in train_data.columns]
        
        if available_cols:
            well_model.anomaly_detector.fit(train_data, available_cols)
            
            # Detect anomalies in all data
            anomalies = []
            for idx, reading in enumerate(well_data["sensor_readings"]):
                is_anomaly, score = well_model.anomaly_detector.predict(reading)
                if is_anomaly or score > 0.5:
                    anomalies.append({
                        "index": idx,
                        "timestamp": reading.get("timestamp"),
                        "is_anomaly": is_anomaly,
                        "anomaly_score": score,
                        "reading": reading
                    })
    
    return {
        "well_id": well_id,
        "well_name": well.well_name,
        "total_readings": len(well_data["sensor_readings"]),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies[:10]  # Return top 10 anomalies
    }


@router.get("/well/{well_id}/health")
async def get_well_health(
    well_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get predictive maintenance and health status for a well.
    
    - **well_id**: ID of the well to analyze
    """
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    well_data = await get_well_data(well_id, db)
    
    if not well_data["sensor_readings"]:
        raise HTTPException(
            status_code=400,
            detail="No sensor data available for health assessment"
        )
    
    import pandas as pd
    sensor_df = pd.DataFrame(well_data["sensor_readings"])
    
    health_score = well_model.maintenance.calculate_health_score(sensor_df)
    needs_maint, message = well_model.maintenance.needs_maintenance(health_score)
    
    return {
        "well_id": well_id,
        "well_name": well.well_name,
        "health_score": round(health_score, 2),
        "status": "MAINTENANCE_REQUIRED" if needs_maint else "OPERATIONAL",
        "message": message,
        "last_reading": well_data["sensor_readings"][-1] if well_data["sensor_readings"] else None
    }


@router.get("/well/{well_id}/analysis")
async def comprehensive_analysis(
    well_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive ML analysis for a well including forecasts, anomalies, and health.
    
    - **well_id**: ID of the well to analyze
    """
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    well_data = await get_well_data(well_id, db)
    analysis = well_model.analyze_well(well_data)
    
    return {
        "well_id": well_id,
        "well_name": well.well_name,
        "analysis": analysis
    }


@router.get("/field/{field_name}/analysis")
async def field_analysis(
    field_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get ML analysis for all wells in a field.
    
    - **field_name**: Name of the field to analyze
    """
    # Get all wells in field
    stmt = select(Well).where(Well.field_name == field_name)
    result = await db.execute(stmt)
    wells = result.scalars().all()
    
    if not wells:
        raise HTTPException(status_code=404, detail="Field not found")
    
    analyses = []
    for well in wells:
        try:
            well_data = await get_well_data(well.id, db)
            if well_data["production_history"] or well_data["sensor_readings"]:
                analysis = well_model.analyze_well(well_data)
                analysis["well_name"] = well.well_name
                analyses.append(analysis)
        except Exception:
            pass
    
    return {
        "field_name": field_name,
        "wells_analyzed": len(analyses),
        "analyses": analyses
    }
