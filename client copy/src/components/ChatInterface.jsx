// Chat.js
import React, { useState, useEffect } from "react";
import io from "socket.io-client";
import { useNavigate, useLocation } from "react-router-dom";

const socket = io("http://localhost:8000");

export default function Chat() {
  const [messages, setMessages] = useState([]); // Array of conversation pairs {user, ai}
  const [input, setInput] = useState("");
  const [task, setTask] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  // Retrieve email and userName from login state
  const { email, userName } = location.state || {};

  // Fetch conversation history on mount if email is available
  useEffect(() => {
    if (!email) return;
    fetch(`http://localhost:8000/api/conversation/${email}`)
      .then((res) => res.json())
      .then((data) => {
        setMessages(data.conversation || []);
        setTask(data.task || "");
      })
      .catch((err) => console.error("Error fetching conversation:", err));
  }, [email]);

  useEffect(() => {
    socket.on("receive_message", (data) => {
      if (data.email === email) {
        setMessages(data.conversation || []);
        setTask(data.task || "");
      }
    });
    socket.on("session_complete", (data) => {
      alert("Journal Report:\n" + data.report);
    });
    return () => {
      socket.off("receive_message");
      socket.off("session_complete");
    };
  }, [email]);

  const sendMessage = () => {
    if (input.trim() === "") return;
    socket.emit("send_message", { user_input: input, email, user_name: userName });
    setInput("");
  };

  const completeSession = () => {
    socket.emit("complete_session", { email, user_name: userName });
  };

  // Navigate to journaling page when the task banner button is clicked
  const handleCompleteTask = () => {
    navigate("/tasks", { state: { email, userName, task } });
  };

  return (
    <div className="chat-container">
      <div className="chat-card">
        <h2 className="chat-title">Chat Interface</h2>
        <div className="chat-messages">
          {messages.map((pair, index) => (
            <div key={index} className="message-pair">
              <div className="message user-message">{pair.user}</div>
              <div className="message ai-message">
                <span className="bot-icon">🤖</span> {pair.ai}
              </div>
            </div>
          ))}
          {task && (
            <div className="task-banner">
              <strong>Kindly complete this task . . . . .   </strong>
              <button onClick={handleCompleteTask}>Complete Your Task</button>
            </div>
          )}
        </div>
        <div className="chat-input-area">
          <input
            type="text"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
        <button className="session-button" onClick={completeSession}>
          Complete Session
        </button>
      </div>
      <style>{`
        .chat-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background-color: #f2f2f2;
          padding: 20px;
        }
        .chat-card {
          background: #fff;
          padding: 20px;
          border-radius: 8px;
          width: 100%;
          max-width: 600px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .chat-title {
          text-align: center;
          margin-bottom: 20px;
          font-size: 22px;
          color: #333;
        }
        .chat-messages {
          max-height: 300px;
          overflow-y: auto;
          margin-bottom: 20px;
        }
        .message-pair {
          margin-bottom: 15px;
        }
        .message {
          padding: 8px 12px;
          border-radius: 8px;
          margin: 4px 0;
          max-width: 80%;
        }
        .user-message {
          background: #ffe5d1;
          text-align: right;
          margin-left: auto;
        }
        .ai-message {
          background: #d4edda;
          text-align: left;
          display: flex;
          align-items: center;
        }
        .bot-icon {
          margin-right: 6px;
          font-size: 20px;
        }
        .task-banner {
          background: #cff4fc;
          padding: 10px;
          text-align: center;
          border-radius: 8px;
          margin-bottom: 10px;
        }
        .task-banner button {
          margin-top: 8px;
          padding: 6px 12px;
          border: none;
          background: #007bff;
          color: #fff;
          border-radius: 4px;
          cursor: pointer;
        }
        .chat-input-area {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
        }
        .chat-input-area input {
          flex: 1;
          padding: 10px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }
        .chat-input-area button {
          padding: 10px 20px;
          border: none;
          background: #007bff;
          color: #fff;
          border-radius: 4px;
          cursor: pointer;
        }
        .session-button {
          width: 100%;
          padding: 10px;
          border: none;
          background: #dc3545;
          color: #fff;
          border-radius: 4px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}
