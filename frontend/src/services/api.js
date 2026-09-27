import axios from 'axios';

// Use relative /api/v1 path in production/docker so Nginx proxies it seamlessly without CORS,
// or fallback to localhost:8000/api/v1 when running Vite dev server locally.
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.port === '5173' ? 'http://localhost:8000/api/v1' : '/api/v1');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('crawlix_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401 unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('crawlix_token');
      localStorage.removeItem('crawlix_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
