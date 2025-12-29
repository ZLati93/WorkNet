/**
 * RPC Client for WorkNet
 * XML-RPC client for communicating with Python RPC server
 */

const xmlrpc = require('xmlrpc');
const { EventEmitter } = require('events');

class RPCClient extends EventEmitter {
  constructor(config = {}) {
    super();
    
    // Configuration
    this.config = {
      host: config.host || process.env.RPC_HOST || 'localhost',
      port: config.port || parseInt(process.env.RPC_PORT) || 8000,
      path: config.path || '/RPC2',
      timeout: config.timeout || 10000, // 10 seconds default
      retries: config.retries || 3,
      retryDelay: config.retryDelay || 1000, // 1 second
      ...config
    };

    // Create XML-RPC client
    this.client = xmlrpc.createClient({
      host: this.config.host,
      port: this.config.port,
      path: this.config.path,
      basic_auth: config.basic_auth || null,
      headers: config.headers || {}
    });

    // Connection state
    this.isConnected = false;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;

    // Statistics
    this.stats = {
      totalCalls: 0,
      successfulCalls: 0,
      failedCalls: 0,
      retries: 0
    };

    // Initialize connection
    this.initialize();
  }

  /**
   * Initialize RPC client connection
   */
  async initialize() {
    try {
      // Test connection with a ping
      await this.callMethod('ping', [], { skipRetry: true });
      this.isConnected = true;
      this.emit('connected');
      console.log(`RPC Client connected to ${this.config.host}:${this.config.port}`);
    } catch (error) {
      this.isConnected = false;
      this.emit('error', error);
      console.warn('RPC Client initialization failed:', error.message);
      // Don't throw - allow graceful degradation
    }
  }

