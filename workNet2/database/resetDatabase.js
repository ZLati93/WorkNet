const { MongoClient } = require('mongodb');
require('dotenv').config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority';
const DB_NAME = 'worknet';

async function resetDatabase() {
  const client = new MongoClient(MONGODB_URI);
  
  try {
    await client.connect();
    console.log('Connected to MongoDB');
    
    const db = client.db(DB_NAME);
    
    // List all collections
    const collections = await db.listCollections().toArray();
    
    if (collections.length === 0) {
      console.log('No collections found. Database is already empty.');
      return;
    }
    
    console.log(`\n⚠️  WARNING: This will delete all data from the following collections:`);
    collections.forEach(col => console.log(`   - ${col.name}`));
    
    // Drop all collections
    for (const collection of collections) {
      await db.collection(collection.name).drop();
      console.log(`✓ Dropped collection: ${collection.name}`);
    }
    
    console.log('\n✅ Database reset completed successfully!');
    console.log('💡 Run "npm run setup" to recreate collections with validators');
    console.log('💡 Run "npm run seed" to insert sample data');
    
  } catch (error) {
    console.error('Error resetting database:', error);
    throw error;
  } finally {
    await client.close();
    console.log('MongoDB connection closed');
  }
}

// Run if executed directly
if (require.main === module) {
  resetDatabase()
    .then(() => {
      console.log('Reset script completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Reset script failed:', error);
      process.exit(1);
    });
}

module.exports = { resetDatabase };

