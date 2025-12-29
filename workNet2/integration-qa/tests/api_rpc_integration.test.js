/*
 * API <-> RPC Integration Tests (Docker Compose)
 * - Starts services with Docker Compose
 * - Tests communication, data flow and error handling between Node API and Python RPC server
 */

const axios = require('axios');
const { execSync } = require('child_process');
const path = require('path');

jest.setTimeout(5 * 60 * 1000); // 5 minutes for slow integration startup

const ROOT_COMPOSE = path.resolve(__dirname, '../../docker-compose.yml');
const API_BASE_URL = process.env.API_URL || 'http://localhost:3000/api';
const RPC_HOST = process.env.RPC_HOST || 'localhost';
const RPC_PORT = parseInt(process.env.RPC_PORT || '8000');

function isDockerAvailable() {
  const { execSync } = require('child_process');
  try {
    // Check for 'docker compose' or 'docker-compose'
    execSync('docker compose version', { stdio: 'ignore' });
    return true;
  } catch (e1) {
    try {
      execSync('docker-compose --version', { stdio: 'ignore' });
      return true;
    } catch (e2) {
      return false;
    }
  }
}

const DOCKER_AVAILABLE = isDockerAvailable();

(DOCKER_AVAILABLE ? describe : describe.skip)('API <-> RPC Integration (Docker Compose)', () => {
  beforeAll(async () => {
    // Try to start the full stack using docker-compose
    try {
      const composeCmd = `docker-compose -f "${ROOT_COMPOSE}" up -d --build`;
      console.info('Starting services with:', composeCmd);
      execSync(composeCmd, { stdio: 'inherit', timeout: 180000 });
    } catch (err) {
      console.warn('docker-compose run failed (docker may not be available). Skipping integration tests.');
      throw err;
    }

    // Wait for API and RPC to become healthy
    await waitForService(API_BASE_URL, 120000);
    await waitForRPCService(RPC_HOST, RPC_PORT, 120000);
  });

  afterAll(() => {
    try {
      const downCmd = `docker-compose -f "${ROOT_COMPOSE}" down`;
      console.info('Stopping services with:', downCmd);
      execSync(downCmd, { stdio: 'inherit', timeout: 120000 });
    } catch (err) {
      console.warn('docker-compose down failed:', err.message);
    }
  });

  // --- Communication tests ---
  it('test_node_js_to_python_rpc_call()', async () => {
    const r = await rpcCall('ping', []);
    expect(r).toHaveProperty('status', 'ok');
    expect(r).toHaveProperty('mongodb_connected');
  });

  it('test_rpc_response_handling()', async () => {
    // Create a user via API then query user stats via RPC to validate the flow
    const timestamp = Date.now();
    const userData = {
      username: `int_user_${timestamp}`,
      email: `int_user_${timestamp}@example.com`,
      password: 'password123',
      role: 'client',
    };

    const reg = await axios.post(`${API_BASE_URL}/users/register`, userData, { timeout: 10000 });
    expect(reg.status).toBe(201);
    const userId = reg.data.data.user.id || reg.data.data.user._id;

    const rpcResp = await rpcCall('usersService.getStats', [userId]);
    // Either success true or a structured error — just assert it returned a JSON like object
    expect(rpcResp).toBeDefined();
    expect(typeof rpcResp).toBe('object');
  });

  it('test_rpc_error_propagation()', async () => {
    // Call a non-existing RPC method and assert RPC responds with an error or the API doesn't crash
    let rpcErrorThrown = false;
    try {
      await rpcCall('nonExistingService.method', []);
    } catch (err) {
      rpcErrorThrown = true;
    }
    expect(rpcErrorThrown).toBe(true);
  });

  it('test_rpc_timeout_handling()', async () => {
    // Call RPC with a short timeout to simulate timeout handling
    const url = `http://${RPC_HOST}:${RPC_PORT}/RPC2`;
    let timedOut = false;
    try {
      await axios.post(url, { methodName: 'ping', params: [] }, { timeout: 1 });
    } catch (err) {
      timedOut = !!err.code && (err.code === 'ECONNABORTED' || err.message.includes('timeout'));
    }
    expect(timedOut).toBe(true);
  });

  // --- Data Flow tests ---
  it('test_user_registration_full_flow()', async () => {
    const timestamp = Date.now();
    const userData = {
      username: `flow_user_${timestamp}`,
      email: `flow_user_${timestamp}@example.com`,
      password: 'password123',
      role: 'freelancer',
    };

    const reg = await axios.post(`${API_BASE_URL}/users/register`, userData, { timeout: 10000 });
    expect(reg.status).toBe(201);
    const userId = reg.data.data.user.id || reg.data.data.user._id;

    // Query RPC for stats to ensure user record is visible to RPC services
    const rpcStats = await rpcCall('usersService.getStats', [userId]);
    expect(rpcStats).toBeDefined();
    expect(rpcStats.success).toBeDefined();
  });

  it('test_gig_creation_to_mongodb()', async () => {
    // Create a freelancer
    const timestamp = Date.now();
    const freelancer = {
      username: `gig_flow_${timestamp}`,
      email: `gig_flow_${timestamp}@example.com`,
      password: 'password123',
      role: 'freelancer',
    };

    const reg = await axios.post(`${API_BASE_URL}/users/register`, freelancer);
    const token = reg.data.data.token;

    const gigData = {
      title: 'Integration Test Gig',
      description: 'Created during integration test',
      category: 'Web Development',
      price: 123,
      deliveryTime: 3,
    };

    const createRes = await axios.post(`${API_BASE_URL}/gigs`, gigData, { headers: { Authorization: `Bearer ${token}` } });
    expect(createRes.status).toBe(201);
    const gigId = createRes.data.data.gig._id || createRes.data.data.gig.id;

    // Use RPC search to find the gig
    const searchResp = await rpcCall('gigsService.search', [{ search: 'Integration Test Gig' }, 1, 10]);
    expect(searchResp).toBeDefined();
    expect(searchResp.success).toBeTruthy();
    expect(Array.isArray(searchResp.gigs)).toBeTruthy();
    const found = searchResp.gigs.find((g) => g._id === gigId || g.id === gigId || g.title === gigData.title);
    expect(found).toBeDefined();
  });

  it('test_order_workflow_complete()', async () => {
    // Create seller/freelancer
    const t = Date.now();
    const seller = { username: `seller_${t}`, email: `seller_${t}@example.com`, password: 'pass', role: 'freelancer' };
    const regSeller = await axios.post(`${API_BASE_URL}/users/register`, seller);
    const sellerToken = regSeller.data.data.token;

    // Create buyer
    const buyer = { username: `buyer_${t}`, email: `buyer_${t}@example.com`, password: 'pass', role: 'client' };
    const regBuyer = await axios.post(`${API_BASE_URL}/users/register`, buyer);
    const buyerToken = regBuyer.data.data.token;

    // Create gig
    const gig = { title: 'Order Flow Gig', description: 'for order', category: 'Dev', price: 10, deliveryTime: 2 };
    const createGig = await axios.post(`${API_BASE_URL}/gigs`, gig, { headers: { Authorization: `Bearer ${sellerToken}` } });
    expect(createGig.status).toBe(201);
    const gigId = createGig.data.data.gig._id || createGig.data.data.gig.id;

    // Create order
    const orderResp = await axios.post(`${API_BASE_URL}/orders`, { gigId, requirements: 'please' }, { headers: { Authorization: `Bearer ${buyerToken}` } });
    expect(orderResp.status).toBe(201);
    const orderId = orderResp.data.data.order._id || orderResp.data.data.order.id;

    // Move order through statuses
    const inProgress = await axios.put(`${API_BASE_URL}/orders/${orderId}/status`, { status: 'in_progress' }, { headers: { Authorization: `Bearer ${sellerToken}` } });
    expect(inProgress.status).toBe(200);

    const complete = await axios.put(`${API_BASE_URL}/orders/${orderId}/status`, { status: 'completed' }, { headers: { Authorization: `Bearer ${sellerToken}` } });
    expect(complete.status).toBe(200);

    // Verify via API GET
    const getOrder = await axios.get(`${API_BASE_URL}/orders/${orderId}`, { headers: { Authorization: `Bearer ${buyerToken}` } });
    expect(getOrder.status).toBe(200);
    expect(getOrder.data.data.order.status).toBe('completed');
  });

  // --- Error Handling Tests ---
  it('test_rpc_server_down_scenario()', async () => {
    // Stop the rpc-server container and ensure API responds gracefully (does not crash)
    try {
      execSync(`docker-compose -f "${ROOT_COMPOSE}" stop rpc-server`, { stdio: 'inherit', timeout: 60000 });
    } catch (err) {
      // ignore
    }

    // API should still accept requests but may return errors for RPC-backed endpoints
    const response = await axios.get(`${API_BASE_URL}/gigs`).catch((e) => e.response || { status: null });
    expect(response.status).toBeDefined();

    // Bring rpc-server back up
    execSync(`docker-compose -f "${ROOT_COMPOSE}" start rpc-server`, { stdio: 'inherit', timeout: 60000 });
    await waitForRPCService(RPC_HOST, RPC_PORT, 120000);
  });

  it('test_invalid_rpc_response()', async () => {
    // Call a valid method with invalid params to provoke RPC error
    const badResp = await rpcCallExpectError('usersService.getStats', ['not-an-id']);
    expect(badResp).toBeTruthy();
  });

  it('test_network_failure_handling()', async () => {
    // Simulate network failure by temporarily stopping api-gateway and assert failure is visible
    try {
      execSync(`docker-compose -f "${ROOT_COMPOSE}" stop api-gateway`, { stdio: 'inherit', timeout: 60000 });
    } catch (err) {}

    const resp = await axios.get(`${API_BASE_URL}/health`).catch((e) => ({ status: e && e.response ? e.response.status : null }));
    expect(resp.status).not.toBe(200);

    // Start api-gateway again
    execSync(`docker-compose -f "${ROOT_COMPOSE}" start api-gateway`, { stdio: 'inherit', timeout: 60000 });
    await waitForService(API_BASE_URL, 120000);
  });
});

