import api from './api';

/**
 * Gigs Service for Freelancers
 * CRUD operations for gigs
 */

export const gigsService = {
  /**
   * Get all gigs for current freelancer
   */
  async getMyGigs(params = {}) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id || user._id;
      
      if (!userId) {
        throw new Error('User not authenticated');
      }
      
      const response = await api.get(`/gigs/user/${userId}`, { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get gig by ID
   */
  async getGigById(id) {
    try {
      const response = await api.get(`/gigs/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create a new gig
   */
  async createGig(gigData) {
    try {
      const response = await api.post('/gigs', gigData);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Update gig
   */
  async updateGig(id, updates) {
    try {
      const response = await api.put(`/gigs/${id}`, updates);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Delete gig
   */
  async deleteGig(id) {
    try {
      const response = await api.delete(`/gigs/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Toggle gig active status
   */
  async toggleGigStatus(id, isActive) {
    try {
      const response = await api.put(`/gigs/${id}`, { isActive });
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default gigsService;

