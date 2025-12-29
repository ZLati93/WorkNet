// Placeholder Gig model - to be implemented with Mongoose schema
const mongoose = require('mongoose');

const GigSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  category: { type: String, required: true },
  subcategory: String,
  price: { type: Number, required: true },
  images: [String],
  deliveryTime: { type: Number, required: true },
  revisionNumber: { type: Number, default: 0 },
  features: [String],
  sales: { type: Number, default: 0 },
  rating: { type: Number, default: 0 },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.models.Gig || mongoose.model('Gig', GigSchema);

