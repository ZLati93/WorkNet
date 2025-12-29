const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware, authorize } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Notification = require('../models/notificationModel');

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

const createNotificationValidation = [
  body('userId').isMongoId().withMessage('Invalid user ID'),
  body('type').isIn(['order', 'message', 'review', 'payment', 'system']).withMessage('Invalid notification type'),
  body('message').trim().isLength({ min: 1, max: 500 }).withMessage('Message must be between 1 and 500 characters'),
  body('link').optional().isString()
];

/**
 * @route   GET /api/notifications
 * @desc    Get all notifications for current user with pagination
 * @access  Private
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('type').optional().isIn(['order', 'message', 'review', 'payment', 'system']),
  query('isRead').optional().isBoolean()
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const { type, isRead } = req.query;

    const query = { userId: req.userId };
    if (type) query.type = type;
    if (isRead !== undefined) query.isRead = isRead === 'true';

    const notifications = await Notification.find(query)
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Notification.countDocuments(query);
    const unreadCount = await Notification.countDocuments({ userId: req.userId, isRead: false });

    const response = paginationResponse(notifications, total, page, limit);
    response.unreadCount = unreadCount;

    res.json(response);
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/notifications/unread-count
 * @desc    Get unread notifications count
 * @access  Private
 */
router.get('/unread-count', authMiddleware, async (req, res, next) => {
  try {
    const count = await Notification.countDocuments({
      userId: req.userId,
      isRead: false
    });

    res.json({
      success: true,
      data: { count }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/notifications/:id
 * @desc    Get notification by ID
 * @access  Private
 */
router.get('/:id', [
  param('id').isMongoId().withMessage('Invalid notification ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const notification = await Notification.findById(req.params.id);

    if (!notification) {
      return res.status(404).json({
        success: false,
        message: 'Notification not found'
      });
    }

    // Check ownership
    if (notification.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    res.json({
      success: true,
      data: notification
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/notifications
 * @desc    Create a new notification
 * @access  Private (Admin or System)
 */
router.post('/', createNotificationValidation, handleValidationErrors, authMiddleware, authorize('admin'), async (req, res, next) => {
  try {
    const { userId, type, message, link } = req.body;

    const notification = await Notification.create({
      userId,
      type,
      message,
      link: link || null,
      isRead: false,
      createdAt: new Date()
    });

    // Call RPC server for real-time notification
    try {
      await callRPC(req, 'notification.create', [notification._id.toString(), userId, type]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Notification created successfully',
      data: notification
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/notifications/:id/read
 * @desc    Mark notification as read
 * @access  Private
 */
router.put('/:id/read', [
  param('id').isMongoId().withMessage('Invalid notification ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const notification = await Notification.findById(req.params.id);

    if (!notification) {
      return res.status(404).json({
        success: false,
        message: 'Notification not found'
      });
    }

    // Check ownership
    if (notification.userId.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    notification.isRead = true;
    await notification.save();

    res.json({
      success: true,
      message: 'Notification marked as read',
      data: notification
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/notifications/read-all
 * @desc    Mark all notifications as read
 * @access  Private
 */
router.put('/read-all', authMiddleware, async (req, res, next) => {
  try {
    await Notification.updateMany(
      { userId: req.userId, isRead: false },
      { $set: { isRead: true } }
    );

    res.json({
      success: true,
      message: 'All notifications marked as read'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/notifications/:id
 * @desc    Update notification
 * @access  Private (Admin only)
 */
router.put('/:id', [
  param('id').isMongoId().withMessage('Invalid notification ID'),
  body('message').optional().trim().isLength({ min: 1, max: 500 }),
  body('isRead').optional().isBoolean()
], handleValidationErrors, authMiddleware, authorize('admin'), async (req, res, next) => {
  try {
    const updates = { ...req.body };
    const notification = await Notification.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true, runValidators: true }
    );

    if (!notification) {
      return res.status(404).json({
        success: false,
        message: 'Notification not found'
      });
    }

    res.json({
      success: true,
      message: 'Notification updated successfully',
      data: notification
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/notifications/:id
 * @desc    Delete notification
 * @access  Private
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid notification ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const notification = await Notification.findById(req.params.id);

    if (!notification) {
      return res.status(404).json({
        success: false,
        message: 'Notification not found'
      });
    }

    // Check ownership or admin
    if (notification.userId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    await Notification.findByIdAndDelete(req.params.id);

    res.json({
      success: true,
      message: 'Notification deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/notifications
 * @desc    Delete all notifications for current user
 * @access  Private
 */
router.delete('/', authMiddleware, async (req, res, next) => {
  try {
    await Notification.deleteMany({ userId: req.userId });

    res.json({
      success: true,
      message: 'All notifications deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
