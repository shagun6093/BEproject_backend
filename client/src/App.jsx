import { BrowserRouter as Router, Routes, Route } from "react-router";
import Chat from "./pages/Chat";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="chat" element={<Chat />} />
      </Routes>
    </Router>
  );
}

export default App;
