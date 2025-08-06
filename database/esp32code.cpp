/*

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <BH1750.h>

// WiFi credentials
const char* ssid = "NordVPN7";
const char* password = "P0s31d0n,02";

// Jetson Nano API endpoint
const char* serverUrl = "http://10.0.0.212:8000/sensor/update";

// Sensor pins and config
#define DHTPIN 14
#define DHTTYPE DHT22
#define SOIL_PIN 36  // VP pin = GPIO 36

DHT dht(DHTPIN, DHTTYPE);
BH1750 bh1750;

void setup() {
    Serial.begin(115200);
    delay(1000);

    dht.begin();
    Wire.begin(25, 33); // SDA = 25, SCL = 33 for ESP32

    if (!bh1750.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
        Serial.println("❌ BH1750 failed to start.");
    }

    // Connect to WiFi
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ WiFi connected.");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    float lightLux = bh1750.readLightLevel();

    // Soil moisture: raw and mapped
    int rawSoil = analogRead(SOIL_PIN);
    int soilPercent = map(rawSoil, 2800, 2200, 0, 100);
    soilPercent = constrain(soilPercent, 0, 100);

    unsigned long timestamp = millis();

    // Debug print
    Serial.print("Raw soil: ");
    Serial.print(rawSoil);
    Serial.print(" -> ");
    Serial.print(soilPercent);
    Serial.println("%");

    // Construct JSON
    String json = "{";
    json += "\"esp_id\":\"esp32-1\",";
    json += "\"timestamp\":" + String(timestamp) + ",";
    json += "\"temperature\":" + String(temperature, 1) + ",";
    json += "\"humidity\":" + String(humidity, 1) + ",";
    json += "\"light_lux\":" + String(lightLux, 1) + ",";
    json += "\"soil_moisture\":" + String(soilPercent);
    json += "}";

    Serial.println("Sending: " + json);

    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/json");

        int httpCode = http.POST(json);

        if (httpCode > 0) {
            Serial.print("✅ Response code: ");
            Serial.println(httpCode);
        }
        else {
            Serial.print("❌ Failed to send! Code: ");
            Serial.println(httpCode);
        }

        http.end();
    }
    else {
        Serial.println("❌ WiFi not connected!");
    }

    delay(2000); // Wait 2 seconds
}
*/