import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UniversitySelectionPage from './pages/UniversitySelectionPage';
import ChatPage from './pages/ChatPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen w-full bg-background text-text selection:bg-primary/20">
        <Routes>
          <Route path="/" element={<UniversitySelectionPage />} />
          <Route path="/chat/:universityId" element={<ChatPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
