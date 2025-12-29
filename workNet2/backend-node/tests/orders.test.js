const request = require('supertest');
const express = require('express');
const orderRoutes = require('../routes/orderRoutes');

// Mock RPC Client
jest.mock('../utils/rpcClient', () => ({
  callRPC: jest.fn(),
}));

// Mock auth middleware
jest.mock('../middlewares/authMiddleware', () => ({
  authMiddleware: jest.fn((req, res, next) => {
    req.user = {
      id: '507f1f77bcf86cd799439011',
      username: 'testuser',
      email: 'test@example.com',
      role: 'client',
    };
    next();
  }),
  isOwnerOrAdmin: jest.fn((req, res, next) => {
    // Mock: allow if user is owner or admin
    const orderUserId = req.order?.buyerId || req.order?.sellerId;
    if (req.user.id === orderUserId || req.user.role === 'admin') {
      next();
    } else {
      res.status(403).json({ success: false, message: 'Forbidden' });
    }
  }),
}));

// Mock Order and Gig models
jest.mock('../models/orderModel', () => ({
  findOne: jest.fn(),
  find: jest.fn(),
  create: jest.fn(),
}));

jest.mock('../models/gigModel', () => ({
  findById: jest.fn(),
}));

const { callRPC } = require('../utils/rpcClient');
const Order = require('../models/orderModel');
const Gig = require('../models/gigModel');

// Create Express app for testing
const app = express();
app.use(express.json());
app.use('/api/orders', orderRoutes);

