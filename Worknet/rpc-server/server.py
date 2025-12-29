#!/usr/bin/env python3
"""
WorkNet XML-RPC Server
A freelance marketplace XML-RPC server with dynamic service registration,
MongoDB integration, and proper authentication error handling.
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable
from functools import wraps
import logging
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import Fault
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

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

# Load environment variables
load_dotenv()


class AuthenticatedXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for authenticated XML-RPC requests"""
    
    def log_request(self, code='-', size='-'):
        """Override to use custom logger"""
        logger.info(f"{self.client_address[0]} - - [{self.log_date_time_string()}] \"{self.requestline}\" {code} {size}")


class DatabaseError(Fault):
    """Custom exception for database errors"""
    pass


class ServiceRegistry:
    """Registry for dynamically loaded RPC services"""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.methods: Dict[str, Callable] = {}
    
    def register_service(self, service_instance: Any):
        """Register a service instance and its methods"""
        service_name = service_instance.__class__.__name__
        
        # Get all public methods (not starting with _)
        methods = inspect.getmembers(service_instance, predicate=inspect.ismethod)
        
        for method_name, method in methods:
            if not method_name.startswith('_'):
                # Create a namespaced method name: ServiceName.method_name
                namespaced_name = f"{service_name}.{method_name}"
                self.methods[namespaced_name] = method
                logger.info(f"Registered method: {namespaced_name}")
        
        self.services[service_name] = service_instance
        logger.info(f"Registered service: {service_name}")
    
    def get_method(self, method_name: str) -> Callable:
        """Get a registered method by name"""
        return self.methods.get(method_name)
    
    def list_methods(self) -> list:
        """List all available methods"""
        return list(self.methods.keys())


