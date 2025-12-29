const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware, authorize } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Category = require('../models/categoryModel');

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

const createCategoryValidation = [
  body('name').trim().isLength({ min: 2, max: 100 }).withMessage('Name must be between 2 and 100 characters'),
  body('slug').trim().matches(/^[a-z0-9-]+$/).withMessage('Slug must be lowercase with hyphens'),
  body('description').optional().isString(),
  body('icon').optional().isString(),
  body('image').optional().isURL().withMessage('Image must be a valid URL')
];

const updateCategoryValidation = [
  body('name').optional().trim().isLength({ min: 2, max: 100 }),
  body('description').optional().isString(),
  body('isActive').optional().isBoolean()
];

/**
 * @route   GET /api/categories
 * @desc    Get all categories with pagination
 * @access  Public
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('isActive').optional().isBoolean()
], handleValidationErrors, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { isActive } = req.query;

    const query = {};
    if (isActive !== undefined) query.isActive = isActive === 'true';

    const categories = await Category.find(query)
      .skip(skip)
      .limit(limit)
      .sort({ name: 1 });

    const total = await Category.countDocuments(query);

    res.json(paginationResponse(categories, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/categories/:id
 * @desc    Get category by ID
 * @access  Public
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid category ID')
], handleValidationErrors, async (req, res, next) => {
  try {
    const category = await Category.findById(req.params.id);

    if (!category) {
      return res.status(404).json({
        success: false,
        message: 'Category not found'
      });
    }

    res.json({
      success: true,
      data: category
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/categories/slug/:slug
 * @desc    Get category by slug
 * @access  Public
 */
router.get('/slug/:slug', [
  param('slug').matches(/^[a-z0-9-]+$/).withMessage('Invalid slug format')
], handleValidationErrors, async (req, res, next) => {
  try {
    const category = await Category.findOne({ slug: req.params.slug });

    if (!category) {
      return res.status(404).json({
        success: false,
        message: 'Category not found'
      });
    }

    res.json({
      success: true,
      data: category
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/categories
 * @desc    Create a new category
 * @access  Private (Admin only)
 */
router.post('/', createCategoryValidation, handleValidationErrors, authMiddleware, authorize('admin'), async (req, res, next) => {
  try {
    const { name, slug, description, icon, image } = req.body;

    // Check if slug already exists
    const existingCategory = await Category.findOne({ slug });
    if (existingCategory) {
      return res.status(400).json({
        success: false,
        message: 'Category with this slug already exists'
      });
    }

    const category = await Category.create({
      name,
      slug,
      description,
      icon,
      image,
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    // Call RPC server
    try {
      await callRPC(req, 'category.create', [category._id.toString(), name, slug]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Category created successfully',
      data: category
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/categories/:id
 * @desc    Update category
 * @access  Private (Admin only)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid category ID')
], updateCategoryValidation, handleValidationErrors, authMiddleware, authorize('admin'), async (req, res, next) => {
  try {
    const updates = { ...req.body, updatedAt: new Date() };
    const category = await Category.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    if (!category) {
      return res.status(404).json({
        success: false,
        message: 'Category not found'
      });
    }

    // Call RPC server
    try {
      await callRPC(req, 'category.update', [req.params.id, updates]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Category updated successfully',
      data: category
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/categories/:id
 * @desc    Delete category
 * @access  Private (Admin only)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid category ID')
], handleValidationErrors, authMiddleware, authorize('admin'), async (req, res, next) => {
  try {
    const category = await Category.findByIdAndDelete(req.params.id);

    if (!category) {
      return res.status(404).json({
        success: false,
        message: 'Category not found'
      });
    }

    // Call RPC server
    try {
      await callRPC(req, 'category.delete', [req.params.id]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.json({
      success: true,
      message: 'Category deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
