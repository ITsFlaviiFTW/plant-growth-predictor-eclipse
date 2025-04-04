from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import HTMLResponse

from database.models import CurrentSensorData
from database.database import get_db

app = FastAPI()

# Schema for incoming sensor data
class SensorData(BaseModel):
    esp_id: str
    temperature: float
    humidity: float
    light_lux: float
    soil_moisture: int
    distance_mm: int

# POST endpoint to receive data from ESP32
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

# GET endpoint to display sensor data as HTML
@app.get("/", response_class=HTMLResponse)
def read_sensor_data(db: Session = Depends(get_db)):
    rows = db.query(CurrentSensorData).order_by(CurrentSensorData.timestamp.desc()).all()

    html = """
    <html>
        <head>
            <title>Plant Sensor Data</title>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Current Sensor Data</h1>
            <table>
                <tr>
                    <th>ID</th>
                    <th>ESP ID</th>
                    <th>Timestamp</th>
                    <th>Temperature (&deg;C)</th>
                    <th>Humidity (%)</th>
                    <th>Light (lux)</th>
                    <th>Distance (mm)</th>
                    <th>Soil Moisture</th>
                </tr>
    """

    for row in rows:
        html += f"""
                <tr>
                    <td>{row.id}</td>
                    <td>{row.esp_id}</td>
                    <td>{row.timestamp}</td>
                    <td>{row.temperature}</td>
                    <td>{row.humidity}</td>
                    <td>{row.light_lux}</td>
                    <td>{row.distance_mm}</td>
                    <td>{row.soil_moisture}</td>
                </tr>
        """

    html += """
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
