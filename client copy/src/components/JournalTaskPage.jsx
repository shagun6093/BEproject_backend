// JournalTaskPage.js
import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import io from "socket.io-client";

const socket = io("http://localhost:8000");

export default function JournalTaskPage() {
  const location = useLocation();
  const { email, userName, task } = location.state || {};
  const [taskDescription, setTaskDescription] = useState(task || "");
  const [response, setResponse] = useState("");
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    if (email && !taskDescription) {
      fetch(`http://localhost:8000/api/task/${email}`)
        .then((res) => res.json())
        .then((data) => {
          setTaskDescription(data.task || "No task assigned or task not found.");
        })
        .catch((err) => console.error("Error fetching task:", err));
    }
  }, [email, taskDescription]);

  useEffect(() => {
    socket.on("task_feedback", (data) => {
      if (data.email === email) {
        setFeedback(data.feedback);
      }
    });
    return () => {
      socket.off("task_feedback");
    };
  }, [email]);

  const handleSubmit = () => {
    socket.emit("complete_task", { email, user_response: response });
  };

  return (
    <div className="journal-container">
      <div className="journal-card">
        <h2 className="journal-title">Journal Task</h2>
        <p className="journal-description">
          {taskDescription ||
            "Reflect on a recent thought or event that troubled you. Write down your response, and we’ll help you gain insight."}
        </p>
        <textarea
          className="journal-textarea"
          rows={4}
          placeholder="Write your response here..."
          value={response}
          onChange={(e) => setResponse(e.target.value)}
        />
        <button className="journal-button" onClick={handleSubmit}>
          Submit
        </button>
        {feedback && <div className="journal-feedback">{feedback}</div>}
      </div>
      <style>{`
        .journal-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background-color: #f3f4f6;
          padding: 20px;
        }
        .journal-card {
          background: #fff;
          padding: 24px;
          border-radius: 12px;
          max-width: 600px;
          width: 100%;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .journal-title {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 16px;
          text-align: center;
          color: #333;
        }
        .journal-description {
          font-size: 16px;
          color: #555;
          margin-bottom: 20px;
        }
        .journal-textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #ccc;
          border-radius: 8px;
          font-size: 16px;
          resize: none;
          outline: none;
          margin-bottom: 16px;
        }
        .journal-button {
          width: 100%;
          background-color: #007bff;
          color: #fff;
          padding: 12px;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }
        .journal-button:hover {
          background-color: #0056b3;
        }
        .journal-feedback {
          margin-top: 20px;
          padding: 12px;
          background-color: #eef2ff;
          border-left: 4px solid #007bff;
          border-radius: 8px;
          font-size: 16px;
          color: #333;
        }
      `}</style>
    </div>
  );
}
