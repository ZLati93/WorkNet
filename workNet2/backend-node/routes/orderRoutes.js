const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware, isOwnerOrAdmin } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Order = require('../models/orderModel');
const Gig = require('../models/gigModel');

const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      message: 'Validation failed',
      errors: errors.array()
    });
  }
  next();
};

const createOrderValidation = [
  body('gigId').isMongoId().withMessage('Invalid gig ID'),
  body('requirements').optional().isString(),
  body('deliveryDate').optional().isISO8601().withMessage('Invalid date format')
];

const updateOrderValidation = [
  body('status').optional().isIn(['pending', 'in_progress', 'completed', 'cancelled', 'disputed']),
  body('deliverables').optional().isArray(),
  body('requirements').optional().isString()
];

/**
 * @route   GET /api/orders
 * @desc    Get all orders with pagination and filtering
 * @access  Private
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('status').optional().isIn(['pending', 'in_progress', 'completed', 'cancelled', 'disputed']),
  query('type').optional().isIn(['buyer', 'seller'])
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { status, type } = req.query;

    // Build query based on user role
    const query = {};
    if (type === 'buyer') {
      query.buyerId = req.userId;
    } else if (type === 'seller') {
      query.sellerId = req.userId;
    } else {
      // Show orders where user is buyer or seller
      query.$or = [
        { buyerId: req.userId },
        { sellerId: req.userId }
      ];
    }
    if (status) query.status = status;

    const orders = await Order.find(query)
      .populate('gigId', 'title images')
      .populate('buyerId', 'username profilePicture')
      .populate('sellerId', 'username profilePicture')
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Order.countDocuments(query);

    res.json(paginationResponse(orders, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/orders/:id
 * @desc    Get order by ID
 * @access  Private (Owner only)
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid order ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const order = await Order.findById(req.params.id)
      .populate('gigId')
      .populate('buyerId', 'username email profilePicture')
      .populate('sellerId', 'username email profilePicture');

    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Check ownership
    if (order.buyerId._id.toString() !== req.userId.toString() && 
        order.sellerId._id.toString() !== req.userId.toString() && 
        req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    res.json({
      success: true,
      data: order
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/orders
 * @desc    Create a new order
 * @access  Private
 */
router.post('/', createOrderValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { gigId, requirements, deliveryDate } = req.body;

    // Get gig
    const gig = await Gig.findById(gigId);
    if (!gig) {
      return res.status(404).json({
        success: false,
        message: 'Gig not found'
      });
    }

    // Check if user is trying to buy their own gig
    if (gig.userId.toString() === req.userId.toString()) {
      return res.status(400).json({
        success: false,
        message: 'You cannot order your own gig'
      });
    }

    // Create order
    const order = await Order.create({
      gigId,
      buyerId: req.userId,
      sellerId: gig.userId,
      price: gig.price,
      status: 'pending',
      requirements: requirements || '',
      deliveryDate: deliveryDate || new Date(Date.now() + gig.deliveryTime * 24 * 60 * 60 * 1000),
      deliverables: [],
      createdAt: new Date(),
      updatedAt: new Date()
    });

    // Call RPC server
    try {
      await callRPC(req, 'order.create', [order._id.toString(), gigId, req.userId.toString()]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Order created successfully',
      data: order
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/orders/:id/status
 * @desc    Update order status
 * @access  Private (Owner or Admin)
 */
router.put('/:id/status', [
  param('id').isMongoId().withMessage('Invalid order ID'),
  body('status').isIn(['pending', 'in_progress', 'completed', 'cancelled', 'disputed']).withMessage('Invalid status')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const order = await Order.findById(req.params.id);

    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Check ownership
    const isBuyer = order.buyerId.toString() === req.userId.toString();
    const isSeller = order.sellerId.toString() === req.userId.toString();
    
    if (!isBuyer && !isSeller && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    // Status transition validation
    const validTransitions = {
      pending: ['in_progress', 'cancelled'],
      in_progress: ['completed', 'disputed', 'cancelled'],
      completed: [],
      cancelled: [],
      disputed: ['completed', 'cancelled']
    };

    if (!validTransitions[order.status].includes(req.body.status) && req.user.role !== 'admin') {
      return res.status(400).json({
        success: false,
        message: `Cannot change status from ${order.status} to ${req.body.status}`
      });
    }

    order.status = req.body.status;
    order.updatedAt = new Date();
    await order.save();

    // Call RPC server
    try {
      await callRPC(req, 'order.updateStatus', [req.params.id, req.body.status]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Order status updated successfully',
      data: order
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/orders/:id
 * @desc    Update order
 * @access  Private (Owner or Admin)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid order ID')
], updateOrderValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const order = await Order.findById(req.params.id);

    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Check ownership
    if (order.buyerId.toString() !== req.userId.toString() && 
        order.sellerId.toString() !== req.userId.toString() && 
        req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    const updates = { ...req.body, updatedAt: new Date() };
    const updatedOrder = await Order.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    res.json({
      success: true,
      message: 'Order updated successfully',
      data: updatedOrder
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/orders/:id
 * @desc    Delete order
 * @access  Private (Admin only)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid order ID')
], handleValidationErrors, authMiddleware, isOwnerOrAdmin, async (req, res, next) => {
  try {
    const order = await Order.findByIdAndDelete(req.params.id);

    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    res.json({
      success: true,
      message: 'Order deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
