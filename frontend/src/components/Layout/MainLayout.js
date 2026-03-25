import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  ShoppingCart as OrderIcon,
  Book as OrderBookIcon,
  TrendingUp as PositionsIcon,
  AccountBalance as HoldingsIcon,
  AttachMoney as FundsIcon,
  ShowChart as MarketIcon,
  Search as SearchIcon,
  Bookmark as WatchlistIcon,
  Person as ProfileIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Circle as CircleIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useWebSocket } from '../../contexts/WebSocketContext';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Place Order', icon: <OrderIcon />, path: '/trading/order' },
  { text: 'Order Book', icon: <OrderBookIcon />, path: '/trading/order-book' },
  { text: 'Positions', icon: <PositionsIcon />, path: '/trading/positions' },
  { text: 'Holdings', icon: <HoldingsIcon />, path: '/portfolio/holdings' },
  { text: 'Funds', icon: <FundsIcon />, path: '/portfolio/funds' },
];

const marketItems = [
  { text: 'Market Watch', icon: <MarketIcon />, path: '/market/watch' },
  { text: 'Search Scrips', icon: <SearchIcon />, path: '/market/search' },
  { text: 'Watchlists', icon: <WatchlistIcon />, path: '/market/watchlists' },
];

const userItems = [
  { text: 'Profile', icon: <ProfileIcon />, path: '/profile' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const MainLayout = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, kotakSession } = useAuth();
  const { isConnected } = useWebSocket();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  const drawer = (
    <div>
      <Toolbar sx={{ justifyContent: 'center', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
          Kotak Trading
        </Typography>
      </Toolbar>
      
      {/* Connection Status */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <CircleIcon 
            sx={{ 
              fontSize: 12, 
              color: isConnected ? 'success.main' : 'error.main' 
            }} 
          />
          <Typography variant="caption">
            {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircleIcon 
            sx={{ 
              fontSize: 12, 
              color: kotakSession?.session_status === 'active' ? 'success.main' : 'warning.main' 
            }} 
          />
          <Typography variant="caption">
            Kotak: {kotakSession?.session_status === 'active' ? 'Connected' : 'Not Connected'}
          </Typography>
        </Box>
      </Box>

      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={isActive(item.path)}
              onClick={() => handleNavigation(item.path)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  '&:hover': {
                    backgroundColor: 'primary.light',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: isActive(item.path) ? 'primary.main' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      <List>
        <ListItem>
          <Typography variant="caption" color="text.secondary">
            MARKET
          </Typography>
        </ListItem>
        {marketItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={isActive(item.path)}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon sx={{ color: isActive(item.path) ? 'primary.main' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      <List>
        <ListItem>
          <Typography variant="caption" color="text.secondary">
            USER
          </Typography>
        </ListItem>
        {userItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={isActive(item.path)}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon sx={{ color: isActive(item.path) ? 'primary.main' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={logout}>
            <ListItemIcon>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItemButton>
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find(item => item.path === location.pathname)?.text ||
             marketItems.find(item => item.path === location.pathname)?.text ||
             userItems.find(item => item.path === location.pathname)?.text ||
             'Kotak Trading'}
          </Typography>

          {/* User Info */}
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                label={user.username}
                color="primary"
                variant="outlined"
                size="small"
              />
              {user.is_kotak_linked && (
                <Tooltip title="Kotak Account Linked">
                  <Badge color="success" variant="dot">
                    <Typography variant="caption" sx={{ color: 'white' }}>
                      Kotak
                    </Typography>
                  </Badge>
                </Tooltip>
              )}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default MainLayout;
