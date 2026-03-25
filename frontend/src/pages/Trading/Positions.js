import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { tradingAPI } from '../../services/apiService';
import { useWebSocket } from '../../contexts/WebSocketContext';

const Positions = () => {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [modifyDialogOpen, setModifyDialogOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [closeData, setCloseData] = useState({
    quantity: '',
    order_type: 'MARKET',
    price: '',
  });
  const [modifyData, setModifyData] = useState({
    stop_loss: '',
    target: '',
  });

  const { enqueueSnackbar } = useSnackbar();
  const { portfolioUpdates } = useWebSocket();

  useEffect(() => {
    fetchPositions();
  }, []);

  useEffect(() => {
    if (portfolioUpdates?.positions) {
      setPositions(portfolioUpdates.positions);
    }
  }, [portfolioUpdates]);

  const fetchPositions = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.getPositions({ show_closed: 'false' });
      if (response.data.success) {
        setPositions(response.data.data);
      }
    } catch (error) {
      enqueueSnackbar('Failed to fetch positions', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleClosePosition = async () => {
    try {
      const response = await tradingAPI.closePosition(selectedPosition.id, closeData);
      
      if (response.data.success) {
        enqueueSnackbar('Position close order placed', { variant: 'success' });
        setCloseDialogOpen(false);
        fetchPositions();
      } else {
        enqueueSnackbar(response.data.message, { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Failed to close position', { variant: 'error' });
    }
  };

  const handleModifyPosition = async () => {
    try {
      const response = await tradingAPI.updatePosition(selectedPosition.id, modifyData);
      
      if (response.data.success) {
        enqueueSnackbar('Position updated successfully', { variant: 'success' });
        setModifyDialogOpen(false);
        fetchPositions();
      } else {
        enqueueSnackbar(response.data.message, { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Failed to update position', { variant: 'error' });
    }
  };

  const openCloseDialog = (position) => {
    setSelectedPosition(position);
    setCloseData({
      quantity: position.quantity,
      order_type: 'MARKET',
      price: '',
    });
    setCloseDialogOpen(true);
  };

  const openModifyDialog = (position) => {
    setSelectedPosition(position);
    setModifyData({
      stop_loss: position.stop_loss || '',
      target: position.target || '',
    });
    setModifyDialogOpen(true);
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

  const totalPnl = positions.reduce((sum, pos) => sum + parseFloat(pos.total_pnl || 0), 0);
  const totalUnrealizedPnl = positions.reduce((sum, pos) => sum + parseFloat(pos.unrealized_pnl || 0), 0);

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Positions</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPositions}
        >
          Refresh
        </Button>
      </Box>

      {/* P&L Summary */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Box>
            <Typography color="textSecondary" variant="body2">
              Total Unrealized P&L
            </Typography>
            <Typography 
              variant="h5" 
              color={getPnlColor(totalUnrealizedPnl)}
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              {totalUnrealizedPnl >= 0 ? <TrendingUp /> : <TrendingDown />}
              {formatCurrency(totalUnrealizedPnl)}
            </Typography>
          </Box>
          <Box>
            <Typography color="textSecondary" variant="body2">
              Total P&L (Realized + Unrealized)
            </Typography>
            <Typography 
              variant="h5" 
              color={getPnlColor(totalPnl)}
            >
              {formatCurrency(totalPnl)}
            </Typography>
          </Box>
          <Box>
            <Typography color="textSecondary" variant="body2">
              Open Positions
            </Typography>
            <Typography variant="h5">
              {positions.length}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {positions.length === 0 ? (
        <Alert severity="info">No open positions</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Exchange</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Product</TableCell>
                <TableCell align="right">Qty</TableCell>
                <TableCell align="right">Avg Price</TableCell>
                <TableCell align="right">LTP</TableCell>
                <TableCell align="right">P&L</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {positions.map((position) => (
                <TableRow key={position.id}>
                  <TableCell>
                    <Typography fontWeight="medium">
                      {position.trading_symbol}
                    </Typography>
                  </TableCell>
                  <TableCell>{position.exchange}</TableCell>
                  <TableCell>
                    <Chip
                      label={position.position_type}
                      size="small"
                      color={position.position_type === 'LONG' ? 'success' : 'error'}
                    />
                  </TableCell>
                  <TableCell>{position.product_type}</TableCell>
                  <TableCell align="right">{position.quantity}</TableCell>
                  <TableCell align="right">
                    {formatCurrency(position.average_price)}
                  </TableCell>
                  <TableCell align="right">
                    {formatCurrency(position.last_price)}
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography
                        color={getPnlColor(parseFloat(position.unrealized_pnl))}
                        variant="body2"
                      >
                        {formatCurrency(position.unrealized_pnl)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        ({position.pnl_percentage}%)
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Modify SL/Target">
                      <IconButton
                        size="small"
                        onClick={() => openModifyDialog(position)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Close Position">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => openCloseDialog(position)}
                      >
                        <CloseIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Close Position Dialog */}
      <Dialog open={closeDialogOpen} onClose={() => setCloseDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Close Position</DialogTitle>
        <DialogContent>
          {selectedPosition && (
            <Box sx={{ pt: 1 }}>
              <Typography gutterBottom>
                Symbol: <strong>{selectedPosition.trading_symbol}</strong>
              </Typography>
              <Typography gutterBottom>
                Current Quantity: <strong>{selectedPosition.quantity}</strong>
              </Typography>
              
              <TextField
                fullWidth
                label="Quantity to Close"
                type="number"
                value={closeData.quantity}
                onChange={(e) => setCloseData({ ...closeData, quantity: e.target.value })}
                margin="normal"
                inputProps={{ min: 1, max: selectedPosition.quantity }}
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Order Type</InputLabel>
                <Select
                  value={closeData.order_type}
                  onChange={(e) => setCloseData({ ...closeData, order_type: e.target.value })}
                  label="Order Type"
                >
                  <MenuItem value="MARKET">Market</MenuItem>
                  <MenuItem value="LIMIT">Limit</MenuItem>
                </Select>
              </FormControl>
              
              {closeData.order_type === 'LIMIT' && (
                <TextField
                  fullWidth
                  label="Price"
                  type="number"
                  value={closeData.price}
                  onChange={(e) => setCloseData({ ...closeData, price: e.target.value })}
                  margin="normal"
                />
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloseDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={handleClosePosition}>
            Close Position
          </Button>
        </DialogActions>
      </Dialog>

      {/* Modify Position Dialog */}
      <Dialog open={modifyDialogOpen} onClose={() => setModifyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Modify Position</DialogTitle>
        <DialogContent>
          {selectedPosition && (
            <Box sx={{ pt: 1 }}>
              <Typography gutterBottom>
                Symbol: <strong>{selectedPosition.trading_symbol}</strong>
              </Typography>
              
              <TextField
                fullWidth
                label="Stop Loss"
                type="number"
                value={modifyData.stop_loss}
                onChange={(e) => setModifyData({ ...modifyData, stop_loss: e.target.value })}
                margin="normal"
              />
              
              <TextField
                fullWidth
                label="Target"
                type="number"
                value={modifyData.target}
                onChange={(e) => setModifyData({ ...modifyData, target: e.target.value })}
                margin="normal"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModifyDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={handleModifyPosition}>
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Positions;