class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # MongoDB connection string
            connection_string = "mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority"
            
            # Extract database name from connection string
            # MongoDB URLs format: mongodb+srv://user:pass@host/dbname
            if '/' in connection_string:
                db_name = connection_string.split('/')[-1].split('?')[0] or 'WorkNetBD'
            else:
                db_name = 'WorkNetBD'
            
            # Connect to MongoDB
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[db_name]
            
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise DatabaseError(500, f"Database connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise DatabaseError(500, f"Database error: {str(e)}")
    
    def get_database(self):
        """Get the database instance"""
        if self.db is None:
            raise DatabaseError(500, "Database not connected")
        return self.db
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


class WorkNetRPCServer:
    """Main XML-RPC server for WorkNet"""
    
    def __init__(self, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self.registry = ServiceRegistry()
        self.db_connection = MongoDBConnection()
        self.server = None
        
        # Load and register services dynamically
        self._load_services()
        
        # Setup server
        self._setup_server()
    
    def _load_services(self):
        """Dynamically load and register services from services directory"""
        # Add the rpc-server directory to Python path
        rpc_server_dir = Path(__file__).parent
        if str(rpc_server_dir) not in sys.path:
            sys.path.insert(0, str(rpc_server_dir))
        
        services_dir = rpc_server_dir / 'services'
        
        # List of service modules to load
        service_modules = [
            'users_service',
            'gigs_service',
            'orders_service',
            'payments_service'
        ]
        
        db = self.db_connection.get_database()
        
        for module_name in service_modules:
            try:
                # Import the service module
                module_path = f"services.{module_name}"
                module = importlib.import_module(module_path)
                
                # Look for a Service class in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a service class (has methods and is not a base class)
                    # Skip BaseService itself and only process classes defined in this module
                    if (name.endswith('Service') and name != 'BaseService' and 
                        obj.__module__ == module.__name__):
                        # Try to instantiate the service with database connection
                        try:
                            # Check if constructor accepts db parameter
                            sig = inspect.signature(obj.__init__)
                            params = list(sig.parameters.keys())[1:]  # Skip 'self'
                            
                            if 'db' in params:
                                service_instance = obj(db=db)
                            elif len(params) == 1:
                                service_instance = obj(db)
                            else:
                                service_instance = obj(db)
                            
                            self.registry.register_service(service_instance)
                            logger.info(f"Successfully loaded service: {name} from {module_name}")
                        except TypeError as e:
                            logger.warning(f"Could not instantiate {name} from {module_name}: {e}")
                        except Exception as e:
                            logger.warning(f"Could not instantiate {name} from {module_name}: {e}")
                
            except ImportError as e:
                logger.warning(f"Could not import service module {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error loading service {module_name}: {e}")
    
    def _setup_server(self):
        """Setup the XML-RPC server"""
        try:
            self.server = SimpleXMLRPCServer(
                (self.host, self.port),
                requestHandler=AuthenticatedXMLRPCRequestHandler,
                allow_none=True,
                use_builtin_types=True
            )
            
            # Register system methods
            self.server.register_function(self.list_methods, 'system.listMethods')
            self.server.register_function(self.method_signature, 'system.methodSignature')
            self.server.register_function(self.method_help, 'system.methodHelp')
            
            # Register custom dispatcher using register_instance
            # This allows dynamic method lookup via __getattr__
            self.server.register_instance(self)
            
            logger.info(f"XML-RPC server initialized on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to setup server: {e}")
            raise
    
    def __getattr__(self, method_name: str):
        """
        Dynamic method lookup for XML-RPC.
        This is called by register_instance when a method is not found directly.
        """
        # Skip system methods
        if method_name.startswith('_') or method_name in ['list_methods', 'method_signature', 'method_help']:
            raise AttributeError(f"Method '{method_name}' not found")
        
        # Get the method from registry
        method = self.registry.get_method(method_name)
        
        if method is None:
            # Try to handle as a direct method call
            if hasattr(self, method_name):
                return getattr(self, method_name)
            else:
                raise AttributeError(f"Method '{method_name}' not found")
        
        # Return a wrapper that handles errors
        def method_wrapper(*args, **kwargs):
            """Wrapper to handle errors consistently"""
            try:
                # Execute the method with parameters
                if kwargs:
                    result = method(*args, **kwargs)
                elif args:
                    result = method(*args)
                else:
                    result = method()
                return result
                
            except Fault as e:
                # Re-raise XML-RPC Faults as-is (includes AuthenticationError, DatabaseError, etc.)
                # Log based on fault code
                if e.faultCode == 401:
                    logger.warning(f"Authentication error in {method_name}: {e}")
                elif e.faultCode == 500:
                    logger.error(f"Server error in {method_name}: {e}")
                else:
                    logger.error(f"Fault in {method_name}: {e}")
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error in {method_name}: {e}", exc_info=True)
                raise Fault(500, f"Internal server error: {str(e)}")
        
        return method_wrapper
    
    def list_methods(self):
        """List all available methods (system method)"""
        return self.registry.list_methods()
    
    def method_signature(self, method_name: str):
        """Get method signature (system method)"""
        method = self.registry.get_method(method_name)
        if method is None:
            raise Fault(404, f"Method '{method_name}' not found")
        # Return signature format: [[return_type, param1_type, param2_type, ...], ...]
        return 'undef'
    
    def method_help(self, method_name: str):
        """Get method help (system method)"""
        method = self.registry.get_method(method_name)
        if method is None:
            raise Fault(404, f"Method '{method_name}' not found")
        # Return docstring if available
        return inspect.getdoc(method) or f"Help for {method_name}"
    
    def serve_forever(self):
        """Start the server and serve forever"""
        try:
            logger.info(f"Starting WorkNet XML-RPC server on {self.host}:{self.port}")
            logger.info(f"Available methods: {', '.join(self.registry.list_methods())}")
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the server gracefully"""
        logger.info("Shutting down server...")
        if self.server:
            self.server.shutdown()
        if self.db_connection:
            self.db_connection.close()
        logger.info("Server shutdown complete")


def create_auth_middleware(required_role=None):
    """
    Decorator factory for authentication middleware
    
    Args:
        required_role: Optional role requirement ('client', 'freelancer', 'admin')
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token from arguments (assuming first or last arg is token)
            # This is a simplified version - adjust based on your auth implementation
            token = kwargs.get('token') or (args[0] if args else None)
            
            if not token:
                raise AuthenticationError(401, "Authentication token required")
            
            # TODO: Implement token validation using JWT or session management
            # For now, this is a placeholder
            
            # If role is required, validate it
            if required_role:
                # TODO: Extract role from token and validate
                pass
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def main():
    """Main entry point"""
    # Get server configuration from environment
    # Support both RPC_HOST/RPC_PORT and RPC_SERVER_HOST/RPC_SERVER_PORT for flexibility
    host = os.getenv('RPC_HOST', os.getenv('RPC_SERVER_HOST', '0.0.0.0'))
    port = int(os.getenv('RPC_PORT', os.getenv('RPC_SERVER_PORT', 8000)))
    
    try:
        # Create and start server
        server = WorkNetRPCServer(host=host, port=port)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

