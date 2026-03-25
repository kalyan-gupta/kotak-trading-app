import React, { createContext, useState, useContext, useEffect, useRef, useCallback } from 'react';
import { useSnackbar } from 'notistack';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [marketData, setMarketData] = useState({});
  const [subscribedSymbols, setSubscribedSymbols] = useState(new Set());
  const [orderUpdates, setOrderUpdates] = useState([]);
  const [portfolioUpdates, setPortfolioUpdates] = useState(null);
  
  const marketWsRef = useRef(null);
  const orderWsRef = useRef(null);
  const portfolioWsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  const { isAuthenticated, user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();

  // Build WebSocket URL
  const getWsUrl = (endpoint) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/${endpoint}/`;
  };

  // Connect to Market Data WebSocket
  const connectMarketData = useCallback(() => {
    if (!isAuthenticated || marketWsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl('market-data'));
    marketWsRef.current = ws;

    ws.onopen = () => {
      console.log('Market Data WebSocket connected');
      setIsConnected(true);
      
      // Resubscribe to previously subscribed symbols
      if (subscribedSymbols.size > 0) {
        const symbols = Array.from(subscribedSymbols).map(key => {
          const [exchange, symbol_token] = key.split(':');
          return { symbol_token, exchange };
        });
        ws.send(JSON.stringify({ type: 'subscribe', symbols }));
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMarketDataMessage(data);
    };

    ws.onclose = () => {
      console.log('Market Data WebSocket disconnected');
      setIsConnected(false);
      
      // Reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connectMarketData();
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('Market Data WebSocket error:', error);
    };
  }, [isAuthenticated, subscribedSymbols]);

  // Connect to Order Updates WebSocket
  const connectOrderUpdates = useCallback(() => {
    if (!isAuthenticated || orderWsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl('order-updates'));
    orderWsRef.current = ws;

    ws.onopen = () => {
      console.log('Order Updates WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleOrderUpdateMessage(data);
    };

    ws.onclose = () => {
      console.log('Order Updates WebSocket disconnected');
      setTimeout(() => connectOrderUpdates(), 5000);
    };

    ws.onerror = (error) => {
      console.error('Order Updates WebSocket error:', error);
    };
  }, [isAuthenticated]);

  // Connect to Portfolio Updates WebSocket
  const connectPortfolioUpdates = useCallback(() => {
    if (!isAuthenticated || portfolioWsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl('portfolio-updates'));
    portfolioWsRef.current = ws;

    ws.onopen = () => {
      console.log('Portfolio Updates WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handlePortfolioUpdateMessage(data);
    };

    ws.onclose = () => {
      console.log('Portfolio Updates WebSocket disconnected');
      setTimeout(() => connectPortfolioUpdates(), 5000);
    };

    ws.onerror = (error) => {
      console.error('Portfolio Updates WebSocket error:', error);
    };
  }, [isAuthenticated]);

  // Handle market data messages
  const handleMarketDataMessage = (data) => {
    switch (data.type) {
      case 'quote':
      case 'quote_update':
        setMarketData(prev => ({
          ...prev,
          [data.symbol]: data.data
        }));
        break;
      case 'depth':
      case 'depth_update':
        setMarketData(prev => ({
          ...prev,
          [`${data.symbol}_depth`]: data.data
        }));
        break;
      case 'error':
        console.error('WebSocket error:', data.message);
        break;
      default:
        break;
    }
  };

  // Handle order update messages
  const handleOrderUpdateMessage = (data) => {
    switch (data.type) {
      case 'order_update':
        setOrderUpdates(prev => [data, ...prev.slice(0, 49)]);
        enqueueSnackbar(
          `Order ${data.order_id}: ${data.status}`,
          { variant: data.status === 'COMPLETE' ? 'success' : 'info' }
        );
        break;
      case 'trade_update':
        enqueueSnackbar(`Trade executed: ${data.trade_id}`, { variant: 'success' });
        break;
      default:
        break;
    }
  };

  // Handle portfolio update messages
  const handlePortfolioUpdateMessage = (data) => {
    switch (data.type) {
      case 'portfolio_snapshot':
        setPortfolioUpdates(data.data);
        break;
      case 'position_update':
        setPortfolioUpdates(prev => ({
          ...prev,
          positions: prev?.positions?.map(p => 
            p.id === data.data.id ? { ...p, ...data.data } : p
          ) || []
        }));
        break;
      case 'pnl_update':
        setPortfolioUpdates(prev => ({
          ...prev,
          ...data.data
        }));
        break;
      default:
        break;
    }
  };

  // Subscribe to symbols
  const subscribeSymbols = useCallback((symbols) => {
    if (marketWsRef.current?.readyState === WebSocket.OPEN) {
      marketWsRef.current.send(JSON.stringify({
        type: 'subscribe',
        symbols
      }));
      
      symbols.forEach(sym => {
        const key = `${sym.exchange}:${sym.symbol_token}`;
        setSubscribedSymbols(prev => new Set([...prev, key]));
      });
    }
  }, []);

  // Unsubscribe from symbols
  const unsubscribeSymbols = useCallback((symbols) => {
    if (marketWsRef.current?.readyState === WebSocket.OPEN) {
      marketWsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        symbols
      }));
      
      symbols.forEach(sym => {
        const key = `${sym.exchange}:${sym.symbol_token}`;
        setSubscribedSymbols(prev => {
          const newSet = new Set(prev);
          newSet.delete(key);
          return newSet;
        });
      });
    }
  }, []);

  // Get quote for a symbol
  const getQuote = useCallback((symbol_token, exchange = 'NSE') => {
    if (marketWsRef.current?.readyState === WebSocket.OPEN) {
      marketWsRef.current.send(JSON.stringify({
        type: 'get_quote',
        symbol_token,
        exchange
      }));
    }
  }, []);

  // Subscribe to market depth
  const subscribeDepth = useCallback((symbol_token, exchange = 'NSE') => {
    if (marketWsRef.current?.readyState === WebSocket.OPEN) {
      marketWsRef.current.send(JSON.stringify({
        type: 'subscribe_depth',
        symbol_token,
        exchange
      }));
    }
  }, []);

  // Disconnect all WebSockets
  const disconnectAll = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    [marketWsRef, orderWsRef, portfolioWsRef].forEach(wsRef => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    });
    
    setIsConnected(false);
    setSubscribedSymbols(new Set());
  }, []);

  // Connect when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      connectMarketData();
      connectOrderUpdates();
      connectPortfolioUpdates();
    } else {
      disconnectAll();
    }

    return () => {
      disconnectAll();
    };
  }, [isAuthenticated, connectMarketData, connectOrderUpdates, connectPortfolioUpdates, disconnectAll]);

  const value = {
    isConnected,
    marketData,
    subscribedSymbols,
    orderUpdates,
    portfolioUpdates,
    subscribeSymbols,
    unsubscribeSymbols,
    getQuote,
    subscribeDepth,
    connectMarketData,
    disconnectAll,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketContext;
