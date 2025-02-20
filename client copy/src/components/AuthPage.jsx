// AuthPage.js
import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export default function AuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [fullName, setFullName] = useState("");
  const [dob, setDob] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Regex for password validation
  const validatePassword = (password) => {
    return /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%?&])[A-Za-z\d@$!%*?&]{8,}$/.test(password);
  };

  const handleSignUpSubmit = async (e) => {
    e.preventDefault();
    if (!validatePassword(password)) {
      setError(
        "Password must contain at least one capital letter, one number, one special character, and be at least 8 characters long."
      );
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullName,
          email,
          password,
          dob,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        alert("Sign-up successful. Please login.");
        setIsSignUp(false);
      } else {
        setError(data.error || "Sign-up failed.");
      }
    } catch (err) {
      console.error("Signup error:", err);
      setError("An error occurred during signup.");
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        // Navigate to chat with email and userName
        navigate("/chat", { state: { email, userName: data.userName } });
      } else {
        setError(data.error || "Login failed.");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("An error occurred during login.");
    }
  };

  return (
    <div className="auth-container">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="auth-card"
      >
        <h2 className="auth-title">
          {isSignUp ? "Create an Account" : "Welcome Back"}
        </h2>
        <form
          className="auth-form"
          onSubmit={isSignUp ? handleSignUpSubmit : handleLoginSubmit}
        >
          {isSignUp && (
            <>
              <input
                type="text"
                placeholder="Full Name"
                className="auth-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
              <input
                type="date"
                placeholder="Date of Birth"
                className="auth-input"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
              />
            </>
          )}
          <input
            type="email"
            placeholder="Email Address"
            className="auth-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            className={`auth-input ${error ? "input-error" : ""}`}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {isSignUp && (
            <input
              type="password"
              placeholder="Confirm Password"
              className={`auth-input ${
                password !== confirmPassword && confirmPassword ? "input-error" : ""
              }`}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          )}
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="auth-button">
            {isSignUp ? "Sign Up" : "Login"}
          </button>
        </form>
        <div className="auth-toggle">
          <p className="toggle-text">
            {isSignUp
              ? "Already have an account?"
              : "Don't have an account?"}{" "}
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="toggle-button"
            >
              {isSignUp ? "Login" : "Sign Up"}
            </button>
          </p>
        </div>
      </motion.div>
      <style>{`
        .auth-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background-color: #f3f4f6;
          padding: 20px;
        }
        .auth-card {
          background-color: #fff;
          padding: 32px;
          border-radius: 16px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          width: 100%;
          max-width: 400px;
          animation: fadeIn 0.5s ease;
        }
        .auth-title {
          font-size: 24px;
          font-weight: 600;
          text-align: center;
          margin-bottom: 24px;
          color: #333;
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .auth-input {
          padding: 12px;
          border: 1px solid #ccc;
          border-radius: 8px;
          font-size: 16px;
          width: 100%;
        }
        .input-error {
          border-color: red;
        }
        .error-text {
          color: red;
          font-size: 14px;
          margin: 0;
        }
        .auth-button {
          background-color: #007bff;
          color: #fff;
          padding: 12px;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }
        .auth-button:hover {
          background-color: #0056b3;
        }
        .auth-toggle {
          text-align: center;
          margin-top: 16px;
        }
        .toggle-text {
          font-size: 14px;
          color: #555;
        }
        .toggle-button {
          background: none;
          border: none;
          color: #007bff;
          font-weight: 600;
          cursor: pointer;
          padding: 0;
          margin-left: 4px;
        }
        @media (max-width: 480px) {
          .auth-card {
            padding: 24px;
            max-width: 90%;
          }
          .auth-title {
            font-size: 20px;
          }
          .auth-input {
            font-size: 14px;
            padding: 10px;
          }
          .auth-button {
            font-size: 14px;
            padding: 10px;
          }
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
