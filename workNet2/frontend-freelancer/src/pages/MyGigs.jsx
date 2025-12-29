import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import gigsService from '../services/gigsService';
import GigForm from '../components/GigForm';
import OrderCard from '../components/OrderCard';

const MyGigs = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingGig, setEditingGig] = useState(null);

  // Fetch gigs
  const { data, isLoading, error } = useQuery({
    queryKey: ['myGigs'],
    queryFn: () => gigsService.getMyGigs(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => gigsService.deleteGig(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['myGigs']);
    },
  });

  // Toggle status mutation
  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, isActive }) => gigsService.toggleGigStatus(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries(['myGigs']);
    },
  });

  const handleEdit = (gig) => {
    setEditingGig(gig);
    setShowCreateForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this gig?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        alert(err.message || 'Failed to delete gig');
      }
    }
  };

  const handleToggleStatus = async (id, currentStatus) => {
    try {
      await toggleStatusMutation.mutateAsync({
        id,
        isActive: !currentStatus,
      });
    } catch (err) {
      alert(err.message || 'Failed to update gig status');
    }
  };

  const handleFormClose = () => {
    setShowCreateForm(false);
    setEditingGig(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">My Gigs</h1>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
          >
            + Create New Gig
          </button>
        </div>

        {/* Gig Form Modal */}
        {showCreateForm && (
          <GigForm
            gig={editingGig}
            onClose={handleFormClose}
            onSuccess={() => {
              handleFormClose();
              queryClient.invalidateQueries(['myGigs']);
            }}
          />
        )}

        {/* Gigs List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
            <p className="mt-4 text-gray-600">Loading gigs...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">Error loading gigs: {error.message}</p>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.data.map((gig) => (
              <div
                key={gig._id || gig.id}
                className="bg-white rounded-lg shadow-md overflow-hidden"
              >
                {/* Gig Image */}
                <div className="h-48 bg-gray-200 overflow-hidden">
                  {gig.images && gig.images.length > 0 ? (
                    <img
                      src={gig.images[0]}
                      alt={gig.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      No Image
                    </div>
                  )}
                </div>

                {/* Gig Content */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                      {gig.title}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        gig.isActive
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {gig.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </div>

                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                    {gig.description}
                  </p>

                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <span className="text-lg font-bold text-green-600">
                        ${gig.price}
                      </span>
                      <span className="text-sm text-gray-500 ml-2">
                        {gig.deliveryTime} {gig.deliveryTime === 1 ? 'day' : 'days'}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <svg
                        className="w-4 h-4 text-yellow-400 fill-current"
                        viewBox="0 0 20 20"
                      >
                        <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                      </svg>
                      <span className="ml-1 text-sm text-gray-700">
                        {gig.rating?.toFixed(1) || '0.0'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                    <span>{gig.sales || 0} sales</span>
                    <span>{gig.category}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(gig)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() =>
                        handleToggleStatus(gig._id || gig.id, gig.isActive)
                      }
                      className={`flex-1 px-3 py-2 rounded text-sm font-medium ${
                        gig.isActive
                          ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      {gig.isActive ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => handleDelete(gig._id || gig.id)}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 text-lg mb-4">No gigs yet</p>
            <p className="text-gray-500 mb-6">
              Create your first gig to start earning
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium"
            >
              Create Your First Gig
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyGigs;

