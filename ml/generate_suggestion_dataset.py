import pandas as pd
import random
from itertools import product
from pathlib import Path

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

# Scoring function for vitals
def compute_score(value, optimal_min, optimal_max, value_min, value_max):
    if optimal_min <= value <= optimal_max:
        return 100
    elif value < optimal_min:
        return max(0, 100 - ((optimal_min - value) / (optimal_min - value_min)) * 100)
    else:
        return max(0, 100 - ((value - optimal_max) / (value_max - optimal_max)) * 100)

# Generate all 81 category combinations
categories = ["low", "optimal", "high"]
combinations = list(product(categories, repeat=4))

records = []

for combo in combinations:
    for _ in range(5):
        temp_cat, hum_cat, light_cat, moist_cat = combo

        # Sample numeric values from category ranges
        temperature = round(random.uniform(*category_ranges["temperature"][temp_cat]), 1)
        humidity = round(random.uniform(*category_ranges["humidity"][hum_cat]), 1)
        light_lux = round(random.uniform(*category_ranges["light_lux"][light_cat]), 1)
        soil_moisture = round(random.uniform(*category_ranges["soil_moisture"][moist_cat]), 1)

        # Score each vital
        temp_score = compute_score(temperature, 18, 25, 5, 35)
        hum_score = compute_score(humidity, 50, 70, 10, 90)
        light_score = compute_score(light_lux, 500, 10000, 0, 30000)
        moist_score = compute_score(soil_moisture, 45, 70, 5, 90)

        health_score = round((temp_score + hum_score + light_score + moist_score) / 4, 1)

        # Health label from score
        if health_score >= 90:
            label = "Excellent"
        elif health_score >= 75:
            label = "Good"
        elif health_score >= 50:
            label = "Moderate"
        elif health_score >= 25:
            label = "Poor"
        else:
            label = "Critical"

        # Prompt
        prompt = (
            f"temperature={temperature}, "
            f"humidity={humidity}, "
            f"light_lux={light_lux}, "
            f"soil_moisture={soil_moisture}"
        )

        # Response
        response_parts = []

        if temp_cat != "optimal":
            reason = "too low" if temp_cat == "low" else "too high"
            response_parts.append(f"Temperature is {reason}. Move the plant to a {'warmer' if temp_cat == 'low' else 'cooler'} location.")
        if hum_cat != "optimal":
            reason = "too low" if hum_cat == "low" else "too high"
            response_parts.append(f"Humidity is {reason}. Adjust misting or ventilation accordingly.")
        if light_cat != "optimal":
            reason = "too low" if light_cat == "low" else "too high"
            response_parts.append(f"Light is {reason}. {'Increase exposure' if light_cat == 'low' else 'Reduce direct sunlight'}.")
        if moist_cat != "optimal":
            reason = "too low" if moist_cat == "low" else "too high"
            response_parts.append(f"Soil moisture is {reason}. {'Water the plant' if moist_cat == 'low' else 'Improve drainage'}.")

        if not response_parts:
            response_parts.append("All vitals are within optimal range. No action needed.")

        response = " ".join(response_parts)

        records.append({
            "temperature": temperature,
            "humidity": humidity,
            "light_lux": light_lux,
            "soil_moisture": soil_moisture,
            "temp_score": round(temp_score, 1),
            "humidity_score": round(hum_score, 1),
            "light_score": round(light_score, 1),
            "moisture_score": round(moist_score, 1),
            "health_score": health_score,
            "label": label,
            "prompt": prompt,
            "response": response
        })

# Save both datasets
df = pd.DataFrame(records)

Path("ml").mkdir(parents=True, exist_ok=True)
df.to_csv("ml/augmented_health_data.csv", index=False)
df[["prompt", "response"]].to_csv("ml/suggestion_dataset.csv", index=False)

print("Dataset generated:")
print("- ml/augmented_health_data.csv")
print("- ml/suggestion_dataset.csv")
