import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
  Refresh,
  ArrowForward,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useAuth } from '../../contexts/AuthContext';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { authAPI, tradingAPI } from '../../services/apiService';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const { user, profile, kotakSession } = useAuth();
  const { portfolioUpdates } = useWebSocket();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (portfolioUpdates) {
      setPositions(portfolioUpdates.positions || []);
    }
  }, [portfolioUpdates]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard data
      const dashboardRes = await authAPI.getDashboard();
      if (dashboardRes.data.success) {
        setDashboardData(dashboardRes.data.data);
      }
      
      // Fetch positions
      const positionsRes = await tradingAPI.getPositions({ show_closed: 'false' });
      if (positionsRes.data.success) {
        setPositions(positionsRes.data.data.slice(0, 5));
      }
      
      // Fetch recent orders
      const ordersRes = await tradingAPI.getOrders({ limit: 5 });
      if (ordersRes.data.success) {
        setOrders(ordersRes.data.data);
      }
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      enqueueSnackbar('Failed to load dashboard data', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(value || 0);
  };

  const getPnlColor = (value) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Dashboard</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchDashboardData}
        >
          Refresh
        </Button>
      </Box>

      {/* Account Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Available Margin
              </Typography>
              <Typography variant="h5" component="div">
                {formatCurrency(profile?.available_margin)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <AccountBalance fontSize="small" color="action" />
                <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                  Account Balance
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Used Margin
              </Typography>
              <Typography variant="h5" component="div">
                {formatCurrency(profile?.used_margin)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <ShowChart fontSize="small" color="action" />
                <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                  Margin Utilized
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Today's P&L
              </Typography>
              <Typography 
                variant="h5" 
                component="div"
                color={getPnlColor(dashboardData?.today_pnl)}
              >
                {formatCurrency(dashboardData?.today_pnl)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {dashboardData?.today_pnl >= 0 ? (
                  <TrendingUp fontSize="small" color="success" />
                ) : (
                  <TrendingDown fontSize="small" color="error" />
                )}
                <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                  {dashboardData?.today_trades_count || 0} Trades
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Open Positions
              </Typography>
              <Typography variant="h5" component="div">
                {dashboardData?.open_positions_count || 0}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  {dashboardData?.pending_orders_count || 0} Pending Orders
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Open Positions */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Open Positions</Typography>
              <Button
                size="small"
                endIcon={<ArrowForward />}
                onClick={() => navigate('/trading/positions')}
              >
                View All
              </Button>
            </Box>
            
            {positions.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Qty</TableCell>
                      <TableCell align="right">P&L</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position) => (
                      <TableRow key={position.id}>
                        <TableCell>{position.trading_symbol}</TableCell>
                        <TableCell>
                          <Chip
                            label={position.position_type}
                            size="small"
                            color={position.position_type === 'LONG' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell align="right">{position.quantity}</TableCell>
                        <TableCell align="right">
                          <Typography
                            color={getPnlColor(parseFloat(position.unrealized_pnl))}
                            variant="body2"
                          >
                            {formatCurrency(position.unrealized_pnl)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="textSecondary" align="center" sx={{ py: 4 }}>
                No open positions
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Recent Orders */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Recent Orders</Typography>
              <Button
                size="small"
                endIcon={<ArrowForward />}
                onClick={() => navigate('/trading/order-book')}
              >
                View All
              </Button>
            </Box>
            
            {orders.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Qty</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orders.map((order) => (
                      <TableRow key={order.id}>
                        <TableCell>{order.trading_symbol}</TableCell>
                        <TableCell>
                          <Chip
                            label={order.transaction_type}
                            size="small"
                            color={order.transaction_type === 'BUY' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell align="right">{order.quantity}</TableCell>
                        <TableCell>
                          <Chip
                            label={order.status}
                            size="small"
                            color={
                              order.status === 'COMPLETE' ? 'success' :
                              order.status === 'REJECTED' ? 'error' :
                              order.status === 'CANCELLED' ? 'default' :
                              'warning'
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="textSecondary" align="center" sx={{ py: 4 }}>
                No recent orders
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Kotak Connection Warning */}
      {!kotakSession?.session_status === 'active' && (
        <Paper sx={{ p: 2, mt: 3, bgcolor: 'warning.light' }}>
          <Typography variant="body1">
            Your Kotak account is not connected. Please link your account to start trading.
          </Typography>
          <Button
            variant="contained"
            sx={{ mt: 1 }}
            onClick={() => navigate('/profile')}
          >
            Connect Kotak Account
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default Dashboard;
