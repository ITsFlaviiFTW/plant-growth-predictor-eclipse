import React from "react";

const SensorBubble: React.FC<{ label: string; value: string }> = ({ label, value }) => {
  return (
    <div className="bubble tooltip">
      <h3>{label}</h3>
      <p>{value}</p>
      <span className="tooltip-text">
        This feature will be added in the future. It will include average, target, lowest, and highest values where applicable.
      </span>
    </div>
  );
};

export default SensorBubble;
