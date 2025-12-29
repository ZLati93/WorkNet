const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware, isOwnerOrAdmin } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Payment = require('../models/paymentModel');
const Order = require('../models/orderModel');

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

const createPaymentValidation = [
  body('orderId').isMongoId().withMessage('Invalid order ID'),
  body('amount').isFloat({ min: 0 }).withMessage('Amount must be a positive number'),
  body('paymentMethod').isIn(['stripe', 'paypal', 'bank_transfer', 'other']).withMessage('Invalid payment method'),
  body('currency').optional().matches(/^[A-Z]{3}$/).withMessage('Currency must be a 3-letter code')
];

/**
 * @route   GET /api/payments
 * @desc    Get all payments with pagination
 * @access  Private
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('status').optional().isIn(['pending', 'completed', 'failed', 'refunded']),
  query('paymentMethod').optional().isIn(['stripe', 'paypal', 'bank_transfer', 'other'])
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { status, paymentMethod } = req.query;

    const query = { userId: req.userId };
    if (status) query.status = status;
    if (paymentMethod) query.paymentMethod = paymentMethod;

    // Admin can see all payments
    if (req.user.role === 'admin') {
      delete query.userId;
    }

    const payments = await Payment.find(query)
      .populate('orderId', 'gigId buyerId sellerId price status')
      .populate('userId', 'username email')
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Payment.countDocuments(query);

    res.json(paginationResponse(payments, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/payments/:id
 * @desc    Get payment by ID
 * @access  Private (Owner or Admin)
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid payment ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const payment = await Payment.findById(req.params.id)
      .populate('orderId')
      .populate('userId', 'username email');

    if (!payment) {
      return res.status(404).json({
        success: false,
        message: 'Payment not found'
      });
    }

    // Check ownership
    if (payment.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    res.json({
      success: true,
      data: payment
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/payments
 * @desc    Create a new payment
 * @access  Private
 */
router.post('/', createPaymentValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { orderId, amount, paymentMethod, currency = 'USD', transactionId } = req.body;

    // Verify order exists
    const order = await Order.findById(orderId);
    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Check if user is the buyer
    if (order.buyerId.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'You can only pay for your own orders'
      });
    }

    // Check if payment already exists
    const existingPayment = await Payment.findOne({ orderId });
    if (existingPayment && existingPayment.status === 'completed') {
      return res.status(400).json({
        success: false,
        message: 'Payment already completed for this order'
      });
    }

    // Create payment
    const payment = await Payment.create({
      orderId,
      userId: req.userId,
      amount,
      status: 'pending',
      paymentMethod,
      transactionId: transactionId || null,
      currency,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    // Call RPC server for payment processing
    try {
      await callRPC(req, 'payment.create', [payment._id.toString(), orderId, amount, paymentMethod]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Payment created successfully',
      data: payment
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/payments/:id/process
 * @desc    Process payment (update status)
 * @access  Private (Admin or Payment Gateway webhook)
 */
router.put('/:id/process', [
  param('id').isMongoId().withMessage('Invalid payment ID'),
  body('status').isIn(['completed', 'failed', 'refunded']).withMessage('Invalid status'),
  body('transactionId').optional().isString()
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { status, transactionId } = req.body;

    // Only admin can process payments (or webhook with secret key)
    if (req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied. Admin only.'
      });
    }

    const payment = await Payment.findById(req.params.id);
    if (!payment) {
      return res.status(404).json({
        success: false,
        message: 'Payment not found'
      });
    }

    const updates = { status, updatedAt: new Date() };
    if (transactionId) updates.transactionId = transactionId;

    const updatedPayment = await Payment.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true }
    );

    // Update order status if payment completed
    if (status === 'completed') {
      await Order.findByIdAndUpdate(payment.orderId, {
        status: 'in_progress',
        updatedAt: new Date()
      });
    }

    // Call RPC server
    try {
      await callRPC(req, 'payment.process', [req.params.id, status]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Payment processed successfully',
      data: updatedPayment
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/payments/:id
 * @desc    Update payment
 * @access  Private (Admin only)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid payment ID'),
  body('status').optional().isIn(['pending', 'completed', 'failed', 'refunded']),
  body('transactionId').optional().isString()
], handleValidationErrors, authMiddleware, isOwnerOrAdmin, async (req, res, next) => {
  try {
    const updates = { ...req.body, updatedAt: new Date() };
    const payment = await Payment.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    if (!payment) {
      return res.status(404).json({
        success: false,
        message: 'Payment not found'
      });
    }

    res.json({
      success: true,
      message: 'Payment updated successfully',
      data: payment
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/payments/:id
 * @desc    Delete payment
 * @access  Private (Admin only)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid payment ID')
], handleValidationErrors, authMiddleware, isOwnerOrAdmin, async (req, res, next) => {
  try {
    const payment = await Payment.findByIdAndDelete(req.params.id);

    if (!payment) {
      return res.status(404).json({
        success: false,
        message: 'Payment not found'
      });
    }

    res.json({
      success: true,
      message: 'Payment deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
