# React + TypeScript + Vite

# 🌱 Plant Growth Predictor

An educational and interactive web app that visualizes real-time plant sensor data like temperature, humidity, soil moisture, light intensity, height, and age. Designed for students, hobbyists, and indoor plant growers to better understand and monitor plant health.

---

## 📸 Preview

![Dashboard Preview](public/sunflower.gif)

---

## 📁 Project Structure

plant-growth-predictor-eclipse/ │ ├── backend/ # Python FastAPI backend │ └── app/ │ ├── routes/ # API routes │ └── init.py # App initialization │ ├── frontend/ # React frontend (Vite + Tailwind CSS) │ ├── public/ # Static files (images, etc.) │ ├── src/ │ │ ├── components/ # Reusable React components │ │ ├── App.tsx # Main React component │ │ ├── index.css # Tailwind & global styles │ │ └── App.css │ ├── tailwind.config.js # Tailwind configuration │ └── vite.config.ts # Vite config │ ├── .gitignore ├── package.json └── README.md


---

## 🚀 Features

- 🌡️ Displays live temperature, humidity, soil moisture, light intensity
- 🌿 Animated plant visual (currently a sunflower gif)
- 💬 Tooltips on hover (coming soon)
- 🎨 Smooth UI with TailwindCSS
- ⚙️ Backend API (FastAPI) for future sensor integration

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/itsflaviiftw/plant-growth-predictor-eclipse.git
cd plant-growth-predictor-eclipse

2. Frontend Setup (React + Tailwind + Vite)
cd frontend
npm install
npm run dev

Open http://localhost:5173 in your browser.

⚠️ Make sure Tailwind is installed and configured properly.


cd backend
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
uvicorn app.routes.main:app --reload



🔧 Technologies Used
Frontend: React, Vite, Tailwind CSS

Backend: FastAPI (Python)

Design: HTML, CSS, responsive layout

Deployment: Local dev for now (Docker/cloud support coming soon)


📦 Dependencies
Frontend
React

Vite

Tailwind CSS

Backend
FastAPI

Uvicorn



🌟 Planned Features
✅ Basic dashboard UI

✅ Hover effect on sensor bubbles

🚧 Tooltips showing average, target, min/max (in progress)

🚧 Real-time sensor data from Arduino/IoT device

🚧 Login/authentication

🚧 Light/dark mode toggle



🧑‍💻 Contributors
Flavius — Full Stack / Backend

Nico — Frontend / UI

Lance — UI/Documentation

Kenneth — Database / Arduino

Team Eclipse — Capstone Team @ [Conestoga]