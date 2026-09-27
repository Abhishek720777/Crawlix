import React from 'react';
import { PlusCircle, Activity, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../styles/navbar.css';

const Navbar = ({ title = "Dashboard" }) => {
  const navigate = useNavigate();

  return (
    <header className="navbar">
      <div className="navbar-title-container">
        <h1 className="navbar-page-title">{title}</h1>
        <div className="system-status-pill">
          <span className="status-dot"></span>
          <span>MESH READY</span>
        </div>
      </div>

      <div className="navbar-actions">
        <button className="btn-quick-new-job" onClick={() => navigate('/jobs?action=new')}>
          <PlusCircle size={16} />
          <span>New Crawl Job</span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;
