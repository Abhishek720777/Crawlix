import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Layers, 
  Network, 
  BrainCircuit, 
  Database, 
  Settings as SettingsIcon, 
  LogOut, 
  Terminal 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import '../styles/sidebar.css';

const Sidebar = () => {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">
          <Terminal size={22} />
        </div>
        <span className="logo-text">Crawlix</span>
        <span className="sidebar-badge">v1.0</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/jobs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Layers size={18} />
          <span>Crawl Pipelines</span>
        </NavLink>

        <NavLink to="/nodes" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Network size={18} />
          <span>Worker Mesh</span>
        </NavLink>

        <NavLink to="/intelligence" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <BrainCircuit size={18} />
          <span>Intelligence Hub</span>
        </NavLink>

        <NavLink to="/data" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Database size={18} />
          <span>Data Explorer</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            {user?.username ? user.username.substring(0, 2).toUpperCase() : 'CX'}
          </div>
          <div className="user-info">
            <span className="user-name">{user?.username || 'Dev Operator'}</span>
            <span className="user-role">{user?.email || 'admin@crawlix.mesh'}</span>
          </div>
        </div>

        <button className="btn-logout" onClick={logout}>
          <LogOut size={16} />
          <span>Disconnect</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
