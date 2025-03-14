import React, { useState, useEffect } from "react";
import axios from "axios";
import Post from "../Post/Post";
import "./Forum.css";

const Forum = () => {
  const [posts, setPosts] = useState([]);
  const [newMessage, setNewMessage] = useState("");

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    const res = await axios.get("http://localhost:5000/api/messages");
    setPosts(res.data);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newMessage.trim() === "") return;

    try {
      await axios.post("http://localhost:5000/api/messages", {
        message: newMessage,
        userId: 1  // Asegúrate de que el usuario existe en la BD
      });

      setNewMessage("");
      fetchPosts();
    } catch (error) {
      console.error("❌ Error en la solicitud:", error);
    }
  };


  return (
    <div className="forum-container">
      <h2>Foro Anónimo</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          placeholder="Escribe tu mensaje..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
        ></textarea>
        <button type="submit">Publicar</button>
      </form>
      <div>
        {posts
          .filter((post) => post.parent_id === null)
          .map((post) => (
            <Post key={post.id} post={post} fetchPosts={fetchPosts} />
          ))}
      </div>
    </div>
  );
};

export default Forum;
