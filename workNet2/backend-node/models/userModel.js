// User model with Mongoose schema
const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, enum: ['client', 'freelancer', 'admin'], default: 'client' },
  profilePicture: String,
  phone: String,
  country: String,
  isSeller: { type: Boolean, default: false },
  skills: [String],
  rating: { type: Number, default: 0, min: 0, max: 5 },
  totalEarnings: { type: Number, default: 0 },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.models.User || mongoose.model('User', UserSchema);
