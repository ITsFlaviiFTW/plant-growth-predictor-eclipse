import React from "react";

const appStyle: React.CSSProperties = {
  backgroundImage: `url('/background.jpg')`,
  backgroundSize: "cover",
  backgroundPosition: "center",
  height: "100vh",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  color: "white",
};

function App() {
  return (
    <div style={appStyle}>
      <h1>Welcome to My React</h1>
    </div>
  );
}

export default App;