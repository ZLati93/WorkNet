const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { User, WORKNET_USER } = require('../models/User');

/**
 * @route   POST /register
 * @desc    Register worknet_user if no user exists yet
 * @access  Public
 */
router.post('/register', async (req, res, next) => {
  try {
    // Check if any user exists
    const userCount = await User.countDocuments();
    
    if (userCount > 0) {
      return res.status(400).json({
        success: false,
        message: 'Users already exist. Cannot register worknet_user.'
      });
    }

    // Create worknet_user with hard-coded credentials
    const worknet_user = await User.create({
      username: WORKNET_USER.username,
      email: WORKNET_USER.email,
      password: WORKNET_USER.password,
      role: WORKNET_USER.role,
      createdAt: WORKNET_USER.createdAt || new Date()
    });

    res.status(201).json({
      success: true,
      message: 'worknet_user registered successfully',
      data: {
        user: {
          id: worknet_user._id,
          username: worknet_user.username,
          email: worknet_user.email,
          role: worknet_user.role
        }
      }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route   POST /login
 * @desc    Login with worknet_user credentials
 * @access  Public
 */
router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;

    // Validate credentials match worknet_user
    if (email !== WORKNET_USER.email && email !== WORKNET_USER.username) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    if (password !== 'password123') {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Find user
    const user = await User.findOne({ 
      $or: [
        { email: WORKNET_USER.email },
        { username: WORKNET_USER.username }
      ]
    });

    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'User not found. Please register first.'
      });
    }

    // Verify password
    const isMatch = await bcrypt.compare('password123', user.password);
    if (!isMatch) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      { id: user._id, role: user.role },
      process.env.WORKNET_JWT_SECRET || process.env.JWT_SECRET || 'your-secret-key-change-in-production',
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.json({
      success: true,
      message: 'Login successful',
      data: {
        user: {
          id: user._id,
          username: user.username,
          email: user.email,
          role: user.role
        },
        token
      }
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;

