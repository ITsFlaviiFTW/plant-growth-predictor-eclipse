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
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
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
from ml.predict import analyze_plant

app = FastAPI()

app.include_router(auth_router)
app.include_router(light_intensity.router)
app.include_router(temp_humidity.router)
app.include_router(soil_moisture.router)

# Load model and encoder
BASE_DIR = Path(__file__).resolve().parent
PLANT_IMG_DIR = BASE_DIR / "static" / "plant-images"
PLANT_IMG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_IMG_WEB = "/static/plant-images/default.png"
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
@app.get("/favicon.ico", include_in_schema=False) # Icon
def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.ico", media_type="image/x-icon")

# Define category ranges
category_ranges = {
    "temperature": {
        "low": (5, 17),
        "optimal": (18, 25),
        "high": (26, 35)
    },
    "humidity": {
        "low": (10, 49),
        "optimal": (50, 70),
        "high": (71, 90)
    },
    "soil_moisture": {
        "low": (5, 44),
        "optimal": (45, 70),
        "high": (71, 90)
    },
    "light_lux": {
        "low": (0, 499),
        "optimal": (500, 10000),
        "high": (10001, 30000)
    }
}

class PlantCreate(BaseModel):
    esp_id: str
    nickname: str = None

class DeletePlantsRequest(BaseModel):
    esp_ids: List[str]

def get_status(value, category):
    ranges = category_ranges[category]
    if ranges["low"][0] <= value <= ranges["low"][1]:
        return "low"
    elif ranges["optimal"][0] <= value <= ranges["optimal"][1]:
        return "optimal"
    elif ranges["high"][0] <= value <= ranges["high"][1]:
        return "high"
    return "critical"

def get_range_config(value, category):
    ranges = category_ranges[category]
    min_val = ranges["low"][0]
    max_val = ranges["high"][1]
    span = max_val - min_val

    def to_pct(v):
        return 100 * (v - min_val) / span

    optimal_midpoint = (ranges["optimal"][0] + ranges["optimal"][1]) / 2

    return {
        "optimal_left": round(to_pct(ranges["optimal"][0]), 1),
        "optimal_width": round(to_pct(ranges["optimal"][1]) - to_pct(ranges["optimal"][0]), 1),
        "target": round(to_pct(optimal_midpoint), 1),
        "target_value": round(optimal_midpoint, 1),
        "current": round(to_pct(value), 1)
    }

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

    # delete image file if it's not the shared default
    try:
        if plant.image_path and plant.image_path != DEFAULT_IMG_WEB:
            img_path = PLANT_IMG_DIR / Path(plant.image_path).name
            if img_path.exists():
                img_path.unlink()
    except Exception:
        pass

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

    # Ensure the esp_id exists in the current_sensor_data table
    exists = db.query(CurrentSensorData).filter_by(esp_id=espId).first()
    if not exists:
        return {"error": f"ESP ID '{espId}' has not sent any data yet. Please power on the device and try again."}

    if not user:
        return {"error": "User not found"}

    # Prevent duplicate ESP ID for this user
    already_added = db.query(Plant).filter_by(user_id=user.id, esp_id=espId).first()
    if already_added:
        return {"error": f"ESP ID '{espId}' is already added to your plants."}

    # Save image if present (preserve extension, otherwise fallback to default)
    image_path = f"/static/plant-images/{espId}.png"
    if plantImage and plantImage.filename:
        # decide extension by content-type
        ext = ".png"
        ct = (plantImage.content_type or "").lower()
        if ct.endswith("jpeg") or ct.endswith("jpg"): ext = ".jpg"
        elif ct.endswith("webp"): ext = ".webp"
        elif ct.endswith("png"): ext = ".png"

        image_path = f"/static/plant-images/{espId}{ext}"
        with open(PLANT_IMG_DIR / f"{espId}{ext}", "wb") as f:
            f.write(await plantImage.read())
    else:
        image_path = DEFAULT_IMG_WEB

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
        soil_moisture=data.soil_moisture
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

    # Run analysis using simpler logic
    result = analyze_plant({
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "light_lux": latest.light_lux,
        "soil_moisture": latest.soil_moisture
    })

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
        "ai_overall_status": result["overall_status"],
        "ai_suggestions": result["suggestions"]
    }

@app.get("/plants/check-esp/{esp_id}")
def check_esp(esp_id: str, db: Session = Depends(get_db)):
    exists = db.query(CurrentSensorData).filter(CurrentSensorData.esp_id == esp_id).first() is not None
    return {"exists": exists}

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

    # Use new AI logic
    analysis = analyze_plant({
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "light_lux": latest.light_lux,
        "soil_moisture": latest.soil_moisture
    })

    # End timing
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    eastern = pytz.timezone("America/Toronto")
    local_time = latest.timestamp.replace(tzinfo=pytz.utc).astimezone(eastern)

    range_data = {
        "temperature": get_range_config(latest.temperature, "temperature"),
        "humidity": get_range_config(latest.humidity, "humidity"),
        "soil_moisture": get_range_config(latest.soil_moisture, "soil_moisture"),
        "light_lux": get_range_config(latest.light_lux, "light_lux"),
    }

    status_data = {
        "temperature": get_status(latest.temperature, "temperature"),
        "humidity": get_status(latest.humidity, "humidity"),
        "soil_moisture": get_status(latest.soil_moisture, "soil_moisture"),
        "light_lux": get_status(latest.light_lux, "light_lux"),
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "latest": latest,
        "esp_ids": esp_ids,
        "esp_id": latest.esp_id,
        "predicted_health": label,
        "confidence": confidence,
        "suggestion": analysis["suggestions"],
        "influencers": top_factors_readable,
        "inference_time": duration_ms,
        "plant": plant,
        "overall_status": analysis["overall_status"],
        "range_data": range_data,          
        "status_data": status_data 
    })