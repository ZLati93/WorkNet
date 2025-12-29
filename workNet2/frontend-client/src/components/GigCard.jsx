import { Link } from 'react-router-dom';

const GigCard = ({ gig }) => {
  if (!gig) return null;

  const {
    _id,
    title,
    description,
    price,
    rating,
    images,
    category,
    deliveryTime,
    sales,
    userId,
  } = gig;

  // Truncate description
  const truncatedDescription =
    description && description.length > 100
      ? `${description.substring(0, 100)}...`
      : description;

  return (
    <Link
      to={`/gigs/${_id}`}
      className="block bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden"
    >
      {/* Gig Image */}
      <div className="h-48 bg-gray-200 overflow-hidden">
        {images && images.length > 0 ? (
          <img
            src={images[0]}
            alt={title}
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
        {/* Category Badge */}
        {category && (
          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mb-2">
            {category}
          </span>
        )}

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {title}
        </h3>

        {/* Description */}
        {truncatedDescription && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {truncatedDescription}
          </p>
        )}

        {/* Rating and Sales */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            {rating > 0 && (
              <>
                <svg
                  className="w-4 h-4 text-yellow-400 fill-current"
                  viewBox="0 0 20 20"
                >
                  <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                </svg>
                <span className="ml-1 text-sm text-gray-700 font-medium">
                  {rating.toFixed(1)}
                </span>
              </>
            )}
          </div>
          {sales > 0 && (
            <span className="text-xs text-gray-500">
              {sales} {sales === 1 ? 'sale' : 'sales'}
            </span>
          )}
        </div>

        {/* Delivery Time and Price */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          <span className="text-xs text-gray-500">
            <svg
              className="w-4 h-4 inline mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {deliveryTime} {deliveryTime === 1 ? 'day' : 'days'}
          </span>
          <span className="text-lg font-bold text-blue-600">
            ${price}
          </span>
        </div>
      </div>
    </Link>
  );
};

export default GigCard;

