import api from './api';

/**
 * Messages Service for Freelancers
 * Handles messaging functionality
 */

export const messagesService = {
  /**
   * Get all conversations
   */
  async getConversations(params = {}) {
    try {
      const response = await api.get('/messages/conversations', { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get messages for a conversation
   */
  async getConversationMessages(conversationId, params = {}) {
    try {
      const response = await api.get(
        `/messages/conversation/${conversationId}`,
        { params }
      );
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Send a message
   */
  async sendMessage(conversationId, text, attachments = []) {
    try {
      const response = await api.post('/messages', {
        conversationId,
        text,
        attachments,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Send message to a user (creates conversation if needed)
   */
  async sendMessageToUser(userId, text, attachments = []) {
    try {
      const response = await api.post(`/messages/send/${userId}`, {
        text,
        attachments,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Mark message as read
   */
  async markAsRead(messageId) {
    try {
      const response = await api.put(`/messages/${messageId}/read`);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get unread message count
   */
  async getUnreadCount() {
    try {
      const response = await api.get('/messages/unread-count');
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default messagesService;