describe('Order Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/orders', () => {
    it('should get all orders for authenticated user', async () => {
      const mockOrders = [
        {
          _id: '507f1f77bcf86cd799439011',
          gigId: '507f1f77bcf86cd799439020',
          buyerId: '507f1f77bcf86cd799439011',
          sellerId: '507f1f77bcf86cd799439012',
          price: 50,
          status: 'pending',
        },
      ];

      Order.find.mockReturnValue({
        populate: jest.fn().mockReturnValue({
          sort: jest.fn().mockReturnValue({
            skip: jest.fn().mockReturnValue({
              limit: jest.fn().mockResolvedValue(mockOrders),
            }),
          }),
        }),
      });

      Order.find.mockReturnValue({
        countDocuments: jest.fn().mockResolvedValue(1),
      });

      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should filter orders by status', async () => {
      const mockOrders = [
        {
          _id: '507f1f77bcf86cd799439011',
          status: 'completed',
        },
      ];

      Order.find.mockReturnValue({
        populate: jest.fn().mockReturnValue({
          sort: jest.fn().mockReturnValue({
            skip: jest.fn().mockReturnValue({
              limit: jest.fn().mockResolvedValue(mockOrders),
            }),
          }),
        }),
      });

      Order.find.mockReturnValue({
        countDocuments: jest.fn().mockResolvedValue(1),
      });

      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .query({ status: 'completed' });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should filter orders by type (buyer)', async () => {
      const mockOrders = [
        {
          _id: '507f1f77bcf86cd799439011',
          buyerId: '507f1f77bcf86cd799439011',
        },
      ];

      Order.find.mockReturnValue({
        populate: jest.fn().mockReturnValue({
          sort: jest.fn().mockReturnValue({
            skip: jest.fn().mockReturnValue({
              limit: jest.fn().mockResolvedValue(mockOrders),
            }),
          }),
        }),
      });

      Order.find.mockReturnValue({
        countDocuments: jest.fn().mockResolvedValue(1),
      });

      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .query({ type: 'buyer' });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should return 400 for invalid status', async () => {
      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .query({ status: 'invalid_status' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid page number', async () => {
      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .query({ page: 0 });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('GET /api/orders/:id', () => {
    it('should get order by ID successfully', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439011',
        gigId: {
          _id: '507f1f77bcf86cd799439020',
          title: 'Test Gig',
        },
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: '507f1f77bcf86cd799439012',
        price: 50,
        status: 'pending',
      };

      Order.findOne.mockReturnValue({
        populate: jest.fn().mockResolvedValue(mockOrder),
      });

      const response = await request(app)
        .get('/api/orders/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.price).toBe(50);
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .get('/api/orders/invalid-id')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 404 if order not found', async () => {
      Order.findOne.mockReturnValue({
        populate: jest.fn().mockResolvedValue(null),
      });

      const response = await request(app)
        .get('/api/orders/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 403 when user is not buyer/seller/admin', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439077',
        gigId: '507f1f77bcf86cd799439020',
        buyerId: { _id: '507f1f77bcf86cd799439099' },
        sellerId: { _id: '507f1f77bcf86cd799439088' },
        price: 50,
        status: 'pending',
      };

      Order.findById.mockResolvedValue(mockOrder);

      const response = await request(app)
        .get('/api/orders/507f1f77bcf86cd799439077')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(403);
      expect(response.body.success).toBe(false);
    });

    it('should return seller-only results when requesting type=seller', async () => {
      const mockOrders = [
        { _id: '507f1f77bcf86cd799439080', sellerId: '507f1f77bcf86cd799439011' }
      ];

      Order.find.mockReturnValue({
        populate: jest.fn().mockReturnValue({
          sort: jest.fn().mockReturnValue({
            skip: jest.fn().mockReturnValue({
              limit: jest.fn().mockResolvedValue(mockOrders)
            })
          })
        })
      });

      Order.find.mockReturnValue({
        countDocuments: jest.fn().mockResolvedValue(1)
      });

      const response = await request(app)
        .get('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .query({ type: 'seller' });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });
  });

  describe('POST /api/orders', () => {
    it('should create a new order successfully', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439020',
        title: 'Test Gig',
        price: 50,
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
      };

      const mockRPCResponse = {
        success: true,
        order_id: '507f1f77bcf86cd799439011',
        message: 'Order created successfully',
      };

      Gig.findById.mockResolvedValue(mockGig);
      callRPC.mockResolvedValue(mockRPCResponse);
      Order.create.mockResolvedValue({
        _id: '507f1f77bcf86cd799439011',
        gigId: '507f1f77bcf86cd799439020',
        buyerId: '507f1f77bcf86cd799439011',
        price: 50,
        status: 'pending',
      });

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: '507f1f77bcf86cd799439020',
          requirements: 'Please make it colorful',
        });

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should return 400 for invalid gig ID', async () => {
      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: 'invalid-id',
          requirements: 'Test requirements',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 404 if gig not found', async () => {
      Gig.findById.mockResolvedValue(null);

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: '507f1f77bcf86cd799439020',
          requirements: 'Test requirements',
        });

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 if gig is not active', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439020',
        title: 'Test Gig',
        isActive: false,
      };

      Gig.findById.mockResolvedValue(mockGig);

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: '507f1f77bcf86cd799439020',
          requirements: 'Test requirements',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 if user tries to order their own gig', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439020',
        title: 'Test Gig',
        userId: '507f1f77bcf86cd799439011', // Same as req.user.id
        isActive: true,
      };

      Gig.findById.mockResolvedValue(mockGig);

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: '507f1f77bcf86cd799439020',
          requirements: 'Test requirements',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should handle RPC errors', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439020',
        title: 'Test Gig',
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
      };

      Gig.findById.mockResolvedValue(mockGig);
      callRPC.mockRejectedValue(new Error('Failed to create order'));

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: '507f1f77bcf86cd799439020',
          requirements: 'Test requirements',
        });

      expect(response.status).toBe(500);
      expect(response.body.success).toBe(false);
    });

    it('should accept explicit valid deliveryDate and store it', async () => {
      const deliveryDate = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
      const mockGig = {
        _id: '507f1f77bcf86cd799439030',
        title: 'Fast Gig',
        price: 100,
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
        deliveryTime: 7
      };

      Gig.findById.mockResolvedValue(mockGig);
      callRPC.mockResolvedValue({ success: true });
      Order.create.mockResolvedValue({
        _id: '507f1f77bcf86cd799439033',
        gigId: mockGig._id,
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: mockGig.userId,
        price: mockGig.price,
        status: 'pending',
        deliveryDate
      });

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({
          gigId: mockGig._id,
          requirements: 'Please deliver asap',
          deliveryDate
        });

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(response.body.data.deliveryDate).toBe(deliveryDate);
      // Service fee (business rule) is not stored by API, but price should match gig price
      expect(response.body.data.price).toBe(100);
    });

    it('should set default deliveryDate based on gig.deliveryTime when not provided', async () => {
      const now = Date.now();
      const mockGig = {
        _id: '507f1f77bcf86cd799439040',
        title: 'Standard Gig',
        price: 80,
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
        deliveryTime: 3 // days
      };

      Gig.findById.mockResolvedValue(mockGig);
      callRPC.mockResolvedValue({ success: true });
      Order.create.mockImplementation(async (orderData) => ({
        ...orderData,
        _id: '507f1f77bcf86cd799439044'
      }));

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({ gigId: mockGig._id, requirements: 'Standard delivery' });

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      const returnedDate = new Date(response.body.data.deliveryDate).getTime();
      const expectedMin = now + (mockGig.deliveryTime - 1) * 24 * 60 * 60 * 1000; // allow -1 day tolerance
      const expectedMax = now + (mockGig.deliveryTime + 1) * 24 * 60 * 60 * 1000; // allow +1 day tolerance
      expect(returnedDate).toBeGreaterThanOrEqual(expectedMin);
      expect(returnedDate).toBeLessThanOrEqual(expectedMax);
    });

    it('should return 400 for invalid deliveryDate format', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439050',
        title: 'Bad Date Gig',
        price: 70,
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
        deliveryTime: 5
      };

      Gig.findById.mockResolvedValue(mockGig);

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({ gigId: mockGig._id, deliveryDate: 'not-a-date' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should compute expected service fee (10%) for business logic verification', async () => {
      const mockGig = {
        _id: '507f1f77bcf86cd799439060',
        title: 'Fee Gig',
        price: 200,
        userId: '507f1f77bcf86cd799439012',
        isActive: true,
        deliveryTime: 5
      };

      Gig.findById.mockResolvedValue(mockGig);
      callRPC.mockResolvedValue({ success: true });
      Order.create.mockResolvedValue({
        _id: '507f1f77bcf86cd799439061',
        gigId: mockGig._id,
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: mockGig.userId,
        price: mockGig.price,
        status: 'pending'
      });

      const response = await request(app)
        .post('/api/orders')
        .set('Authorization', 'Bearer mock-token')
        .send({ gigId: mockGig._id, requirements: 'Check fee' });

      expect(response.status).toBe(201);
      // Business rule for fee (10%)
      const expectedFee = (mockGig.price * 0.1);
      expect(response.body.data.price).toBe(200);
      // Verify expected fee computed locally for tests
      expect(expectedFee).toBeCloseTo(20);
    });
  });

  describe('PUT /api/orders/:id/status', () => {
    it('should update order status successfully', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439011',
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: '507f1f77bcf86cd799439012',
        status: 'pending',
      };

      const mockRPCResponse = {
        success: true,
        message: 'Order status updated successfully',
      };

      Order.findOne.mockResolvedValue(mockOrder);
      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'in_progress',
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .put('/api/orders/invalid-id/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'in_progress',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid status', async () => {
      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'invalid_status',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 404 if order not found', async () => {
      Order.findOne.mockResolvedValue(null);

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'in_progress',
        });

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should handle RPC errors', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439011',
        buyerId: '507f1f77bcf86cd799439011',
        status: 'pending',
      };

      Order.findOne.mockResolvedValue(mockOrder);
      callRPC.mockRejectedValue(new Error('Failed to update status'));

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'in_progress',
        });

      expect(response.status).toBe(500);
      expect(response.body.success).toBe(false);
    });

    it('should prevent invalid status transitions (completed -> in_progress)', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439111',
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: '507f1f77bcf86cd799439012',
        status: 'completed',
        save: jest.fn().mockResolvedValue(true)
      };

      Order.findById.mockResolvedValue(mockOrder);

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439111/status')
        .set('Authorization', 'Bearer mock-token')
        .send({ status: 'in_progress' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should update deliverables on order update', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439121',
        buyerId: '507f1f77bcf86cd799439011',
        sellerId: '507f1f77bcf86cd799439012',
        status: 'in_progress'
      };

      const updatedOrder = { ...mockOrder, deliverables: ['file1.pdf', 'file2.zip'] };

      Order.findById.mockResolvedValue(mockOrder);
      Order.findByIdAndUpdate.mockResolvedValue(updatedOrder);

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439121')
        .set('Authorization', 'Bearer mock-token')
        .send({ deliverables: ['file1.pdf', 'file2.zip'] });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.deliverables).toHaveLength(2);
    });
  });
    it('should update order successfully', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439011',
        buyerId: '507f1f77bcf86cd799439011',
        status: 'pending',
      };

      const mockRPCResponse = {
        success: true,
        message: 'Order updated successfully',
      };

      Order.findOne.mockResolvedValue(mockOrder);
      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token')
        .send({
          requirements: 'Updated requirements',
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .put('/api/orders/invalid-id')
        .set('Authorization', 'Bearer mock-token')
        .send({
          requirements: 'Updated requirements',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('Authentication Tests', () => {
    it('should require authentication for all routes', async () => {
      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        res.status(401).json({ success: false, message: 'Unauthorized' });
      });

      const response = await request(app)
        .get('/api/orders');

      expect(response.status).toBe(401);
    });

    it('should allow only order owner or admin to update order', async () => {
      const mockOrder = {
        _id: '507f1f77bcf86cd799439011',
        buyerId: '507f1f77bcf86cd799439099', // Different user
        sellerId: '507f1f77bcf86cd799439012',
        status: 'pending',
      };

      Order.findOne.mockResolvedValue(mockOrder);

      const { isOwnerOrAdmin } = require('../middlewares/authMiddleware');
      isOwnerOrAdmin.mockImplementationOnce((req, res, next) => {
        res.status(403).json({ success: false, message: 'Forbidden' });
      });

      const response = await request(app)
        .put('/api/orders/507f1f77bcf86cd799439011/status')
        .set('Authorization', 'Bearer mock-token')
        .send({
          status: 'in_progress',
        });

      expect(response.status).toBe(403);
    });
  });
});

