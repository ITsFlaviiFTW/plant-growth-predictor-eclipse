import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier

# Load the dataset
df = pd.read_csv("ml/augmented_health_data.csv")

# Extract tags from response text
def extract_tags(text):
    tags = []
    if "Temperature is too low" in text: tags.append("temperature_low")
    if "Temperature is too high" in text: tags.append("temperature_high")
    if "Humidity is too low" in text: tags.append("humidity_low")
    if "Humidity is too high" in text: tags.append("humidity_high")
    if "Light is too low" in text: tags.append("light_low")
    if "Light is too high" in text: tags.append("light_high")
    if "Soil moisture is too low" in text: tags.append("moisture_low")
    if "Soil moisture is too high" in text: tags.append("moisture_high")
    if not tags:
        tags.append("all_optimal")
    return tags

df["tags"] = df["response"].apply(extract_tags)

# Features and target
X = df[["temperature", "humidity", "light_lux", "soil_moisture"]]
y = df["tags"]

# Binarize the tags
binarizer = MultiLabelBinarizer()
Y = binarizer.fit_transform(y)

# Train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# Train model
model = OneVsRestClassifier(LogisticRegression(max_iter=1000))
model.fit(X_train, Y_train)

# Save model and binarizer
with open("ml/suggestion_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("ml/suggestion_binarizer.pkl", "wb") as f:
    pickle.dump(binarizer, f)

print("Suggestion model training complete.")
print("Train accuracy:", model.score(X_train, Y_train))
print("Test accuracy:", model.score(X_test, Y_test))