// --- Helpers ---
async function rpcCall(methodName, params = [], timeout = 10000) {
  const url = `http://${RPC_HOST}:${RPC_PORT}/RPC2`;
  const resp = await axios.post(url, { methodName, params }, { timeout });
  if (resp && resp.data) return resp.data;
  throw new Error('No RPC response');
}

async function rpcCallExpectError(methodName, params = [], timeout = 10000) {
  const url = `http://${RPC_HOST}:${RPC_PORT}/RPC2`;
  try {
    const resp = await axios.post(url, { methodName, params }, { timeout });
    // Some servers may return structured error in 200 response
    return resp.data && resp.data.error;
  } catch (err) {
    return true;
  }
}

async function waitForService(url, timeout = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      const healthUrl = url.replace('/api', '/health');
      const r = await axios.get(healthUrl, { timeout: 3000 });
      if (r.status === 200) return;
    } catch (err) {
      await new Promise((res) => setTimeout(res, 1000));
    }
  }
  throw new Error(`Service ${url} not ready after ${timeout}ms`);
}

async function waitForRPCService(host, port, timeout = 30000) {
  const url = `http://${host}:${port}/RPC2`;
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      const r = await axios.post(url, { methodName: 'ping', params: [] }, { timeout: 3000 });
      if (r && r.data) return;
    } catch (err) {
      await new Promise((res) => setTimeout(res, 1000));
    }
  }
  throw new Error(`RPC ${host}:${port} not ready after ${timeout}ms`);
}
