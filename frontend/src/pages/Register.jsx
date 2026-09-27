import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Terminal, Mail, Lock, User as UserIcon, ShieldCheck, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import '../styles/auth.css';

const Register = () => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const { register, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long');
      return;
    }

    const res = await register(email, username, password, confirmPassword);
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
          <h2 className="auth-title">Register Mesh Account</h2>
          <p className="auth-subtitle">Initialize your distributed scraping cluster</p>
        </div>

        {errorMessage && <div className="auth-error-alert">{errorMessage}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Address</label>
            <div className="input-with-icon">
              <Mail size={18} className="input-icon" />
              <input
                type="email"
                placeholder="dev@crawlix.mesh"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Username</label>
            <div className="input-with-icon">
              <UserIcon size={18} className="input-icon" />
              <input
                type="text"
                placeholder="mesh_operator"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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

          <div className="form-group">
            <label>Confirm Password</label>
            <div className="input-with-icon">
              <ShieldCheck size={18} className="input-icon" />
              <input
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><span>Create Mesh Account</span> <ArrowRight size={18} /></>}
          </button>
        </form>

        <p className="auth-footer-prompt">
          Already have an account?
          <Link to="/login">Sign in here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
