import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import NodeMesh from './pages/NodeMesh';
import Intelligence from './pages/Intelligence';
import DataExplorer from './pages/DataExplorer';
import './styles/global.css';

const ProtectedLayout = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-container">
      <Sidebar />
      {children}
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route
            path="/dashboard"
            element={
              <ProtectedLayout>
                <Dashboard />
              </ProtectedLayout>
            }
          />
          <Route
            path="/jobs"
            element={
              <ProtectedLayout>
                <Jobs />
              </ProtectedLayout>
            }
          />
          <Route
            path="/nodes"
            element={
              <ProtectedLayout>
                <NodeMesh />
              </ProtectedLayout>
            }
          />
          <Route
            path="/intelligence"
            element={
              <ProtectedLayout>
                <Intelligence />
              </ProtectedLayout>
            }
          />
          <Route
            path="/data"
            element={
              <ProtectedLayout>
                <DataExplorer />
              </ProtectedLayout>
            }
          />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
