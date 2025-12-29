const { MongoClient, ObjectId } = require('mongodb');
require('dotenv').config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority';
const DB_NAME = 'worknet';

// Sample Categories
const sampleCategories = [
  {
    name: 'Graphic Design',
    slug: 'graphic-design',
    description: 'Professional graphic design services including logos, branding, and visual identity',
    icon: 'palette',
    image: 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Web Development',
    slug: 'web-development',
    description: 'Custom website development and web application services',
    icon: 'code',
    image: 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Writing & Translation',
    slug: 'writing-translation',
    description: 'Professional writing, editing, and translation services',
    icon: 'pen',
    image: 'https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Video & Animation',
    slug: 'video-animation',
    description: 'Video editing, animation, and motion graphics services',
    icon: 'video',
    image: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Music & Audio',
    slug: 'music-audio',
    description: 'Music production, voice-over, and audio editing services',
    icon: 'music',
    image: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Programming & Tech',
    slug: 'programming-tech',
    description: 'Software development, mobile apps, and technical services',
    icon: 'laptop',
    image: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Business',
    slug: 'business',
    description: 'Business consulting, marketing, and strategy services',
    icon: 'briefcase',
    image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Digital Marketing',
    slug: 'digital-marketing',
    description: 'SEO, social media marketing, and online advertising services',
    icon: 'megaphone',
    image: 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

// Sample Users
const sampleUsers = [
  {
    username: 'john_doe',
    email: 'john.doe@example.com',
    password: '$2b$10$rOzJqXQZqXQZqXQZqXQZqOeXQZqXQZqXQZqXQZqXQZqXQZqXQZqXQZ', // hashed password
    role: 'client',
    profilePicture: 'https://i.pravatar.cc/150?img=1',
    phone: '+1234567890',
    country: 'United States',
    isSeller: false,
    skills: [],
    rating: 0,
    totalEarnings: 0,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    username: 'jane_smith',
    email: 'jane.smith@example.com',
    password: '$2b$10$rOzJqXQZqXQZqXQZqXQZqOeXQZqXQZqXQZqXQZqXQZqXQZqXQZqXQZ',
    role: 'freelancer',
    profilePicture: 'https://i.pravatar.cc/150?img=2',
    phone: '+1234567891',
    country: 'Canada',
    isSeller: true,
    skills: ['Graphic Design', 'Logo Design', 'Branding'],
    rating: 4.8,
    totalEarnings: 15000,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    username: 'mike_dev',
    email: 'mike.dev@example.com',
    password: '$2b$10$rOzJqXQZqXQZqXQZqXQZqOeXQZqXQZqXQZqXQZqXQZqXQZqXQZqXQZ',
    role: 'freelancer',
    profilePicture: 'https://i.pravatar.cc/150?img=3',
    phone: '+1234567892',
    country: 'United Kingdom',
    isSeller: true,
    skills: ['Web Development', 'React', 'Node.js', 'MongoDB'],
    rating: 4.9,
    totalEarnings: 25000,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    username: 'sarah_writer',
    email: 'sarah.writer@example.com',
    password: '$2b$10$rOzJqXQZqXQZqXQZqXQZqOeXQZqXQZqXQZqXQZqXQZqXQZqXQZqXQZ',
    role: 'freelancer',
    profilePicture: 'https://i.pravatar.cc/150?img=4',
    phone: '+1234567893',
    country: 'Australia',
    isSeller: true,
    skills: ['Content Writing', 'Copywriting', 'SEO'],
    rating: 4.7,
    totalEarnings: 12000,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    username: 'admin_user',
    email: 'admin@worknet.com',
    password: '$2b$10$rOzJqXQZqXQZqXQZqXQZqOeXQZqXQZqXQZqXQZqXQZqXQZqXQZqXQZ',
    role: 'admin',
    profilePicture: 'https://i.pravatar.cc/150?img=5',
    phone: '+1234567894',
    country: 'United States',
    isSeller: false,
    skills: [],
    rating: 0,
    totalEarnings: 0,
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

async function insertSampleData() {
  const client = new MongoClient(MONGODB_URI);
  
  try {
    await client.connect();
    console.log('Connected to MongoDB');
    
    const db = client.db(DB_NAME);
    
    // Insert Categories
    console.log('\n📁 Inserting categories...');
    const categoriesCollection = db.collection('categories');
    const existingCategories = await categoriesCollection.find({}).toArray();
    
    if (existingCategories.length === 0) {
      const categoryResult = await categoriesCollection.insertMany(sampleCategories);
      console.log(`✓ Inserted ${categoryResult.insertedCount} categories`);
    } else {
      console.log(`⚠ Categories already exist (${existingCategories.length} found). Skipping...`);
    }
    
    // Get category IDs for gigs
    const categories = await categoriesCollection.find({}).toArray();
    const categoryMap = {};
    categories.forEach(cat => {
      categoryMap[cat.slug] = cat._id;
    });
    
    // Insert Users
    console.log('\n👥 Inserting users...');
    const usersCollection = db.collection('users');
    const existingUsers = await usersCollection.find({}).toArray();
    
    let userIds = [];
    if (existingUsers.length === 0) {
      const userResult = await usersCollection.insertMany(sampleUsers);
      console.log(`✓ Inserted ${userResult.insertedCount} users`);
      userIds = Object.values(userResult.insertedIds);
    } else {
      console.log(`⚠ Users already exist (${existingUsers.length} found). Using existing users...`);
      userIds = existingUsers.map(u => u._id);
    }
    
    // Get freelancer and client IDs
    const freelancers = await usersCollection.find({ role: 'freelancer' }).toArray();
    const clients = await usersCollection.find({ role: 'client' }).toArray();
    
    if (freelancers.length === 0 || clients.length === 0) {
      console.log('⚠ Need at least one freelancer and one client to create sample gigs and orders');
      return;
    }
    
    const freelancerId = freelancers[0]._id;
    const clientId = clients[0]._id;
    
    // Sample Gigs
    const sampleGigs = [
      {
        userId: freelancerId,
        title: 'Professional Logo Design',
        description: 'I will create a professional logo design for your brand. Includes 3 initial concepts, unlimited revisions, and final files in multiple formats (PNG, SVG, PDF).',
        category: 'Graphic Design',
        subcategory: 'Logo Design',
        price: 50,
        images: [
          'https://images.unsplash.com/photo-1611262588024-d12430b98920?w=800',
          'https://images.unsplash.com/photo-1558655146-9f40138edfeb?w=800'
        ],
        deliveryTime: 3,
        revisionNumber: 3,
        features: ['3 Logo Concepts', 'Unlimited Revisions', 'High Resolution Files', 'Source Files'],
        sales: 25,
        rating: 4.8,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        userId: freelancerId,
        title: 'Modern Website Development',
        description: 'I will build a modern, responsive website using React and Node.js. Includes frontend, backend, database setup, and deployment assistance.',
        category: 'Web Development',
        subcategory: 'Full Stack Development',
        price: 500,
        images: [
          'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800'
        ],
        deliveryTime: 14,
        revisionNumber: 2,
        features: ['Responsive Design', 'SEO Optimized', 'Database Integration', 'Deployment Support'],
        sales: 10,
        rating: 4.9,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        userId: freelancers.length > 1 ? freelancers[1]._id : freelancerId,
        title: 'SEO-Optimized Blog Content',
        description: 'I will write high-quality, SEO-optimized blog posts for your website. Includes keyword research, content writing, and optimization.',
        category: 'Writing & Translation',
        subcategory: 'Content Writing',
        price: 30,
        images: [
          'https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800'
        ],
        deliveryTime: 2,
        revisionNumber: 2,
        features: ['SEO Optimized', 'Keyword Research', 'Original Content', 'Proofreading'],
        sales: 45,
        rating: 4.7,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ];
    
    // Insert Gigs
    console.log('\n💼 Inserting gigs...');
    const gigsCollection = db.collection('gigs');
    const existingGigs = await gigsCollection.find({}).toArray();
    
    let gigIds = [];
    if (existingGigs.length === 0) {
      const gigResult = await gigsCollection.insertMany(sampleGigs);
      console.log(`✓ Inserted ${gigResult.insertedCount} gigs`);
      gigIds = Object.values(gigResult.insertedIds);
    } else {
      console.log(`⚠ Gigs already exist (${existingGigs.length} found). Using existing gigs...`);
      gigIds = existingGigs.map(g => g._id);
    }
    
    if (gigIds.length > 0) {
      // Sample Orders
      const sampleOrders = [
        {
          gigId: gigIds[0],
          buyerId: clientId,
          sellerId: freelancerId,
          price: 50,
          status: 'completed',
          paymentIntent: 'pi_sample_123456',
          deliveryDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
          requirements: 'Need a logo for a tech startup. Colors: blue and white. Style: modern and minimalist.',
          deliverables: ['Logo PNG', 'Logo SVG', 'Logo PDF'],
          createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
          updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        },
        {
          gigId: gigIds[0],
          buyerId: clientId,
          sellerId: freelancerId,
          price: 50,
          status: 'in_progress',
          paymentIntent: 'pi_sample_789012',
          deliveryDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
          requirements: 'Logo for a restaurant. Theme: Italian cuisine.',
          deliverables: [],
          createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
          updatedAt: new Date()
        }
      ];
      
      // Insert Orders
      console.log('\n📦 Inserting orders...');
      const ordersCollection = db.collection('orders');
      const existingOrders = await ordersCollection.find({}).toArray();
      
      if (existingOrders.length === 0) {
        const orderResult = await ordersCollection.insertMany(sampleOrders);
        console.log(`✓ Inserted ${orderResult.insertedCount} orders`);
      } else {
        console.log(`⚠ Orders already exist (${existingOrders.length} found). Skipping...`);
      }
      
      // Sample Reviews
      const sampleReviews = [
        {
          gigId: gigIds[0],
          userId: clientId,
          orderId: sampleOrders[0]._id || new ObjectId(),
          rating: 5,
          comment: 'Excellent work! The logo exceeded my expectations. Very professional and delivered on time.',
          isVerified: true,
          createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
          updatedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000)
        }
      ];
      
      // Insert Reviews
      console.log('\n⭐ Inserting reviews...');
      const reviewsCollection = db.collection('reviews');
      const existingReviews = await reviewsCollection.find({}).toArray();
      
      if (existingReviews.length === 0) {
        const reviewResult = await reviewsCollection.insertMany(sampleReviews);
        console.log(`✓ Inserted ${reviewResult.insertedCount} reviews`);
      } else {
        console.log(`⚠ Reviews already exist (${existingReviews.length} found). Skipping...`);
      }
    }
    
    // Sample Notifications
    const sampleNotifications = [
      {
        userId: clientId,
        type: 'order',
        message: 'Your order has been completed',
        link: '/orders/123',
        isRead: false,
        createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000)
      },
      {
        userId: freelancerId,
        type: 'message',
        message: 'You have a new message',
        link: '/messages',
        isRead: false,
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000)
      }
    ];
    
    // Insert Notifications
    console.log('\n🔔 Inserting notifications...');
    const notificationsCollection = db.collection('notifications');
    const existingNotifications = await notificationsCollection.find({}).toArray();
    
    if (existingNotifications.length === 0) {
      const notificationResult = await notificationsCollection.insertMany(sampleNotifications);
      console.log(`✓ Inserted ${notificationResult.insertedCount} notifications`);
    } else {
      console.log(`⚠ Notifications already exist (${existingNotifications.length} found). Skipping...`);
    }
    
    console.log('\n✅ Sample data insertion completed successfully!');
    
  } catch (error) {
    console.error('Error inserting sample data:', error);
    throw error;
  } finally {
    await client.close();
    console.log('MongoDB connection closed');
  }
}

// Run if executed directly
if (require.main === module) {
  insertSampleData()
    .then(() => {
      console.log('Insert script completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Insert script failed:', error);
      process.exit(1);
    });
}

module.exports = { insertSampleData };

