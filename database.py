"""
Database Persistence & Transactional Management Layer
=====================================================
Provides SQLAlchemy 2.0 Object-Relational Mapping (ORM) models for the SQLite
persistent store ('data/inventory.db'). Implements thread-safe scoped session
management and ACID transactional stock reallocation functions to eliminate
concurrent allocation race conditions.

Models Defined:
---------------
- Component: Physical component specifications (pack size, unit cost, unit weight, criticality).
- Location: Manufacturing facilities & regional logistics hubs.
- Inventory: Operational stock levels (current, safety, reserved).
- Forecast: Demand predictions, uncertainty intervals, and SLA urgency ratings.
- TransferRoute: Inter-location transport distances, freight costs, and vehicle carbon modes.
- OverrideLog: Planner audit trail logging decision overrides with reasons.
- ValidationCase: Line-item experiment comparative evaluation records.
"""

import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship

Base = declarative_base()

class Component(Base):
    """
    ORM model representing physical manufacturing component specifications.
    
    :param component_id: Primary key unique component identifier (e.g., C001).
    :param component_name: Descriptive component name (e.g., Motor Bearing).
    :param pack_size: Fixed integer multiple pack size for shipping.
    :param unit_cost: Cost per unit in Indian Rupees (INR).
    :param unit_weight_kg: Weight per unit in kilograms (used for transport carbon footprint calculation).
    :param criticality: Component operational criticality level (CRITICAL, HIGH, MEDIUM, LOW).
    """
    __tablename__ = 'components'

    component_id = Column(String(50), primary_key=True)
    component_name = Column(String(100), nullable=False)
    pack_size = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    unit_weight_kg = Column(Float, nullable=False, default=1.5)
    criticality = Column(String(20), nullable=False)

class Location(Base):
    """
    ORM model representing manufacturing plants or distribution centers.
    
    :param location_id: Primary key unique location identifier (e.g., L001).
    :param location_name: Facility name (e.g., Chennai, Bangalore, Pune).
    """
    __tablename__ = 'locations'

    location_id = Column(String(50), primary_key=True)
    location_name = Column(String(100), nullable=False, unique=True)

class Inventory(Base):
    """
    ORM model representing facility inventory stock levels.
    
    :param id: Primary key auto-increment integer ID.
    :param component_id: Foreign key mapping to Component.
    :param location: Facility location name.
    :param batch: Production batch identifier (e.g., B1, B2).
    :param current_stock: Physical stock currently in warehouse.
    :param safety_stock: Minimum mandatory safety stock threshold.
    :param reserved_stock: Stock reserved for active production orders.
    """
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(50), ForeignKey('components.component_id'), nullable=False)
    location = Column(String(100), nullable=False)
    batch = Column(String(20), nullable=False, default='B1')
    current_stock = Column(Integer, nullable=False)
    safety_stock = Column(Integer, nullable=False)
    reserved_stock = Column(Integer, nullable=False, default=0)

class Forecast(Base):
    """
    ORM model representing 7-day rolling consumption demand forecasts.
    
    :param id: Primary key auto-increment integer ID.
    :param component_id: Foreign key mapping to Component.
    :param location: Target facility location name.
    :param batch: Production batch identifier.
    :param forecast_7_days: Predicted component consumption over 7 days.
    :param uncertainty_percent: Forecast error margin percentage (+/- %).
    :param urgency: Service level agreement urgency rating (CRITICAL, HIGH, MEDIUM, LOW).
    """
    __tablename__ = 'forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(50), ForeignKey('components.component_id'), nullable=False)
    location = Column(String(100), nullable=False)
    batch = Column(String(20), nullable=False, default='B1')
    forecast_7_days = Column(Float, nullable=False)
    uncertainty_percent = Column(Float, nullable=False)
    urgency = Column(String(20), nullable=False)

class TransferRoute(Base):
    """
    ORM model representing pairwise inter-location logistics routes.
    
    :param id: Primary key auto-increment integer ID.
    :param source: Origin source facility location name.
    :param destination: Target destination facility location name.
    :param distance_km: Highway/Air transport distance in kilometers.
    :param transfer_time_days: Transport lead time in days.
    :param transfer_cost_per_unit: Freight cost per unit shipped (INR).
    :param transport_mode: Logistics vehicle mode (EV_TRUCK, DIESEL_TRUCK, EXPRESS_AIR).
    :param vehicle_emission_rate: Carbon emissions rate (kg CO2 per ton-km).
    :param reliability: Route historical reliability rating (0.0 to 1.0).
    """
    __tablename__ = 'transfer_routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    distance_km = Column(Float, nullable=False)
    transfer_time_days = Column(Integer, nullable=False)
    transfer_cost_per_unit = Column(Float, nullable=False)
    transport_mode = Column(String(50), nullable=False, default='DIESEL_TRUCK')
    vehicle_emission_rate = Column(Float, nullable=False, default=0.18) # kg CO2 / ton-km
    reliability = Column(Float, nullable=False)

