from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.models import WellStatus, WellType


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WellBase(BaseModel):
    well_name: str
    field_name: str
    operator: str
    well_type: WellType
    status: WellStatus = WellStatus.active
    latitude: float
    longitude: float
    depth_m: float
    spud_date: datetime
    first_production_date: datetime | None = None


class WellCreate(WellBase):
    pass


class WellUpdate(BaseModel):
    well_name: str | None = None
    field_name: str | None = None
    operator: str | None = None
    well_type: WellType | None = None
    status: WellStatus | None = None
    latitude: float | None = None
    longitude: float | None = None
    depth_m: float | None = None
    spud_date: datetime | None = None
    first_production_date: datetime | None = None


class WellResponse(WellBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class ProductionLogBase(BaseModel):
    well_id: int
    log_date: datetime
    oil_bbl: float = 0.0
    gas_mcf: float = 0.0
    water_bbl: float = 0.0
    downtime_hrs: float = 0.0
    choke_size_mm: float | None = None
    tubing_pressure_psi: float | None = None
    casing_pressure_psi: float | None = None


class ProductionLogCreate(ProductionLogBase):
    pass


class ProductionLogUpdate(BaseModel):
    log_date: datetime | None = None
    oil_bbl: float | None = None
    gas_mcf: float | None = None
    water_bbl: float | None = None
    downtime_hrs: float | None = None
    choke_size_mm: float | None = None
    tubing_pressure_psi: float | None = None
    casing_pressure_psi: float | None = None


class ProductionLogResponse(ProductionLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class SensorReadingBase(BaseModel):
    well_id: int
    recorded_at: datetime
    temperature_c: float | None = None
    pressure_psi: float | None = None
    flow_rate_bpd: float | None = None
    gas_oil_ratio: float | None = None
    water_cut_pct: float | None = None
    vibration_mms: float | None = None


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingUpdate(BaseModel):
    recorded_at: datetime | None = None
    temperature_c: float | None = None
    pressure_psi: float | None = None
    flow_rate_bpd: float | None = None
    gas_oil_ratio: float | None = None
    water_cut_pct: float | None = None
    vibration_mms: float | None = None


class SensorReadingResponse(SensorReadingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class MaintenanceEventBase(BaseModel):
    well_id: int
    event_date: datetime
    event_type: str
    description: str | None = None
    cost_usd: float | None = None
    duration_hrs: float | None = None
    technician: str | None = None
    is_unplanned: bool = False


class MaintenanceEventCreate(MaintenanceEventBase):
    pass


class MaintenanceEventUpdate(BaseModel):
    event_date: datetime | None = None
    event_type: str | None = None
    description: str | None = None
    cost_usd: float | None = None
    duration_hrs: float | None = None
    technician: str | None = None
    is_unplanned: bool | None = None


class MaintenanceEventResponse(MaintenanceEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class WellSummary(BaseModel):
    well_id: int
    well_name: str
    field_name: str
    total_oil_bbl: float
    total_gas_mcf: float
    avg_daily_oil: float
    latest_log_date: datetime | None = None


class ProductionTrendPoint(BaseModel):
    log_date: datetime
    field_name: str
    total_oil_bbl: float
    total_gas_mcf: float
    total_water_bbl: float


class DeclineCurvePoint(BaseModel):
    log_date: datetime
    oil_bbl: float
    gas_mcf: float
    water_bbl: float


class WaterCutPoint(BaseModel):
    log_date: datetime
    water_cut_pct: float | None = None


class DowntimeSummary(BaseModel):
    well_id: int
    well_name: str
    field_name: str
    total_downtime_hrs: float


class FieldComparison(BaseModel):
    field_name: str
    total_oil_bbl: float
    total_gas_mcf: float
    total_water_bbl: float
    well_count: int
