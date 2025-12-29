#!/usr/bin/env python3
"""
WorkNet RPC Server (XML-RPC)
Python XML-RPC server for WorkNet platform
"""

import os
import sys
import logging
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from socketserver import ThreadingMixIn
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpc_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
RPC_PORT = int(os.getenv('RPC_PORT', '8000'))
RPC_HOST = os.getenv('RPC_HOST', '0.0.0.0')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority')
DB_NAME = os.getenv('DB_NAME', 'worknet')

# MongoDB connection
mongodb_client = None
db = None

def connect_mongodb():
    """Connect to MongoDB"""
    global mongodb_client, db
    try:
        mongodb_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongodb_client.admin.command('ping')
        db = mongodb_client[DB_NAME]
        logger.info(f"✓ Connected to MongoDB: {DB_NAME}")
        return True
    except ConnectionFailure as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        return False

# Threading XML-RPC Server
class ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """Threading XML-RPC Server"""
    pass

# Request handler with CORS support
class CORSRequestHandler(SimpleXMLRPCRequestHandler):
    """Request handler with CORS support"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

# Import services
try:
    from services.users_service import UsersService
    from services.gigs_service import GigsService
    from services.orders_service import OrdersService
    from services.categories_service import CategoriesService
    from services.reviews_service import ReviewsService
    from services.messages_service import MessagesService
    from services.payments_service import PaymentsService
    from services.notifications_service import NotificationsService
except ImportError as e:
    logger.warning(f"Some services not available: {e}")
    # Create placeholder services
    class UsersService:
        pass
    class GigsService:
        pass
    class OrdersService:
        pass
    class CategoriesService:
        pass
    class ReviewsService:
        pass
    class MessagesService:
        pass
    class PaymentsService:
        pass
    class NotificationsService:
        pass

class WorkNetRPCServer:
    """WorkNet RPC Server"""
    
    def __init__(self):
        self.server = None
        self.services = {}
        
    def initialize_services(self):
        """Initialize all RPC services"""
        try:
            # Initialize services with database connection
            self.services['users'] = UsersService(db) if db else UsersService(None)
            self.services['gigs'] = GigsService(db) if db else GigsService(None)
            self.services['orders'] = OrdersService(db) if db else OrdersService(None)
            self.services['categories'] = CategoriesService(db) if db else CategoriesService(None)
            self.services['reviews'] = ReviewsService(db) if db else ReviewsService(None)
            self.services['messages'] = MessagesService(db) if db else MessagesService(None)
            self.services['payments'] = PaymentsService(db) if db else PaymentsService(None)
            self.services['notifications'] = NotificationsService(db) if db else NotificationsService(None)
            
            logger.info("✓ All services initialized")
        except Exception as e:
            logger.error(f"✗ Error initializing services: {e}")
    
    def register_services(self):
        """Register all RPC methods"""
        # Users Service
        self.server.register_function(self.services['users'].create, 'usersService.create')
        self.server.register_function(self.services['users'].update, 'usersService.update')
        self.server.register_function(self.services['users'].delete, 'usersService.delete')
        self.server.register_function(self.services['users'].get_stats, 'usersService.getStats')
        
        # Gigs Service
        self.server.register_function(self.services['gigs'].create, 'gigsService.create')
        self.server.register_function(self.services['gigs'].update, 'gigsService.update')
        self.server.register_function(self.services['gigs'].delete, 'gigsService.delete')
        self.server.register_function(self.services['gigs'].search, 'gigsService.search')
        self.server.register_function(self.services['gigs'].update_rating, 'gigsService.updateRating')
        
        # Orders Service
        self.server.register_function(self.services['orders'].create, 'ordersService.create')
        self.server.register_function(self.services['orders'].update_status, 'ordersService.updateStatus')
        self.server.register_function(self.services['orders'].get_analytics, 'ordersService.getAnalytics')
        self.server.register_function(self.services['orders'].cancel, 'ordersService.cancel')
        
        # Categories Service
        self.server.register_function(self.services['categories'].create, 'categoriesService.create')
        self.server.register_function(self.services['categories'].update, 'categoriesService.update')
        self.server.register_function(self.services['categories'].delete, 'categoriesService.delete')
        self.server.register_function(self.services['categories'].get_stats, 'categoriesService.getStats')
        
        # Reviews Service
        self.server.register_function(self.services['reviews'].create, 'reviewsService.create')
        self.server.register_function(self.services['reviews'].update, 'reviewsService.update')
        self.server.register_function(self.services['reviews'].delete, 'reviewsService.delete')
        self.server.register_function(self.services['reviews'].calculate_rating, 'reviewsService.calculateRating')
        
        # Messages Service
        self.server.register_function(self.services['messages'].create, 'messagesService.create')
        self.server.register_function(self.services['messages'].mark_as_read, 'messagesService.markAsRead')
        self.server.register_function(self.services['messages'].get_unread_count, 'messagesService.getUnreadCount')
        
        # Payments Service
        self.server.register_function(self.services['payments'].create, 'paymentsService.create')
        self.server.register_function(self.services['payments'].process, 'paymentsService.process')
        self.server.register_function(self.services['payments'].refund, 'paymentsService.refund')
        self.server.register_function(self.services['payments'].get_status, 'paymentsService.getStatus')
        
        # Notifications Service
        self.server.register_function(self.services['notifications'].create, 'notificationsService.create')
        self.server.register_function(self.services['notifications'].mark_as_read, 'notificationsService.markAsRead')
        self.server.register_function(self.services['notifications'].get_unread_count, 'notificationsService.getUnreadCount')
        self.server.register_function(self.services['notifications'].send_bulk, 'notificationsService.sendBulk')
        
        # Health check
        self.server.register_function(self.ping, 'ping')
        
        logger.info("✓ All RPC methods registered")
    
    def ping(self):
        """Health check endpoint"""
        return {
            'status': 'ok',
            'message': 'RPC Server is running',
            'mongodb_connected': db is not None
        }
    
    def start(self):
        """Start the RPC server"""
        try:
            # Connect to MongoDB
            if not connect_mongodb():
                logger.warning("Starting server without MongoDB connection")
            
            # Initialize services
            self.initialize_services()
            
            # Create server
            self.server = ThreadingXMLRPCServer(
                (RPC_HOST, RPC_PORT),
                requestHandler=CORSRequestHandler,
                allow_none=True,
                use_builtin_types=True
            )
            
            # Register services
            self.register_services()
            
            # Enable introspection
            self.server.register_introspection_functions()
            
            logger.info(f"✓ RPC Server started on {RPC_HOST}:{RPC_PORT}")
            logger.info(f"✓ Server ready to accept requests")
            
            # Start serving
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("Shutting down RPC server...")
            self.shutdown()
        except Exception as e:
            logger.error(f"✗ Server error: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the server"""
        if self.server:
            self.server.shutdown()
        if mongodb_client:
            mongodb_client.close()
        logger.info("✓ Server shut down gracefully")

def main():
    """Main function"""
    server = WorkNetRPCServer()
    try:
        server.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
