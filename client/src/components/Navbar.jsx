import { NavLink } from "react-router-dom";

export default function Navbar() {
  const tabs = [
    { name: "Chat", path: "/chat" },
    { name: "Tasks", path: "/tasks" },
    { name: "Games", path: "/games" },
    { name: "Profile", path: "/profile" },
  ];

  const containerStyle = {
    display: "flex",
    justifyContent: "space-evenly",
    background: "#fff",
    borderRadius: "50px",
    padding: "10px 20px",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
    marginBottom: "20px",
    width: "80%",
    maxWidth: "450px",
    margin: "20px auto",
  };

  const linkStyle = {
    padding: "10px 23px",
    borderRadius: "50px",
    textDecoration: "none",
    transition: "all 0.3s ease",
  };

  return (
    <div style={containerStyle}>
      {tabs.map((tab) => (
        <NavLink
          key={tab.name}
          to={tab.path}
          style={({ isActive }) => ({
            ...linkStyle,
            background: isActive ? "#007bff" : "#ccc",
            color: isActive ? "#fff" : "#000",
          })}
        >
          {tab.name}
        </NavLink>
      ))}
    </div>
  );
}
