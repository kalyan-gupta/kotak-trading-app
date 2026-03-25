import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useSnackbar } from 'notistack';
import apiService from '../services/apiService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [kotakSession, setKotakSession] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      apiService.setAuthToken(token);
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await apiService.get('/auth/profile/');
      if (response.data.success) {
        setUser(response.data.user);
        setProfile(response.data.profile);
        setIsAuthenticated(true);
        
        // Check Kotak session status
        checkKotakSession();
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const checkKotakSession = async () => {
    try {
      const response = await apiService.get('/auth/kotak/session-status/');
      if (response.data.success) {
        setKotakSession(response.data.data);
      }
    } catch (error) {
      console.error('Failed to check Kotak session:', error);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await apiService.post('/auth/login/', {
        username,
        password
      });

      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        apiService.setAuthToken(response.data.token);
        setUser(response.data.user);
        setIsAuthenticated(true);
        enqueueSnackbar('Login successful!', { variant: 'success' });
        return { success: true };
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Login failed';
      enqueueSnackbar(message, { variant: 'error' });
      return { success: false, message };
    }
  };

  const register = async (userData) => {
    try {
      const response = await apiService.post('/auth/register/', userData);
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        apiService.setAuthToken(response.data.token);
        setUser(response.data.user);
        setIsAuthenticated(true);
        enqueueSnackbar('Registration successful!', { variant: 'success' });
        return { success: true };
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Registration failed';
      enqueueSnackbar(message, { variant: 'error' });
      return { success: false, message };
    }
  };

  const logout = useCallback(async () => {
    try {
      await apiService.post('/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      apiService.setAuthToken(null);
      setUser(null);
      setProfile(null);
      setIsAuthenticated(false);
      setKotakSession(null);
      enqueueSnackbar('Logged out successfully', { variant: 'info' });
    }
  }, [enqueueSnackbar]);

  const kotakLogin = async (credentials) => {
    try {
      const response = await apiService.post('/auth/kotak/login/', credentials);
      
      if (response.data.success) {
        enqueueSnackbar(response.data.message, { variant: 'success' });
        return { success: true, step: response.data.step };
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Kotak login failed';
      enqueueSnackbar(message, { variant: 'error' });
      return { success: false, message };
    }
  };

  const verifyTOTP = async (otp) => {
    try {
      const response = await apiService.post('/auth/kotak/verify-totp/', { otp });
      
      if (response.data.success) {
        setUser(prev => ({ ...prev, is_kotak_linked: true }));
        setKotakSession({
          session_status: response.data.session_status,
          token_expiry: response.data.token_expiry
        });
        enqueueSnackbar('Kotak login successful!', { variant: 'success' });
        return { success: true };
      }
    } catch (error) {
      const message = error.response?.data?.message || 'TOTP verification failed';
      enqueueSnackbar(message, { variant: 'error' });
      return { success: false, message };
    }
  };

  const kotakLogout = async () => {
    try {
      await apiService.post('/auth/kotak/logout/');
      setUser(prev => ({ ...prev, is_kotak_linked: false }));
      setKotakSession(null);
      enqueueSnackbar('Logged out from Kotak', { variant: 'info' });
    } catch (error) {
      enqueueSnackbar('Failed to logout from Kotak', { variant: 'error' });
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await apiService.put('/auth/profile/update/', profileData);
      if (response.data.success) {
        setProfile(response.data.profile);
        enqueueSnackbar('Profile updated successfully!', { variant: 'success' });
        return { success: true };
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Failed to update profile';
      enqueueSnackbar(message, { variant: 'error' });
      return { success: false, message };
    }
  };

  const value = {
    user,
    profile,
    isAuthenticated,
    loading,
    kotakSession,
    login,
    register,
    logout,
    kotakLogin,
    verifyTOTP,
    kotakLogout,
    updateProfile,
    fetchUserProfile,
    checkKotakSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
