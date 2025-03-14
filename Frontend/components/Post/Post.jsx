import React, { useState } from "react";
import axios from "axios";
import Reply from "../Reply/Reply";
import "./Post.css";

const Post = ({ post, fetchPosts }) => {
  const [reply, setReply] = useState("");
  const [showReplies, setShowReplies] = useState(false);

  const handleReply = async () => {
    if (reply.trim() === "") return;
    await axios.post("http://localhost:3001/posts", { message: reply, parent_id: post.id });
    setReply("");
    fetchPosts();
  };

  return (
    <div className="post">
      <p><strong>User:</strong> {post.message}</p>
      <button onClick={() => setShowReplies(!showReplies)}>Respuestas</button>
      {showReplies && (
        <div className="reply-section">
          <textarea
            placeholder="Escribe una respuesta..."
            value={reply}
            onChange={(e) => setReply(e.target.value)}
          ></textarea>
          <button onClick={handleReply}>Responder</button>
          <div>
            {post.replies && post.replies.map((r) => <Reply key={r.id} reply={r} />)}
          </div>
        </div>
      )}
    </div>
  );
};

export default Post;
