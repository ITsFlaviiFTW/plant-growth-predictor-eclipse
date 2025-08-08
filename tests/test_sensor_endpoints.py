import json
from dateutil.parser import parse


def test_update_sensor_data_success(client):
    payload = {
        "esp_id": "TEST123",
        "temperature": 23.4,
        "humidity": 50.1,
        "light_lux": 300.0,
        "soil_moisture": 45
    }
    response = client.post("/sensor/update", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_predict_health_no_data(client):
    response = client.get("/predict/NONE_PRESENT")
    assert response.status_code == 200
    assert response.json()["error"] == "No data found for ESP ID."

def test_predict_health_with_data(client):
    payload = {
        "esp_id": "TEST456",
        "temperature": 21.0,
        "humidity": 40.0,
        "light_lux": 500.0,
        "soil_moisture": 60
    }
    client.post("/sensor/update", json=payload)
    response = client.get("/predict/TEST456")
    body = response.json()
    assert response.status_code == 200
    assert body["esp_id"] == "TEST456"
    assert "predicted_health" in body
    assert parse(body["timestamp"])

def test_dashboard_no_data(client):
    response = client.get("/?esp_id=DOES_NOT_EXIST")
    assert response.status_code == 200
    assert "<h2>No data for DOES_NOT_EXIST</h2>" in response.text

def test_dashboard_with_data(client):
    payload = {
        "esp_id": "DASH123",
        "temperature": 22.2,
        "humidity": 55.5,
        "light_lux": 400.0,
        "soil_moisture": 50
    }
    client.post("/sensor/update", json=payload)
    response = client.get("/?esp_id=DASH123")
    html = response.text
    assert response.status_code == 200
    assert "Eclipse Dashboard" in html
    assert "DASH123" in html
    assert "22.2" in html
    assert "55.5" in html
