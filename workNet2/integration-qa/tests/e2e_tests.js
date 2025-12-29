/**
 * End-to-End Tests
 * Complete integration tests for the entire WorkNet platform
 */

const axios = require('axios');

// Optional: Playwright for browser tests (install if needed)
let playwright = null;
try {
  playwright = require('playwright');
} catch (error) {
  console.warn('Playwright not available, browser tests will be skipped');
}

const API_BASE_URL = process.env.API_URL || 'http://localhost:3000/api';
const CLIENT_URL = process.env.CLIENT_URL || 'http://localhost:3000';
const FREELANCER_URL = process.env.FREELANCER_URL || 'http://localhost:3001';

describe('End-to-End Tests', () => {
  let browser;
  let clientPage;
  let freelancerPage;
  let clientToken;
  let freelancerToken;
  let clientUserId;
  let freelancerUserId;
  let gigId;
  let orderId;

  beforeAll(async () => {
    // Wait for services
    await waitForService(API_BASE_URL, 60000);
    
    // Launch browser if Playwright is available
    if (playwright && playwright.chromium) {
      browser = await playwright.chromium.launch({ headless: true });
    }
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    if (browser) {
      clientPage = await browser.newPage();
      freelancerPage = await browser.newPage();
    }
  });

  afterEach(async () => {
    if (clientPage) await clientPage.close();
    if (freelancerPage) await freelancerPage.close();
  });

  describe('Complete User Journey - Client', () => {
    it('should complete full client journey: register → search → order', async () => {
      const timestamp = Date.now();
      const userData = {
        username: `client_${timestamp}`,
        email: `client_${timestamp}@example.com`,
        password: 'password123',
        role: 'client',
      };

      // 1. Register client
      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        userData
      );
      expect(registerResponse.status).toBe(201);
      clientToken = registerResponse.data.data.token;
      clientUserId = registerResponse.data.data.user.id;

      // 2. Login client
      const loginResponse = await axios.post(`${API_BASE_URL}/users/login`, {
        email: userData.email,
        password: userData.password,
      });
      expect(loginResponse.status).toBe(200);
      expect(loginResponse.data.data.token).toBeDefined();

      // 3. Search for gigs
      const searchResponse = await axios.get(
        `${API_BASE_URL}/gigs?search=design&page=1&limit=10`
      );
      expect(searchResponse.status).toBe(200);
      expect(searchResponse.data.data.gigs).toBeDefined();

      // 4. Get gig details
      if (searchResponse.data.data.gigs.length > 0) {
        const firstGig = searchResponse.data.data.gigs[0];
        const gigDetailsResponse = await axios.get(
          `${API_BASE_URL}/gigs/${firstGig._id || firstGig.id}`
        );
        expect(gigDetailsResponse.status).toBe(200);
        expect(gigDetailsResponse.data.data.title).toBeDefined();
      }
    });
  });

  describe('Complete User Journey - Freelancer', () => {
    it('should complete full freelancer journey: register → create gig → manage orders', async () => {
      const timestamp = Date.now();
      const freelancerData = {
        username: `freelancer_${timestamp}`,
        email: `freelancer_${timestamp}@example.com`,
        password: 'password123',
        role: 'freelancer',
      };

      // 1. Register freelancer
      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        freelancerData
      );
      expect(registerResponse.status).toBe(201);
      freelancerToken = registerResponse.data.data.token;
      freelancerUserId = registerResponse.data.data.user.id;

      // 2. Create gig
      const gigData = {
        title: 'E2E Test Gig',
        description: 'This is a gig created during end-to-end testing',
        category: 'Web Development',
        price: 100,
        deliveryTime: 5,
        revisionNumber: 3,
        features: ['Responsive Design', 'SEO Optimized'],
      };

      const createGigResponse = await axios.post(
        `${API_BASE_URL}/gigs`,
        gigData,
        {
          headers: {
            Authorization: `Bearer ${freelancerToken}`,
          },
        }
      );
      expect(createGigResponse.status).toBe(201);
      gigId = createGigResponse.data.data.gig._id || createGigResponse.data.data.gig.id;

      // 3. Get freelancer's gigs
      const myGigsResponse = await axios.get(
        `${API_BASE_URL}/gigs/user/${freelancerUserId}`,
        {
          headers: {
            Authorization: `Bearer ${freelancerToken}`,
          },
        }
      );
      expect(myGigsResponse.status).toBe(200);
      expect(myGigsResponse.data.data.gigs.length).toBeGreaterThan(0);
    });
  });

  describe('Complete Order Flow', () => {
    beforeAll(async () => {
      // Setup: Create client and freelancer
      const timestamp = Date.now();

      // Create freelancer
      const freelancerData = {
        username: `freelancer_e2e_${timestamp}`,
        email: `freelancer_e2e_${timestamp}@example.com`,
        password: 'password123',
        role: 'freelancer',
      };
      const freelancerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        freelancerData
      );
      freelancerToken = freelancerResponse.data.data.token;
      freelancerUserId = freelancerResponse.data.data.user.id;

      // Create gig
      const gigData = {
        title: 'E2E Order Test Gig',
        description: 'Gig for end-to-end order testing',
        category: 'Graphic Design',
        price: 75,
        deliveryTime: 3,
      };
      const gigResponse = await axios.post(`${API_BASE_URL}/gigs`, gigData, {
        headers: { Authorization: `Bearer ${freelancerToken}` },
      });
      gigId = gigResponse.data.data.gig._id || gigResponse.data.data.gig.id;

      // Create client
      const clientData = {
        username: `client_e2e_${timestamp}`,
        email: `client_e2e_${timestamp}@example.com`,
        password: 'password123',
        role: 'client',
      };
      const clientResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        clientData
      );
      clientToken = clientResponse.data.data.token;
      clientUserId = clientResponse.data.data.user.id;
    });

    it('should complete full order lifecycle', async () => {
      // 1. Client creates order
      const orderData = {
        gigId: gigId,
        requirements: 'Please make it modern and clean',
      };

      const createOrderResponse = await axios.post(
        `${API_BASE_URL}/orders`,
        orderData,
        {
          headers: {
            Authorization: `Bearer ${clientToken}`,
          },
        }
      );
      expect(createOrderResponse.status).toBe(201);
      orderId = createOrderResponse.data.data.order._id || createOrderResponse.data.data.order.id;

      // 2. Freelancer views order
      const freelancerOrdersResponse = await axios.get(
        `${API_BASE_URL}/orders?type=seller`,
        {
          headers: {
            Authorization: `Bearer ${freelancerToken}`,
          },
        }
      );
      expect(freelancerOrdersResponse.status).toBe(200);
      expect(freelancerOrdersResponse.data.data.orders.length).toBeGreaterThan(0);

      // 3. Freelancer updates order status to in_progress
      const updateStatusResponse = await axios.put(
        `${API_BASE_URL}/orders/${orderId}/status`,
        { status: 'in_progress' },
        {
          headers: {
            Authorization: `Bearer ${freelancerToken}`,
          },
        }
      );
      expect(updateStatusResponse.status).toBe(200);

      // 4. Client views order status
      const clientOrdersResponse = await axios.get(
        `${API_BASE_URL}/orders?type=buyer`,
        {
          headers: {
            Authorization: `Bearer ${clientToken}`,
          },
        }
      );
      expect(clientOrdersResponse.status).toBe(200);
      const order = clientOrdersResponse.data.data.orders.find(
        (o) => (o._id || o.id) === orderId
      );
      expect(order.status).toBe('in_progress');

      // 5. Freelancer completes order
      const completeResponse = await axios.put(
        `${API_BASE_URL}/orders/${orderId}/status`,
        { status: 'completed' },
        {
          headers: {
            Authorization: `Bearer ${freelancerToken}`,
          },
        }
      );
      expect(completeResponse.status).toBe(200);
    });
  });

  describe('Frontend Integration Tests', () => {
    it('should load client homepage', async () => {
      if (!clientPage) {
        console.log('Skipping browser test - Playwright not available');
        return;
      }

      await clientPage.goto(CLIENT_URL);
      await clientPage.waitForSelector('body');

      const title = await clientPage.title();
      expect(title).toContain('WorkNet');

      const heading = await clientPage.textContent('h1, h2');
      expect(heading).toBeTruthy();
    });

    it('should search for gigs on client homepage', async () => {
      if (!clientPage) {
        console.log('Skipping browser test - Playwright not available');
        return;
      }

      await clientPage.goto(CLIENT_URL);
      await clientPage.waitForSelector('input[type="text"]');

      const searchInput = await clientPage.$('input[placeholder*="search" i]');
      if (searchInput) {
        await searchInput.fill('logo design');
        await searchInput.press('Enter');

        // Wait for results or loading state
        await clientPage.waitForTimeout(2000);
      }
    });

    it('should load freelancer dashboard', async () => {
      if (!freelancerPage) {
        console.log('Skipping browser test - Playwright not available');
        return;
      }

      await freelancerPage.goto(`${FREELANCER_URL}/login`);
      await freelancerPage.waitForSelector('body');

      // Should redirect to login if not authenticated
      const url = freelancerPage.url();
      expect(url).toContain('login');
    });
  });

  describe('Cross-Service Communication', () => {
    it('should verify data consistency across services', async () => {
      // Create user via API
      const timestamp = Date.now();
      const userData = {
        username: `consistency_${timestamp}`,
        email: `consistency_${timestamp}@example.com`,
        password: 'password123',
        role: 'client',
      };

      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`,
        userData
      );
      const userId = registerResponse.data.data.user.id;

      // Verify user exists via RPC (if accessible)
      // This would require direct RPC access or API endpoint
      const profileResponse = await axios.get(
        `${API_BASE_URL}/users/profile/me`,
        {
          headers: {
            Authorization: `Bearer ${registerResponse.data.data.token}`,
          },
        }
      );
      expect(profileResponse.status).toBe(200);
      expect(profileResponse.data.data.username).toBe(userData.username);
    });

    it('should handle payment flow end-to-end', async () => {
      // This would test: Order → Payment → Update Order Status
      // Requires full setup of order and payment services
      if (!orderId) return;

      // Get order details
      const orderResponse = await axios.get(`${API_BASE_URL}/orders/${orderId}`, {
        headers: {
          Authorization: `Bearer ${clientToken}`,
        },
      });

      expect(orderResponse.status).toBe(200);
      expect(orderResponse.data.data.price).toBeDefined();
    });
  });

  describe('Error Scenarios', () => {
    it('should handle invalid authentication', async () => {
      const response = await axios.get(`${API_BASE_URL}/users/profile/me`, {
        headers: {
          Authorization: 'Bearer invalid-token',
        },
        validateStatus: () => true, // Don't throw on error
      });

      expect(response.status).toBe(401);
    });

    it('should handle missing required fields', async () => {
      const response = await axios.post(
        `${API_BASE_URL}/users/register`,
        {
          username: 'test',
          // Missing email and password
        },
        {
          validateStatus: () => true,
        }
      );

      expect(response.status).toBe(400);
    });

    it('should handle non-existent resources', async () => {
      const response = await axios.get(
        `${API_BASE_URL}/gigs/507f1f77bcf86cd799439999`,
        {
          validateStatus: () => true,
        }
      );

      expect(response.status).toBeGreaterThanOrEqual(400);
    });
  });

  describe('Performance and Load Tests', () => {
    it('should handle multiple concurrent requests', async () => {
      const requests = Array(20)
        .fill()
        .map(() => axios.get(`${API_BASE_URL}/gigs`));

      const startTime = Date.now();
      const responses = await Promise.all(requests);
      const endTime = Date.now();

      expect(responses.length).toBe(20);
      expect(endTime - startTime).toBeLessThan(10000); // Should complete within 10 seconds
    });

    it('should handle pagination correctly', async () => {
      const page1Response = await axios.get(
        `${API_BASE_URL}/gigs?page=1&limit=5`
      );
      const page2Response = await axios.get(
        `${API_BASE_URL}/gigs?page=2&limit=5`
      );

      expect(page1Response.status).toBe(200);
      expect(page2Response.status).toBe(200);

      if (
        page1Response.data.data.gigs.length > 0 &&
        page2Response.data.data.gigs.length > 0
      ) {
        // Results should be different
        const page1Ids = page1Response.data.data.gigs.map(
          (g) => g._id || g.id
        );
        const page2Ids = page2Response.data.data.gigs.map(
          (g) => g._id || g.id
        );
        expect(page1Ids).not.toEqual(page2Ids);
      }
    });
  });
});

// Helper functions
async function waitForService(url, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      const healthUrl = url.includes('/api') ? url.replace('/api', '/health') : `${url}/health`;
      await axios.get(healthUrl, { timeout: 2000 });
      return;
    } catch (error) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
  throw new Error(`Service at ${url} not available after ${timeout}ms`);
}

