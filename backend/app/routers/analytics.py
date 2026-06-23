from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import ProductionLog, Well
from app.schemas.schemas import (
    DeclineCurvePoint,
    DashboardKPI,
    DowntimeSummary,
    EfficiencyMetrics,
    FieldComparison,
    FieldKPI,
    ProductionComparison,
    ProductionTrendPoint,
    WaterCutPoint,
    WellKPI,
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


@router.get("/dashboard-kpi", response_model=DashboardKPI)
async def dashboard_kpi(db: AsyncSession = Depends(get_db)):
    """Get portfolio-level KPIs"""
    # Total wells and active wells
    well_stmt = select(
        func.count(Well.id).label("total_wells"),
        func.count(func.filter(Well.status == "active")).label("active_wells"),
    )
    well_result = await db.execute(well_stmt)
    well_data = well_result.first()
    
    # Production totals
    prod_stmt = select(
        func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil_bbl"),
        func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas_mcf"),
        func.count(func.distinct(ProductionLog.log_date)).label("total_days"),
    )
    prod_result = await db.execute(prod_stmt)
    prod_data = prod_result.first()
    
    # Downtime totals
    downtime_stmt = select(
        func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).label("total_downtime_hrs"),
    )
    downtime_result = await db.execute(downtime_stmt)
    downtime_data = downtime_result.first()
    
    # Maintenance costs
    from app.models.models import MaintenanceEvent
    cost_stmt = select(
        func.coalesce(func.sum(MaintenanceEvent.cost_usd), 0).label("total_cost"),
        func.coalesce(func.avg(MaintenanceEvent.duration_hrs), 0).label("avg_hrs"),
    )
    cost_result = await db.execute(cost_stmt)
    cost_data = cost_result.first()
    
    # Calculate averages
    total_days = prod_data.total_days if prod_data.total_days else 1
    avg_daily_oil = prod_data.total_oil_bbl / total_days if total_days > 0 else 0
    total_downtime_hrs = downtime_data.total_downtime_hrs or 0
    total_uptime_hrs = (total_days * 24) - total_downtime_hrs
    uptime_pct = (total_uptime_hrs / (total_days * 24) * 100) if (total_days * 24) > 0 else 0
    
    return DashboardKPI(
        total_wells=well_data.total_wells,
        active_wells=well_data.active_wells,
        total_production_oil_bbl=float(prod_data.total_oil_bbl),
        total_production_gas_mcf=float(prod_data.total_gas_mcf),
        avg_portfolio_uptime_pct=float(uptime_pct),
        total_maintenance_cost_usd=float(cost_data.total_cost),
        avg_daily_production_oil_bbl=float(avg_daily_oil),
        avg_maintenance_hrs=float(cost_data.avg_hrs),
    )


