import { BrowserRouter as Router, Routes, Route } from "react-router";
import Chat from "./components/ChatInterface";
import JournalTaskPage from "./components/JournalTaskPage";
import ProgressReport from "./components/ProgressReport";
import AuthPage from "./components/AuthPage";
function App() {
  return (
    <Router>
      <Routes>
        <Route path="chat" element={<Chat />} />
        <Route path="tasks" element={<JournalTaskPage />} />
<Route path="progress" element={<ProgressReport />}></Route>
<Route path="signup" element={<AuthPage />}></Route>

      </Routes>
    </Router>
  );
}

export default App;