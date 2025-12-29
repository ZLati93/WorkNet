import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import authService from '../services/authService';
import ordersService from '../services/ordersService';
import gigsService from '../services/gigsService';
import paymentsService from '../services/paymentsService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

const Dashboard = () => {
  const navigate = useNavigate();

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
    }
  }, [navigate]);

  const user = authService.getCurrentUser();

  // Fetch orders
  const { data: ordersData } = useQuery({
    queryKey: ['freelancerOrders'],
    queryFn: () => ordersService.getOrders({ type: 'seller' }),
    enabled: authService.isAuthenticated(),
  });

  // Fetch gigs
  const { data: gigsData } = useQuery({
    queryKey: ['myGigs'],
    queryFn: () => gigsService.getMyGigs(),
    enabled: authService.isAuthenticated(),
  });

  // Fetch earnings
  const { data: earningsData } = useQuery({
    queryKey: ['earnings'],
    queryFn: () => paymentsService.getEarningsSummary('month'),
    enabled: authService.isAuthenticated(),
  });

  // Calculate statistics
  const stats = {
    totalGigs: gigsData?.data?.length || 0,
    activeGigs: gigsData?.data?.filter(g => g.isActive).length || 0,
    totalOrders: ordersData?.data?.length || 0,
    completedOrders: ordersData?.data?.filter(o => o.status === 'completed').length || 0,
    pendingOrders: ordersData?.data?.filter(o => o.status === 'pending').length || 0,
    inProgressOrders: ordersData?.data?.filter(o => o.status === 'in_progress').length || 0,
    totalEarnings: earningsData?.totalEarnings || user?.totalEarnings || 0,
    averageRating: user?.rating || 0,
  };

  // Prepare chart data
  const ordersByStatus = [
    { name: 'Pending', value: stats.pendingOrders },
    { name: 'In Progress', value: stats.inProgressOrders },
    { name: 'Completed', value: stats.completedOrders },
  ];

  const earningsDataChart = [
    { month: 'Jan', earnings: 1200 },
    { month: 'Feb', earnings: 1900 },
    { month: 'Mar', earnings: 1500 },
    { month: 'Apr', earnings: 2200 },
    { month: 'May', earnings: 1800 },
    { month: 'Jun', earnings: 2500 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Gigs</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalGigs}</p>
                <p className="text-xs text-gray-500">{stats.activeGigs} active</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Orders</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalOrders}</p>
                <p className="text-xs text-gray-500">{stats.completedOrders} completed</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-100 rounded-md p-3">
                <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Earnings</p>
                <p className="text-2xl font-semibold text-gray-900">${stats.totalEarnings.toLocaleString()}</p>
                <p className="text-xs text-gray-500">This month</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-100 rounded-md p-3">
                <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Rating</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.averageRating.toFixed(1)}</p>
                <p className="text-xs text-gray-500">Average rating</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Orders by Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Orders by Status</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ordersByStatus}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Earnings Trend */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Earnings Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={earningsDataChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="earnings" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Orders</h3>
          </div>
          <div className="p-6">
            {ordersData?.data && ordersData.data.length > 0 ? (
              <div className="space-y-4">
                {ordersData.data.slice(0, 5).map((order) => (
                  <div
                    key={order._id || order.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {order.gigId?.title || 'Gig Title'}
                      </p>
                      <p className="text-sm text-gray-500">
                        Buyer: {order.buyerId?.username || 'Unknown'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">${order.price}</p>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        order.status === 'completed' ? 'bg-green-100 text-green-800' :
                        order.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {order.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No recent orders</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

