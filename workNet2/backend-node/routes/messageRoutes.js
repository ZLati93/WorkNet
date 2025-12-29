const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const { authMiddleware } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');
const { paginate, paginationResponse } = require('../utils/pagination');
const Message = require('../models/messageModel');
const Conversation = require('../models/conversationModel');

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

const createMessageValidation = [
  body('conversationId').isMongoId().withMessage('Invalid conversation ID'),
  body('text').trim().isLength({ min: 1, max: 5000 }).withMessage('Message must be between 1 and 5000 characters'),
  body('attachments').optional().isArray()
];

// Helper to get or create conversation
const getOrCreateConversation = async (userId1, userId2) => {
  let conversation = await Conversation.findOne({
    $or: [
      { user1Id: userId1, user2Id: userId2 },
      { user1Id: userId2, user2Id: userId1 }
    ]
  });

  if (!conversation) {
    conversation = await Conversation.create({
      user1Id: userId1,
      user2Id: userId2,
      lastMessageAt: new Date(),
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  return conversation;
};

/**
 * @route   GET /api/messages/conversations
 * @desc    Get all conversations for current user
 * @access  Private
 */
router.get('/conversations', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 })
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);

    const conversations = await Conversation.find({
      $or: [
        { user1Id: req.userId },
        { user2Id: req.userId }
      ]
    })
      .populate('user1Id', 'username profilePicture')
      .populate('user2Id', 'username profilePicture')
      .skip(skip)
      .limit(limit)
      .sort({ lastMessageAt: -1 });

    const total = await Conversation.countDocuments({
      $or: [
        { user1Id: req.userId },
        { user2Id: req.userId }
      ]
    });

    res.json(paginationResponse(conversations, total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   GET /api/messages/conversation/:conversationId
 * @desc    Get messages for a conversation
 * @access  Private
 */
router.get('/conversation/:conversationId', [
  param('conversationId').isMongoId().withMessage('Invalid conversation ID'),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 })
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { page, limit, skip } = paginate(req.query.page, req.query.limit);
    const conversation = await Conversation.findById(req.params.conversationId);

    if (!conversation) {
      return res.status(404).json({
        success: false,
        message: 'Conversation not found'
      });
    }

    // Check if user is part of conversation
    if (conversation.user1Id.toString() !== req.userId.toString() && 
        conversation.user2Id.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    const messages = await Message.find({ conversationId: req.params.conversationId })
      .populate('senderId', 'username profilePicture')
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const total = await Message.countDocuments({ conversationId: req.params.conversationId });

    res.json(paginationResponse(messages.reverse(), total, page, limit));
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/messages
 * @desc    Create a new message
 * @access  Private
 */
router.post('/', createMessageValidation, handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { conversationId, text, attachments = [] } = req.body;

    // Verify conversation exists and user is part of it
    const conversation = await Conversation.findById(conversationId);
    if (!conversation) {
      return res.status(404).json({
        success: false,
        message: 'Conversation not found'
      });
    }

    if (conversation.user1Id.toString() !== req.userId.toString() && 
        conversation.user2Id.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    // Create message
    const message = await Message.create({
      conversationId,
      senderId: req.userId,
      text,
      attachments,
      isRead: false,
      createdAt: new Date()
    });

    // Update conversation last message time
    await Conversation.findByIdAndUpdate(conversationId, {
      lastMessageAt: new Date(),
      updatedAt: new Date()
    });

    // Call RPC server for real-time messaging
    try {
      await callRPC(req, 'message.create', [message._id.toString(), conversationId, req.userId.toString()]);
    } catch (rpcError) {
      console.error('RPC call failed:', rpcError);
    }

    res.status(201).json({
      success: true,
      message: 'Message sent successfully',
      data: message
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /api/messages/send/:userId
 * @desc    Send message to a user (creates conversation if needed)
 * @access  Private
 */
router.post('/send/:userId', [
  param('userId').isMongoId().withMessage('Invalid user ID'),
  body('text').trim().isLength({ min: 1, max: 5000 }).withMessage('Message must be between 1 and 5000 characters')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const { text, attachments = [] } = req.body;
    const recipientId = req.params.userId;

    if (recipientId === req.userId.toString()) {
      return res.status(400).json({
        success: false,
        message: 'You cannot send a message to yourself'
      });
    }

    // Get or create conversation
    const conversation = await getOrCreateConversation(req.userId, recipientId);

    // Create message
    const message = await Message.create({
      conversationId: conversation._id,
      senderId: req.userId,
      text,
      attachments,
      isRead: false,
      createdAt: new Date()
    });

    // Update conversation
    await Conversation.findByIdAndUpdate(conversation._id, {
      lastMessageAt: new Date(),
      updatedAt: new Date()
    });

    res.status(201).json({
      success: true,
      message: 'Message sent successfully',
      data: message
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   PUT /api/messages/:id/read
 * @desc    Mark message as read
 * @access  Private
 */
router.put('/:id/read', [
  param('id').isMongoId().withMessage('Invalid message ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const message = await Message.findById(req.params.id);

    if (!message) {
      return res.status(404).json({
        success: false,
        message: 'Message not found'
      });
    }

    // Check if user is recipient
    const conversation = await Conversation.findById(message.conversationId);
    const isRecipient = conversation.user1Id.toString() === req.userId.toString() || 
                        conversation.user2Id.toString() === req.userId.toString();

    if (!isRecipient && message.senderId.toString() !== req.userId.toString()) {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    message.isRead = true;
    await message.save();

    res.json({
      success: true,
      message: 'Message marked as read',
      data: message
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   DELETE /api/messages/:id
 * @desc    Delete message
 * @access  Private (Owner only)
 */
router.delete('/:id', [
  param('id').isMongoId().withMessage('Invalid message ID')
], handleValidationErrors, authMiddleware, async (req, res, next) => {
  try {
    const message = await Message.findById(req.params.id);

    if (!message) {
      return res.status(404).json({
        success: false,
        message: 'Message not found'
      });
    }

    if (message.senderId.toString() !== req.userId.toString() && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Access denied'
      });
    }

    await Message.findByIdAndDelete(req.params.id);

    res.json({
      success: true,
      message: 'Message deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
