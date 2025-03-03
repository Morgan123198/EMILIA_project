import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.css";
import LoginPopup from "../components/LoginPopup/LoginPopup";
import Dashboard from "../pages/Dashboard";
import EmotionCalendar from "../components/EmotionCalendar/EmotionCalendar"; // Importamos el calendario

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPopup />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/calendar" element={<EmotionCalendar />} /> {/* Nueva ruta */}
      </Routes>
    </Router>
  );
}

export default App;
