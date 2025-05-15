// This is a copy of the code used in the ESP32 microcontroller

/*

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <BH1750.h>
#include <Adafruit_VL53L0X.h>

// === PIN DEFINITIONS ===
#define DHTPIN 14
#define DHTTYPE DHT22
#define SOIL_PIN 27  // Analog pin for EK1940
#define SDA_PIN 25
#define SCL_PIN 33

// === SENSOR OBJECTS ===
DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

void setup() {
    Serial.begin(115200);

    // Setup I2C
    Wire.begin(SDA_PIN, SCL_PIN);

    // Init sensors
    dht.begin();

    if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
        Serial.println("BH1750 not detected. Check wiring.");
    }

    if (!lox.begin()) {
        Serial.println("VL53L0X not detected. Check wiring.");
    }
}

void loop() {
    // === DHT22 ===
    float temp = dht.readTemperature();
    float humid = dht.readHumidity();
    if (isnan(temp) || isnan(humid)) {
        Serial.println("Failed to read from DHT22");
    }
    else {
        Serial.print("Temp: "); Serial.print(temp); Serial.print(" °C, ");
        Serial.print("Humidity: "); Serial.print(humid); Serial.println(" %");
    }

    // === BH1750 ===
    float lux = lightMeter.readLightLevel();
    Serial.print("Light: "); Serial.print(lux); Serial.println(" lux");

    // === VL53L0X ===
    VL53L0X_RangingMeasurementData_t measure;
    lox.rangingTest(&measure, false);  // pass in 'true' to get debug data
    if (measure.RangeStatus != 4) {
        Serial.print("Distance: "); Serial.print(measure.RangeMilliMeter); Serial.println(" mm");
    }
    else {
        Serial.println("Out of range");
    }

    // === Soil Moisture ===
    int moisture = analogRead(SOIL_PIN);
    Serial.print("Soil Moisture (raw ADC): "); Serial.println(moisture);

    Serial.println("--------------------------------------------------");
    delay(2000);  // Wait 2 seconds between reads
}

*/