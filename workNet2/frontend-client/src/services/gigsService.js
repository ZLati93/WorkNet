import api from './api';

/**
 * Gigs Service
 * Handles gig-related API calls
 */

export const gigsService = {
  /**
   * Get all gigs with pagination and filters
   */
  async getGigs(params = {}) {
    try {
      const response = await api.get('/gigs', { params });
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
   * Search gigs
   */
  async searchGigs(query, filters = {}) {
    try {
      const params = {
        search: query,
        ...filters,
      };
      const response = await api.get('/gigs', { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get gigs by category
   */
  async getGigsByCategory(category, params = {}) {
    try {
      const response = await api.get('/gigs', {
        params: {
          category,
          ...params,
        },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get gigs by user ID
   */
  async getGigsByUser(userId, params = {}) {
    try {
      const response = await api.get(`/gigs/user/${userId}`, { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create a new gig (requires authentication)
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
   * Update gig (requires authentication)
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
   * Delete gig (requires authentication)
   */
  async deleteGig(id) {
    try {
      const response = await api.delete(`/gigs/${id}`);
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default gigsService;

