import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Terminal, Lock, User as UserIcon, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import '../styles/auth.css';

const Login = () => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (!usernameOrEmail || !password) {
      setErrorMessage('Please fill in all fields');
      return;
    }

    const res = await login(usernameOrEmail, password);
    if (res.success) {
      navigate('/dashboard');
    } else {
      setErrorMessage(res.error);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-brand-logo">
            <Terminal size={26} />
          </div>
          <h2 className="auth-title">Welcome to Crawlix</h2>
          <p className="auth-subtitle">Distributed Web Scraping & Intelligence Platform</p>
        </div>

        {errorMessage && <div className="auth-error-alert">{errorMessage}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username or Email</label>
            <div className="input-with-icon">
              <UserIcon size={18} className="input-icon" />
              <input
                type="text"
                placeholder="developer or dev@crawlix.mesh"
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-with-icon">
              <Lock size={18} className="input-icon" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><span>Sign In</span> <ArrowRight size={18} /></>}
          </button>
        </form>

        <p className="auth-footer-prompt">
          Don't have an account?
          <Link to="/register">Register mesh access</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
