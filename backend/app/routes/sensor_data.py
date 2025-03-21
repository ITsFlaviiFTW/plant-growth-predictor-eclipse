import random
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Temporary in-memory storage for sensor data
sensor_data_store = []

# Request model for sensor data
class SensorDataRequest(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: int
    light_intensity: int

@router.post("/sensor-data")
def receive_sensor_data(data: SensorDataRequest):
    sensor_data_store.append(data.dict())  # Store data in memory
    return {"message": "Data received successfully", "data": data}

@router.get("/sensor-data")
def get_sensor_data():
    return {"sensor_data": sensor_data_store}

@router.get("/mock-sensor-data")
def get_mock_sensor_data():
    """Generates random sensor data for testing the frontend."""
    mock_data = {
        "temperature": round(random.uniform(18, 30), 2),
        "humidity": random.randint(30, 90),
        "soil_moisture": random.randint(10, 100),
        "light_intensity": random.randint(100, 10000),
    }
    return mock_data
