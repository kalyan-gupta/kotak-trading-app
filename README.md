# Kotak Neo Trading Platform

A comprehensive Django-based trading application that integrates with the Kotak Neo API v2. This platform provides real-time trading capabilities, portfolio management, market data analysis, and WebSocket-based live updates.

## Features

### Backend (Django)
- **Kotak Neo API v2 Integration**
  - TOTP-based authentication flow
  - Session management with token refresh
  - Order placement (Market, Limit, SL, SL-M)
  - Cover Orders and Bracket Orders support
  - Order modification and cancellation
  - Real-time portfolio tracking

- **Models**
  - User profile with encrypted Kotak credentials
  - Order tracking and history
  - Position management
  - Scrip master data cache

- **API Endpoints (DRF)**
  - Authentication (login/logout/session management)
  - Order management (place/modify/cancel)
  - Portfolio (holdings/positions/order book/trade book)
  - Market data (quotes/scrip search/historical data)
  - WebSocket for real-time updates

- **Security**
  - Fernet encryption for sensitive credentials
  - Rate limiting on API calls
  - Session management with proper token handling

### Frontend (React)
- **Dashboard**
  - Account balance and margin overview
  - Real-time P&L tracking
  - Open positions summary
  - Recent orders

- **Trading Interface**
  - Order placement with validation
  - Support for all order types
  - Order confirmation modal
  - Margin check before order placement

- **Portfolio Management**
  - Positions table with real-time P&L
  - One-click position closing
  - SL/Target modification for bracket orders

- **Market Data**
  - Scrip search with autocomplete
  - Real-time quotes
  - Market depth visualization
  - Watchlist management

- **Real-time Updates**
  - WebSocket integration for live prices
  - Toast notifications for order updates
  - Portfolio P&L updates

## Tech Stack

### Backend
- Django 4.2+
- Django REST Framework
- Django Channels (WebSocket)
- PostgreSQL
- Redis (caching & message broker)
- Celery (background tasks)
- neo-api-client (Kotak Neo API)

### Frontend
- React 18
- Material-UI (MUI)
- Axios (HTTP client)
- WebSocket API

### Infrastructure
- Docker & Docker Compose
- Nginx (reverse proxy)
- Daphne (ASGI server)

## Project Structure

```
kotak-trading-app/
├── backend/                    # Django backend
│   ├── accounts/              # User authentication & profiles
│   ├── trading/               # Order & position management
│   ├── market_data/           # Scrip data & quotes
│   ├── websocket_server/      # WebSocket consumers
│   ├── trading_project/       # Django settings
│   ├── requirements.txt
│   ├── Dockerfile
│   └── manage.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── contexts/          # React contexts
│   │   ├── services/          # API services
│   │   └── styles/            # CSS styles
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker/                     # Docker configurations
│   └── nginx/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Git

### Quick Start (Docker)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kotak-trading-app
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` file and set your values:
   ```bash
   # Required settings
   SECRET_KEY=your-secure-secret-key
   ENCRYPTION_KEY=your-encryption-key
   
   # Kotak API credentials
   KOTAK_CONSUMER_KEY=your-consumer-key
   KOTAK_CONSUMER_SECRET=your-consumer-secret
   ```

4. **Build and start services**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/
   - Admin Panel: http://localhost:8000/admin/

6. **Create superuser (optional)**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

### Manual Setup (Development)

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   - Install PostgreSQL
   - Create database: `trading_db`
   - Create user: `trading_user`

4. **Set up Redis**
   ```bash
   # On macOS
   brew install redis
   brew services start redis
   
   # On Ubuntu
   sudo apt-get install redis-server
   sudo service redis-server start
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm start
   ```

## Kotak Neo API Setup

1. **Register for Kotak Neo API access**
   - Visit Kotak Securities developer portal
   - Create an application
   - Get Consumer Key and Consumer Secret

2. **Configure API credentials**
   - Add your credentials to `.env` file
   - Set up TOTP secret for 2FA

3. **Link your account**
   - Login to the trading platform
   - Go to Profile → Kotak Settings
   - Enter your Kotak credentials
   - Complete TOTP verification

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/update/` - Update profile
- `POST /api/auth/kotak/login/` - Kotak API login
- `POST /api/auth/kotak/verify-totp/` - Verify TOTP
- `GET /api/auth/kotak/session-status/` - Check session status

### Trading Endpoints
- `GET /api/trading/orders/` - List orders
- `POST /api/trading/orders/place/` - Place order
- `PUT /api/trading/orders/{id}/modify/` - Modify order
- `POST /api/trading/orders/{id}/cancel/` - Cancel order
- `GET /api/trading/positions/` - List positions
- `POST /api/trading/positions/{id}/close/` - Close position
- `GET /api/trading/holdings/` - Get holdings
- `GET /api/trading/funds/` - Get funds/margin

### Market Data Endpoints
- `GET /api/market/scrips/search/?q={query}` - Search scrips
- `GET /api/market/quotes/?symbol_token={token}` - Get quote
- `GET /api/market/watchlists/` - List watchlists
- `POST /api/market/historical/` - Get historical data

### WebSocket Endpoints
- `ws://localhost:8000/ws/market-data/` - Market data stream
- `ws://localhost:8000/ws/order-updates/` - Order updates
- `ws://localhost:8000/ws/portfolio-updates/` - Portfolio updates

## Security Considerations

1. **Never commit `.env` file** with real credentials
2. **Use strong encryption keys** for sensitive data
3. **Enable HTTPS** in production
4. **Set up proper firewall rules**
5. **Regularly rotate API credentials**
6. **Monitor API usage** for suspicious activity

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`

2. **Redis connection errors**
   - Ensure Redis server is running
   - Check Redis URL in settings

3. **Kotak API authentication failures**
   - Verify Consumer Key and Secret
   - Check TOTP secret is correct
   - Ensure mobile number and UCC are valid

4. **WebSocket connection issues**
   - Check Daphne is running
   - Verify WebSocket URL in frontend

### Logs

View logs for debugging:
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All logs
docker-compose logs -f
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This software is for educational purposes only. Trading involves significant risk. Always consult with a financial advisor before making investment decisions. The authors are not responsible for any financial losses incurred through the use of this software.

## Support

For issues and feature requests, please create an issue in the repository.
