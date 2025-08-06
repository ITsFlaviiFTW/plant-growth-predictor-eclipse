import pickle
import numpy as np

# Load health classifier and encoder
with open("ml/health_model.pkl", "rb") as f:
    health_model = pickle.load(f)

with open("ml/label_encoder.pkl", "rb") as f:
    health_label_encoder = pickle.load(f)

with open("ml/feature_columns.pkl", "rb") as f:
    feature_columns = pickle.load(f)

# Load suggestion model and tag binarizer
with open("ml/suggestion_model.pkl", "rb") as f:
    suggestion_model = pickle.load(f)

with open("ml/suggestion_binarizer.pkl", "rb") as f:
    suggestion_binarizer = pickle.load(f)

# Suggestion templates
TEMPLATES = {
    "temperature_low": "Temperature is too low. Move the plant to a warmer location.",
    "temperature_high": "Temperature is too high. Move the plant to a cooler location.",
    "humidity_low": "Humidity is too low. Increase misting or reduce airflow.",
    "humidity_high": "Humidity is too high. Improve ventilation or reduce misting.",
    "light_low": "Light is too low. Increase exposure.",
    "light_high": "Light is too high. Reduce direct sunlight.",
    "moisture_low": "Soil moisture is too low. Water the plant.",
    "moisture_high": "Soil moisture is too high. Improve drainage.",
    "all_optimal": "All vitals are within optimal range. No action needed."
}

def analyze_plant(sensor_input: dict) -> dict:
    # Prepare input vector
    X = np.array([[sensor_input[col] for col in feature_columns]])

    # Overall health prediction
    health_class = health_model.predict(X)[0]
    overall_status = health_label_encoder.inverse_transform([health_class])[0]

    # Suggestion prediction
    y_pred = suggestion_model.predict(X)
    tags = suggestion_binarizer.inverse_transform(y_pred)[0]

    # Convert tags to messages
    suggestions = [TEMPLATES[tag] for tag in tags if tag in TEMPLATES]

    return {
        "overall_status": overall_status,
        "suggestions": suggestions
    }