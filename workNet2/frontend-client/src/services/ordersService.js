import api from './api';

/**
 * Orders Service
 * Handles order-related API calls
 */

export const ordersService = {
  /**
   * Get all orders for current user
   */
  async getOrders(params = {}) {
    try {
      const response = await api.get('/orders', { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get orders by type (buyer or seller)
   */
  async getOrdersByType(type, params = {}) {
    try {
      const response = await api.get('/orders', {
        params: {
          type,
          ...params,
        },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get order by ID
   */
  async getOrderById(id) {
    try {
      const response = await api.get(`/orders/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create a new order
   */
  async createOrder(orderData) {
    try {
      const response = await api.post('/orders', orderData);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Update order status
   */
  async updateOrderStatus(id, status) {
    try {
      const response = await api.put(`/orders/${id}/status`, { status });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Update order
   */
  async updateOrder(id, updates) {
    try {
      const response = await api.put(`/orders/${id}`, updates);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Cancel order
   */
  async cancelOrder(id, reason) {
    try {
      const response = await api.put(`/orders/${id}/status`, {
        status: 'cancelled',
        reason,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default ordersService;