@router.get("/well-kpi/{well_id}", response_model=WellKPI)
async def well_kpi(well_id: int, db: AsyncSession = Depends(get_db)):
    """Get KPIs for a specific well"""
    # Get well info
    well_stmt = select(Well).where(Well.id == well_id)
    well_result = await db.execute(well_stmt)
    well = well_result.scalar_one_or_none()
    
    if not well:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Well not found")
    
    # Production stats
    prod_stmt = select(
        func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil"),
        func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas"),
        func.coalesce(func.avg(ProductionLog.oil_bbl), 0).label("avg_oil"),
        func.coalesce(func.avg(ProductionLog.gas_mcf), 0).label("avg_gas"),
        func.count(ProductionLog.id).label("log_count"),
    ).where(ProductionLog.well_id == well_id)
    prod_result = await db.execute(prod_stmt)
    prod_data = prod_result.first()
    
    # Downtime stats
    downtime_stmt = select(
        func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).label("total_downtime"),
        func.count(ProductionLog.id).label("log_count"),
    ).where(ProductionLog.well_id == well_id)
    downtime_result = await db.execute(downtime_stmt)
    downtime_data = downtime_result.first()
    
    # Pressure stats
    pressure_stmt = select(
        func.coalesce(func.avg(ProductionLog.tubing_pressure_psi), None).label("avg_tubing"),
        func.coalesce(func.avg(ProductionLog.casing_pressure_psi), None).label("avg_casing"),
    ).where(ProductionLog.well_id == well_id)
    pressure_result = await db.execute(pressure_stmt)
    pressure_data = pressure_result.first()
    
    # Latest water cut and log date
    latest_stmt = select(
        ProductionLog.log_date,
        (ProductionLog.water_bbl / func.nullif(ProductionLog.oil_bbl + ProductionLog.water_bbl, 0) * 100).label("water_cut"),
    ).where(ProductionLog.well_id == well_id).order_by(ProductionLog.log_date.desc()).limit(1)
    latest_result = await db.execute(latest_stmt)
    latest_data = latest_result.first()
    
    # Calculate uptime percentage
    log_count = prod_data.log_count if prod_data.log_count else 1
    total_downtime_hrs = downtime_data.total_downtime if downtime_data.total_downtime else 0
    total_possible_hrs = log_count * 24  # Assume 24 hrs per log day
    uptime_pct = ((total_possible_hrs - total_downtime_hrs) / total_possible_hrs * 100) if total_possible_hrs > 0 else 100
    avg_downtime_per_day = total_downtime_hrs / log_count if log_count > 0 else 0
    
    return WellKPI(
        well_id=well.id,
        well_name=well.well_name,
        field_name=well.field_name,
        total_oil_bbl=float(prod_data.total_oil),
        total_gas_mcf=float(prod_data.total_gas),
        avg_daily_oil_bbl=float(prod_data.avg_oil),
        avg_daily_gas_mcf=float(prod_data.avg_gas),
        uptime_percentage=float(uptime_pct),
        avg_downtime_hrs_per_day=float(avg_downtime_per_day),
        total_downtime_hrs=float(total_downtime_hrs),
        avg_tubing_pressure_psi=float(pressure_data.avg_tubing) if pressure_data.avg_tubing else None,
        avg_casing_pressure_psi=float(pressure_data.avg_casing) if pressure_data.avg_casing else None,
        latest_water_cut_pct=float(latest_data.water_cut) if latest_data and latest_data.water_cut else None,
        latest_log_date=latest_data.log_date if latest_data else None,
    )


@router.get("/field-kpi/{field_name}", response_model=FieldKPI)
async def field_kpi(field_name: str, db: AsyncSession = Depends(get_db)):
    """Get KPIs for a specific field"""
    stmt = select(
        Well.field_name,
        func.count(func.distinct(Well.id)).label("well_count"),
        func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil"),
        func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas"),
        func.coalesce(func.avg(ProductionLog.oil_bbl), 0).label("avg_daily_oil"),
        func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).label("total_downtime"),
        func.count(ProductionLog.id).label("log_count"),
    ).join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True).where(
        Well.field_name == field_name
    ).group_by(Well.field_name)
    
    result = await db.execute(stmt)
    data = result.first()
    
    if not data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Field not found")
    
    log_count = data.log_count if data.log_count else 1
    total_downtime = data.total_downtime or 0
    total_possible_hrs = log_count * 24
    uptime_pct = ((total_possible_hrs - total_downtime) / total_possible_hrs * 100) if total_possible_hrs > 0 else 100
    
    return FieldKPI(
        field_name=data.field_name,
        well_count=data.well_count,
        total_production_oil_bbl=float(data.total_oil),
        total_production_gas_mcf=float(data.total_gas),
        avg_daily_production_oil_bbl=float(data.avg_daily_oil),
        avg_uptime_pct=float(uptime_pct),
        total_downtime_hrs=float(total_downtime),
    )


