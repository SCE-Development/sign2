import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AnnouncementDashboard from './pages/Annoucement-Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/announcement" element={<AnnouncementDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
