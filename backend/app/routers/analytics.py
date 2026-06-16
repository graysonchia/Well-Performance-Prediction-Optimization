from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import ProductionLog, Well
from app.schemas.schemas import (
    DeclineCurvePoint,
    DowntimeSummary,
    FieldComparison,
    ProductionTrendPoint,
    WaterCutPoint,
    WellSummary,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/production-trend", response_model=list[ProductionTrendPoint])
async def production_trend(field_name: str | None = None, db: AsyncSession = Depends(get_db)):
    log_day = func.date_trunc("day", ProductionLog.log_date).label("log_date")
    stmt = (
        select(
            log_day,
            Well.field_name,
            func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil_bbl"),
            func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas_mcf"),
            func.coalesce(func.sum(ProductionLog.water_bbl), 0).label("total_water_bbl"),
        )
        .join(Well, Well.id == ProductionLog.well_id)
        .group_by(log_day, Well.field_name)
        .order_by(log_day, Well.field_name)
    )
    if field_name:
        stmt = stmt.where(Well.field_name == field_name)

    result = await db.execute(stmt)
    return [ProductionTrendPoint(**row._mapping) for row in result.all()]


@router.get("/decline-curve/{well_id}", response_model=list[DeclineCurvePoint])
async def decline_curve(well_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            ProductionLog.log_date,
            ProductionLog.oil_bbl,
            ProductionLog.gas_mcf,
            ProductionLog.water_bbl,
        )
        .where(ProductionLog.well_id == well_id)
        .order_by(ProductionLog.log_date)
    )
    return [DeclineCurvePoint(**row._mapping) for row in result.all()]


@router.get("/water-cut-trend/{well_id}", response_model=list[WaterCutPoint])
async def water_cut_trend(well_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            ProductionLog.log_date,
            (
                ProductionLog.water_bbl
                / func.nullif(ProductionLog.oil_bbl + ProductionLog.water_bbl, 0)
                * 100
            ).label("water_cut_pct"),
        )
        .where(ProductionLog.well_id == well_id)
        .order_by(ProductionLog.log_date)
    )
    return [WaterCutPoint(**row._mapping) for row in result.all()]


@router.get("/top-producers", response_model=list[WellSummary])
async def top_producers(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Well.id.label("well_id"),
            Well.well_name,
            Well.field_name,
            func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil_bbl"),
            func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas_mcf"),
            func.coalesce(func.avg(ProductionLog.oil_bbl), 0).label("avg_daily_oil"),
            func.max(ProductionLog.log_date).label("latest_log_date"),
        )
        .join(ProductionLog, ProductionLog.well_id == Well.id)
        .group_by(Well.id, Well.well_name, Well.field_name)
        .order_by(func.sum(ProductionLog.oil_bbl).desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    return [WellSummary(**row._mapping) for row in result.all()]


@router.get("/downtime-summary", response_model=list[DowntimeSummary])
async def downtime_summary(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Well.id.label("well_id"),
            Well.well_name,
            Well.field_name,
            func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).label("total_downtime_hrs"),
        )
        .join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True)
        .group_by(Well.id, Well.well_name, Well.field_name)
        .order_by(func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).desc())
    )
    result = await db.execute(stmt)
    return [DowntimeSummary(**row._mapping) for row in result.all()]


@router.get("/field-comparison", response_model=list[FieldComparison])
async def field_comparison(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Well.field_name,
            func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil_bbl"),
            func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas_mcf"),
            func.coalesce(func.sum(ProductionLog.water_bbl), 0).label("total_water_bbl"),
            func.count(func.distinct(Well.id)).label("well_count"),
        )
        .join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True)
        .group_by(Well.field_name)
        .order_by(Well.field_name)
    )
    result = await db.execute(stmt)
    return [FieldComparison(**row._mapping) for row in result.all()]
