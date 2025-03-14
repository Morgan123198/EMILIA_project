import React from "react";
import "./Reply.css";

const Reply = ({ reply }) => (
  <div className="reply">
    <p><strong>User:</strong> {reply.message}</p>
  </div>
);

export default Reply;
