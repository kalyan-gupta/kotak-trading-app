import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const apiService = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiService.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiService.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Set auth token
apiService.setAuthToken = (token) => {
  if (token) {
    apiService.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    delete apiService.defaults.headers.common['Authorization'];
  }
};

// Auth APIs
export const authAPI = {
  login: (credentials) => apiService.post('/auth/login/', credentials),
  register: (userData) => apiService.post('/auth/register/', userData),
  logout: () => apiService.post('/auth/logout/'),
  getProfile: () => apiService.get('/auth/profile/'),
  updateProfile: (data) => apiService.put('/auth/profile/update/', data),
  kotakLogin: (credentials) => apiService.post('/auth/kotak/login/', credentials),
  verifyTOTP: (otp) => apiService.post('/auth/kotak/verify-totp/', { otp }),
  kotakLogout: () => apiService.post('/auth/kotak/logout/'),
  getSessionStatus: () => apiService.get('/auth/kotak/session-status/'),
  refreshSession: () => apiService.post('/auth/kotak/refresh-session/'),
  getDashboard: () => apiService.get('/auth/dashboard/'),
  changePassword: (data) => apiService.post('/auth/change-password/', data),
};

// Trading APIs
export const tradingAPI = {
  // Orders
  getOrders: (params) => apiService.get('/trading/orders/', { params }),
  getOrder: (orderId) => apiService.get(`/trading/orders/${orderId}/`),
  placeOrder: (orderData) => apiService.post('/trading/orders/place/', orderData),
  modifyOrder: (orderId, data) => apiService.put(`/trading/orders/${orderId}/modify/`, data),
  cancelOrder: (orderId) => apiService.post(`/trading/orders/${orderId}/cancel/`),
  getOrderStatus: (orderId) => apiService.get(`/trading/orders/${orderId}/status/`),
  validateOrder: (orderData) => apiService.post('/trading/orders/validate/', orderData),
  
  // Positions
  getPositions: (params) => apiService.get('/trading/positions/', { params }),
  getLivePositions: () => apiService.get('/trading/positions/live/'),
  getPosition: (positionId) => apiService.get(`/trading/positions/${positionId}/`),
  closePosition: (positionId, data) => apiService.post(`/trading/positions/${positionId}/close/`, data),
  updatePosition: (positionId, data) => apiService.put(`/trading/positions/${positionId}/update/`, data),
  
  // Portfolio
  getHoldings: () => apiService.get('/trading/holdings/'),
  getFunds: () => apiService.get('/trading/funds/'),
  getOrderBook: () => apiService.get('/trading/order-book/'),
  getTradeBook: () => apiService.get('/trading/trade-book/'),
  
  // Trade History
  getTradeHistory: (params) => apiService.get('/trading/trades/', { params }),
};

// Market Data APIs
export const marketAPI = {
  searchScrips: (query, params = {}) => apiService.get('/market/scrips/search/', {
    params: { q: query, ...params }
  }),
  getScripDetail: (token, exchange = 'NSE') => apiService.get(`/market/scrips/detail/${token}/`, {
    params: { exchange }
  }),
  getScripBySymbol: (symbol, exchange = 'NSE') => apiService.get('/market/scrips/by-symbol/', {
    params: { symbol, exchange }
  }),
  
  // Quotes
  getQuote: (token, exchange = 'NSE') => apiService.get('/market/quotes/', {
    params: { symbol_token: token, exchange }
  }),
  getMultipleQuotes: (symbols) => apiService.post('/market/quotes/multiple/', { symbols }),
  getMarketDepth: (token, exchange = 'NSE') => apiService.get('/market/quotes/depth/', {
    params: { symbol_token: token, exchange }
  }),
  
  // Watchlists
  getWatchlists: () => apiService.get('/market/watchlists/'),
  createWatchlist: (data) => apiService.post('/market/watchlists/create/', data),
  getWatchlist: (id) => apiService.get(`/market/watchlists/${id}/`),
  updateWatchlist: (id, data) => apiService.put(`/market/watchlists/${id}/`, data),
  deleteWatchlist: (id) => apiService.delete(`/market/watchlists/${id}/`),
  addToWatchlist: (id, scripId) => apiService.post(`/market/watchlists/${id}/add/`, { scrip_id: scripId }),
  removeFromWatchlist: (id, scripId) => apiService.post(`/market/watchlists/${id}/remove/`, { scrip_id: scripId }),
  
  // Scrip Master
  getScripCacheStatus: () => apiService.get('/market/scrips/cache-status/'),
  syncScripMaster: (exchange = 'NSE') => apiService.post('/market/scrips/sync/', { exchange }),
  
  // Historical Data
  getHistoricalData: (data) => apiService.post('/market/historical/', data),
  
  // Indices
  getIndexQuotes: () => apiService.get('/market/indices/'),
  getTopMovers: (params = {}) => apiService.get('/market/top-movers/', { params }),
};

export default apiService;
