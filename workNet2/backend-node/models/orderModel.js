// Placeholder Order model - to be implemented with Mongoose schema
const mongoose = require('mongoose');

const OrderSchema = new mongoose.Schema({
  gigId: { type: mongoose.Schema.Types.ObjectId, ref: 'Gig', required: true },
  buyerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  price: { type: Number, required: true },
  status: { type: String, enum: ['pending', 'in_progress', 'completed', 'cancelled', 'disputed'], default: 'pending' },
  paymentIntent: String,
  deliveryDate: Date,
  requirements: String,
  deliverables: [String],
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.models.Order || mongoose.model('Order', OrderSchema);

