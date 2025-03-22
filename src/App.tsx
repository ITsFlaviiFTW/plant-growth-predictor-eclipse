import React from "react";
import SensorBubble from "./components/SensorBubble";

const sensorData = {
  temperature: "22°C",
  humidity: "65%",
  soilMoisture: "30%",
  lightIntensity: "1200 lux",
  height: "15 cm",
  age: "3 months"
};

const App: React.FC = () => {
  return (
    <div className="h-screen w-screen flex flex-col items-center bg-cover bg-center relative" style={{ backgroundImage: `url('/background.jpg')` }}>
      
      {/* Fixed Title at the Top */}
      <div className="absolute top-4 w-full flex justify-center">
        <h1 className="text-4xl font-bold" style={{ color: "darkslategray" }}>
          🌱 Plant Monitoring Dashboard
        </h1>
      </div>

      {/* Wrapper to Keep Everything Centered */}
      <div className="flex flex-col justify-center items-center h-full mt-16">
        {/* Plant Image & Bubbles */}
        <div className="relative w-64 h-80 flex justify-center items-center">
          {/* Plant Image */}
          <img src="/sunflower.gif" alt="Plant" className="w-64 h-auto" />

          {/* Sensor Bubbles */}
          <div className="absolute top-[-150px] left-[-200px]">
            <SensorBubble label="Temperature" value={sensorData.temperature} />
          </div>
          <div className="absolute top-[-150px] right-[-250px]">
            <SensorBubble label="Humidity" value={sensorData.humidity} />
          </div>
          <div className="absolute bottom-[-150px] left-[-200px]">
            <SensorBubble label="Soil Moisture" value={sensorData.soilMoisture} />
          </div>
          <div className="absolute bottom-[-150px] right-[-250px]">
            <SensorBubble label="Light Intensity" value={sensorData.lightIntensity} />
          </div>
          <div className="absolute bottom-[-280px] left-[40%] translate-x-[-30%]">
            <SensorBubble label="Height" value={sensorData.height} />
          </div>
          <div className="absolute bottom-[350px] left-[40%] translate-x-[-30%]">
            <SensorBubble label="Age" value={sensorData.age} />
          </div>
        </div>
      </div>

    </div>
  );
};

export default App;
