/**
 * RPC Client Utility (Legacy wrapper)
 * Wrapper for backward compatibility with existing routes
 * Uses the new RPC client from rpc-client/rpcClient.js
 */

const { getRPCClient } = require('../rpc-client/rpcClient');

/**
 * Call RPC method (legacy function for backward compatibility)
 * @param {Object} req - Express request object
 * @param {string} method - RPC method name
 * @param {Array} params - Method parameters
 * @param {Object} options - Options (timeout, retries)
 * @returns {Promise} - Promise resolving to RPC response
 */
const callRPC = async (req, method, params = [], options = {}) => {
  try {
    // Try to get RPC client from app.locals (new way)
    let rpcClient = req?.app?.locals?.rpcClient;
    
    // Fallback to singleton if not available
    if (!rpcClient) {
      rpcClient = getRPCClient();
    }
    
    if (!rpcClient || !rpcClient.isConnected) {
      // If RPC server is not available, resolve with null
      // This allows the API to work without RPC server
      console.warn(`RPC client not available, skipping RPC call: ${method}`);
      return null;
    }
    
    // Use the new RPC client's callMethod
    return await rpcClient.callMethod(method, params, options);
  } catch (error) {
    // Log error but don't throw - allow graceful degradation
    console.error(`RPC Error (${method}):`, error.message);
    return null;
  }
};

module.exports = { callRPC };
