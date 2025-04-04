# database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CurrentSensorData(Base):
    __tablename__ = "current_sensor_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    esp_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    light_lux = Column(Float)
    distance_mm = Column(Integer)
    soil_moisture = Column(Integer)
