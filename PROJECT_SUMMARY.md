# Kotak Neo Trading Platform - Project Summary

## Overview
A comprehensive Django-based trading application with React frontend that integrates with Kotak Neo API v2 for real-time trading, portfolio management, and market data analysis.

## Project Structure

```
kotak-trading-app/
├── backend/                    # Django Backend
│   ├── accounts/              # User authentication & Kotak integration
│   │   ├── models.py          # User, UserProfile, LoginHistory, APILog
│   │   ├── views.py           # Authentication & Kotak login endpoints
│   │   ├── serializers.py     # DRF serializers
│   │   ├── services/          # KotakAuthService for API authentication
│   │   ├── tasks.py           # Celery tasks for session management
│   │   └── urls.py            # API routes
│   │
│   ├── trading/               # Order & Position management
│   │   ├── models.py          # Order, Position, Trade, OrderBook, TradeBook
│   │   ├── views.py           # Trading API endpoints
│   │   ├── serializers.py     # DRF serializers
│   │   ├── services/          # KotakTradingService for trading operations
│   │   ├── tasks.py           # Celery tasks for sync & P&L
│   │   └── urls.py            # API routes
│   │
│   ├── market_data/           # Scrip master & quotes
│   │   ├── models.py          # Scrip, Quote, MarketDepth, Watchlist
│   │   ├── views.py           # Market data API endpoints
│   │   ├── serializers.py     # DRF serializers
│   │   ├── tasks.py           # Celery tasks for data sync
│   │   └── urls.py            # API routes
│   │
│   ├── websocket_server/      # WebSocket for real-time updates
│   │   ├── consumers.py       # MarketDataConsumer, OrderUpdatesConsumer
│   │   ├── routing.py         # WebSocket URL routing
│   │   └── urls.py            # WebSocket status endpoints
│   │
│   ├── trading_project/       # Django configuration
│   │   ├── settings.py        # Django settings
│   │   ├── urls.py            # Root URL configuration
│   │   ├── asgi.py            # ASGI application (WebSocket)
│   │   ├── wsgi.py            # WSGI application
│   │   └── celery.py          # Celery configuration
│   │
│   ├── manage.py              # Django management script
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend Docker image
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   └── Layout/        # MainLayout with navigation
│   │   │
│   │   ├── pages/             # Page components
│   │   │   ├── Auth/          # Login, Register
│   │   │   ├── Dashboard/     # Dashboard with overview
│   │   │   ├── Trading/       # OrderPlacement, OrderBook, Positions
│   │   │   ├── Portfolio/     # Holdings, Funds
│   │   │   └── Market/        # MarketWatch, ScripSearch, Watchlists
│   │   │
│   │   ├── contexts/          # React contexts
│   │   │   ├── AuthContext.js # Authentication state
│   │   │   └── WebSocketContext.js # WebSocket connections
│   │   │
│   │   ├── services/          # API services
│   │   │   └── apiService.js  # Axios configuration & API calls
│   │   │
│   │   ├── styles/            # CSS styles
│   │   ├── App.js             # Main App component
│   │   └── index.js           # React entry point
│   │
│   ├── public/                # Static files
│   ├── package.json           # Node dependencies
│   └── Dockerfile             # Frontend Docker image
│
├── docker/                     # Docker configurations
│   └── nginx/
│       └── nginx.conf         # Nginx reverse proxy config
│
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation
```

## Key Features Implemented

### Backend (Django)

#### 1. Kotak Neo API v2 Integration
- **Authentication Service** (`accounts/services/kotak_auth.py`)
  - TOTP-based login flow
  - Session management with token refresh
  - MPIN validation
  - QR code generation for TOTP setup

- **Trading Service** (`trading/services/kotak_trading.py`)
  - Place orders (Market, Limit, SL, SL-M)
  - Cover Orders and Bracket Orders
  - Modify and cancel orders
  - Fetch order status
  - Portfolio management (holdings, positions, order book, trade book)
  - Margin checking

#### 2. Models
- **UserProfile**: Stores Kotak credentials (encrypted MPIN, TOTP secret)
- **Order**: Tracks all orders with status
- **Position**: Tracks open positions with P&L
- **Trade**: Records executed trades
- **Scrip**: Master scrip/symbol data
- **Quote**: Real-time market quotes
- **Watchlist**: User watchlists

#### 3. API Endpoints
- **Authentication**: `/api/auth/`
  - Login/logout
  - Kotak login with TOTP
  - Session status
  - Profile management

- **Trading**: `/api/trading/`
  - Order CRUD operations
  - Position management
  - Portfolio data

- **Market Data**: `/api/market/`
  - Scrip search
  - Quotes
  - Historical data
  - Watchlists

#### 4. WebSocket
- **Market Data**: Real-time price updates
- **Order Updates**: Order status notifications
- **Portfolio Updates**: P&L updates

#### 5. Security
- Fernet encryption for sensitive data
- Rate limiting on API calls
- Session management
- Token-based authentication

#### 6. Background Tasks (Celery)
- Session refresh every 30 minutes
- Scrip master sync daily
- Quote updates every 5 seconds
- Order book sync every 10 seconds
- P&L calculation every minute

