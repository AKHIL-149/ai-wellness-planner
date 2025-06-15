// frontend/src/hooks/useAuth.js

import { useState, useEffect, useCallback, useContext, createContext } from 'react';
import authService from '../services/authService';

// Auth Context
const AuthContext = createContext(null);

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth service
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const isAuthenticated = await authService.initialize();
        if (isAuthenticated) {
          setUser(authService.getUser());
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setError('Failed to initialize authentication');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Subscribe to auth changes
    const unsubscribe = authService.subscribe((event, data) => {
      switch (event) {
        case 'loginSuccess':
        case 'registerSuccess':
        case 'userChanged':
          setUser(data);
          setError(null);
          break;
        case 'logout':
        case 'tokenExpired':
          setUser(null);
          setError(null);
          break;
        case 'loginError':
        case 'registerError':
          setError(data);
          break;
        default:
          break;
      }
    });

    return unsubscribe;
  }, []);

  const login = useCallback(async (credentials) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await authService.login(credentials);
      if (result.success) {
        setUser(result.user);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await authService.register(userData);
      if (result.success && result.user) {
        setUser(result.user);
      } else if (result.success) {
        // Registration successful but may need verification
        setError(null);
      } else {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProfile = useCallback(async (updates) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await authService.updateProfile(updates);
      if (result.success) {
        setUser(result.user);
      } else {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateProfile,
    setError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth;