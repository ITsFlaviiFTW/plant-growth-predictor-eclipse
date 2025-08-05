# Standard library imports
from datetime import datetime
from pathlib import Path
import pickle
import time

# Third-party imports
import pandas as pd
import pytz
from fastapi import (
    Body, Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List

# Local application imports
from database.database import get_db
from database.models import CurrentSensorData, Plant, User
from login.auth import ALGORITHM, SECRET_KEY
from login.login_routes import router as auth_router
from plot import light_intensity, soil_moisture, temp_humidity

app = FastAPI()

app.include_router(auth_router)
app.include_router(light_intensity.router)
app.include_router(temp_humidity.router)
app.include_router(soil_moisture.router)

# Load model and encoder
BASE_DIR = Path(__file__).resolve().parent
model_path = BASE_DIR / "ml" / "health_model.pkl"
encoder_path = BASE_DIR / "ml" / "label_encoder.pkl"
features_path = BASE_DIR / "ml" / "feature_columns.pkl"

with model_path.open("rb") as f:
    model = pickle.load(f)
with encoder_path.open("rb") as f:
    label_encoder = pickle.load(f)
with features_path.open("rb") as f:
    feature_columns = pickle.load(f)

# Ensure valid model
if isinstance(model, (pd.DataFrame, pd.Series, list, tuple, str, bytes, int, float)):
    raise TypeError("Loaded object from health_model.pkl is not a valid sklearn model.")

# Static files + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class PlantCreate(BaseModel):
    esp_id: str
    nickname: str = None

class DeletePlantsRequest(BaseModel):
    esp_ids: List[str]

@app.get("/plants/list")
def list_user_plants(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError
    except (JWTError, ValueError):
        return RedirectResponse("/auth/login", status_code=302)

    user = db.query(User).filter_by(username=username).first()
    if not user:
        return {"error": "User not found"}

    plants = db.query(Plant).filter_by(user_id=user.id).all()
    results = []

    for plant in plants:
        latest = (
            db.query(CurrentSensorData)
            .filter(CurrentSensorData.esp_id == plant.esp_id)
            .order_by(CurrentSensorData.timestamp.desc())
            .first()
        )

        if not latest:
            continue

        input_data = pd.DataFrame([{
            "temperature": latest.temperature,
            "humidity": latest.humidity,
            "light_lux": latest.light_lux,
            "soil_moisture": latest.soil_moisture
        }])
        input_data = input_data.reindex(columns=feature_columns, fill_value=0)

        prediction = model.predict(input_data)[0]
        confidence = round(model.predict_proba(input_data)[0][prediction] * 100, 2)

        results.append({
            "id": plant.id,
            "name": plant.nickname,
            "esp_id": plant.esp_id,
            "health": confidence
        })

    return {"plants": results}

@app.delete("/plants/delete/{plant_id}")
def delete_plant_by_id(plant_id: int, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter_by(username=username).first()
    plant = db.query(Plant).filter_by(id=plant_id, user_id=user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    db.delete(plant)
    db.commit()
    return {"message": "Plant deleted successfully"}

@app.post("/plants/submit")
async def submit_new_plant(
    request: Request,
    plantName: str = Form(...),
    espId: str = Form(...),
    useCustomRanges: str = Form(...),
    tempMin: int = Form(...),
    tempMax: int = Form(...),
    humidityMin: int = Form(...),
    humidityMax: int = Form(...),
    soilMin: int = Form(...),
    soilMax: int = Form(...),
    lightMin: int = Form(...),
    lightMax: int = Form(...),
    plantImage: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Auth check
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError
    except (JWTError, ValueError):
        return RedirectResponse("/auth/login", status_code=302)

    user = db.query(User).filter_by(username=username).first()
    if not user:
        return {"error": "User not found"}

    # Prevent duplicate
    exists = db.query(Plant).filter_by(esp_id=espId, user_id=user.id).first()
    if exists:
        return {"error": "You already added this plant"}

    # Save image if present
    image_path = f"/static/plant-images/{espId}.png"
    if plantImage:
        with open(f"static/plant-images/{espId}.png", "wb") as f:
            f.write(await plantImage.read())
    else:
        image_path = "/static/plant-images/default.png"  # fallback image

    # Create new plant
    new_plant = Plant(
        user_id=user.id,
        esp_id=espId,
        nickname=plantName,
        temp_min=tempMin,
        temp_max=tempMax,
        humidity_min=humidityMin,
        humidity_max=humidityMax,
        soil_min=soilMin,
        soil_max=soilMax,
        light_min=lightMin,
        light_max=lightMax,
        image_path=image_path
    )
    db.add(new_plant)
    db.commit()
    return {"message": "Plant added successfully"}

@app.get("/plants/add", response_class=HTMLResponse)
def serve_add_plant_form(request: Request):
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise ValueError
    except (JWTError, ValueError):
        return RedirectResponse("/auth/login")
    return templates.TemplateResponse("add-plant.html", {"request": request})

# Incoming sensor data schema
class SensorData(BaseModel):
    esp_id: str
    temperature: float
    humidity: float
    light_lux: float
    soil_moisture: int
    distance_mm: int
    plant_height_mm: int

# POST: sensor update
@app.post("/sensor/update")
def update_sensor_data(data: SensorData, db: Session = Depends(get_db)):
    # Check if esp_id is assigned to a plant
    from database.models import Plant
    entry = CurrentSensorData(
        esp_id=data.esp_id,
        timestamp=datetime.utcnow(),
        temperature=data.temperature,
        humidity=data.humidity,
        light_lux=data.light_lux,
        soil_moisture=data.soil_moisture,
        distance_mm=data.distance_mm,
        plant_height_mm=data.plant_height_mm
    )
    db.add(entry)
    db.commit()
    return {"status": "success"}

@app.get("/evaluate/{esp_id}")
def evaluate_health_for_esp(esp_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(CurrentSensorData)
        .filter(CurrentSensorData.esp_id == esp_id)
        .order_by(CurrentSensorData.timestamp.desc())
        .first()
    )

    if not latest:
        return {"error": "No data found for ESP ID."}

    # Prepare raw input
    input_data = pd.DataFrame([{
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "light_lux": latest.light_lux,
        "soil_moisture": latest.soil_moisture
    }])
    input_data = input_data.reindex(columns=feature_columns, fill_value=0)

    # Prediction
    prediction = model.predict(input_data)[0]
    label = label_encoder.inverse_transform([prediction])[0]
    confidence = round(model.predict_proba(input_data)[0][prediction] * 100, 2)

    # Feature importance
    importances = dict(zip(feature_columns, model.feature_importances_))
    sorted_importance = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    top_factors = [f[0] for f in sorted_importance[:2]]
    top_factors_readable = ', '.join(f.replace('_', ' ').title() for f in top_factors)

    # AI suggestion
    suggestion = None
    if label.lower() != "healthy":
        from ml.t5_predict import generate_suggestion
        prompt = (
            f"temperature={latest.temperature}, "
            f"humidity={latest.humidity}, "
            f"light_lux={latest.light_lux}, "
            f"soil_moisture={latest.soil_moisture}"
        )
        suggestion = generate_suggestion(prompt)

    return {
        "esp_id": esp_id,
        "timestamp": latest.timestamp.isoformat(),
        "predicted_health": label,
        "confidence": confidence,
        "features": {
            "temperature": float(latest.temperature),
            "humidity": float(latest.humidity),
            "light_lux": float(latest.light_lux),
            "soil_moisture": int(latest.soil_moisture),
        },
        "feature_importance": [
            [feature, float(importance)] for feature, importance in sorted_importance
        ],
        "suggestion": suggestion
    }

@app.get("/plants/check-esp/{esp_id}")
def check_esp(esp_id: str, db: Session = Depends(get_db)):
    exists = db.query(CurrentSensorData).filter(CurrentSensorData.esp_id == esp_id).first() is not None
    return {"exists": exists}

# GET: live dashboard
@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    esp_id: str = Query(None)
):
    # Check auth
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/auth/login")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError
    except (JWTError, ValueError):
        return RedirectResponse("/auth/login")

    user = db.query(User).filter_by(username=username).first()
    esp_ids = [plant.esp_id for plant in user.plants]
    plant = db.query(Plant).filter_by(esp_id=esp_id, user_id=user.id).first()

    # If no plants added, render empty state
    if not esp_ids:
        return templates.TemplateResponse("empty-dashboard.html", {"request": request})
    
    if not esp_id:
        esp_id = esp_ids[0]

    latest = (
        db.query(CurrentSensorData)
        .filter_by(esp_id=esp_id)
        .order_by(CurrentSensorData.timestamp.desc())
        .first()
    )

    if not latest:
        return HTMLResponse(f"<h2>No data for {esp_id}</h2>")

    # Start timing
    start = time.perf_counter()

    input_data = pd.DataFrame([{
    "temperature": latest.temperature,
    "humidity": latest.humidity,
    "light_lux": latest.light_lux,
    "soil_moisture": latest.soil_moisture
    }])
    input_data = input_data.reindex(columns=feature_columns, fill_value=0)

    prediction = model.predict(input_data)[0]
    label = label_encoder.inverse_transform([prediction])[0]
    confidence = round(model.predict_proba(input_data)[0][prediction] * 100, 2)
    importances = dict(zip(feature_columns, model.feature_importances_))
    sorted_importance = sorted(importances.items(), key=lambda x: x[1], reverse=True)

    top_factors = [f[0] for f in sorted_importance[:2]]
    top_factors_readable = ', '.join(f.replace('_', ' ').title() for f in top_factors)

    suggestion = None
    if label.lower() != "healthy":
        from ml.t5_predict import generate_suggestion
        prompt = (
            f"temperature={latest.temperature}, "
            f"humidity={latest.humidity}, "
            f"light_lux={latest.light_lux}, "
            f"soil_moisture={latest.soil_moisture}"
        )
        suggestion = generate_suggestion(prompt)

    # End timing
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    eastern = pytz.timezone("America/Toronto")
    local_time = latest.timestamp.replace(tzinfo=pytz.utc).astimezone(eastern)

    return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "latest": latest,
    "esp_ids": esp_ids,
    "esp_id": latest.esp_id,
    "predicted_health": label,
    "confidence": confidence,
    "suggestion": suggestion,
    "influencers": top_factors_readable,
    "inference_time": duration_ms,
    "plant": plant
})
