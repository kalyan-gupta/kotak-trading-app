import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Autocomplete,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { tradingAPI, marketAPI } from '../../services/apiService';

const OrderPlacement = () => {
  const [orderData, setOrderData] = useState({
    exchange: 'NSE',
    trading_symbol: '',
    symbol_token: '',
    transaction_type: 'BUY',
    order_type: 'MARKET',
    product_type: 'INTRADAY',
    quantity: 1,
    price: '',
    trigger_price: '',
    stop_loss: '',
    target: '',
    validity: 'DAY',
    is_amo: false,
    disclosed_quantity: 0,
  });
  
  const [scripOptions, setScripOptions] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  
  const { enqueueSnackbar } = useSnackbar();

  // Search scrips
  useEffect(() => {
    const timeoutId = setTimeout(async () => {
      if (searchQuery.length >= 2) {
        setSearchLoading(true);
        try {
          const response = await marketAPI.searchScrips(searchQuery);
          if (response.data.success) {
            setScripOptions(response.data.data);
          }
        } catch (error) {
          console.error('Search error:', error);
        }
        setSearchLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setOrderData({
      ...orderData,
      [name]: type === 'checkbox' ? checked : value,
    });
    setValidationResult(null);
  };

  const handleScripSelect = (event, value) => {
    if (value) {
      setOrderData({
        ...orderData,
        trading_symbol: value.trading_symbol,
        symbol_token: value.symbol_token,
        exchange: value.exchange,
        instrument_type: value.instrument_type,
      });
      setSearchQuery(value.trading_symbol);
    }
  };

  const validateOrder = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.validateOrder(orderData);
      if (response.data.success) {
        setValidationResult(response.data.data);
        if (response.data.data.is_valid) {
          setShowConfirmation(true);
        } else {
          enqueueSnackbar(response.data.data.message, { variant: 'warning' });
        }
      }
    } catch (error) {
      enqueueSnackbar('Validation failed', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const placeOrder = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.placeOrder(orderData);
      
      if (response.data.success) {
        enqueueSnackbar('Order placed successfully!', { variant: 'success' });
        setShowConfirmation(false);
        resetForm();
      } else {
        enqueueSnackbar(response.data.message || 'Order placement failed', { variant: 'error' });
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Failed to place order';
      enqueueSnackbar(message, { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setOrderData({
      exchange: 'NSE',
      trading_symbol: '',
      symbol_token: '',
      transaction_type: 'BUY',
      order_type: 'MARKET',
      product_type: 'INTRADAY',
      quantity: 1,
      price: '',
      trigger_price: '',
      stop_loss: '',
      target: '',
      validity: 'DAY',
      is_amo: false,
      disclosed_quantity: 0,
    });
    setSearchQuery('');
    setValidationResult(null);
    setActiveStep(0);
  };

  const steps = ['Select Scrip', 'Order Details', 'Review & Confirm'];

  const isPriceRequired = orderData.order_type === 'LIMIT' || orderData.order_type === 'SL';
  const isTriggerRequired = orderData.order_type === 'SL' || orderData.order_type === 'SL-M';
  const isSLRequired = orderData.product_type === 'CO' || orderData.product_type === 'BO';
  const isTargetRequired = orderData.product_type === 'BO';

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Place Order
      </Typography>

      <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {/* Scrip Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={scripOptions}
              getOptionLabel={(option) => 
                `${option.trading_symbol} - ${option.symbol_name || option.company_name || ''}`
              }
              loading={searchLoading}
              onInputChange={(e, value) => setSearchQuery(value)}
              onChange={handleScripSelect}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Search Scrip"
                  variant="outlined"
                  fullWidth
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {searchLoading ? <CircularProgress color="inherit" size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
          </Grid>

          {/* Transaction Type */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Transaction Type</InputLabel>
              <Select
                name="transaction_type"
                value={orderData.transaction_type}
                onChange={handleChange}
                label="Transaction Type"
              >
                <MenuItem value="BUY">
                  <Chip label="BUY" color="success" size="small" />
                </MenuItem>
                <MenuItem value="SELL">
                  <Chip label="SELL" color="error" size="small" />
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Quantity */}
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Quantity"
              name="quantity"
              type="number"
              value={orderData.quantity}
              onChange={handleChange}
              inputProps={{ min: 1 }}
            />
          </Grid>

          {/* Order Type */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Order Type</InputLabel>
              <Select
                name="order_type"
                value={orderData.order_type}
                onChange={handleChange}
                label="Order Type"
              >
                <MenuItem value="MARKET">Market</MenuItem>
                <MenuItem value="LIMIT">Limit</MenuItem>
                <MenuItem value="SL">Stop Loss (SL)</MenuItem>
                <MenuItem value="SL-M">Stop Loss Market (SL-M)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Product Type */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Product Type</InputLabel>
              <Select
                name="product_type"
                value={orderData.product_type}
                onChange={handleChange}
                label="Product Type"
              >
                <MenuItem value="INTRADAY">Intraday (MIS)</MenuItem>
                <MenuItem value="DELIVERY">Delivery (CNC)</MenuItem>
                <MenuItem value="CO">Cover Order</MenuItem>
                <MenuItem value="BO">Bracket Order</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Price - for Limit orders */}
          {isPriceRequired && (
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Price"
                name="price"
                type="number"
                value={orderData.price}
                onChange={handleChange}
                required
              />
            </Grid>
          )}

          {/* Trigger Price - for SL orders */}
          {isTriggerRequired && (
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Trigger Price"
                name="trigger_price"
                type="number"
                value={orderData.trigger_price}
                onChange={handleChange}
                required
              />
            </Grid>
          )}

          {/* Stop Loss - for CO/BO */}
          {isSLRequired && (
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Stop Loss"
                name="stop_loss"
                type="number"
                value={orderData.stop_loss}
                onChange={handleChange}
                required
              />
            </Grid>
          )}

          {/* Target - for BO */}
          {isTargetRequired && (
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Target"
                name="target"
                type="number"
                value={orderData.target}
                onChange={handleChange}
                required
              />
            </Grid>
          )}

          {/* Validity */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Validity</InputLabel>
              <Select
                name="validity"
                value={orderData.validity}
                onChange={handleChange}
                label="Validity"
              >
                <MenuItem value="DAY">Day</MenuItem>
                <MenuItem value="IOC">Immediate or Cancel</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* AMO */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  name="is_amo"
                  checked={orderData.is_amo}
                  onChange={handleChange}
                />
              }
              label="After Market Order (AMO)"
            />
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Validation Result */}
        {validationResult && (
          <Alert 
            severity={validationResult.is_valid ? 'success' : 'warning'}
            sx={{ mb: 2 }}
          >
            {validationResult.message}
            {validationResult.required_margin && (
              <div>Required Margin: ₹{validationResult.required_margin}</div>
            )}
            {validationResult.available_margin && (
              <div>Available Margin: ₹{validationResult.available_margin}</div>
            )}
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={resetForm}
            disabled={loading}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={validateOrder}
            disabled={!orderData.symbol_token || loading}
            startIcon={loading && <CircularProgress size={20} />}
          >
            Review Order
          </Button>
        </Box>
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmation} onClose={() => setShowConfirmation(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm Order</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography color="textSecondary">Symbol</Typography>
              <Typography variant="h6">{orderData.trading_symbol}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography color="textSecondary">Type</Typography>
              <Chip 
                label={orderData.transaction_type} 
                color={orderData.transaction_type === 'BUY' ? 'success' : 'error'}
              />
            </Grid>
            <Grid item xs={6}>
              <Typography color="textSecondary">Quantity</Typography>
              <Typography>{orderData.quantity}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography color="textSecondary">Order Type</Typography>
              <Typography>{orderData.order_type}</Typography>
            </Grid>
            {orderData.price && (
              <Grid item xs={6}>
                <Typography color="textSecondary">Price</Typography>
                <Typography>₹{orderData.price}</Typography>
              </Grid>
            )}
            {orderData.stop_loss && (
              <Grid item xs={6}>
                <Typography color="textSecondary">Stop Loss</Typography>
                <Typography>₹{orderData.stop_loss}</Typography>
              </Grid>
            )}
            {orderData.target && (
              <Grid item xs={6}>
                <Typography color="textSecondary">Target</Typography>
                <Typography>₹{orderData.target}</Typography>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfirmation(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="primary"
            onClick={placeOrder}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Place Order'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrderPlacement;
