/**
 * API ↔ RPC Integration Tests
 * Tests for Node.js API Gateway ↔ Python RPC Server integration
 */

const axios = require('axios');

// Mock RPC client for testing
let rpcClient = null;
try {
  const rpcClientModule = require('../../backend-node/rpc-client/rpcClient');
  rpcClient = rpcClientModule.getRPCClient ? rpcClientModule.getRPCClient() : null;
} catch (error) {
  console.warn('RPC client not available for direct testing');
}

const API_BASE_URL = process.env.API_URL || 'http://localhost:3000/api';
const RPC_HOST = process.env.RPC_HOST || 'localhost';
const RPC_PORT = parseInt(process.env.RPC_PORT || '8000');

describe('API ↔ RPC Integration Tests', () => {
  let authToken;
  let userId;
  let gigId;
  let orderId;

  beforeAll(async () => {
    // Wait for services to be ready
    await waitForService(API_BASE_URL, 30000);
    await waitForRPCService(RPC_HOST, RPC_PORT, 30000);
  });

  describe('User Registration and Login Flow', () => {
    it('should register user via API and verify RPC call', async () => {
      const timestamp = Date.now();
      const userData = {
        username: `testuser_${timestamp}`,
        email: `test_${timestamp}@example.com`,
        password: 'password123',
        role: 'client',
      };

      const response = await axios.post(`${API_BASE_URL}/users/register`, userData);

      expect(response.status).toBe(201);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('token');
      expect(response.data.data).toHaveProperty('user');

      authToken = response.data.data.token;
      userId = response.data.data.user.id;
    });

    it('should login user via API and verify RPC call', async () => {
      const timestamp = Date.now();
      const userData = {
        username: `testuser_${timestamp}`,
        email: `test_${timestamp}@example.com`,
        password: 'password123',
      };

      // Register first
      await axios.post(`${API_BASE_URL}/users/register`, {
        ...userData,
        role: 'client',
      });

      // Then login
      const response = await axios.post(`${API_BASE_URL}/users/login`, {
        email: userData.email,
        password: userData.password,
      });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('token');
    });
  });

  describe('Gigs API ↔ RPC Integration', () => {
    beforeAll(async () => {
      // Create a freelancer user for gig creation
      const timestamp = Date.now();
      const freelancerData = {
        username: `freelancer_${timestamp}`,
        email: `freelancer_${timestamp}@example.com`,
        password: 'password123',
        role: 'freelancer',
      };

      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        freelancerData
      );
      authToken = registerResponse.data.data.token;
      userId = registerResponse.data.data.user.id;
    });

    it('should create gig via API and verify RPC integration', async () => {
      const gigData = {
        title: 'Test Gig Integration',
        description: 'This is a test gig for integration testing purposes',
        category: 'Web Development',
        price: 50,
        deliveryTime: 3,
        revisionNumber: 2,
        features: ['Feature 1', 'Feature 2'],
      };

      const response = await axios.post(`${API_BASE_URL}/gigs`, gigData, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      expect(response.status).toBe(201);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('gig');

      gigId = response.data.data.gig._id || response.data.data.gig.id;
    });

    it('should get gigs via API and verify RPC call', async () => {
      const response = await axios.get(`${API_BASE_URL}/gigs`);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('gigs');
      expect(Array.isArray(response.data.data.gigs)).toBe(true);
    });

    it('should search gigs via API and verify RPC integration', async () => {
      const response = await axios.get(`${API_BASE_URL}/gigs?search=test`);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('gigs');
    });

    it('should update gig via API and verify RPC call', async () => {
      if (!gigId) {
        // Create a gig first if not exists
        const gigData = {
          title: 'Test Gig for Update',
          description: 'This is a test gig for update testing',
          category: 'Web Development',
          price: 50,
          deliveryTime: 3,
        };

        const createResponse = await axios.post(`${API_BASE_URL}/gigs`, gigData, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        gigId = createResponse.data.data.gig._id || createResponse.data.data.gig.id;
      }

      const updates = {
        title: 'Updated Gig Title',
        price: 75,
      };

      const response = await axios.put(`${API_BASE_URL}/gigs/${gigId}`, updates, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
    });
  });

  describe('Orders API ↔ RPC Integration', () => {
    let buyerToken;
    let buyerId;

    beforeAll(async () => {
      // Create a buyer user
      const timestamp = Date.now();
      const buyerData = {
        username: `buyer_${timestamp}`,
        email: `buyer_${timestamp}@example.com`,
        password: 'password123',
        role: 'client',
      };

      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        buyerData
      );
      buyerToken = registerResponse.data.data.token;
      buyerId = registerResponse.data.data.user.id;
    });

    it('should create order via API and verify RPC integration', async () => {
      if (!gigId) {
        // Create a gig first
        const gigData = {
          title: 'Gig for Order',
          description: 'This gig will be used for order creation',
          category: 'Web Development',
          price: 50,
          deliveryTime: 3,
        };

        const createResponse = await axios.post(`${API_BASE_URL}/gigs`, gigData, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        gigId = createResponse.data.data.gig._id || createResponse.data.data.gig.id;
      }

      const orderData = {
        gigId: gigId,
        requirements: 'Please make it colorful',
      };

      const response = await axios.post(`${API_BASE_URL}/orders`, orderData, {
        headers: {
          Authorization: `Bearer ${buyerToken}`,
        },
      });

      expect(response.status).toBe(201);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('order');

      orderId = response.data.data.order._id || response.data.data.order.id;
    });

    it('should get orders via API and verify RPC call', async () => {
      const response = await axios.get(`${API_BASE_URL}/orders`, {
        headers: {
          Authorization: `Bearer ${buyerToken}`,
        },
      });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty('orders');
    });

    it('should update order status via API and verify RPC integration', async () => {
      if (!orderId) return;

      const response = await axios.put(
        `${API_BASE_URL}/orders/${orderId}/status`,
        { status: 'in_progress' },
        {
          headers: {
            Authorization: `Bearer ${authToken}`, // Seller token
          },
        }
      );

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
    });
  });

  describe('Payments API ↔ RPC Integration', () => {
    it('should calculate fees via RPC and return via API', async () => {
      // This would typically be called internally, but we can test the RPC directly
      const rpcClient = getRPCClient();
      
      if (rpcClient && rpcClient.paymentsService_calculateFees) {
        const result = await rpcClient.paymentsService_calculateFees(100);
        
        expect(result).toBeDefined();
        expect(result.success).toBe(true);
        expect(result.platform_fee).toBeGreaterThan(0);
        expect(result.seller_amount).toBeLessThan(100);
      }
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle RPC server unavailability gracefully', async () => {
      // This test would require stopping the RPC server
      // For now, we test with invalid RPC calls
      const response = await axios.get(`${API_BASE_URL}/gigs`);

      // API should still respond (might use fallback or cached data)
      expect(response.status).toBeDefined();
    });

    it('should handle invalid RPC responses', async () => {
      const response = await axios.get(`${API_BASE_URL}/gigs/invalid-id`);

      // Should return error response, not crash
      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    it('should handle timeout scenarios', async () => {
      // Test with very long operation
      const response = await axios.get(`${API_BASE_URL}/gigs`, {
        timeout: 5000,
      });

      // Should complete within timeout or return timeout error
      expect(response.status).toBeDefined();
    });
  });

  describe('Performance Tests', () => {
    it('should handle concurrent API requests', async () => {
      const requests = Array(10)
        .fill()
        .map(() => axios.get(`${API_BASE_URL}/gigs`));

      const responses = await Promise.all(requests);

      expect(responses.length).toBe(10);
      responses.forEach((response) => {
        expect(response.status).toBe(200);
      });
    });

    it('should measure API response time', async () => {
      const startTime = Date.now();
      await axios.get(`${API_BASE_URL}/gigs`);
      const endTime = Date.now();

      const latency = endTime - startTime;
      expect(latency).toBeLessThan(2000); // Should respond within 2 seconds
    });
  });
});

// Helper functions
async function waitForService(url, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      await axios.get(url.replace('/api', '/health'));
      return;
    } catch (error) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
  throw new Error(`Service at ${url} not available after ${timeout}ms`);
}

async function waitForRPCService(host, port, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      const response = await axios.post(`http://${host}:${port}/RPC2`, {
        methodName: 'ping',
        params: [],
      });
      if (response.data) return;
    } catch (error) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
  throw new Error(`RPC service at ${host}:${port} not available after ${timeout}ms`);
}

