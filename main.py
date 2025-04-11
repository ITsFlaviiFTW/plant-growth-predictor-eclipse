from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # Just used to fill in values

from database.models import CurrentSensorData
from database.database import get_db

app = FastAPI()

# Mount static files so the image can be loaded
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template engine (just to load .html, even if it’s already made)
templates = Jinja2Templates(directory="templates")

class SensorData(BaseModel):
    esp_id: str
    temperature: float
    humidity: float
    light_lux: float
    soil_moisture: int
    distance_mm: int

@app.post("/sensor/update")
def update_sensor_data(data: SensorData, db: Session = Depends(get_db)):
    entry = CurrentSensorData(
        esp_id=data.esp_id,
        timestamp=datetime.utcnow(),
        temperature=data.temperature,
        humidity=data.humidity,
        light_lux=data.light_lux,
        soil_moisture=data.soil_moisture,
        distance_mm=data.distance_mm,
    )
    db.add(entry)
    db.commit()
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    latest = db.query(CurrentSensorData).order_by(CurrentSensorData.timestamp.desc()).first()
    if not latest:
        return HTMLResponse("<h2>No sensor data available.</h2>")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "temperature": f"{latest.temperature:.1f}",
        "humidity": f"{latest.humidity:.1f}",
        "light_lux": f"{latest.light_lux:.0f}",
        "soil_moisture": latest.soil_moisture,
        "distance_mm": latest.distance_mm,
    })
