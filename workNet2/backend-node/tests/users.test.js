const request = require('supertest');
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

// Mock RPC Client
jest.mock('../utils/rpcClient', () => ({
  callRPC: jest.fn(),
}));

// Mock User Model
jest.mock('../models/userModel', () => ({
  findOne: jest.fn(),
  find: jest.fn(),
  create: jest.fn(),
  findById: jest.fn(),
  findByIdAndUpdate: jest.fn(),
  findByIdAndDelete: jest.fn(),
  countDocuments: jest.fn(),
}));

// Mock auth middleware
jest.mock('../middlewares/authMiddleware', () => ({
  authMiddleware: jest.fn((req, res, next) => {
    // Simulate authenticated user
    req.user = {
      id: '507f1f77bcf86cd799439011',
      _id: '507f1f77bcf86cd799439011',
      username: 'testuser',
      email: 'test@example.com',
      role: 'client',
    };
    next();
  }),
  authorize: jest.fn((...roles) => (req, res, next) => {
    if (roles.includes(req.user.role)) {
      next();
    } else {
      res.status(403).json({ success: false, message: 'Forbidden' });
    }
  }),
  isOwnerOrAdmin: jest.fn((req, res, next) => {
    if (req.user.id === req.params.id || req.user.role === 'admin') {
      next();
    } else {
      res.status(403).json({ success: false, message: 'Forbidden' });
    }
  }),
}));

const { callRPC } = require('../utils/rpcClient');
const User = require('../models/userModel');
const userRoutes = require('../routes/userRoutes');

// Create Express app for testing
const app = express();
app.use(express.json());
app.use('/api/users', userRoutes);

