import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import ordersService from '../services/ordersService';

const OrderCard = ({ order }) => {
  const queryClient = useQueryClient();
  const [showDetails, setShowDetails] = useState(false);

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }) => ordersService.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries(['freelancerOrders']);
    },
  });

  const handleStatusUpdate = async (newStatus) => {
    if (window.confirm(`Change order status to ${newStatus}?`)) {
      try {
        await updateStatusMutation.mutateAsync({
          id: order._id || order.id,
          status: newStatus,
        });
      } catch (err) {
        alert(err.message || 'Failed to update order status');
      }
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      disputed: 'bg-orange-100 text-orange-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {order.gigId?.title || 'Gig Title'}
          </h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>
              Buyer: <span className="font-medium">{order.buyerId?.username || 'Unknown'}</span>
            </span>
            <span>•</span>
            <span>Ordered: {formatDate(order.createdAt)}</span>
          </div>
        </div>
        <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
          {order.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500">Price</p>
          <p className="text-lg font-bold text-green-600">${order.price}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Delivery Date</p>
          <p className="text-sm font-medium text-gray-900">
            {formatDate(order.deliveryDate)}
          </p>
        </div>
      </div>

      {order.requirements && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-1">Requirements:</p>
          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
            {order.requirements}
          </p>
        </div>
      )}

      {/* Status Actions */}
      <div className="flex gap-2 flex-wrap">
        {order.status === 'pending' && (
          <>
            <button
              onClick={() => handleStatusUpdate('in_progress')}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Start Work
            </button>
            <button
              onClick={() => handleStatusUpdate('cancelled')}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Cancel
            </button>
          </>
        )}
        {order.status === 'in_progress' && (
          <>
            <button
              onClick={() => handleStatusUpdate('completed')}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Mark Complete
            </button>
            <button
              onClick={() => handleStatusUpdate('disputed')}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Dispute
            </button>
          </>
        )}
        {order.status === 'completed' && (
          <div className="w-full text-center text-sm text-green-600 font-medium">
            ✓ Order Completed
          </div>
        )}
      </div>

      {/* Deliverables */}
      {order.deliverables && order.deliverables.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-2">Deliverables:</p>
          <ul className="list-disc list-inside text-sm text-gray-600">
            {order.deliverables.map((deliverable, index) => (
              <li key={index}>{deliverable}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default OrderCard;