  /**
   * Generic method to call any RPC method with retry logic
   * @param {string} method - RPC method name
   * @param {Array} params - Method parameters
   * @param {Object} options - Options (timeout, retries, skipRetry)
   * @returns {Promise} - Promise resolving to RPC response
   */
  async callMethod(method, params = [], options = {}) {
    const timeout = options.timeout || this.config.timeout;
    const retries = options.skipRetry ? 0 : (options.retries !== undefined ? options.retries : this.config.retries);
    const retryDelay = options.retryDelay || this.config.retryDelay;

    this.stats.totalCalls++;

    let lastError;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const result = await this._executeCall(method, params, timeout);
        this.stats.successfulCalls++;
        this.isConnected = true;
        return result;
      } catch (error) {
        lastError = error;
        this.stats.failedCalls++;
        
        if (attempt < retries) {
          this.stats.retries++;
          const delay = retryDelay * Math.pow(2, attempt); // Exponential backoff
          console.warn(`RPC call failed (${method}), retrying in ${delay}ms... (attempt ${attempt + 1}/${retries})`);
          await this._sleep(delay);
        } else {
          this.isConnected = false;
          this.emit('error', error);
          throw this._formatError(error, method, params);
        }
      }
    }
  }

  /**
   * Execute RPC call with timeout
   * @private
   */
  _executeCall(method, params, timeout) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`RPC call timeout after ${timeout}ms`));
      }, timeout);

      this.client.methodCall(method, params, (error, value) => {
        clearTimeout(timer);
        
        if (error) {
          reject(error);
        } else {
          resolve(value);
        }
      });
    });
  }

  /**
   * Format error for better error handling
   * @private
   */
  _formatError(error, method, params) {
    const rpcError = new Error(`RPC Error: ${method} - ${error.message}`);
    rpcError.name = 'RPCError';
    rpcError.method = method;
    rpcError.params = params;
    rpcError.originalError = error;
    return rpcError;
  }

  /**
   * Sleep utility for retry delays
   * @private
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ==================== User Service Methods ====================

  /**
   * User service - Create user
   */
  async usersService_create(userId, username, email, role) {
    return this.callMethod('usersService.create', [userId, username, email, role]);
  }

  /**
   * User service - Update user
   */
  async usersService_update(userId, updates) {
    return this.callMethod('usersService.update', [userId, updates]);
  }

  /**
   * User service - Delete user
   */
  async usersService_delete(userId) {
    return this.callMethod('usersService.delete', [userId]);
  }

  /**
   * User service - Get user stats
   */
  async usersService_getStats(userId) {
    return this.callMethod('usersService.getStats', [userId]);
  }

  // ==================== Gig Service Methods ====================

  /**
   * Gig service - Create gig
   */
  async gigsService_create(gigId, userId, title) {
    return this.callMethod('gigsService.create', [gigId, userId, title]);
  }

  /**
   * Gig service - Update gig
   */
  async gigsService_update(gigId, updates) {
    return this.callMethod('gigsService.update', [gigId, updates]);
  }

  /**
   * Gig service - Delete gig
   */
  async gigsService_delete(gigId) {
    return this.callMethod('gigsService.delete', [gigId]);
  }

  /**
   * Gig service - Search gigs
   */
  async gigsService_search(query, filters) {
    return this.callMethod('gigsService.search', [query, filters]);
  }

  /**
   * Gig service - Update gig rating
   */
  async gigsService_updateRating(gigId) {
    return this.callMethod('gigsService.updateRating', [gigId]);
  }

  // ==================== Order Service Methods ====================

  /**
   * Order service - Create order
   */
  async ordersService_create(orderId, gigId, buyerId) {
    return this.callMethod('ordersService.create', [orderId, gigId, buyerId]);
  }

  /**
   * Order service - Update order status
   */
  async ordersService_updateStatus(orderId, status) {
    return this.callMethod('ordersService.updateStatus', [orderId, status]);
  }

  /**
   * Order service - Get order analytics
   */
  async ordersService_getAnalytics(userId, period) {
    return this.callMethod('ordersService.getAnalytics', [userId, period]);
  }

  /**
   * Order service - Cancel order
   */
  async ordersService_cancel(orderId, reason) {
    return this.callMethod('ordersService.cancel', [orderId, reason]);
  }

  // ==================== Category Service Methods ====================

  /**
   * Category service - Create category
   */
  async categoriesService_create(categoryId, name, slug) {
    return this.callMethod('categoriesService.create', [categoryId, name, slug]);
  }

  /**
   * Category service - Update category
   */
  async categoriesService_update(categoryId, updates) {
    return this.callMethod('categoriesService.update', [categoryId, updates]);
  }

  /**
   * Category service - Delete category
   */
  async categoriesService_delete(categoryId) {
    return this.callMethod('categoriesService.delete', [categoryId]);
  }

  /**
   * Category service - Get category stats
   */
  async categoriesService_getStats(categoryId) {
    return this.callMethod('categoriesService.getStats', [categoryId]);
  }

  // ==================== Review Service Methods ====================

  /**
   * Review service - Create review
   */
  async reviewsService_create(reviewId, gigId, rating) {
    return this.callMethod('reviewsService.create', [reviewId, gigId, rating]);
  }

  /**
   * Review service - Update review
   */
  async reviewsService_update(reviewId, updates) {
    return this.callMethod('reviewsService.update', [reviewId, updates]);
  }

  /**
   * Review service - Delete review
   */
  async reviewsService_delete(reviewId) {
    return this.callMethod('reviewsService.delete', [reviewId]);
  }

  /**
   * Review service - Calculate average rating
   */
  async reviewsService_calculateRating(gigId) {
    return this.callMethod('reviewsService.calculateRating', [gigId]);
  }

  // ==================== Message Service Methods ====================

  /**
   * Message service - Create message
   */
  async messagesService_create(messageId, conversationId, senderId) {
    return this.callMethod('messagesService.create', [messageId, conversationId, senderId]);
  }

  /**
   * Message service - Mark as read
   */
  async messagesService_markAsRead(messageId) {
    return this.callMethod('messagesService.markAsRead', [messageId]);
  }

  /**
   * Message service - Get unread count
   */
  async messagesService_getUnreadCount(userId) {
    return this.callMethod('messagesService.getUnreadCount', [userId]);
  }

  // ==================== Payment Service Methods ====================

  /**
   * Payment service - Create payment
   */
  async paymentsService_create(paymentId, orderId, amount, paymentMethod) {
    return this.callMethod('paymentsService.create', [paymentId, orderId, amount, paymentMethod]);
  }

  /**
   * Payment service - Process payment
   */
  async paymentsService_process(paymentId, status) {
    return this.callMethod('paymentsService.process', [paymentId, status]);
  }

  /**
   * Payment service - Refund payment
   */
  async paymentsService_refund(paymentId, amount) {
    return this.callMethod('paymentsService.refund', [paymentId, amount]);
  }

  /**
   * Payment service - Get payment status
   */
  async paymentsService_getStatus(paymentId) {
    return this.callMethod('paymentsService.getStatus', [paymentId]);
  }

  // ==================== Notification Service Methods ====================

  /**
   * Notification service - Create notification
   */
  async notificationsService_create(notificationId, userId, type) {
    return this.callMethod('notificationsService.create', [notificationId, userId, type]);
  }

  /**
   * Notification service - Mark as read
   */
  async notificationsService_markAsRead(notificationId) {
    return this.callMethod('notificationsService.markAsRead', [notificationId]);
  }

  /**
   * Notification service - Get unread count
   */
  async notificationsService_getUnreadCount(userId) {
    return this.callMethod('notificationsService.getUnreadCount', [userId]);
  }

  /**
   * Notification service - Send bulk notification
   */
  async notificationsService_sendBulk(userIds, type, message) {
    return this.callMethod('notificationsService.sendBulk', [userIds, type, message]);
  }

  // ==================== Utility Methods ====================

  /**
   * Health check - Ping RPC server
   */
  async ping() {
    try {
      return await this.callMethod('ping', [], { skipRetry: true, timeout: 5000 });
    } catch (error) {
      return { status: 'error', message: error.message };
    }
  }

  /**
   * Get RPC client statistics
   */
  getStats() {
    return {
      ...this.stats,
      isConnected: this.isConnected,
      successRate: this.stats.totalCalls > 0 
        ? ((this.stats.successfulCalls / this.stats.totalCalls) * 100).toFixed(2) + '%'
        : '0%'
    };
  }

  /**
   * Reset statistics
   */
  resetStats() {
    this.stats = {
      totalCalls: 0,
      successfulCalls: 0,
      failedCalls: 0,
      retries: 0
    };
  }

  /**
   * Close RPC client connection
   */
  close() {
    this.isConnected = false;
    this.emit('close');
    // XML-RPC client doesn't have explicit close method
    // Connection will be closed when process exits
  }

  /**
   * Reconnect to RPC server
   */
  async reconnect() {
    this.close();
    await this._sleep(1000);
    await this.initialize();
  }
}

// Create singleton instance
let rpcClientInstance = null;

/**
 * Get or create RPC client instance
 * @param {Object} config - Configuration object
 * @returns {RPCClient} - RPC client instance
 */
function getRPCClient(config = {}) {
  if (!rpcClientInstance) {
    rpcClientInstance = new RPCClient(config);
  }
  return rpcClientInstance;
}

/**
 * Create new RPC client instance
 * @param {Object} config - Configuration object
 * @returns {RPCClient} - New RPC client instance
 */
function createRPCClient(config = {}) {
  return new RPCClient(config);
}

// Export
module.exports = {
  RPCClient,
  getRPCClient,
  createRPCClient,
  // Convenience methods for backward compatibility
  callRPC: (method, params, options) => {
    const client = getRPCClient();
    return client.callMethod(method, params, options);
  }
};

