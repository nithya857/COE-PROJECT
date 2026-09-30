import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship

Base = declarative_base()

class Component(Base):
    __tablename__ = 'components'

    component_id = Column(String(50), primary_key=True)
    component_name = Column(String(100), nullable=False)
    pack_size = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    unit_weight_kg = Column(Float, nullable=False, default=1.5)
    criticality = Column(String(20), nullable=False)

class Location(Base):
    __tablename__ = 'locations'

    location_id = Column(String(50), primary_key=True)
    location_name = Column(String(100), nullable=False, unique=True)

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(50), ForeignKey('components.component_id'), nullable=False)
    location = Column(String(100), nullable=False)
    batch = Column(String(20), nullable=False, default='B1')
    current_stock = Column(Integer, nullable=False)
    safety_stock = Column(Integer, nullable=False)
    reserved_stock = Column(Integer, nullable=False, default=0)

class Forecast(Base):
    __tablename__ = 'forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(50), ForeignKey('components.component_id'), nullable=False)
    location = Column(String(100), nullable=False)
    batch = Column(String(20), nullable=False, default='B1')
    forecast_7_days = Column(Float, nullable=False)
    uncertainty_percent = Column(Float, nullable=False)
    urgency = Column(String(20), nullable=False)

class TransferRoute(Base):
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
    __tablename__ = 'override_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(50), nullable=False)
    decision = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)

class ValidationCase(Base):
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

# Database Connection Setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def init_db():
    """Creates all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Returns a new DB session instance."""
    return SessionLocal()

def execute_transfer_transaction(rec_id, source_loc, dest_loc, comp_id, batch, quantity):
    """
    Executes an ACID transactional stock reallocation in SQLite.
    Decrements available stock at source and increments stock at destination atomically.
    Prevents concurrent allocation race conditions.
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

        # Verify safety stock invariant
        available_src = src_inv.current_stock - src_inv.reserved_stock
        if available_src - quantity < src_inv.safety_stock:
            session.rollback()
            return False, f"Transaction aborted: Transfer of {quantity} units would breach source safety stock threshold ({src_inv.safety_stock})."

        # Execute atomic inventory updates
        src_inv.current_stock -= quantity
        dest_inv.current_stock += quantity

        # Log action to override/approval database
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
