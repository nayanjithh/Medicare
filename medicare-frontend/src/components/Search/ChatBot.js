import React, { useState } from "react";
import "./ChatBot.css";

export default function RAGChat() {
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!inputMsg.trim()) return;

    // Add user's message
    setMessages((prev) => [...prev, { sender: "user", text: inputMsg }]);
    setInputMsg("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: inputMsg }),
      });

      const data = await response.json();

      // Add bot response
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.response || "No response received." },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Error: Could not get answer." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rag-container">
      <h1>🩺 Medicare RAG Chatbot</h1>

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={msg.sender === "user" ? "chat-user" : "chat-bot"}
            style={{ whiteSpace: "pre-wrap" }} // Preserve \n from backend
          >
            {msg.text}
          </div>
        ))}
        {loading && <div className="chat-bot" style={{ whiteSpace: "pre-wrap" }}>Loading...</div>}
      </div>

      <div className="chat-input">
        <input
          type="text"
          placeholder="Ask about patient records..."
          value={inputMsg}
          onChange={(e) => setInputMsg(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}
