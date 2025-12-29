const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

// Hard-coded credentials for worknet_user
const WORKNET_USER = {
  username: 'test@example.com',
  email: 'test@example.com',
  password: '$2a$10$AlgeWfbh6iCt/RavVb71IOx1jG7xkSfvtrzsldEAnanyvhHANlAf2', // bcrypt hash of "password123" with 10 rounds
  role: 'user',
  createdAt: new Date()
};

const UserSchema = new mongoose.Schema({
  username: { 
    type: String, 
    required: true, 
    unique: true,
    default: WORKNET_USER.username
  },
  email: { 
    type: String, 
    required: true, 
    unique: true,
    default: WORKNET_USER.email
  },
  password: { 
    type: String, 
    required: true,
    default: WORKNET_USER.password
  },
  role: { 
    type: String, 
    enum: ['client', 'freelancer', 'admin', 'user'], 
    default: WORKNET_USER.role
  },
  profilePicture: String,
  phone: String,
  country: String,
  isSeller: { type: Boolean, default: false },
  skills: [String],
  rating: { type: Number, default: 0, min: 0, max: 5 },
  totalEarnings: { type: Number, default: 0 },
  createdAt: { 
    type: Date, 
    default: WORKNET_USER.createdAt || Date.now
  },
  updatedAt: { type: Date, default: Date.now }
});

// Export the model and the worknet_user constant
module.exports = {
  User: mongoose.models.User || mongoose.model('User', UserSchema),
  WORKNET_USER
};

