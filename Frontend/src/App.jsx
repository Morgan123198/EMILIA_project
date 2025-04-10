import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.css";
import LoginPopup from "../components/LoginPopup/LoginPopup";
import Dashboard from "../pages/Dashboard";
import ProtectedRoute from "../components/ProtectedRoute";
import Survey from "../pages/Survey";
import EmotionCalendar from "../pages/EmotionCalendar";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPopup />} />
        {/* 🔹 ENVUELVE DASHBOARD CON PROTECTEDROUTE */}
        <Route
          path="/dashboard/*"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/survey"
          element={
            <ProtectedRoute>
              <Survey />
            </ProtectedRoute>
          }
        />
        <Route path="/calendar" element={<EmotionCalendar />} />
      </Routes>
    </Router>
  );
}

export default App;
