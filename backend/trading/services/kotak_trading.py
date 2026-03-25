"""
Kotak Neo API v2 Trading Service
"""
import logging
from decimal import Decimal
from django.conf import settings
from neo_api_client import NeoAPI

from accounts.services.kotak_auth import KotakAuthService
from trading.models import Order, Position, Trade

logger = logging.getLogger(__name__)


class KotakTradingService:
    """Service for handling trading operations with Kotak Neo API."""
    
    def __init__(self, user_profile):
        """
        Initialize Kotak Trading Service.
        
        Args:
            user_profile: UserProfile instance with Kotak credentials
        """
        self.profile = user_profile
        self.auth_service = KotakAuthService(user_profile)
        self.client = None
        self._ensure_client()
    
    def _ensure_client(self):
        """Ensure API client is authenticated."""
        try:
            self.client = self.auth_service.get_client()
        except Exception as e:
            logger.error(f"Failed to get authenticated client: {e}")
            raise Exception("Session expired. Please login again.")
    
    def place_order(self, order_data):
        """
        Place a new order with Kotak Neo API.
        
        Args:
            order_data: Dictionary containing order details
        
        Returns:
            Dictionary with order result
        """
        try:
            # Validate margin before placing order
            if self.profile.enable_margin_check:
                margin_check = self.check_margin(order_data)
                if not margin_check.get('sufficient'):
                    return {
                        'success': False,
                        'message': margin_check.get('message', 'Insufficient margin'),
                        'required_margin': margin_check.get('required_margin'),
                        'available_margin': margin_check.get('available_margin')
                    }
            
            # Prepare order parameters
            params = self._prepare_order_params(order_data)
            logger.info(f"Placing order with params: {params}")
            
            # Place order via API
            response = self.client.place_order(**params)
            logger.info(f"Order response: {response}")
            
            if response and 'data' in response:
                order_id = response['data'].get('order_id')
                
                # Create order record in database
                order = Order.objects.create(
                    user=self.profile.user,
                    order_id=order_id,
                    exchange=order_data.get('exchange', 'NSE'),
                    trading_symbol=order_data.get('trading_symbol'),
                    symbol_token=order_data.get('symbol_token'),
                    instrument_type=order_data.get('instrument_type'),
                    transaction_type=order_data.get('transaction_type'),
                    order_type=order_data.get('order_type', 'MARKET'),
                    product_type=order_data.get('product_type', 'INTRADAY'),
                    quantity=order_data.get('quantity'),
                    disclosed_quantity=order_data.get('disclosed_quantity', 0),
                    price=Decimal(str(order_data.get('price', 0))),
                    trigger_price=Decimal(str(order_data.get('trigger_price', 0))),
                    stop_loss=Decimal(str(order_data.get('stop_loss', 0))) if order_data.get('stop_loss') else None,
                    target=Decimal(str(order_data.get('target', 0))) if order_data.get('target') else None,
                    trailing_stop_loss=Decimal(str(order_data.get('trailing_stop_loss', 0))) if order_data.get('trailing_stop_loss') else None,
                    validity=order_data.get('validity', 'DAY'),
                    is_amo=order_data.get('is_amo', False),
                    amo_time=order_data.get('amo_time'),
                    status=Order.STATUS_PENDING,
                    tags=order_data.get('tags', {})
                )
                
                return {
                    'success': True,
                    'message': 'Order placed successfully',
                    'order_id': order_id,
                    'local_order_id': str(order.id),
                    'data': response['data']
                }
            else:
                error_msg = response.get('message', 'Order placement failed') if isinstance(response, dict) else 'Order placement failed'
                return {
                    'success': False,
                    'message': error_msg,
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {
                'success': False,
                'message': 'Failed to place order',
                'error': str(e)
            }
    
    def modify_order(self, order, modify_data):
        """
        Modify an existing order.
        
        Args:
            order: Order instance to modify
            modify_data: Dictionary with fields to modify
        
        Returns:
            Dictionary with modification result
        """
        try:
            if not order.is_modifiable:
                return {
                    'success': False,
                    'message': 'Order cannot be modified'
                }
            
            params = {
                'order_id': order.order_id,
                'exchange': order.exchange,
                'trading_symbol': order.trading_symbol,
                'symbol_token': order.symbol_token,
            }
            
            # Add modifiable fields
            if 'quantity' in modify_data:
                params['quantity'] = modify_data['quantity']
            if 'price' in modify_data:
                params['price'] = float(modify_data['price'])
            if 'trigger_price' in modify_data:
                params['trigger_price'] = float(modify_data['trigger_price'])
            if 'order_type' in modify_data:
                params['order_type'] = modify_data['order_type']
            
            logger.info(f"Modifying order with params: {params}")
            
            response = self.client.modify_order(**params)
            logger.info(f"Modify order response: {response}")
            
            if response and 'data' in response:
                # Update order in database
                if 'quantity' in modify_data:
                    order.quantity = modify_data['quantity']
                if 'price' in modify_data:
                    order.price = Decimal(str(modify_data['price']))
                if 'trigger_price' in modify_data:
                    order.trigger_price = Decimal(str(modify_data['trigger_price']))
                if 'stop_loss' in modify_data:
                    order.stop_loss = Decimal(str(modify_data['stop_loss'])) if modify_data['stop_loss'] else None
                if 'target' in modify_data:
                    order.target = Decimal(str(modify_data['target'])) if modify_data['target'] else None
                
                order.status = Order.STATUS_MODIFIED
                order.save()
                
                return {
                    'success': True,
                    'message': 'Order modified successfully',
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', 'Order modification failed'),
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return {
                'success': False,
                'message': 'Failed to modify order',
                'error': str(e)
            }
    
    def cancel_order(self, order):
        """
        Cancel an existing order.
        
        Args:
            order: Order instance to cancel
        
        Returns:
            Dictionary with cancellation result
        """
        try:
            if not order.is_cancellable:
                return {
                    'success': False,
                    'message': 'Order cannot be cancelled'
                }
            
            params = {
                'order_id': order.order_id,
                'exchange': order.exchange,
                'trading_symbol': order.trading_symbol,
                'symbol_token': order.symbol_token,
            }
            
            logger.info(f"Cancelling order: {order.order_id}")
            
            response = self.client.cancel_order(**params)
            logger.info(f"Cancel order response: {response}")
            
            if response and 'data' in response:
                order.status = Order.STATUS_CANCELLED
                order.save()
                
                return {
                    'success': True,
                    'message': 'Order cancelled successfully',
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', 'Order cancellation failed'),
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return {
                'success': False,
                'message': 'Failed to cancel order',
                'error': str(e)
            }
    
    def get_order_status(self, order_id):
        """
        Get status of a specific order.
        
        Args:
            order_id: Order ID to check
        
        Returns:
            Dictionary with order status
        """
        try:
            response = self.client.order_history(order_id=order_id)
            logger.info(f"Order status response: {response}")
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get order status',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get order status error: {e}")
            return {
                'success': False,
                'message': 'Failed to get order status',
                'error': str(e)
            }
    
    def get_order_book(self):
        """
        Get order book from Kotak.
        
        Returns:
            Dictionary with order book data
        """
        try:
            response = self.client.order_book()
            logger.info(f"Order book response received")
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get order book',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get order book error: {e}")
            return {
                'success': False,
                'message': 'Failed to get order book',
                'error': str(e)
            }
    
    def get_trade_book(self):
        """
        Get trade book from Kotak.
        
        Returns:
            Dictionary with trade book data
        """
        try:
            response = self.client.trade_book()
            logger.info(f"Trade book response received")
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get trade book',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get trade book error: {e}")
            return {
                'success': False,
                'message': 'Failed to get trade book',
                'error': str(e)
            }
    
    def get_positions(self):
        """
        Get positions from Kotak.
        
        Returns:
            Dictionary with positions data
        """
        try:
            response = self.client.positions()
            logger.info(f"Positions response received")
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get positions',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return {
                'success': False,
                'message': 'Failed to get positions',
                'error': str(e)
            }
    
    def get_holdings(self):
        """
        Get holdings from Kotak.
        
        Returns:
            Dictionary with holdings data
        """
        try:
            response = self.client.holdings()
            logger.info(f"Holdings response received")
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get holdings',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get holdings error: {e}")
            return {
                'success': False,
                'message': 'Failed to get holdings',
                'error': str(e)
            }
    
    def get_funds(self):
        """
        Get funds/margin information.
        
        Returns:
            Dictionary with funds data
        """
        try:
            response = self.client.limits()
            logger.info(f"Funds response received")
            
            if response and 'data' in response:
                # Update profile with latest margin info
                data = response['data']
                self.profile.account_balance = Decimal(str(data.get('available_cash', 0)))
                self.profile.available_margin = Decimal(str(data.get('available_margin', 0)))
                self.profile.used_margin = Decimal(str(data.get('used_margin', 0)))
                self.profile.save()
                
                return {
                    'success': True,
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get funds',
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"Get funds error: {e}")
            return {
                'success': False,
                'message': 'Failed to get funds',
                'error': str(e)
            }
    
    def check_margin(self, order_data):
        """
        Check if sufficient margin is available for order.
        
        Args:
            order_data: Dictionary containing order details
        
        Returns:
            Dictionary with margin check result
        """
        try:
            # Get current funds
            funds_response = self.get_funds()
            if not funds_response.get('success'):
                return {
                    'sufficient': False,
                    'message': 'Could not fetch margin information'
                }
            
            available_margin = Decimal(str(funds_response['data'].get('available_margin', 0)))
            
            # Calculate required margin (simplified calculation)
            quantity = order_data.get('quantity', 0)
            price = Decimal(str(order_data.get('price', 0)))
            
            if order_data.get('order_type') == 'MARKET':
                # For market orders, estimate price
                price = Decimal('100')  # This should be fetched from market data
            
            required_margin = quantity * price
            
            # Add margin requirements based on product type
            product_type = order_data.get('product_type', 'INTRADAY')
            if product_type == 'INTRADAY':
                required_margin *= Decimal('0.2')  # 20% for MIS
            elif product_type in ['CO', 'BO']:
                required_margin *= Decimal('0.15')  # 15% for CO/BO
            
            if available_margin >= required_margin:
                return {
                    'sufficient': True,
                    'required_margin': required_margin,
                    'available_margin': available_margin
                }
            else:
                return {
                    'sufficient': False,
                    'message': f'Insufficient margin. Required: ₹{required_margin}, Available: ₹{available_margin}',
                    'required_margin': required_margin,
                    'available_margin': available_margin
                }
                
        except Exception as e:
            logger.error(f"Margin check error: {e}")
            return {
                'sufficient': False,
                'message': f'Error checking margin: {str(e)}'
            }
    
    def _prepare_order_params(self, order_data):
        """Prepare order parameters for API call."""
        params = {
            'exchange': order_data.get('exchange', 'NSE'),
            'trading_symbol': order_data.get('trading_symbol'),
            'symbol_token': order_data.get('symbol_token'),
            'transaction_type': order_data.get('transaction_type'),
            'quantity': order_data.get('quantity'),
            'order_type': order_data.get('order_type', 'MARKET'),
            'product_type': order_data.get('product_type', 'INTRADAY'),
            'validity': order_data.get('validity', 'DAY'),
        }
        
        # Add optional parameters
        if order_data.get('price') and order_data.get('order_type') in ['LIMIT', 'SL']:
            params['price'] = float(order_data['price'])
        
        if order_data.get('trigger_price') and order_data.get('order_type') in ['SL', 'SL-M']:
            params['trigger_price'] = float(order_data['trigger_price'])
        
        if order_data.get('disclosed_quantity'):
            params['disclosed_quantity'] = order_data['disclosed_quantity']
        
        # Bracket Order fields
        if order_data.get('product_type') == 'BO':
            if order_data.get('stop_loss'):
                params['stop_loss'] = float(order_data['stop_loss'])
            if order_data.get('target'):
                params['target'] = float(order_data['target'])
            if order_data.get('trailing_stop_loss'):
                params['trailing_stop_loss'] = float(order_data['trailing_stop_loss'])
        
        # Cover Order fields
        if order_data.get('product_type') == 'CO' and order_data.get('stop_loss'):
            params['stop_loss'] = float(order_data['stop_loss'])
        
        return params
    
    def close_position(self, position, close_data=None):
        """
        Close an open position by placing opposite order.
        
        Args:
            position: Position instance to close
            close_data: Optional dictionary with closing parameters
        
        Returns:
            Dictionary with closing result
        """
        try:
            if not position.is_open:
                return {
                    'success': False,
                    'message': 'Position is already closed'
                }
            
            # Determine opposite transaction type
            opposite_transaction = (
                Order.TRANSACTION_SELL if position.position_type == Position.POSITION_LONG
                else Order.TRANSACTION_BUY
            )
            
            # Prepare order data
            order_data = {
                'exchange': position.exchange,
                'trading_symbol': position.trading_symbol,
                'symbol_token': position.symbol_token,
                'instrument_type': position.instrument_type,
                'transaction_type': opposite_transaction,
                'order_type': close_data.get('order_type', 'MARKET') if close_data else 'MARKET',
                'product_type': position.product_type,
                'quantity': close_data.get('quantity', position.quantity) if close_data else position.quantity,
                'price': close_data.get('price', 0) if close_data else 0,
                'tags': {'closing_position': str(position.id)}
            }
            
            return self.place_order(order_data)
            
        except Exception as e:
            logger.error(f"Close position error: {e}")
            return {
                'success': False,
                'message': 'Failed to close position',
                'error': str(e)
            }
