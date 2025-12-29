import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ordersService from '../services/ordersService';
import authService from '../services/authService';

const Orders = () => {
  const navigate = useNavigate();
  const [orderType, setOrderType] = useState('all'); // 'all', 'buyer', 'seller'
  const [statusFilter, setStatusFilter] = useState('');

  // Check authentication
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
    }
  }, [navigate]);

  // Fetch orders
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['orders', orderType, statusFilter],
    queryFn: () =>
      ordersService.getOrders({
        type: orderType === 'all' ? undefined : orderType,
        status: statusFilter || undefined,
      }),
    enabled: authService.isAuthenticated(),
  });

  const getStatusBadge = (status) => {
    const statusColors = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      disputed: 'bg-orange-100 text-orange-800',
    };

    return (
      <span
        className={`px-2 py-1 text-xs font-semibold rounded-full ${
          statusColors[status] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">My Orders</h1>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order Type
              </label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Orders</option>
                <option value="buyer">Orders I Bought</option>
                <option value="seller">Orders I Sold</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
                <option value="disputed">Disputed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Orders List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading orders...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">Error loading orders: {error.message}</p>
            <button
              onClick={() => refetch()}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <div className="space-y-4">
            {data.data.map((order) => (
              <div
                key={order._id || order.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {order.gigId?.title || 'Gig Title'}
                      </h3>
                      {getStatusBadge(order.status)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Price:</span> ${order.price}
                      </div>
                      <div>
                        <span className="font-medium">Order Date:</span>{' '}
                        {formatDate(order.createdAt)}
                      </div>
                      {order.deliveryDate && (
                        <div>
                          <span className="font-medium">Delivery Date:</span>{' '}
                          {formatDate(order.deliveryDate)}
                        </div>
                      )}
                    </div>

                    {order.requirements && (
                      <div className="mt-3">
                        <span className="text-sm font-medium text-gray-700">
                          Requirements:
                        </span>
                        <p className="text-sm text-gray-600 mt-1">
                          {order.requirements}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 md:mt-0 md:ml-4 flex flex-col gap-2">
                    <button
                      onClick={() => navigate(`/orders/${order._id || order.id}`)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                    >
                      View Details
                    </button>
                    {order.status === 'pending' && (
                      <button
                        onClick={async () => {
                          if (
                            window.confirm('Are you sure you want to cancel this order?')
                          ) {
                            try {
                              await ordersService.cancelOrder(
                                order._id || order.id,
                                'Cancelled by user'
                              );
                              refetch();
                            } catch (err) {
                              alert(err.message || 'Failed to cancel order');
                            }
                          }
                        }}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
                      >
                        Cancel Order
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 text-lg">No orders found</p>
            <p className="text-gray-500 mt-2">
              {orderType === 'all'
                ? "You don't have any orders yet"
                : `You don't have any ${orderType} orders`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;

