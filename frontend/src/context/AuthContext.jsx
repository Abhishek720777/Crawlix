import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('crawlix_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('crawlix_token'));
  const [loading, setLoading] = useState(false);

  const login = async (username_or_email, password) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { username_or_email, password });
      const { access_token, user: userData } = response.data;
      localStorage.setItem('crawlix_token', access_token);
      localStorage.setItem('crawlix_user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed. Please check credentials.'
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, username, password, confirm_password) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/register', {
        email,
        username,
        password,
        confirm_password
      });
      const { access_token, user: userData } = response.data;
      localStorage.setItem('crawlix_token', access_token);
      localStorage.setItem('crawlix_user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed. Please try again.'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('crawlix_token');
    localStorage.removeItem('crawlix_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
