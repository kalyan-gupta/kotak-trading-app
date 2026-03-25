import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Toolbar } from '@mui/material';
import { useAuth } from './contexts/AuthContext';

// Layouts
import MainLayout from './components/Layout/MainLayout';

// Pages
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import OrderPlacement from './pages/Trading/OrderPlacement';
import OrderBook from './pages/Trading/OrderBook';
import Positions from './pages/Trading/Positions';
import Holdings from './pages/Portfolio/Holdings';
import Funds from './pages/Portfolio/Funds';
import MarketWatch from './pages/Market/MarketWatch';
import ScripSearch from './pages/Market/ScripSearch';
import Watchlists from './pages/Market/Watchlists';
import Profile from './pages/Profile/Profile';
import Settings from './pages/Settings/Settings';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Toolbar /> {/* Spacer for AppBar */}
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  
                  {/* Trading Routes */}
                  <Route path="/trading/order" element={<OrderPlacement />} />
                  <Route path="/trading/order-book" element={<OrderBook />} />
                  <Route path="/trading/positions" element={<Positions />} />
                  
                  {/* Portfolio Routes */}
                  <Route path="/portfolio/holdings" element={<Holdings />} />
                  <Route path="/portfolio/funds" element={<Funds />} />
                  
                  {/* Market Routes */}
                  <Route path="/market/watch" element={<MarketWatch />} />
                  <Route path="/market/search" element={<ScripSearch />} />
                  <Route path="/market/watchlists" element={<Watchlists />} />
                  
                  {/* User Routes */}
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Box>
  );
}

export default App;
