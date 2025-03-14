import express from "express";
import cors from "cors";
import authRoutes from "./routes/authRoutes";
import "dotenv/config";
import messagesRoutes from "./routes/messagesRoutes"
const app = express();

app.use(cors({ origin: "http://localhost:5173",
               credentials: true,
               methods: "GET,POST,PUT,DELETE",
               allowedHeaders: "Content-Type,Authorization",
 })); // 🔥 Permitir solicitudes de cualquier origen
app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/messages", messagesRoutes);

app.get("/", (req, res) => {
  res.send("✅ Servidor funcionando");
});
export default app;