class OverrideLog(Base):
    """
    ORM model representing planner audit trail records.
    
    :param id: Primary key auto-increment integer ID.
    :param recommendation_id: Target recommendation ID (e.g., REC-001).
    :param decision: Decision status (APPROVED, REJECTED, OVERRIDE).
    :param reason: Planner operational justification reason text.
    :param timestamp: DateTime timestamp of decision execution.
    """
    __tablename__ = 'override_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(50), nullable=False)
    decision = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)

class ValidationCase(Base):
    """
    ORM model storing comparative line-item validation experiment metrics.
    """
    __tablename__ = 'validation_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(50), nullable=False)
    component_id = Column(String(50), nullable=False)
    component_name = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    shortage_quantity = Column(Integer, nullable=False)
    pack_size = Column(Integer, nullable=False)
    baseline_action = Column(String(20), nullable=False)
    baseline_purchase_cost = Column(Float, nullable=False)
    recommender_action = Column(String(20), nullable=False)
    selected_source = Column(String(100), nullable=False)
    recommender_quantity = Column(Integer, nullable=False)
    recommender_transfer_cost = Column(Float, nullable=False)
    recommender_purchase_cost = Column(Float, nullable=False)
    baseline_emissions_kg = Column(Float, nullable=False, default=0.0)
    recommender_emissions_kg = Column(Float, nullable=False, default=0.0)
    emissions_avoided_kg = Column(Float, nullable=False, default=0.0)
    purchase_avoided = Column(Float, nullable=False)
    net_financial_savings = Column(Float, nullable=False)
    confidence = Column(String(20), nullable=False)
    edge_case_flag = Column(String(100), nullable=False)

# Database Connection Setup & Path Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy Engine & Scoped Session Factory
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def init_db():
    """
    Initializes database tables by creating schema metadata in SQLite.
    Safe to call multiple times (creates tables only if missing).
    """
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """
    Returns a new thread-local database session instance.
    Caller is responsible for committing or closing the session.
    """
    return SessionLocal()

def execute_transfer_transaction(rec_id, source_loc, dest_loc, comp_id, batch, quantity):
    """
    Executes an ACID transactional stock reallocation in SQLite.
    Decrements available stock at source and increments stock at destination atomically.
    Prevents concurrent allocation race conditions.
    
    :param rec_id: Unique recommendation ID (e.g., REC-001).
    :param source_loc: Source location facility name.
    :param dest_loc: Destination location facility name.
    :param comp_id: Component ID being transferred.
    :param batch: Production batch identifier.
    :param quantity: Integer quantity to reallocate (must be complete pack multiple).
    :return: Tuple (success: bool, message: str).
    """
    session = SessionLocal()
    try:
        # Fetch source inventory record
        src_inv = session.query(Inventory).filter(
            Inventory.location == source_loc,
            Inventory.component_id == comp_id,
            Inventory.batch == batch
        ).first()

        # Fetch destination inventory record
        dest_inv = session.query(Inventory).filter(
            Inventory.location == dest_loc,
            Inventory.component_id == comp_id,
            Inventory.batch == batch
        ).first()

        if not src_inv or not dest_inv:
            session.rollback()
            return False, "Source or destination inventory record not found."

        # Verify safety stock invariant prior to state mutation
        available_src = src_inv.current_stock - src_inv.reserved_stock
        if available_src - quantity < src_inv.safety_stock:
            session.rollback()
            return False, f"Transaction aborted: Transfer of {quantity} units would breach source safety stock threshold ({src_inv.safety_stock})."

        # Execute atomic inventory updates
        src_inv.current_stock -= quantity
        dest_inv.current_stock += quantity

        # Log audit entry to OverrideLog table
        log_entry = OverrideLog(
            recommendation_id=rec_id,
            decision="APPROVED_TRANSACTION",
            reason=f"Atomic transfer of {quantity} units executed from {source_loc} to {dest_loc}.",
            timestamp=datetime.datetime.now()
        )
        session.add(log_entry)

        # Commit transaction atomically
        session.commit()
        return True, f"Successfully executed transaction: Transferred {quantity} units from {source_loc} to {dest_loc}."
    except Exception as e:
        session.rollback()
        return False, f"Transaction failed due to error: {str(e)}"
    finally:
        session.close()
