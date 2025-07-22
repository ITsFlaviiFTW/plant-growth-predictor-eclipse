from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pytz
from fastapi import Query
from database.models import CurrentSensorData
from database.database import get_db
import pickle
import pandas as pd
from pathlib import Path
import types

app = FastAPI()

# Load model and encoder
model_path = Path("ml/health_model.pkl")
encoder_path = Path("ml/label_encoder.pkl")

with model_path.open("rb") as f:
    model = pickle.load(f)

with encoder_path.open("rb") as f:
    label_encoder = pickle.load(f)

# ✅ Check if model is valid
if isinstance(model, pd.DataFrame) or isinstance(model, pd.Series) or isinstance(model, (list, tuple)) or isinstance(model, (str, bytes)) or isinstance(model, (int, float)):
    raise TypeError("Loaded object from health_model.pkl is not a valid sklearn model. It appears to be a raw data object.")

# Static + template setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Incoming sensor data schema
class SensorData(BaseModel):
    esp_id: str
    temperature: float
    humidity: float
    light_lux: float
    soil_moisture: int
    distance_mm: int

# ESP32 POST endpoint
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

# ESP32 Predict endpoint
@app.get("/predict/{esp_id}")
def predict_health_for_esp(esp_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(CurrentSensorData)
        .filter(CurrentSensorData.esp_id == esp_id)
        .order_by(CurrentSensorData.timestamp.desc())
        .first()
    )
    if not latest:
        return {"error": "No data found for ESP ID."}

    X = pd.DataFrame([{
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "light_lux": latest.light_lux,
        "soil_moisture": latest.soil_moisture
    }])
    prediction = model.predict(X)[0]
    label = label_encoder.inverse_transform([prediction])[0]

    return {
        "predicted_health": label,
        "timestamp": latest.timestamp,
        "esp_id": latest.esp_id
    }

# Render live dashboard
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), esp_id: str = Query(None)):
    esp_ids = db.query(CurrentSensorData.esp_id).distinct().all()
    esp_ids = [row.esp_id for row in esp_ids]

    if not esp_id:
        first = db.query(CurrentSensorData.esp_id).order_by(CurrentSensorData.timestamp.desc()).first()
        if not first:
            return HTMLResponse("<h2>No sensor data available.</h2>")
        esp_id = first.esp_id

    latest = db.query(CurrentSensorData).filter_by(esp_id=esp_id).order_by(CurrentSensorData.timestamp.desc()).first()
    if not latest:
        return HTMLResponse(f"<h2>No data for {esp_id}</h2>")

    eastern = pytz.timezone("America/Toronto")
    local_time = latest.timestamp.replace(tzinfo=pytz.utc).astimezone(eastern)

    # Predict health from latest record
    X = pd.DataFrame([{
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "light_lux": latest.light_lux,
        "soil_moisture": latest.soil_moisture
    }])
    prediction = model.predict(X)[0]
    label = label_encoder.inverse_transform([prediction])[0]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "temperature": f"{latest.temperature:.1f}",
        "humidity": f"{latest.humidity:.1f}",
        "light_lux": f"{latest.light_lux:.0f}",
        "soil_moisture": latest.soil_moisture,
        "distance_mm": latest.distance_mm,
        "esp_id": latest.esp_id,
        "timestamp": local_time.strftime("%Y-%m-%d %H:%M:%S"),
        "esp_ids": esp_ids,
        "predicted_health": label
    })
