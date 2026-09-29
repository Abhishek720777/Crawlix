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
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" fill="currentColor" />
            <path d="M12 9V3M12 15v6M9 12H3M15 12h6M9.9 9.9 5.6 5.6M14.1 14.1l4.3 4.3M14.1 9.9l4.3-4.3M9.9 14.1l-4.3 4.3" />
          </svg>
        </div>
        <span className="logo-text">Crawlix</span>
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
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
