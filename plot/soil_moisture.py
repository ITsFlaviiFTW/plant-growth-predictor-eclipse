from fastapi import Request, HTTPException
from database.models import Plant, User
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

from matplotlib import rcParams
rcParams.update({
    'axes.facecolor': '#111827',
    'figure.facecolor': '#1f2937',
    'axes.edgecolor': 'white',
    'axes.labelcolor': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'text.color': 'white',
    'grid.color': '#4b5563',
    'grid.linestyle': '--',
    'grid.linewidth': 0.5,
    'legend.facecolor': '#1f2937',
    'legend.edgecolor': '#4b5563',
    'savefig.facecolor': '#1f2937',
})

from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from database.database import get_db
from jose import jwt, JWTError
from login.auth import SECRET_KEY, ALGORITHM

router = APIRouter()

@router.get("/plot/soil-moisture")
def soil_moisture_plot(request: Request, db: Session = Depends(get_db)):

    # Authenticate user
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's plant list
    plant_ids = request.query_params.get("plants")
    user_plant_query = db.query(Plant).filter_by(user_id=user.id)

    if plant_ids:
        ids = [int(p) for p in plant_ids.split(",") if p.isdigit()]
        user_plant_query = user_plant_query.filter(Plant.id.in_(ids))

    esp_ids = [p.esp_id for p in user_plant_query.all()]
    if not esp_ids:
        return Response(content=b"", media_type="image/png")

    # Query data
    result = db.execute("""
        SELECT DATE(timestamp) AS date, esp_id, AVG(soil_moisture) AS avg_moisture
        FROM current_sensor_data
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        AND esp_id = ANY(:esp_ids)
        GROUP BY DATE(timestamp), esp_id
        ORDER BY DATE(timestamp) ASC
    """, {"esp_ids": esp_ids}).fetchall()

    df = pd.DataFrame(result, columns=["date", "esp_id", "avg_moisture"])
    if df.empty:
        return Response(content=b"", media_type="image/png")

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 4))
    for esp_id, group in df.groupby("esp_id"):
        ax.plot(group["date"], group["avg_moisture"], marker='o', label=esp_id)

    ax.set_title("Average Daily Soil Moisture")
    ax.set_xlabel("Date")
    ax.set_ylabel("Moisture (%)")
    ax.grid(True)
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    # Return image
    buf = BytesIO()
    FigureCanvas(fig).print_png(buf)
    buf.seek(0)
    image_bytes = buf.read()
    buf.close()
    plt.close(fig)

    return Response(content=image_bytes, media_type="image/png")
