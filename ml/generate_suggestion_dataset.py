import pandas as pd

df = pd.read_csv("ml/plant_health_data.csv")

# Clean and rename
df = df.rename(columns={
    "Ambient_Temperature": "temperature",
    "Humidity": "humidity",
    "Light_Intensity": "light_lux",
    "Soil_Moisture": "soil_moisture",
    "Plant_Health_Status": "label"
})

# Drop missing values
df = df[["temperature", "humidity", "light_lux", "soil_moisture", "label"]].dropna()

def build_prompt(row):
    return (
        f"temperature={round(row.temperature, 1)}, "
        f"humidity={round(row.humidity, 1)}, "
        f"light_lux={round(row.light_lux, 1)}, "
        f"soil_moisture={round(row.soil_moisture, 1)}"
    )

def generate_response(label, row):
    if label.lower() == "healthy":
        return "Conditions are optimal. No action needed."
    elif label.lower() == "moderate stress":
        return "Increase light or check watering levels."
    elif label.lower() == "high stress":
        if row.soil_moisture < 10:
            return "Water the plant immediately and increase light exposure."
        return "Check for under-watering and increase ambient conditions."
    else:
        return "Evaluate plant environment and adjust care."

df["prompt"] = df.apply(build_prompt, axis=1)
df["response"] = df.apply(lambda row: generate_response(row.label, row), axis=1)

df[["prompt", "response"]].to_csv("ml/suggestion_dataset.csv", index=False)
print("suggestion_dataset.csv generated.")
