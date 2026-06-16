from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class WellStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    abandoned = "abandoned"

class WellType(enum.Enum):
    oil = "oil"
    gas = "gas"
    oil_gas = "oil_gas"
    water_injection = "water_injection"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    well_name = Column(String(100), unique=True, nullable=False)
    field_name = Column(String(100), nullable=False)
    operator = Column(String(100), nullable=False)
    well_type = Column(Enum(WellType), nullable=False)
    status = Column(Enum(WellStatus), default=WellStatus.active)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    depth_m = Column(Float, nullable=False)        # total depth in meters
    spud_date = Column(DateTime, nullable=False)    # date drilling began
    first_production_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    production_logs = relationship("ProductionLog", back_populates="well")
    sensor_readings = relationship("SensorReading", back_populates="well")
    maintenance_events = relationship("MaintenanceEvent", back_populates="well")


class ProductionLog(Base):
    __tablename__ = "production_logs"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False)
    log_date = Column(DateTime, nullable=False)
    oil_bbl = Column(Float, default=0.0)           # barrels of oil
    gas_mcf = Column(Float, default=0.0)           # thousand cubic feet of gas
    water_bbl = Column(Float, default=0.0)         # barrels of water
    downtime_hrs = Column(Float, default=0.0)      # hours of downtime
    choke_size_mm = Column(Float)                  # choke valve size
    tubing_pressure_psi = Column(Float)
    casing_pressure_psi = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    well = relationship("Well", back_populates="production_logs")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    temperature_c = Column(Float)                  # downhole temperature
    pressure_psi = Column(Float)                   # downhole pressure
    flow_rate_bpd = Column(Float)                  # barrels per day
    gas_oil_ratio = Column(Float)                  # GOR
    water_cut_pct = Column(Float)                  # % water in produced fluid
    vibration_mms = Column(Float)                  # pump vibration
    created_at = Column(DateTime, default=datetime.utcnow)

    well = relationship("Well", back_populates="sensor_readings")


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String(100), nullable=False)   # e.g. pump replacement
    description = Column(Text)
    cost_usd = Column(Float)
    duration_hrs = Column(Float)
    technician = Column(String(100))
    is_unplanned = Column(Boolean, default=False)      # planned vs emergency
    created_at = Column(DateTime, default=datetime.utcnow)

    well = relationship("Well", back_populates="maintenance_events")
