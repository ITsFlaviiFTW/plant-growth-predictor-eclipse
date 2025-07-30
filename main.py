from fastapi import FastAPI, Depends, Request, Query, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime
import pytz
import pickle
import pandas as pd
from pathlib import Path
from database.models import CurrentSensorData
from database.database import get_db
from ml.preprocess_kaggle_data import bin_temperature, bin_humidity, bin_light, bin_soil
from ml.recommendations import suggest
from ml.t5_predict import generate_suggestion
from login.login_routes import router as auth_router
from fastapi.responses import RedirectResponse
from login.auth import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError


app = FastAPI()
app.include_router(auth_router)

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

# GET: prediction API
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

    binned = {
        "temp_bin": bin_temperature(latest.temperature),
        "humidity_bin": bin_humidity(latest.humidity),
        "light_bin": bin_light(latest.light_lux),
        "moisture_bin": bin_soil(latest.soil_moisture),
    }

    X = pd.get_dummies(pd.DataFrame([binned]))
    X = X.reindex(columns=feature_columns, fill_value=0)

    prediction = model.predict(X)[0]
    label = label_encoder.inverse_transform([prediction])[0]
    confidence = round(model.predict_proba(X)[0][prediction] * 100, 2)

    importances = model.feature_importances_
    importance_dict = dict(zip(X.columns, importances))
    sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)

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
    }
def explain_prediction(binned, importances):
    feature_map = {
        "temp_bin": "temperature",
        "humidity_bin": "humidity",
        "moisture_bin": "soil moisture",
        "light_bin": "light level"
    }

    # Sort features by importance
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    top_features = [f for f, _ in sorted_features[:2]]

    explanations = []
    for f in top_features:
        bin_value = binned.get(f)
        readable = f"{feature_map.get(f)} is {bin_value}"
        explanations.append(readable)

    return "Health status primarily influenced because " + " and ".join(explanations) + "."

# Suggestion route
@app.get("/suggestion/{esp_id}")
def suggestion_for_esp(esp_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(CurrentSensorData)
        .filter(CurrentSensorData.esp_id == esp_id)
        .order_by(CurrentSensorData.timestamp.desc())
        .first()
    )

    if not latest:
        return {"error": "No data for ESP ID."}

    prompt = f"temperature={latest.temperature}, humidity={latest.humidity}, light_lux={latest.light_lux}, soil_moisture={latest.soil_moisture}"
    suggestion = generate_suggestion(prompt)

    return {
        "esp_id": esp_id,
        "prompt": prompt,
        "suggestion": suggestion
    }

# Custom suggestion route
@app.post("/custom-suggestion")
def custom_suggestion(data: dict = Body(...)):
    from ml.suggestion_model import generate_suggestion
    prompt = data.get("prompt", "")
    suggestion = generate_suggestion(prompt)
    return {"prompt": prompt, "suggestion": suggestion}

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

    # Same existing dashboard logic below
    esp_ids = [row.esp_id for row in db.query(CurrentSensorData.esp_id).distinct().all()]

    if not esp_id:
        first = db.query(CurrentSensorData.esp_id).order_by(CurrentSensorData.timestamp.desc()).first()
        if not first:
            return HTMLResponse("<h2>No sensor data available.</h2>")
        esp_id = first.esp_id

    latest = (
        db.query(CurrentSensorData)
        .filter_by(esp_id=esp_id)
        .order_by(CurrentSensorData.timestamp.desc())
        .first()
    )

    if not latest:
        return HTMLResponse(f"<h2>No data for {esp_id}</h2>")

    eastern = pytz.timezone("America/Toronto")
    local_time = latest.timestamp.replace(tzinfo=pytz.utc).astimezone(eastern)

    binned = {
        "temp_bin": bin_temperature(latest.temperature),
        "humidity_bin": bin_humidity(latest.humidity),
        "light_bin": bin_light(latest.light_lux),
        "moisture_bin": bin_soil(latest.soil_moisture),
    }

    X = pd.get_dummies(pd.DataFrame([binned]))
    X = X.reindex(columns=feature_columns, fill_value=0)

    prediction = model.predict(X)[0]
    label = label_encoder.inverse_transform([prediction])[0]
    confidence = round(model.predict_proba(X)[0][prediction] * 100, 2)
    importances = dict(zip(X.columns, model.feature_importances_))
    explanation = explain_prediction(binned, importances)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "latest": latest,
        "esp_ids": esp_ids,
        "esp_id": latest.esp_id,
        "predicted_health": label,
        "confidence": confidence,
        "explanation": explanation
    })
