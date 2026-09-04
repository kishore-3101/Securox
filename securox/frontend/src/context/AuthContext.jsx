import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('securox_token'));
  const [user, setUser] = useState({
    username: 'operator',
    full_name: 'Traffic Operations Lead',
    role: 'OPERATOR',
    risk_score: 10.0
  });
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  useEffect(() => {
    if (token) {
      fetch('http://localhost:8001/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => (res.ok ? res.json() : null))
        .then(data => {
          if (data) {
            setUser(data);
            setIsAuthenticated(true);
          }
        })
        .catch(() => {});
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      const res = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      
      localStorage.setItem('securox_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      setIsAuthenticated(true);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('securox_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext) || { user: null, token: null, isAuthenticated: false, login: async () => ({}), logout: () => {} };