### Frontend (React)

#### 1. Dashboard
- Account balance and margin overview
- Real-time P&L tracking
- Open positions summary
- Recent orders

#### 2. Order Placement
- Scrip search with autocomplete
- All order types support
- Margin validation
- Order confirmation modal

#### 3. Positions Management
- Real-time P&L display
- One-click position closing
- SL/Target modification

#### 4. Market Data
- Scrip search
- Real-time quotes
- Watchlist management
- Market depth

#### 5. Real-time Updates
- WebSocket integration
- Toast notifications
- Live price updates

## Tech Stack

### Backend
- **Django 4.2+** - Web framework
- **Django REST Framework** - API framework
- **Django Channels** - WebSocket support
- **PostgreSQL** - Database
- **Redis** - Cache & message broker
- **Celery** - Background tasks
- **neo-api-client** - Kotak Neo API
- **cryptography** - Encryption
- **pyotp** - TOTP generation

### Frontend
- **React 18** - UI framework
- **Material-UI (MUI)** - Component library
- **Axios** - HTTP client
- **React Router** - Routing
- **Notistack** - Notifications

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy
- **Daphne** - ASGI server

## API Endpoints Summary

### Authentication
```
POST /api/auth/register/           # User registration
POST /api/auth/login/              # User login
POST /api/auth/logout/             # User logout
GET  /api/auth/profile/            # Get profile
PUT  /api/auth/profile/update/     # Update profile
POST /api/auth/kotak/login/        # Kotak login
POST /api/auth/kotak/verify-totp/  # Verify TOTP
GET  /api/auth/kotak/session-status/  # Check session
POST /api/auth/kotak/refresh-session/ # Refresh session
GET  /api/auth/dashboard/          # Dashboard data
```

### Trading
```
GET    /api/trading/orders/              # List orders
POST   /api/trading/orders/place/        # Place order
POST   /api/trading/orders/validate/     # Validate order
GET    /api/trading/orders/{id}/         # Order detail
PUT    /api/trading/orders/{id}/modify/  # Modify order
POST   /api/trading/orders/{id}/cancel/  # Cancel order
GET    /api/trading/orders/{id}/status/  # Order status
GET    /api/trading/positions/           # List positions
GET    /api/trading/positions/live/      # Live positions
POST   /api/trading/positions/{id}/close/    # Close position
PUT    /api/trading/positions/{id}/update/   # Update position
GET    /api/trading/holdings/            # Get holdings
GET    /api/trading/funds/               # Get funds/margin
GET    /api/trading/order-book/          # Get order book
GET    /api/trading/trade-book/          # Get trade book
GET    /api/trading/trades/              # Trade history
```

### Market Data
```
GET  /api/market/scrips/search/?q={query}     # Search scrips
GET  /api/market/scrips/detail/{token}/       # Scrip detail
GET  /api/market/scrips/by-symbol/?symbol={s} # Get by symbol
GET  /api/market/quotes/?symbol_token={token} # Get quote
POST /api/market/quotes/multiple/             # Multiple quotes
GET  /api/market/quotes/depth/                # Market depth
GET  /api/market/watchlists/                  # List watchlists
POST /api/market/watchlists/create/           # Create watchlist
GET  /api/market/watchlists/{id}/             # Watchlist detail
POST /api/market/watchlists/{id}/add/         # Add scrip
POST /api/market/watchlists/{id}/remove/      # Remove scrip
GET  /api/market/scrips/cache-status/         # Cache status
POST /api/market/scrips/sync/                 # Sync scrip master
POST /api/market/historical/                  # Historical data
GET  /api/market/indices/                     # Index quotes
GET  /api/market/top-movers/                  # Top gainers/losers
```

### WebSocket
```
ws://localhost:8000/ws/market-data/       # Market data stream
ws://localhost:8000/ws/order-updates/     # Order updates
ws://localhost:8000/ws/portfolio-updates/ # Portfolio updates
```

## Setup Instructions

### 1. Using Docker (Recommended)
```bash
# Clone repository
cd kotak-trading-app

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up --build

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

### 2. Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Setup PostgreSQL and Redis
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Environment Variables

### Required
- `SECRET_KEY` - Django secret key
- `ENCRYPTION_KEY` - Fernet encryption key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database credentials
- `KOTAK_CONSUMER_KEY`, `KOTAK_CONSUMER_SECRET` - Kotak API credentials

### Optional
- `DEBUG` - Debug mode (default: False)
- `ALLOWED_HOSTS` - Allowed hosts
- `CORS_ALLOWED_ORIGINS` - CORS origins
- `MAX_LOSS_PERCENTAGE` - Risk management
- `MAX_POSITION_SIZE_PERCENTAGE` - Position limits

## Security Considerations

1. **Never commit `.env` file**
2. **Use strong encryption keys**
3. **Enable HTTPS in production**
4. **Regularly rotate API credentials**
5. **Monitor API usage**

## License

MIT License - See LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Trading involves significant risk. Always consult with a financial advisor before making investment decisions.
