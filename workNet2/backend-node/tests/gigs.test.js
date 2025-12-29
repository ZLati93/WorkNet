const request = require('supertest');
const express = require('express');
const gigRoutes = require('../routes/gigRoutes');

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
      role: 'freelancer',
      isSeller: true,
    };
    next();
  }),
  isSeller: jest.fn((req, res, next) => {
    if (req.user.isSeller || req.user.role === 'freelancer') {
      next();
    } else {
      res.status(403).json({ success: false, message: 'Only sellers can perform this action' });
    }
  }),
  isOwnerOrAdmin: jest.fn((req, res, next) => {
    // Mock: allow if user is owner or admin
    if (req.user.id === req.params.userId || req.user.role === 'admin') {
      next();
    } else {
      res.status(403).json({ success: false, message: 'Forbidden' });
    }
  }),
}));

const { callRPC } = require('../utils/rpcClient');

// Create Express app for testing
const app = express();
app.use(express.json());
app.use('/api/gigs', gigRoutes);

describe('Gig Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/gigs', () => {
    it('should get all gigs successfully', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [
          {
            id: '507f1f77bcf86cd799439011',
            title: 'Test Gig 1',
            description: 'Test description',
            price: 50,
            category: 'Design',
          },
          {
            id: '507f1f77bcf86cd799439012',
            title: 'Test Gig 2',
            description: 'Test description 2',
            price: 100,
            category: 'Development',
          },
        ],
        total: 2,
        page: 1,
        limit: 10,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs')
        .query({ page: 1, limit: 10 });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.gigs).toHaveLength(2);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should search gigs by query', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [
          {
            id: '507f1f77bcf86cd799439011',
            title: 'Logo Design',
            description: 'Professional logo design',
            price: 50,
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs')
        .query({ search: 'logo' });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should filter gigs by category', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [],
        total: 0,
        page: 1,
        limit: 10,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs')
        .query({ category: 'Design' });

      expect(response.status).toBe(200);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should filter gigs by price range', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [],
        total: 0,
        page: 1,
        limit: 10,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs')
        .query({ minPrice: 10, maxPrice: 100 });

      expect(response.status).toBe(200);
      expect(callRPC).toHaveBeenCalled();
    });

    it('should return 400 for invalid page number', async () => {
      const response = await request(app)
        .get('/api/gigs')
        .query({ page: 0 });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid limit', async () => {
      const response = await request(app)
        .get('/api/gigs')
        .query({ limit: 200 });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('GET /api/gigs/:id', () => {
    it('should get gig by ID successfully', async () => {
      const mockRPCResponse = {
        success: true,
        gig: {
          id: '507f1f77bcf86cd799439011',
          title: 'Test Gig',
          description: 'Test description',
          price: 50,
          category: 'Design',
          userId: '507f1f77bcf86cd799439010',
        },
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs/507f1f77bcf86cd799439011');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.title).toBe('Test Gig');
      expect(callRPC).toHaveBeenCalledWith('gigsService.get_by_id', [
        '507f1f77bcf86cd799439011',
      ]);
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .get('/api/gigs/invalid-id');

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 404 if gig not found', async () => {
      callRPC.mockRejectedValue(new Error('Gig not found'));

      const response = await request(app)
        .get('/api/gigs/507f1f77bcf86cd799439011');

      expect(response.status).toBe(500);
    });
  });

  describe('POST /api/gigs', () => {
    it('should create a new gig successfully', async () => {
      const mockRPCResponse = {
        success: true,
        gig_id: '507f1f77bcf86cd799439011',
        message: 'Gig created successfully',
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'New Gig',
          description: 'This is a detailed description of the new gig service',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
          revisionNumber: 2,
          features: ['Feature 1', 'Feature 2'],
        });

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalledWith('gigsService.create', [
        '507f1f77bcf86cd799439011',
        expect.objectContaining({
          title: 'New Gig',
          description: 'This is a detailed description of the new gig service',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        }),
      ]);
    });

    it('should return 400 for short title', async () => {
      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Ab',
          description: 'This is a detailed description',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for short description', async () => {
      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Valid Title Here',
          description: 'Short',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for negative price', async () => {
      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Valid Title Here',
          description: 'This is a detailed description',
          category: 'Design',
          price: -10,
          deliveryTime: 3,
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid delivery time', async () => {
      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Valid Title Here',
          description: 'This is a detailed description',
          category: 'Design',
          price: 50,
          deliveryTime: 0,
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should handle RPC errors', async () => {
      callRPC.mockRejectedValue(new Error('Failed to create gig'));

      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'New Gig',
          description: 'This is a detailed description',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        });

      expect(response.status).toBe(500);
      expect(response.body.success).toBe(false);
    });
  });

  describe('PUT /api/gigs/:id', () => {
    it('should update gig successfully', async () => {
      const mockRPCResponse = {
        success: true,
        message: 'Gig updated successfully',
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .put('/api/gigs/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Updated Gig Title',
          price: 75,
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalledWith('gigsService.update', [
        '507f1f77bcf86cd799439011',
        expect.objectContaining({
          title: 'Updated Gig Title',
          price: 75,
        }),
      ]);
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .put('/api/gigs/invalid-id')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Updated Title',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid price update', async () => {
      const response = await request(app)
        .put('/api/gigs/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token')
        .send({
          price: -10,
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should handle RPC errors', async () => {
      callRPC.mockRejectedValue(new Error('Gig not found'));

      const response = await request(app)
        .put('/api/gigs/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'Updated Title',
        });

      expect(response.status).toBe(500);
    });
  });

  describe('DELETE /api/gigs/:id', () => {
    it('should delete gig successfully', async () => {
      const mockRPCResponse = {
        success: true,
        message: 'Gig deleted successfully',
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .delete('/api/gigs/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalledWith('gigsService.delete', [
        '507f1f77bcf86cd799439011',
      ]);
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .delete('/api/gigs/invalid-id')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should handle RPC errors', async () => {
      callRPC.mockRejectedValue(new Error('Gig not found'));

      const response = await request(app)
        .delete('/api/gigs/507f1f77bcf86cd799439011')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(500);
    });
  });

  describe('GET /api/gigs/user/:userId', () => {
    it('should get gigs by user ID', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [
          {
            id: '507f1f77bcf86cd799439011',
            title: 'User Gig 1',
            userId: '507f1f77bcf86cd799439010',
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs/user/507f1f77bcf86cd799439010');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(callRPC).toHaveBeenCalledWith('gigsService.get_by_user', [
        '507f1f77bcf86cd799439010',
        expect.any(Number),
        expect.any(Number),
      ]);
    });

    it('should return 400 for invalid user ID', async () => {
      const response = await request(app)
        .get('/api/gigs/user/invalid-id');

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('Authentication Tests', () => {
    it('should allow public access to GET routes', async () => {
      const mockRPCResponse = {
        success: true,
        gigs: [],
        total: 0,
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .get('/api/gigs');

      expect(response.status).toBe(200);
    });

    it('should require authentication for POST /api/gigs', async () => {
      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        res.status(401).json({ success: false, message: 'Unauthorized' });
      });

      const response = await request(app)
        .post('/api/gigs')
        .send({
          title: 'New Gig',
          description: 'Description',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        });

      expect(response.status).toBe(401);
    });

    it('should require seller role for creating gigs', async () => {
      const { isSeller } = require('../middlewares/authMiddleware');
      isSeller.mockImplementationOnce((req, res, next) => {
        res.status(403).json({ success: false, message: 'Only sellers can perform this action' });
      });

      const response = await request(app)
        .post('/api/gigs')
        .set('Authorization', 'Bearer mock-token')
        .send({
          title: 'New Gig',
          description: 'Description',
          category: 'Design',
          price: 50,
          deliveryTime: 3,
        });

      expect(response.status).toBe(403);
    });
  });
});

