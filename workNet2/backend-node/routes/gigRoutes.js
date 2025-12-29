const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware, isSeller, isOwnerOrAdmin } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
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

const createGigValidation = [
  body('title').trim().isLength({ min: 5, max: 200 }).withMessage('Title must be between 5 and 200 characters'),
  body('description').trim().isLength({ min: 20 }).withMessage('Description must be at least 20 characters'),
  body('category').notEmpty().withMessage('Category is required'),
  body('price').isFloat({ min: 0 }).withMessage('Price must be a positive number'),
  body('deliveryTime').isInt({ min: 1 }).withMessage('Delivery time must be at least 1 day'),
  body('revisionNumber').optional().isInt({ min: 0 }),
  body('images').optional().isArray(),
  body('features').optional().isArray()
];

const updateGigValidation = [
  body('title').optional().trim().isLength({ min: 5, max: 200 }),
  body('description').optional().trim().isLength({ min: 20 }),
  body('price').optional().isFloat({ min: 0 }),
  body('deliveryTime').optional().isInt({ min: 1 }),
  body('isActive').optional().isBoolean()
];

/**
 * @route   GET /api/gigs
 * @desc    Get all gigs with pagination, search, and filtering
 * @access  Public
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('category').optional().isString(),
  query('minPrice').optional().isFloat({ min: 0 }),
  query('maxPrice').optional().isFloat({ min: 0 }),
  query('search').optional().isString(),
  query('sort').optional().isIn(['price', 'rating', 'sales', 'createdAt']),
  query('order').optional().isIn(['asc', 'desc'])
], handleValidationErrors, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { category, minPrice, maxPrice, search, sort = 'createdAt', order = 'desc' } = req.query;

    // Build query
    const query = { isActive: true };
    if (category) query.category = category;
    if (minPrice || maxPrice) {
      query.price = {};
      if (minPrice) query.price.$gte = parseFloat(minPrice);
      if (maxPrice) query.price.$lte = parseFloat(maxPrice);
    }
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } }
      ];
    }

    // Sort
    const sortOrder = order === 'asc' ? 1 : -1;
    const sortObj = { [sort]: sortOrder };

    // Get gigs
    const gigs = await Gig.find(query)
      .populate('userId', 'username profilePicture rating')
      .skip(skip)
      .limit(limit)
      .sort(sortObj);

    const total = await Gig.countDocuments(query);

    res.json(paginationResponse(gigs, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/gigs/:id
 * @desc    Get gig by ID
 * @access  Public
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid gig ID')
], handleValidationErrors, async (req, res, next) => {
  try {
    const gig = await Gig.findById(req.params.id)
      .populate('userId', 'username profilePicture rating totalEarnings');

    if (!gig) {
      return res.status(404).json({
        success: false,
        message: 'Gig not found'
      });
    }

    res.json({
      success: true,
      data: gig
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/gigs
 * @desc    Create a new gig
 * @access  Private (Seller only)
 */
router.post('/', createGigValidation, handleValidationErrors, authMiddleware, isSeller, async (req, res, next) => {
  try {
    const gigData = {
      ...req.body,
      userId: req.userId,
      createdAt: new Date(),
      updatedAt: new Date(),
      sales: 0,
      rating: 0,
      isActive: true
    };

    const gig = await Gig.create(gigData);

    // Call RPC server
    try {
      await callRPC(req, 'gig.create', [gig._id.toString(), gig.userId.toString(), gig.title]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Gig created successfully',
      data: gig
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/gigs/:id
 * @desc    Update gig
 * @access  Private (Owner only)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid gig ID')
], updateGigValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const gig = await Gig.findById(req.params.id);

    if (!gig) {
      return res.status(404).json({
        success: false,
        message: 'Gig not found'
      });
    }

    // Check ownership
    if (gig.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied. You can only update your own gigs.'
      });
    }

    const updates = { ...req.body, updatedAt: new Date() };
    const updatedGig = await Gig.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    // Call RPC server
    try {
      await callRPC(req, 'gig.update', [req.params.id, updates]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Gig updated successfully',
      data: updatedGig
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/gigs/:id
 * @desc    Delete gig
 * @access  Private (Owner or Admin)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid gig ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const gig = await Gig.findById(req.params.id);

    if (!gig) {
      return res.status(404).json({
        success: false,
        message: 'Gig not found'
      });
    }

    // Check ownership
    if (gig.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied. You can only delete your own gigs.'
      });
    }

    await Gig.findByIdAndDelete(req.params.id);

    // Call RPC server
    try {
      await callRPC(req, 'gig.delete', [req.params.id]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Gig deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/gigs/user/:userId
 * @desc    Get gigs by user ID
 * @access  Public
 */
router.get('/user/:userId', [
  param('userId').isMongoId().withMessage('Invalid user ID'),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 })
], handleValidationErrors, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);

    const gigs = await Gig.find({ userId: req.params.userId, isActive: true })
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Gig.countDocuments({ userId: req.params.userId, isActive: true });

    res.json(paginationResponse(gigs, total, page, limit));
  } catch (error) {
    next(error);
  }
});

module.exports = router;
