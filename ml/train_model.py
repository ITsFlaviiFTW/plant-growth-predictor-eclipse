# ml/train_model.py

import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Load and inspect
df = pd.read_csv("ml/augmented_health_data.csv")
print("Raw columns:", df.columns.tolist())

# Standardize format
df.columns = df.columns.str.strip().str.lower()

print("Final columns:", df.columns.tolist())

# Filter bad data
df = df.dropna()
df = df[
    (df["temperature"] > -10) & (df["temperature"] < 60) &
    (df["humidity"] >= 0) & (df["humidity"] <= 100) &
    (df["light_lux"] >= 0) &
    (df["soil_moisture"] >= 0) & (df["soil_moisture"] <= 100)
]

# Label encoding
label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df["label"])

# Features and target
features = ["temperature", "humidity", "light_lux", "soil_moisture"]
X = df[features]
y = df["label"]

# Train/test split (optional)
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

# Model training
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Save model, encoder, and feature list
with open("ml/health_model.pkl", "wb") as f:
    pickle.dump(clf, f)

with open("ml/label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

with open("ml/feature_columns.pkl", "wb") as f:
    pickle.dump(features, f)

print("Model training complete.")
print("Training size:", len(X_train))
print("Class distribution:", df["label"].value_counts())
print("Feature importances:", clf.feature_importances_)
print("Train Accuracy:", clf.score(X_train, y_train))
print("Test Accuracy:", clf.score(X_test, y_test))
