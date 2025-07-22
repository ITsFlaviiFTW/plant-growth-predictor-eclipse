import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import pickle

plant_df = pd.read_csv("ml/plant_health_data.csv")

plant_df = plant_df.rename(columns={
    "Soil_Moisture": "soil_moisture",
    "Ambient_Temperature": "temperature",
    "Humidity": "humidity",
    "Light_Intensity": "light_lux",
    "Plant_Health_Status": "health_status"
})

label_encoder = LabelEncoder()
plant_df["health_label"] = label_encoder.fit_transform(plant_df["health_status"])

X = plant_df[["soil_moisture", "temperature", "humidity", "light_lux"]]
y = plant_df["health_label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test), target_names=label_encoder.classes_))

with open("ml/health_model.pkl", "wb") as f:
    pickle.dump(model, f)
with open("ml/label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)
