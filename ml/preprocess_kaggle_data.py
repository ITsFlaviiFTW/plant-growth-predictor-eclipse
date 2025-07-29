import pandas as pd
import numpy as np
import sys

# Load original
df = pd.read_csv("ml/plant_health_data.csv")

# Rename to match your schema
df = df.rename(columns={
    "Soil_Moisture": "soil_moisture",
    "Ambient_Temperature": "temperature",
    "Humidity": "humidity",
    "Light_Intensity": "light_lux",
    "Plant_Health_Status": "health_status"
})

# Drop rows that make no logical sense
df = df[~((df["soil_moisture"] > 65) & (df["health_status"] == "High Stress"))]
df = df[~((df["humidity"] > 55) & (df["health_status"] == "High Stress"))]
df = df[~((df["temperature"] > 17) & (df["health_status"] == "High Stress"))]

# Bin features for robustness
def bin_temperature(t):
    if t < 18: return "low"
    elif t > 24: return "high"
    return "optimal"

def bin_humidity(h):
    if h < 50: return "low"
    elif h > 70: return "high"
    return "optimal"

def bin_light(lux):
    if lux < 500: return "dark"
    elif lux > 6000: return "bright"
    return "normal"

def bin_soil(m):
    if m < 40: return "dry"
    elif m > 70: return "wet"
    return "normal"

# Apply binned columns
df["temp_bin"] = df["temperature"].apply(bin_temperature)
df["humidity_bin"] = df["humidity"].apply(bin_humidity)
df["moisture_bin"] = df["soil_moisture"].apply(bin_soil)
df["light_bin"] = df["light_lux"].apply(bin_light)

# Save processed dataset
if "--save" in sys.argv:
    df.to_csv("ml/plant_health_data_processed.csv", index=False)
    print("Saved: ml/plant_health_data_processed.csv")