@router.get("/production-ranking", response_model=list[ProductionComparison])
async def production_ranking(group_by: str = "well", db: AsyncSession = Depends(get_db)):
    """Rank wells or fields by production"""
    if group_by == "field":
        stmt = (
            select(
                Well.field_name.label("name"),
                func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil"),
                func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas"),
                func.coalesce(func.avg(ProductionLog.oil_bbl), 0).label("avg_daily_oil"),
                func.row_number().over(
                    order_by=func.sum(ProductionLog.oil_bbl).desc()
                ).label("ranking"),
            )
            .join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True)
            .group_by(Well.field_name)
        )
    else:  # group_by == "well"
        stmt = (
            select(
                Well.well_name.label("name"),
                func.coalesce(func.sum(ProductionLog.oil_bbl), 0).label("total_oil"),
                func.coalesce(func.sum(ProductionLog.gas_mcf), 0).label("total_gas"),
                func.coalesce(func.avg(ProductionLog.oil_bbl), 0).label("avg_daily_oil"),
                func.row_number().over(
                    order_by=func.sum(ProductionLog.oil_bbl).desc()
                ).label("ranking"),
            )
            .join(ProductionLog, ProductionLog.well_id == Well.id, isouter=True)
            .group_by(Well.id, Well.well_name)
        )
    
    result = await db.execute(stmt)
    return [
        ProductionComparison(
            name=row.name,
            production_oil_bbl=float(row.total_oil),
            production_gas_mcf=float(row.total_gas),
            avg_daily_oil_bbl=float(row.avg_daily_oil),
            ranking=row.ranking,
        )
        for row in result.all()
    ]


@router.get("/efficiency-metrics/{well_id}", response_model=EfficiencyMetrics)
async def efficiency_metrics(well_id: int, db: AsyncSession = Depends(get_db)):
    """Get efficiency metrics for a well"""
    # Get well info
    well_stmt = select(Well).where(Well.id == well_id)
    well_result = await db.execute(well_stmt)
    well = well_result.scalar_one_or_none()
    
    if not well:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Well not found")
    
    # Production logs for operational days
    from app.models.models import MaintenanceEvent
    prod_stmt = select(
        func.count(func.distinct(func.date(ProductionLog.log_date))).label("op_days"),
        func.coalesce(func.sum(ProductionLog.downtime_hrs), 0).label("total_downtime"),
    ).where(ProductionLog.well_id == well_id)
    prod_result = await db.execute(prod_stmt)
    prod_data = prod_result.first()
    
    # Maintenance events
    maint_stmt = select(
        func.count(MaintenanceEvent.id).label("total_events"),
        func.coalesce(func.avg(MaintenanceEvent.duration_hrs), 0).label("avg_hrs"),
        func.count(func.filter(MaintenanceEvent.is_unplanned == True)).label("unplanned"),
    ).where(MaintenanceEvent.well_id == well_id)
    maint_result = await db.execute(maint_stmt)
    maint_data = maint_result.first()
    
    op_days = prod_data.op_days if prod_data.op_days else 1
    total_downtime_hrs = prod_data.total_downtime or 0
    downtime_days = total_downtime_hrs / 24
    uptime_days = op_days - downtime_days
    uptime_pct = (uptime_days / op_days * 100) if op_days > 0 else 0
    downtime_pct = 100 - uptime_pct
    total_events = maint_data.total_events or 0
    unplanned_count = maint_data.unplanned or 0
    planned_count = total_events - unplanned_count
    
    return EfficiencyMetrics(
        well_id=well.id,
        well_name=well.well_name,
        uptime_percentage=float(uptime_pct),
        downtime_percentage=float(downtime_pct),
        total_operational_days=int(op_days),
        total_downtime_days=int(downtime_days),
        avg_downtime_hrs_per_event=float(maint_data.avg_hrs) if total_events > 0 else 0,
        planned_maintenance_pct=(planned_count / total_events * 100) if total_events > 0 else 0,
        unplanned_maintenance_pct=(unplanned_count / total_events * 100) if total_events > 0 else 0,
    )

