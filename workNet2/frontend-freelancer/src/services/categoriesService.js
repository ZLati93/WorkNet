import api from './api';

/**
 * Categories Service
 */

export const categoriesService = {
  async getCategories(params = {}) {
    try {
      const response = await api.get('/categories', { params });
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default categoriesService;

