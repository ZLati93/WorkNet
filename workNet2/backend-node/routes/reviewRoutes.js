const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Review = require('../models/reviewModel');
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

const createReviewValidation = [
  body('gigId').isMongoId().withMessage('Invalid gig ID'),
  body('orderId').isMongoId().withMessage('Invalid order ID'),
  body('rating').isInt({ min: 1, max: 5 }).withMessage('Rating must be between 1 and 5'),
  body('comment').trim().isLength({ min: 10, max: 1000 }).withMessage('Comment must be between 10 and 1000 characters')
];

/**
 * @route   GET /api/reviews
 * @desc    Get all reviews with pagination
 * @access  Public
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('gigId').optional().isMongoId(),
  query('userId').optional().isMongoId(),
  query('rating').optional().isInt({ min: 1, max: 5 })
], handleValidationErrors, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { gigId, userId, rating } = req.query;

    const query = {};
    if (gigId) query.gigId = gigId;
    if (userId) query.userId = userId;
    if (rating) query.rating = parseInt(rating);

    const reviews = await Review.find(query)
      .populate('userId', 'username profilePicture')
      .populate('gigId', 'title')
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Review.countDocuments(query);

    res.json(paginationResponse(reviews, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/reviews/:id
 * @desc    Get review by ID
 * @access  Public
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid review ID')
], handleValidationErrors, async (req, res, next) => {
  try {
    const review = await Review.findById(req.params.id)
      .populate('userId', 'username profilePicture')
      .populate('gigId', 'title');

    if (!review) {
      return res.status(404).json({
        success: false,
        message: 'Review not found'
      });
    }

    res.json({
      success: true,
      data: review
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/reviews
 * @desc    Create a new review
 * @access  Private
 */
router.post('/', createReviewValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { gigId, orderId, rating, comment } = req.body;

    // Verify order exists and belongs to user
    const order = await Order.findById(orderId);
    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }

    if (order.buyerId.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'You can only review orders you purchased'
      });
    }

    if (order.status !== 'completed') {
      return res.status(400).json({
        success: false,
        message: 'You can only review completed orders'
      });
    }

    // Check if review already exists for this order
    const existingReview = await Review.findOne({ orderId, userId: req.userId });
    if (existingReview) {
      return res.status(400).json({
        success: false,
        message: 'You have already reviewed this order'
      });
    }

    // Create review
    const review = await Review.create({
      gigId,
      userId: req.userId,
      orderId,
      rating,
      comment,
      isVerified: true,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    // Update gig rating
    const gigReviews = await Review.find({ gigId });
    const avgRating = gigReviews.reduce((sum, r) => sum + r.rating, 0) / gigReviews.length;
    await Gig.findByIdAndUpdate(gigId, { rating: avgRating });

    // Call RPC server for rating calculation
    try {
      await callRPC(req, 'review.create', [review._id.toString(), gigId, rating]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Review created successfully',
      data: review
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/reviews/:id
 * @desc    Update review
 * @access  Private (Owner only)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid review ID'),
  body('rating').optional().isInt({ min: 1, max: 5 }),
  body('comment').optional().trim().isLength({ min: 10, max: 1000 })
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const review = await Review.findById(req.params.id);

    if (!review) {
      return res.status(404).json({
        success: false,
        message: 'Review not found'
      });
    }

    if (review.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied. You can only update your own reviews.'
      });
    }

    const updates = { ...req.body, updatedAt: new Date() };
    const updatedReview = await Review.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    // Recalculate gig rating if rating changed
    if (req.body.rating) {
      const gigReviews = await Review.find({ gigId: review.gigId });
      const avgRating = gigReviews.reduce((sum, r) => sum + r.rating, 0) / gigReviews.length;
      await Gig.findByIdAndUpdate(review.gigId, { rating: avgRating });
    }

    res.json({
      success: true,
      message: 'Review updated successfully',
      data: updatedReview
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/reviews/:id
 * @desc    Delete review
 * @access  Private (Owner or Admin)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid review ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const review = await Review.findById(req.params.id);

    if (!review) {
      return res.status(404).json({
        success: false,
        message: 'Review not found'
      });
    }

    if (review.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    await Review.findByIdAndDelete(req.params.id);

    // Recalculate gig rating
    const gigReviews = await Review.find({ gigId: review.gigId });
    const avgRating = gigReviews.length > 0 
      ? gigReviews.reduce((sum, r) => sum + r.rating, 0) / gigReviews.length 
      : 0;
    await Gig.findByIdAndUpdate(review.gigId, { rating: avgRating });

    res.json({
      success: true,
      message: 'Review deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
