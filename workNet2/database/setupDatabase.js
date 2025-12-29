const { MongoClient } = require('mongodb');
require('dotenv').config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority';
const DB_NAME = 'worknet';

// JSON Schema Validators for each collection
const validators = {
  users: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'email', 'password', 'role', 'createdAt'],
      properties: {
        username: {
          bsonType: 'string',
          minLength: 3,
          maxLength: 50,
          description: 'must be a string between 3 and 50 characters'
        },
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
          description: 'must be a valid email address'
        },
        password: {
          bsonType: 'string',
          minLength: 6,
          description: 'must be a string with at least 6 characters'
        },
        role: {
          enum: ['client', 'freelancer', 'admin'],
          description: 'must be one of: client, freelancer, admin'
        },
        profilePicture: {
          bsonType: 'string',
          description: 'must be a string (URL)'
        },
        phone: {
          bsonType: 'string',
          description: 'must be a string'
        },
        country: {
          bsonType: 'string',
          description: 'must be a string'
        },
        isSeller: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        skills: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings'
        },
        rating: {
          bsonType: 'number',
          minimum: 0,
          maximum: 5,
          description: 'must be a number between 0 and 5'
        },
        totalEarnings: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  gigs: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['userId', 'title', 'description', 'category', 'price', 'createdAt'],
      properties: {
        userId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        title: {
          bsonType: 'string',
          minLength: 5,
          maxLength: 200,
          description: 'must be a string between 5 and 200 characters'
        },
        description: {
          bsonType: 'string',
          minLength: 20,
          description: 'must be a string with at least 20 characters'
        },
        category: {
          bsonType: 'string',
          description: 'must be a string'
        },
        subcategory: {
          bsonType: 'string',
          description: 'must be a string'
        },
        price: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        images: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings (URLs)'
        },
        deliveryTime: {
          bsonType: 'number',
          minimum: 1,
          description: 'must be a positive number (days)'
        },
        revisionNumber: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        features: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings'
        },
        sales: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        rating: {
          bsonType: 'number',
          minimum: 0,
          maximum: 5,
          description: 'must be a number between 0 and 5'
        },
        isActive: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  orders: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['gigId', 'buyerId', 'sellerId', 'price', 'status', 'createdAt'],
      properties: {
        gigId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        buyerId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        sellerId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        price: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        status: {
          enum: ['pending', 'in_progress', 'completed', 'cancelled', 'disputed'],
          description: 'must be one of: pending, in_progress, completed, cancelled, disputed'
        },
        paymentIntent: {
          bsonType: 'string',
          description: 'must be a string'
        },
        deliveryDate: {
          bsonType: 'date',
          description: 'must be a date'
        },
        requirements: {
          bsonType: 'string',
          description: 'must be a string'
        },
        deliverables: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  categories: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'slug', 'createdAt'],
      properties: {
        name: {
          bsonType: 'string',
          minLength: 2,
          maxLength: 100,
          description: 'must be a string between 2 and 100 characters'
        },
        slug: {
          bsonType: 'string',
          pattern: '^[a-z0-9-]+$',
          description: 'must be a lowercase string with hyphens'
        },
        description: {
          bsonType: 'string',
          description: 'must be a string'
        },
        icon: {
          bsonType: 'string',
          description: 'must be a string (icon name or URL)'
        },
        image: {
          bsonType: 'string',
          description: 'must be a string (URL)'
        },
        isActive: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  reviews: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['gigId', 'userId', 'rating', 'comment', 'createdAt'],
      properties: {
        gigId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        userId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        orderId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        rating: {
          bsonType: 'number',
          minimum: 1,
          maximum: 5,
          description: 'must be a number between 1 and 5'
        },
        comment: {
          bsonType: 'string',
          minLength: 10,
          maxLength: 1000,
          description: 'must be a string between 10 and 1000 characters'
        },
        isVerified: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  messages: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['conversationId', 'senderId', 'text', 'createdAt'],
      properties: {
        conversationId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        senderId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        text: {
          bsonType: 'string',
          minLength: 1,
          maxLength: 5000,
          description: 'must be a string between 1 and 5000 characters'
        },
        attachments: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings (URLs)'
        },
        isRead: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  payments: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['orderId', 'userId', 'amount', 'status', 'createdAt'],
      properties: {
        orderId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        userId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        amount: {
          bsonType: 'number',
          minimum: 0,
          description: 'must be a non-negative number'
        },
        status: {
          enum: ['pending', 'completed', 'failed', 'refunded'],
          description: 'must be one of: pending, completed, failed, refunded'
        },
        paymentMethod: {
          enum: ['stripe', 'paypal', 'bank_transfer', 'other'],
          description: 'must be one of: stripe, paypal, bank_transfer, other'
        },
        transactionId: {
          bsonType: 'string',
          description: 'must be a string'
        },
        currency: {
          bsonType: 'string',
          pattern: '^[A-Z]{3}$',
          description: 'must be a 3-letter currency code'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  favorites: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['userId', 'gigId', 'createdAt'],
      properties: {
        userId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        gigId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  notifications: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['userId', 'type', 'message', 'createdAt'],
      properties: {
        userId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        type: {
          enum: ['order', 'message', 'review', 'payment', 'system'],
          description: 'must be one of: order, message, review, payment, system'
        },
        message: {
          bsonType: 'string',
          minLength: 1,
          maxLength: 500,
          description: 'must be a string between 1 and 500 characters'
        },
        link: {
          bsonType: 'string',
          description: 'must be a string (URL)'
        },
        isRead: {
          bsonType: 'bool',
          description: 'must be a boolean'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  },
  complaints: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['orderId', 'complainantId', 'defendantId', 'reason', 'status', 'createdAt'],
      properties: {
        orderId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        complainantId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        defendantId: {
          bsonType: 'objectId',
          description: 'must be an ObjectId'
        },
        reason: {
          bsonType: 'string',
          minLength: 10,
          maxLength: 2000,
          description: 'must be a string between 10 and 2000 characters'
        },
        status: {
          enum: ['pending', 'under_review', 'resolved', 'rejected'],
          description: 'must be one of: pending, under_review, resolved, rejected'
        },
        resolution: {
          bsonType: 'string',
          description: 'must be a string'
        },
        attachments: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'must be an array of strings (URLs)'
        },
        createdAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'must be a date'
        },
        resolvedAt: {
          bsonType: 'date',
          description: 'must be a date'
        }
      }
    }
  }
};

// Indexes for each collection
const indexes = {
  users: [
    { key: { email: 1 }, unique: true, name: 'email_unique' },
    { key: { username: 1 }, unique: true, name: 'username_unique' },
    { key: { role: 1 }, name: 'role_index' },
    { key: { isSeller: 1 }, name: 'isSeller_index' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' }
  ],
  gigs: [
    { key: { userId: 1 }, name: 'userId_index' },
    { key: { category: 1 }, name: 'category_index' },
    { key: { isActive: 1 }, name: 'isActive_index' },
    { key: { price: 1 }, name: 'price_asc' },
    { key: { rating: -1 }, name: 'rating_desc' },
    { key: { sales: -1 }, name: 'sales_desc' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' },
    { key: { title: 'text', description: 'text' }, name: 'text_search' }
  ],
  orders: [
    { key: { buyerId: 1 }, name: 'buyerId_index' },
    { key: { sellerId: 1 }, name: 'sellerId_index' },
    { key: { gigId: 1 }, name: 'gigId_index' },
    { key: { status: 1 }, name: 'status_index' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' },
    { key: { buyerId: 1, status: 1 }, name: 'buyer_status' },
    { key: { sellerId: 1, status: 1 }, name: 'seller_status' }
  ],
  categories: [
    { key: { slug: 1 }, unique: true, name: 'slug_unique' },
    { key: { name: 1 }, name: 'name_index' },
    { key: { isActive: 1 }, name: 'isActive_index' }
  ],
  reviews: [
    { key: { gigId: 1 }, name: 'gigId_index' },
    { key: { userId: 1 }, name: 'userId_index' },
    { key: { orderId: 1 }, name: 'orderId_index' },
    { key: { rating: -1 }, name: 'rating_desc' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' },
    { key: { gigId: 1, userId: 1 }, unique: true, name: 'gig_user_unique' }
  ],
  messages: [
    { key: { conversationId: 1 }, name: 'conversationId_index' },
    { key: { senderId: 1 }, name: 'senderId_index' },
    { key: { isRead: 1 }, name: 'isRead_index' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' },
    { key: { conversationId: 1, createdAt: -1 }, name: 'conversation_created' }
  ],
  payments: [
    { key: { orderId: 1 }, name: 'orderId_index' },
    { key: { userId: 1 }, name: 'userId_index' },
    { key: { status: 1 }, name: 'status_index' },
    { key: { transactionId: 1 }, unique: true, sparse: true, name: 'transactionId_unique' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' }
  ],
  favorites: [
    { key: { userId: 1 }, name: 'userId_index' },
    { key: { gigId: 1 }, name: 'gigId_index' },
    { key: { userId: 1, gigId: 1 }, unique: true, name: 'user_gig_unique' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' }
  ],
  notifications: [
    { key: { userId: 1 }, name: 'userId_index' },
    { key: { type: 1 }, name: 'type_index' },
    { key: { isRead: 1 }, name: 'isRead_index' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' },
    { key: { userId: 1, isRead: 1 }, name: 'user_unread' }
  ],
  complaints: [
    { key: { orderId: 1 }, name: 'orderId_index' },
    { key: { complainantId: 1 }, name: 'complainantId_index' },
    { key: { defendantId: 1 }, name: 'defendantId_index' },
    { key: { status: 1 }, name: 'status_index' },
    { key: { createdAt: -1 }, name: 'createdAt_desc' }
  ]
};

async function setupDatabase() {
  const client = new MongoClient(MONGODB_URI);
  
  try {
    await client.connect();
    console.log('Connected to MongoDB');
    
    const db = client.db(DB_NAME);
    
    // Drop existing collections (optional - comment out if you want to keep existing data)
    // const collections = await db.listCollections().toArray();
    // for (const collection of collections) {
    //   await db.collection(collection.name).drop();
    //   console.log(`Dropped collection: ${collection.name}`);
    // }
    
    // Create collections with validators
    for (const [collectionName, validator] of Object.entries(validators)) {
      try {
        // Check if collection exists
        const collections = await db.listCollections({ name: collectionName }).toArray();
        
        if (collections.length === 0) {
          // Create collection with validator
          await db.createCollection(collectionName, {
            validator: validator
          });
          console.log(`✓ Created collection: ${collectionName} with validator`);
        } else {
          // Update existing collection validator
          await db.command({
            collMod: collectionName,
            validator: validator,
            validationLevel: 'strict',
            validationAction: 'error'
          });
          console.log(`✓ Updated validator for collection: ${collectionName}`);
        }
        
        // Create indexes
        if (indexes[collectionName]) {
          const collection = db.collection(collectionName);
          for (const index of indexes[collectionName]) {
            try {
              await collection.createIndex(index.key, {
                unique: index.unique || false,
                name: index.name,
                sparse: index.sparse || false
              });
              console.log(`  ✓ Created index: ${index.name} on ${collectionName}`);
            } catch (error) {
              if (error.code !== 85) { // Ignore duplicate key error
                console.log(`  ⚠ Index ${index.name} already exists or error: ${error.message}`);
              }
            }
          }
        }
      } catch (error) {
        console.error(`Error setting up collection ${collectionName}:`, error.message);
      }
    }
    
    console.log('\n✅ Database setup completed successfully!');
    
  } catch (error) {
    console.error('Error setting up database:', error);
    throw error;
  } finally {
    await client.close();
    console.log('MongoDB connection closed');
  }
}

// Run if executed directly
if (require.main === module) {
  setupDatabase()
    .then(() => {
      console.log('Setup script completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Setup script failed:', error);
      process.exit(1);
    });
}

module.exports = { setupDatabase, validators, indexes };

