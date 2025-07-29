import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import pickle

# Load processed dataset
df = pd.read_csv("ml/plant_health_data_processed.csv")

# Encode class labels
label_encoder = LabelEncoder()
df["health_label"] = label_encoder.fit_transform(df["health_status"])

# One-hot encode binned features
X = pd.get_dummies(df[["temp_bin", "humidity_bin", "moisture_bin", "light_bin"]])
y = df["health_label"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# XGBoost model
model = XGBClassifier(use_label_encoder=False, eval_metric="mlogloss", random_state=42)
model.fit(X_train, y_train)

# Report
print(classification_report(y_test, model.predict(X_test), target_names=label_encoder.classes_))

# Save model + encoder
with open("ml/health_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("ml/label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

with open("ml/feature_columns.pkl", "wb") as f:
    pickle.dump(list(X.columns), f)
