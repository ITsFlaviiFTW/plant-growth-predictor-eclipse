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

@router.get("/plot/light-intensity")
def light_intensity_plot(db: Session = Depends(get_db)):
    # Query: Get daily average light per sensor
    result = db.execute("""
        SELECT DATE(timestamp) AS date, esp_id, AVG(light_lux) AS avg_lux
        FROM current_sensor_data
        GROUP BY DATE(timestamp), esp_id
        ORDER BY DATE(timestamp) ASC
    """).fetchall()

    # Convert to DataFrame
    df = pd.DataFrame(result, columns=["date", "esp_id", "avg_lux"])

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 3))
    for esp_id, group in df.groupby("esp_id"):
        ax.bar(group["date"], group["avg_lux"], label=esp_id)
    ax.set_title("Average Daily Light Intensity per Sensor")
    ax.set_xlabel("Date")
    ax.set_ylabel("Average Daily Lux")
    ax.legend()
    plt.xticks(rotation=45)
    #plt.tight_layout()

    # Render to image
    buf = BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    buf.seek(0)
    image_bytes = buf.read()
    buf.close()
    plt.close(fig)
    return Response(content=image_bytes, media_type="image/png")