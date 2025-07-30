# database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base
from datetime import datetime
from database.database import Base

Base = declarative_base()

class CurrentSensorData(Base):
    __tablename__ = "current_sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    esp_id = Column(String)
    timestamp = Column(DateTime)
    temperature = Column(Float)
    humidity = Column(Float)
    light_lux = Column(Float)
    soil_moisture = Column(Integer)
    distance_mm = Column(Integer)
    plant_height_mm = Column(Integer)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())