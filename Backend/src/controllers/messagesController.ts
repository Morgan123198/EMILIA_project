import { Request, Response } from "express";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Obtener todos los mensajes y sus respuestas
export const getMessages = async (req: Request, res: Response): Promise<void> => {
  try {
    const messages = await prisma.message.findMany({
      where: { parentId: null },
      include: { replies: { include: { replies: true } } },
    });
    res.json(messages);
  } catch (error) {
    res.status(500).json({ error: "Error al obtener mensajes" });
  }
};

// Crear un nuevo mensaje
export const createMessage = async (req: Request, res: Response): Promise<void> => {
  try {
    const { message, parentId, userId } = req.body;

    if (!message || !userId) {
      res.status(400).json({ error: "El mensaje y el userId son obligatorios" });
      return;
    }

    const newMessage = await prisma.message.create({
      data: {
        message,
        parentId: parentId || null,
        user: { connect: { id: userId } } // 🔥 Conectamos el mensaje con el usuario
      },
    });

    res.status(201).json(newMessage);
  } catch (error) {
    res.status(500).json({ error: "Error al crear mensaje" });
  }
};

