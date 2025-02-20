import React, { useState, useEffect } from "react";
import io from "socket.io-client";
import Navbar from "./Navbar";

const socket = io("http://localhost:8000");

export default function Chat() {
  const [messages, setMessages] = useState([]); // Array of conversation pairs: { user, ai }
  const [input, setInput] = useState("");
  const [task, setTask] = useState("");
  const [userId, setUserId] = useState("");
  const [userName, setUserName] = useState("");

  useEffect(() => {
    // Prompt for user ID and name when the component mounts
    const uid = window.prompt("Please enter your user ID:");
    const uname = window.prompt("Please enter your user name:");
    setUserId(uid);
    setUserName(uname);

    socket.on("receive_message", (data) => {
      // data.conversation is assumed to be an array of conversation pairs
      setMessages(data.conversation);
      setTask(data.task || "");
    });

    socket.on("session_complete", (data) => {
      alert("Journal Report:\n" + data.report);
    });

    return () => {
      socket.off("receive_message");
      socket.off("session_complete");
    };
  }, []);

  const sendMessage = () => {
    if (input.trim() === "") return;
    // Emit the message along with user id and name
    socket.emit("send_message", {
      user_input: input,
      user_id: userId,
      user_name: userName,
    });
    setInput("");
  };

  const completeSession = () => {
    socket.emit("complete_session", { user_id: userId, user_name: userName });
  };

  return (
    <div
      style={{
        padding: "20px",
        fontFamily: "Arial, sans-serif",
        backgroundColor: "#f2f2f2",
        minHeight: "100vh",
      }}
    >
      <Navbar />
      <h2 style={{ textAlign: "center", margin: "20px 0" }}>Chat Interface</h2>
      <div
        style={{
          background: "#fff",
          padding: "20px",
          borderRadius: "5px",
          maxWidth: "500px",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          height: "70vh",
        }}
      >
        {/* Scrollable container for messages and task */}
        <div style={{ flex: 1, overflowY: "auto", marginBottom: "20px" }}>
          {messages.map((pair, index) => (
            <div
              key={index}
              style={{
                padding: "10px",
                marginBottom: "10px",
                border: "1px solid #ccc",
                borderRadius: "5px",
                backgroundColor: "#e2e3e5",
              }}
            >
              <div style={{ textAlign: "right", fontWeight: "bold" }}>
                User: {pair.user}
              </div>
              <div style={{ textAlign: "left", marginTop: "5px" }}>
                AI: {pair.ai}
              </div>
            </div>
          ))}
          {task && (
            <div
              style={{
                backgroundColor: "#cff4fc",
                padding: "10px",
                borderRadius: "5px",
                textAlign: "center",
                marginBottom: "10px",
              }}
            >
              Task: {task}
            </div>
          )}
        </div>
        {/* Input area */}
        <div style={{ display: "flex", marginBottom: "10px" }}>
          <input
            type="text"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{
              flex: "1",
              padding: "10px",
              border: "1px solid #ccc",
              borderRadius: "5px",
            }}
          />
          <button
            onClick={sendMessage}
            style={{
              marginLeft: "10px",
              padding: "10px 20px",
              border: "none",
              backgroundColor: "#007bff",
              color: "#fff",
              borderRadius: "5px",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </div>
        <button
          onClick={completeSession}
          style={{
            width: "100%",
            padding: "10px",
            border: "none",
            backgroundColor: "#dc3545",
            color: "#fff",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Complete Session
        </button>
      </div>
    </div>
  );
}
