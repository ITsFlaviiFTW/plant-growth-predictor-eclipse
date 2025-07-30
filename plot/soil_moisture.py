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

router = APIRouter()

@router.get("/plot/soil-moisture")
def soil_moisture_plot(db: Session = Depends(get_db)):
    result = db.execute("""
        SELECT DATE(timestamp) AS date, esp_id, AVG(soil_moisture) AS avg_moisture
        FROM current_sensor_data
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(timestamp), esp_id
        ORDER BY DATE(timestamp) ASC
    """).fetchall()

    df = pd.DataFrame(result, columns=["date", "esp_id", "avg_moisture"])
    if df.empty:
        return Response(content="No data", media_type="text/plain", status_code=404)

    fig, ax = plt.subplots(figsize=(12, 4))

    for esp_id, group in df.groupby("esp_id"):
        ax.plot(group["date"], group["avg_moisture"], marker='o', label=esp_id)

    ax.set_title("Average Daily Soil Moisture")
    ax.set_xlabel("Date")
    ax.set_ylabel("Moisture (%)")
    ax.grid(True)
    ax.legend()
    plt.xticks(rotation=45)
    # plt.tight_layout()

    buf = BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    buf.seek(0)
    image_bytes = buf.read()
    buf.close()
    plt.close(fig)
    return Response(content=image_bytes, media_type="image/png")