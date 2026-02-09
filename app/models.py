from sqlalchemy import Column, Integer, String, Float, Date, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    unit_cost = Column(Float)
    quantity_on_hand = Column(Integer)
    expiry_date = Column(Date)


class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True)
    units_sold = Column(Integer)
    date = Column(Date)


class RunsLog(Base):
    __tablename__ = "runs_log"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    outcome = Column(String)  # alert | silent | failed


class AlertsLog(Base):
    __tablename__ = "alerts_log"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    return create_engine("sqlite:///./inventory.db")


def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
