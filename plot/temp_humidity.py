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

@router.get("/plot/temp-humidity")
def temp_humidity_plot(db: Session = Depends(get_db)):
    # Pull data for the last 7 days
    result = db.execute("""
        SELECT timestamp, esp_id, temperature, humidity, soil_moisture
        FROM current_sensor_data
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        ORDER BY timestamp ASC
    """).fetchall()

    df = pd.DataFrame(result, columns=["timestamp", "esp_id", "temperature", "humidity", "soil_moisture"])
    if df.empty:
        return Response(content="No data", media_type="text/plain", status_code=404)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    fig, axs = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    for esp_id, group in df.groupby("esp_id"):
        axs[0].plot(group.index, group["temperature"], label=esp_id)
        axs[1].plot(group.index, group["humidity"], label=esp_id)
        axs[2].plot(group.index, group["soil_moisture"], label=esp_id)

    axs[0].set_title("Temperature")
    axs[1].set_title("Humidity")
    axs[2].set_title("Soil Moisture")
    for ax in axs:
        ax.legend()
        ax.grid(True)

    buf = BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    buf.seek(0)
    image_bytes = buf.read()
    buf.close()
    plt.close(fig)
    return Response(content=image_bytes, media_type="image/png")