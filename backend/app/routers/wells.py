from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import MaintenanceEvent, ProductionLog, SensorReading, Well, WellStatus, WellType
from app.schemas.schemas import (
    MaintenanceEventResponse,
    ProductionLogResponse,
    SensorReadingResponse,
    WellResponse,
    WellSummary,
)


router = APIRouter(prefix="/wells", tags=["wells"])


@router.get("/summary", response_model=list[WellSummary])
async def get_well_summary(db: AsyncSession = Depends(get_db)):
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
        .join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True)
        .group_by(Well.id, Well.well_name, Well.field_name)
        .order_by(Well.well_name)
    )
    result = await db.execute(stmt)
    return [WellSummary(**row._mapping) for row in result.all()]


@router.get("", response_model=list[WellResponse])
async def list_wells(
    field_name: str | None = None,
    status: WellStatus | None = None,
    well_type: WellType | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt: Select[tuple[Well]] = select(Well).order_by(Well.field_name, Well.well_name)

    if field_name:
        stmt = stmt.where(Well.field_name == field_name)
    if status:
        stmt = stmt.where(Well.status == status)
    if well_type:
        stmt = stmt.where(Well.well_type == well_type)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{well_id}", response_model=WellResponse)
async def get_well(well_id: int, db: AsyncSession = Depends(get_db)):
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    return well


@router.get("/{well_id}/production", response_model=list[ProductionLogResponse])
async def get_well_production(
    well_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    await ensure_well_exists(db, well_id)
    stmt = select(ProductionLog).where(ProductionLog.well_id == well_id)
    if start_date:
        stmt = stmt.where(ProductionLog.log_date >= start_date)
    if end_date:
        stmt = stmt.where(ProductionLog.log_date <= end_date)

    result = await db.execute(stmt.order_by(ProductionLog.log_date))
    return result.scalars().all()


@router.get("/{well_id}/sensors", response_model=list[SensorReadingResponse])
async def get_well_sensors(
    well_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    await ensure_well_exists(db, well_id)
    stmt = select(SensorReading).where(SensorReading.well_id == well_id)
    if start_date:
        stmt = stmt.where(SensorReading.recorded_at >= start_date)
    if end_date:
        stmt = stmt.where(SensorReading.recorded_at <= end_date)

    result = await db.execute(stmt.order_by(SensorReading.recorded_at))
    return result.scalars().all()


@router.get("/{well_id}/maintenance", response_model=list[MaintenanceEventResponse])
async def get_well_maintenance(well_id: int, db: AsyncSession = Depends(get_db)):
    await ensure_well_exists(db, well_id)
    result = await db.execute(
        select(MaintenanceEvent)
        .where(MaintenanceEvent.well_id == well_id)
        .order_by(MaintenanceEvent.event_date)
    )
    return result.scalars().all()


async def ensure_well_exists(db: AsyncSession, well_id: int) -> None:
    well = await db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
