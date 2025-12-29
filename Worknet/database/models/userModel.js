const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema(
  {
    // Authentication fields
    email: {
      type: String,
      required: [true, 'Email is required'],
      unique: true,
      lowercase: true,
      trim: true,
      match: [/^\S+@\S+\.\S+$/, 'Please provide a valid email address'],
    },
    password: {
      type: String,
      required: [true, 'Password is required'],
      minlength: [6, 'Password must be at least 6 characters'],
      select: false, // Don't return password by default
    },
    username: {
      type: String,
      required: [true, 'Username is required'],
      unique: true,
      trim: true,
      minlength: [3, 'Username must be at least 3 characters'],
      maxlength: [30, 'Username cannot exceed 30 characters'],
    },

    // Basic profile fields
    firstName: {
      type: String,
      required: [true, 'First name is required'],
      trim: true,
    },
    lastName: {
      type: String,
      required: [true, 'Last name is required'],
      trim: true,
    },
    avatar: {
      type: String,
      default: null,
    },
    phone: {
      type: String,
      trim: true,
    },
    country: {
      type: String,
      trim: true,
    },
    city: {
      type: String,
      trim: true,
    },
    timezone: {
      type: String,
      default: 'UTC',
    },

    // Role management
    role: {
      type: String,
      enum: ['client', 'freelancer', 'admin'],
      default: 'client',
      required: true,
    },

    // Account status
    isEmailVerified: {
      type: Boolean,
      default: false,
    },
    emailVerificationToken: {
      type: String,
      select: false,
    },
    emailVerificationExpires: {
      type: Date,
      select: false,
    },
    passwordResetToken: {
      type: String,
      select: false,
    },
    passwordResetExpires: {
      type: Date,
      select: false,
    },
    isActive: {
      type: Boolean,
      default: true,
    },
    isSuspended: {
      type: Boolean,
      default: false,
    },
    lastLogin: {
      type: Date,
    },

    // Freelancer-specific fields
    freelancerProfile: {
      bio: {
        type: String,
        maxlength: [2000, 'Bio cannot exceed 2000 characters'],
      },
      title: {
        type: String,
        maxlength: [100, 'Title cannot exceed 100 characters'],
      },
      skills: [{
        type: String,
        trim: true,
      }],
      hourlyRate: {
        type: Number,
        min: [0, 'Hourly rate must be positive'],
      },
      availability: {
        type: String,
        enum: ['available', 'busy', 'unavailable'],
        default: 'available',
      },
      portfolio: [{
        title: String,
        description: String,
        url: String,
        image: String,
      }],
      education: [{
        institution: String,
        degree: String,
        field: String,
        startDate: Date,
        endDate: Date,
        description: String,
      }],
      experience: [{
        company: String,
        position: String,
        startDate: Date,
        endDate: Date,
        description: String,
        current: Boolean,
      }],
      languages: [{
        language: String,
        proficiency: {
          type: String,
          enum: ['basic', 'conversational', 'fluent', 'native'],
        },
      }],
      certifications: [{
        name: String,
        issuer: String,
        issueDate: Date,
        expiryDate: Date,
        credentialId: String,
        credentialUrl: String,
      }],
      rating: {
        average: {
          type: Number,
          default: 0,
          min: 0,
          max: 5,
        },
        count: {
          type: Number,
          default: 0,
        },
      },
      totalEarnings: {
        type: Number,
        default: 0,
        min: 0,
      },
      totalJobsCompleted: {
        type: Number,
        default: 0,
        min: 0,
      },
      responseTime: {
        type: Number, // in hours
        default: null,
      },
      responseRate: {
        type: Number, // percentage
        default: 0,
        min: 0,
        max: 100,
      },
    },

    // Client-specific fields (optional, for clients who may become freelancers)
    clientProfile: {
      companyName: {
        type: String,
        trim: true,
      },
      companyWebsite: {
        type: String,
        trim: true,
      },
      totalSpent: {
        type: Number,
        default: 0,
        min: 0,
      },
      totalProjects: {
        type: Number,
        default: 0,
        min: 0,
      },
    },

    // Preferences
    preferences: {
      emailNotifications: {
        type: Boolean,
        default: true,
      },
      pushNotifications: {
        type: Boolean,
        default: true,
      },
      newsletter: {
        type: Boolean,
        default: false,
      },
      language: {
        type: String,
        default: 'en',
      },
    },

    // Social authentication
    googleId: {
      type: String,
      select: false,
    },
    githubId: {
      type: String,
      select: false,
    },
  },
  {
    timestamps: true, // Adds createdAt and updatedAt fields
    toJSON: { virtuals: true },
    toObject: { virtuals: true },
  }
);

// Indexes for performance
userSchema.index({ email: 1 }); // Unique index (already unique)
userSchema.index({ username: 1 }); // Unique index (already unique)
userSchema.index({ role: 1 });
userSchema.index({ 'freelancerProfile.skills': 1 });
userSchema.index({ 'freelancerProfile.availability': 1 });
userSchema.index({ 'freelancerProfile.rating.average': -1 }); // Descending for sorting
userSchema.index({ isActive: 1, isSuspended: 1 });
userSchema.index({ createdAt: -1 });
userSchema.index({ 'freelancerProfile.hourlyRate': 1 }); // For range queries

// Compound indexes
userSchema.index({ role: 1, isActive: 1 });
userSchema.index({ role: 1, 'freelancerProfile.availability': 1 });

// Virtual for full name
userSchema.virtual('fullName').get(function() {
  return `${this.firstName} ${this.lastName}`;
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  // Only hash the password if it has been modified (or is new)
  if (!this.isModified('password')) return next();

  try {
    // Hash password with cost of 12
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Instance method to compare passwords
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Instance method to check if user is freelancer
userSchema.methods.isFreelancer = function() {
  return this.role === 'freelancer';
};

// Instance method to check if user is client
userSchema.methods.isClient = function() {
  return this.role === 'client';
};

// Instance method to check if user is admin
userSchema.methods.isAdmin = function() {
  return this.role === 'admin';
};

// Static method to find active freelancers
userSchema.statics.findActiveFreelancers = function() {
  return this.find({
    role: 'freelancer',
    isActive: true,
    isSuspended: false,
  });
};

const User = mongoose.model('User', userSchema);

module.exports = User;

