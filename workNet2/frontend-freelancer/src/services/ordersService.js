import api from './api';

/**
 * Orders Service for Freelancers
 */

export const ordersService = {
  async getOrders(params = {}) {
    try {
      const response = await api.get('/orders', {
        params: {
          type: 'seller',
          ...params,
        },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  async getOrderById(id) {
    try {
      const response = await api.get(`/orders/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  async updateOrderStatus(id, status) {
    try {
      const response = await api.put(`/orders/${id}/status`, { status });
      return response;
    } catch (error) {
      throw error;
    }
  },

  async updateOrder(id, updates) {
    try {
      const response = await api.put(`/orders/${id}`, updates);
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default ordersService;

