import { useState } from "react";
import { motion } from "framer-motion";
import "./EmotionCalendar.css"; // Importamos el CSS separado

const emotions = [
  { name: "Feliz", color: "happy" },
  { name: "Triste", color: "sad" },
  { name: "Furia", color: "angry" },
  { name: "Miedo", color: "fear" },
  { name: "Estrés", color: "stress" },
];

function Calendar({ entries, onDayClick }) {
  return (
    <div className="calendar">
      {[...Array(30)].map((_, i) => (
        <motion.div
          key={i}
          className={`day ${entries[i] ? emotions.find(e => e.name === entries[i].emotion)?.color : "default"}`}
          onClick={() => onDayClick(i)}
          whileHover={{ scale: 1.1 }}
        >
          {i + 1}
        </motion.div>
      ))}
    </div>
  );
}

function EmotionModal({ selectedDay, emotion, intensity, setEmotion, setIntensity, saveEmotion, close }) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Día {selectedDay + 1}</h2>
        <select value={emotion} onChange={(e) => setEmotion(e.target.value)}>
          <option value="">Selecciona una emoción</option>
          {emotions.map((e) => (
            <option key={e.name} value={e.name}>{e.name}</option>
          ))}
        </select>
        <div className="intensity">
          Intensidad:
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => setIntensity(n)} className={n <= intensity ? "active-star" : "star"}>
              {n <= intensity ? "⭐" : "☆"}
            </button>
          ))}
        </div>
        <div className="buttons">
          <button onClick={saveEmotion} className="save">Guardar</button>
          <button onClick={close} className="close">Cerrar</button>
        </div>
      </div>
    </div>
  );
}

function Dashboard({ entries }) {
  const emotionCounts = emotions.reduce((acc, e) => ({ ...acc, [e.name]: 0 }), {});
  const intensityCounts = [0, 0, 0, 0, 0];

  Object.values(entries).forEach(({ emotion, intensity }) => {
    emotionCounts[emotion]++;
    intensityCounts[intensity - 1]++;
  });

  return (
    <div className="dashboard">
      <h2>Estadísticas</h2>
      <div className="stats">
        {emotions.map((e) => (
          <p key={e.name} className={e.color}>{e.name}: {emotionCounts[e.name]}</p>
        ))}
      </div>
      <h3>Distribución de Intensidad</h3>
      <p>⭐ {intensityCounts[0]} ⭐⭐ {intensityCounts[1]} ⭐⭐⭐ {intensityCounts[2]} ⭐⭐⭐⭐ {intensityCounts[3]} ⭐⭐⭐⭐⭐ {intensityCounts[4]}</p>
    </div>
  );
}

export default function EmotionCalendar() {
  const [entries, setEntries] = useState({});
  const [selectedDay, setSelectedDay] = useState(null);
  const [emotion, setEmotion] = useState("");
  const [intensity, setIntensity] = useState(3);

  const handleDayClick = (day) => {
    setSelectedDay(day);
    if (entries[day]) {
      setEmotion(entries[day].emotion);
      setIntensity(entries[day].intensity);
    } else {
      setEmotion("");
      setIntensity(3);
    }
  };

  const saveEmotion = () => {
    if (emotion) {
      setEntries({ ...entries, [selectedDay]: { emotion, intensity } });
      setSelectedDay(null);
    }
  };

  return (
    <div className="container">
      <h1>Calendario de Emociones</h1>
      <Calendar entries={entries} onDayClick={handleDayClick} />
      {selectedDay !== null && (
        <EmotionModal
          selectedDay={selectedDay}
          emotion={emotion}
          intensity={intensity}
          setEmotion={setEmotion}
          setIntensity={setIntensity}
          saveEmotion={saveEmotion}
          close={() => setSelectedDay(null)}
        />
      )}
      <Dashboard entries={entries} />
    </div>
  );
}
