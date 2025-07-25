# database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

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