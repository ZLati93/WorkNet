import api from './api';

/**
 * Payments Service for Freelancers
 * Handles payment-related operations
 */

export const paymentsService = {
  /**
   * Get all payments
   */
  async getPayments(params = {}) {
    try {
      const response = await api.get('/payments', { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get payment by ID
   */
  async getPaymentById(id) {
    try {
      const response = await api.get(`/payments/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get payment status
   */
  async getPaymentStatus(id) {
    try {
      const response = await api.get(`/payments/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get earnings summary
   */
  async getEarningsSummary(period = 'month') {
    try {
      const payments = await this.getPayments({
        status: 'completed',
      });
      
      if (payments.success && payments.data) {
        const totalEarnings = payments.data.reduce(
          (sum, payment) => sum + (payment.amount || 0),
          0
        );
        
        return {
          success: true,
          totalEarnings,
          paymentCount: payments.data.length,
          period,
        };
      }
      
      return {
        success: true,
        totalEarnings: 0,
        paymentCount: 0,
        period,
      };
    } catch (error) {
      throw error;
    }
  },
};

export default paymentsService;

