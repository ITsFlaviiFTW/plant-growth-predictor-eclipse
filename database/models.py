# database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plants = relationship("Plant", back_populates="user")

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    esp_id = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="plants")
    image_path = Column(String, default="/static/plant-images/default.png")
    temp_min = Column(Integer)
    temp_max = Column(Integer)
    humidity_min = Column(Integer)
    humidity_max = Column(Integer)
    soil_min = Column(Integer)
    soil_max = Column(Integer)
    light_min = Column(Integer)
    light_max = Column(Integer)