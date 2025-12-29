import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import gigsService from '../services/gigsService';
import authService from '../services/authService';

const GigDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [gig, setGig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await gigsService.getGigById(id);
        if (mounted) {
          setGig(res.data || res.gig || res);
        }
      } catch (err) {
        setError(err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, [id]);

  const handleOrder = () => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }
    navigate(`/orders/create?gigId=${id}`);
  };

  if (loading) return <p>Loading gig...</p>;
  if (error) return <p>Error loading gig: {error.message || 'error'}</p>;
  if (!gig) return <p>Gig not found</p>;

  return (
    <div>
      <h1>{gig.title}</h1>
      <p>{gig.description}</p>
      <p>Price: ${gig.price}</p>
      <p>Delivery: {gig.deliveryTime} days</p>
      <button onClick={handleOrder}>Order Now</button>
    </div>
  );
};

export default GigDetails;
