import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SetupPage from './pages/SetupPage';
import ViewPage from './pages/ViewPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Routes>
          <Route path="/" element={<Navigate to="/setup" replace />} />
          <Route path="/setup" element={<SetupPage />} />
          <Route path="/view" element={<ViewPage />} />
          <Route path="/view/:weekId" element={<ViewPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