describe('User Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Ensure a known JWT secret for tests and default RPC response
    process.env.JWT_SECRET = 'test-secret';
    callRPC.mockResolvedValue({ success: true });
  });

  afterEach(() => {
    jest.resetAllMocks();
    delete process.env.JWT_SECRET;
  });

  describe('POST /api/users/register', () => {
    it('should register a new user successfully', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'hashedpassword',
        role: 'client',
      };

      User.findOne.mockResolvedValue(null); // No existing user
      User.create.mockResolvedValue(mockUser);
      callRPC.mockResolvedValue({ success: true });

      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'newuser',
          email: 'newuser@example.com',
          password: 'password123',
          role: 'client',
        });

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('token');
      expect(response.body.data.user.username).toBe('newuser');
      expect(User.create).toHaveBeenCalled();
    });

    it('should return 400 for invalid email', async () => {
      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'newuser',
          email: 'invalid-email',
          password: 'password123',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
      expect(response.body.message).toBe('Validation failed');
    });

    it('should return 400 for short password', async () => {
      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'newuser',
          email: 'user@example.com',
          password: '123',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for short username', async () => {
      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'ab',
          email: 'user@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 if user already exists', async () => {
      User.findOne.mockResolvedValue({
        _id: '507f1f77bcf86cd799439011',
        email: 'existing@example.com',
      });

      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'existinguser',
          email: 'existing@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('already exists');
    });

    it('should return 400 when required fields are missing', async () => {
      const response = await request(app)
        .post('/api/users/register')
        .send({ email: 'nofields@example.com' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
      expect(Array.isArray(response.body.errors)).toBe(true);
      // Expect validation errors for username and password
      const params = response.body.errors.map(e => e.param);
      expect(params).toEqual(expect.arrayContaining(['username', 'password']));
    });

    it('should call RPC client on successful registration', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439099',
        username: 'rpcuser',
        email: 'rpcuser@example.com',
        password: 'hashed',
        role: 'client',
      };

      User.findOne.mockResolvedValue(null);
      User.create.mockResolvedValue(mockUser);

      const response = await request(app)
        .post('/api/users/register')
        .send({ username: 'rpcuser', email: 'rpcuser@example.com', password: 'password123' });

      expect(response.status).toBe(201);
      expect(callRPC).toHaveBeenCalledWith(expect.any(Object), 'user.create', expect.any(Array));
    });
  });

  describe('POST /api/users/login', () => {
    it('should login user successfully', async () => {
      const hashedPassword = await bcrypt.hash('password123', 10);
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        username: 'testuser',
        email: 'test@example.com',
        password: hashedPassword,
        role: 'client',
      };

      User.findOne.mockResolvedValue(mockUser);

      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'test@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('token');
      expect(response.body.data.user.email).toBe('test@example.com');

      // Verify token payload
      const token = response.body.data.token;
      const payload = jwt.verify(token, process.env.JWT_SECRET);
      expect(payload).toHaveProperty('id', mockUser._id);
      expect(payload).toHaveProperty('role', mockUser.role);
    });

    it('should return 400 for invalid email format', async () => {
      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'invalid-email',
          password: 'password123',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for missing password', async () => {
      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'test@example.com',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 401 for invalid credentials - user not found', async () => {
      User.findOne.mockResolvedValue(null);

      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'nonexistent@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(401);
      expect(response.body.success).toBe(false);
      expect(response.body.message).toBe('Invalid credentials');
    });

    it('should return 401 for invalid credentials - wrong password', async () => {
      const hashedPassword = await bcrypt.hash('correctpassword', 10);
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        email: 'test@example.com',
        password: hashedPassword,
      };

      User.findOne.mockResolvedValue(mockUser);

      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'test@example.com',
          password: 'wrongpassword',
        });

      expect(response.status).toBe(401);
      expect(response.body.success).toBe(false);
      expect(response.body.message).toBe('Invalid credentials');
    });
  });

  describe('GET /api/users/profile/me', () => {
    it('should get current user profile', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        username: 'testuser',
        email: 'test@example.com',
        role: 'client',
        toObject: jest.fn().mockReturnValue({
          _id: '507f1f77bcf86cd799439011',
          username: 'testuser',
          email: 'test@example.com',
          role: 'client',
        }),
      };

      User.findById.mockResolvedValue(mockUser);

      const response = await request(app)
        .get('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.username).toBe('testuser');
      expect(User.findById).toHaveBeenCalledWith('507f1f77bcf86cd799439011');
    });

    it('should return 404 if user not found', async () => {
      User.findById.mockResolvedValue(null);

      const response = await request(app)
        .get('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 401 for invalid token', async () => {
      // Simulate auth middleware rejecting token
      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        res.status(401).json({ success: false, message: 'Invalid token' });
      });

      const response = await request(app)
        .get('/api/users/profile/me')
        .set('Authorization', 'Bearer invalid-token');

      expect(response.status).toBe(401);
      expect(response.body.success).toBe(false);
    });
  });

  describe('PUT /api/users/profile/me', () => {
    it('should update user profile successfully', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        username: 'testuser',
        email: 'test@example.com',
        save: jest.fn().mockResolvedValue(true),
      };

      User.findById.mockResolvedValue(mockUser);
      User.findByIdAndUpdate.mockResolvedValue(mockUser);

      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({
          username: 'updateduser',
          phone: '1234567890',
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should return 400 for invalid email in update', async () => {
      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({
          email: 'invalid-email',
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 404 if user not found', async () => {
      User.findById.mockResolvedValue(null);

      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({
          username: 'updateduser',
        });

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for invalid profile picture URL', async () => {
      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({ profilePicture: 'not-a-url' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 if skills is not an array', async () => {
      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({ skills: 'javascript' });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should call RPC client on profile update', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439011',
        username: 'testuser',
        email: 'test@example.com',
        save: jest.fn().mockResolvedValue(true),
      };

      User.findById.mockResolvedValue(mockUser);
      User.findByIdAndUpdate.mockResolvedValue(mockUser);

      const response = await request(app)
        .put('/api/users/profile/me')
        .set('Authorization', 'Bearer mock-token')
        .send({ username: 'updateduser' });

      expect(response.status).toBe(200);
      expect(callRPC).toHaveBeenCalledWith(expect.any(Object), 'user.update', expect.any(Array));
    });
  });

  describe('GET /api/users/:id', () => {
    it('should get user by ID', async () => {
      const mockUser = {
        _id: '507f1f77bcf86cd799439012',
        username: 'otheruser',
        email: 'other@example.com',
        role: 'freelancer',
        toObject: jest.fn().mockReturnValue({
          _id: '507f1f77bcf86cd799439012',
          username: 'otheruser',
          email: 'other@example.com',
          role: 'freelancer',
        }),
      };

      User.findById.mockResolvedValue(mockUser);

      const response = await request(app)
        .get('/api/users/507f1f77bcf86cd799439012')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.username).toBe('otheruser');
    });

    it('should return 400 for invalid MongoDB ID', async () => {
      const response = await request(app)
        .get('/api/users/invalid-id')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('GET /api/users', () => {
    it('should get all users with pagination', async () => {
      const mockUsers = [
        {
          _id: '507f1f77bcf86cd799439011',
          username: 'user1',
          email: 'user1@example.com',
          toObject: jest.fn().mockReturnValue({
            _id: '507f1f77bcf86cd799439011',
            username: 'user1',
            email: 'user1@example.com',
          }),
        },
        {
          _id: '507f1f77bcf86cd799439012',
          username: 'user2',
          email: 'user2@example.com',
          toObject: jest.fn().mockReturnValue({
            _id: '507f1f77bcf86cd799439012',
            username: 'user2',
            email: 'user2@example.com',
          }),
        },
      ];

      User.find.mockReturnValue({
        skip: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            select: jest.fn().mockResolvedValue(mockUsers),
          }),
        }),
      });
      User.countDocuments.mockResolvedValue(2);

      const response = await request(app)
        .get('/api/users?page=1&limit=10')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data.users).toHaveLength(2);
    });

    it('should filter users by role', async () => {
      User.find.mockReturnValue({
        skip: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            select: jest.fn().mockResolvedValue([]),
          }),
        }),
      });
      User.countDocuments.mockResolvedValue(0);

      const response = await request(app)
        .get('/api/users?role=freelancer')
        .set('Authorization', 'Bearer mock-token');

        expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should search users by query', async () => {
      const mockUsers = [
        {
          _id: '507f1f77bcf86cd799439011',
          username: 'searchuser',
          email: 'search@example.com',
          toObject: jest.fn().mockReturnValue({
            _id: '507f1f77bcf86cd799439011',
            username: 'searchuser',
            email: 'search@example.com',
          }),
        },
      ];

      User.find.mockReturnValue({
        skip: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            select: jest.fn().mockResolvedValue(mockUsers),
          }),
        }),
      });
      User.countDocuments.mockResolvedValue(1);

      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        req.user = { id: 'admin', _id: 'admin', role: 'admin' };
        next();
      });

      const response = await request(app)
        .get('/api/users?search=searchuser')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.data.users).toHaveLength(1);
    });

    it('should accept skills filter without error', async () => {
      User.find.mockReturnValue({
        skip: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            select: jest.fn().mockResolvedValue([]),
          }),
        }),
      });
      User.countDocuments.mockResolvedValue(0);

      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        req.user = { id: 'admin', _id: 'admin', role: 'admin' };
        next();
      });

      const response = await request(app)
        .get('/api/users?skills[]=js')
        .set('Authorization', 'Bearer mock-token');

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });
  });

  describe('Authentication Tests', () => {
    it('should require authentication for protected routes', async () => {
      // Mock authMiddleware to reject
      const { authMiddleware } = require('../middlewares/authMiddleware');
      authMiddleware.mockImplementationOnce((req, res, next) => {
        res.status(401).json({ success: false, message: 'Unauthorized' });
      });

      const response = await request(app)
        .get('/api/users/profile/me');

      expect(response.status).toBe(401);
    });

    it('should allow public access to register route', async () => {
      const mockRPCResponse = {
        success: true,
        data: {
          user_id: '507f1f77bcf86cd799439011',
          token: 'mock-token',
        },
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .post('/api/users/register')
        .send({
          username: 'publicuser',
          email: 'public@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(201);
    });

    it('should allow public access to login route', async () => {
      const mockRPCResponse = {
        success: true,
        data: {
          token: 'mock-token',
        },
      };

      callRPC.mockResolvedValue(mockRPCResponse);

      const response = await request(app)
        .post('/api/users/login')
        .send({
          email: 'test@example.com',
          password: 'password123',
        });

      expect(response.status).toBe(200);
    });
  });
});

