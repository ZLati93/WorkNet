"""
Tests for Gigs Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from bson import ObjectId
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.gigs_service import GigsService


class TestGigsService:
    """Test suite for GigsService"""

    def test_create_gig_success(self, mock_db, sample_gig, sample_user):
        """Test successful gig creation"""
        service = GigsService(mock_db)
        
        # Mock user exists and is freelancer
        sample_user['role'] = 'freelancer'
        mock_db.users.find_one.return_value = sample_user
        
        # Mock category exists
        mock_db.categories.find_one.return_value = {'_id': sample_gig['category_id']}
        
        # Mock gig insertion
        mock_db.gigs.insert_one.return_value = Mock(inserted_id=sample_gig['_id'])
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        gig_data = {
            'title': sample_gig['title'],
            'description': sample_gig['description'],
            'category_id': str(sample_gig['category_id']),
            'price': sample_gig['price'],
            'delivery_time': sample_gig['delivery_time']
        }
        
        result = service.create(str(sample_user['_id']), gig_data)
        
        assert result['success'] is True
        assert 'gig_id' in result

    def test_create_gig_user_not_freelancer(self, mock_db, sample_gig, sample_user):
        """Test gig creation when user is not a freelancer"""
        service = GigsService(mock_db)
        
        sample_user['role'] = 'client'
        mock_db.users.find_one.return_value = sample_user
        
        gig_data = {
            'title': sample_gig['title'],
            'description': sample_gig['description'],
            'category_id': str(sample_gig['category_id']),
            'price': sample_gig['price']
        }
        
        result = service.create(str(sample_user['_id']), gig_data)
        
        assert result['success'] is False
        assert 'authorized' in result['error'].lower() or 'freelancer' in result['error'].lower()

    def test_create_gig_category_not_found(self, mock_db, sample_gig, sample_user):
        """Test gig creation with non-existent category"""
        service = GigsService(mock_db)
        
        sample_user['role'] = 'freelancer'
        mock_db.users.find_one.return_value = sample_user
        mock_db.categories.find_one.return_value = None
        
        gig_data = {
            'title': sample_gig['title'],
            'category_id': str(sample_gig['category_id']),
            'price': sample_gig['price']
        }
        
        result = service.create(str(sample_user['_id']), gig_data)
        
        assert result['success'] is False
        assert 'category' in result['error'].lower()

    def test_create_gig_no_database(self, sample_gig):
        """Test gig creation when database is not available"""
        service = GigsService(None)
        
        gig_data = {'title': sample_gig['title']}
        result = service.create(str(ObjectId()), gig_data)
        
        assert result['success'] is False
        assert 'database' in result['error'].lower()

    def test_update_gig_success(self, mock_db, sample_gig):
        """Test successful gig update"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.gigs.update_one.return_value = Mock(modified_count=1)
        
        updates = {'title': 'Updated Title', 'price': 75.0}
        result = service.update(str(sample_gig['_id']), updates)
        
        assert result['success'] is True
        mock_db.gigs.update_one.assert_called_once()

    def test_update_gig_not_found(self, mock_db):
        """Test gig update when gig doesn't exist"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = None
        
        result = service.update(str(ObjectId()), {'title': 'Updated'})
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_update_gig_category_not_found(self, mock_db, sample_gig):
        """Test gig update with invalid category"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.categories.find_one.return_value = None
        
        updates = {'category_id': str(ObjectId())}
        result = service.update(str(sample_gig['_id']), updates)
        
        assert result['success'] is False
        assert 'category' in result['error'].lower()

    def test_delete_gig_success(self, mock_db, sample_gig):
        """Test successful gig deletion"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.orders.find_one.return_value = None  # No active orders
        mock_db.gigs.delete_one.return_value = Mock(deleted_count=1)
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        result = service.delete(str(sample_gig['_id']))
        
        assert result['success'] is True
        mock_db.gigs.delete_one.assert_called_once()

    def test_delete_gig_with_active_orders(self, mock_db, sample_gig):
        """Test gig deletion when gig has active orders"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.orders.find_one.return_value = {'_id': ObjectId()}  # Active order exists
        
        result = service.delete(str(sample_gig['_id']))
        
        assert result['success'] is False
        assert 'active orders' in result['error'].lower()

    def test_delete_gig_not_found(self, mock_db):
        """Test gig deletion when gig doesn't exist"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = None
        
        result = service.delete(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_by_id_success(self, mock_db, sample_gig):
        """Test getting gig by ID"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        
        result = service.get_by_id(str(sample_gig['_id']))
        
        assert result['success'] is True
        assert result['gig']['title'] == sample_gig['title']

    def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent gig"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = None
        
        result = service.get_by_id(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_by_user_success(self, mock_db, sample_gig):
        """Test getting gigs by user ID"""
        service = GigsService(mock_db)
        
        gigs_list = [sample_gig]
        mock_db.gigs.find.return_value.skip.return_value.limit.return_value = gigs_list
        mock_db.gigs.count_documents.return_value = 1
        
        result = service.get_by_user(str(sample_gig['user_id']), 1, 10)
        
        assert result['success'] is True
        assert len(result['gigs']) == 1

    def test_search_gigs_success(self, mock_db, sample_gig):
        """Test searching gigs"""
        service = GigsService(mock_db)
        
        gigs_list = [sample_gig]
        mock_db.gigs.find.return_value.skip.return_value.limit.return_value = gigs_list
        mock_db.gigs.count_documents.return_value = 1
        
        result = service.search('test', {}, 1, 10)
        
        assert result['success'] is True
        assert len(result['gigs']) == 1

    def test_search_gigs_with_filters(self, mock_db, sample_gig):
        """Test searching gigs with filters"""
        service = GigsService(mock_db)
        
        gigs_list = [sample_gig]
        mock_db.gigs.find.return_value.skip.return_value.limit.return_value = gigs_list
        mock_db.gigs.count_documents.return_value = 1
        
        filters = {
            'category_id': str(sample_gig['category_id']),
            'min_price': 10,
            'max_price': 100
        }
        
        result = service.search('test', filters, 1, 10)
        
        assert result['success'] is True
        mock_db.gigs.find.assert_called()

    def test_update_rating_success(self, mock_db, sample_gig):
        """Test updating gig rating"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.gigs.update_one.return_value = Mock(modified_count=1)
        
        result = service.update_rating(str(sample_gig['_id']), 4.5)
        
        assert result['success'] is True
        assert 'average_rating' in result

    def test_update_rating_invalid_value(self, mock_db, sample_gig):
        """Test updating rating with invalid value"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = sample_gig
        
        result = service.update_rating(str(sample_gig['_id']), 10)  # Invalid: > 5
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'rating' in result['error'].lower()

    def test_update_rating_gig_not_found(self, mock_db):
        """Test updating rating for non-existent gig"""
        service = GigsService(mock_db)
        
        mock_db.gigs.find_one.return_value = None
        
        result = service.update_rating(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_update_rating_aggregate_success(self, mock_db, sample_gig):
        """Test updating rating when reviews exist"""
        service = GigsService(mock_db)

        mock_db.reviews.aggregate.return_value = iter([{'avgRating': 4.25, 'count': 4}])
        mock_db.gigs.update_one.return_value = Mock(modified_count=1)

        result = service.update_rating(str(sample_gig['_id']))

        assert result['success'] is True
        assert result['rating'] == 4.25 or round(result['rating'], 2) == 4.25
        assert result['reviewCount'] == 4

    def test_update_rating_no_reviews_sets_zero(self, mock_db, sample_gig):
        """Test updating rating when no reviews exist"""
        service = GigsService(mock_db)

        mock_db.reviews.aggregate.return_value = iter([])
        mock_db.gigs.update_one.return_value = Mock(modified_count=1)

        result = service.update_rating(str(sample_gig['_id']))

        assert result['success'] is True
        assert result['rating'] == 0
        assert result['reviewCount'] == 0

    def test_update_gig_invalid_price(self, mock_db, sample_gig):
        """Test that updating a gig with negative price fails validation"""
        service = GigsService(mock_db)

        mock_db.gigs.find_one.return_value = sample_gig

        result = service.update(str(sample_gig['_id']), {'price': -10})

        assert result['success'] is False
        assert 'price' in result['error'].lower() or 'invalid' in result['error'].lower()

    def test_update_images_urls(self, mock_db, sample_gig):
        """Test updating images array on gig"""
        service = GigsService(mock_db)

        mock_db.gigs.find_one.return_value = sample_gig
        mock_db.gigs.update_one.return_value = Mock(modified_count=1)

        images = ['https://example.com/img1.png', 'https://cdn.example.com/img2.jpg']
        result = service.update(str(sample_gig['_id']), {'images': images})

        assert result['success'] is True
        mock_db.gigs.update_one.assert_called_once()

    def test_search_gigs_by_keywords_multiple(self, mock_db, sample_gig):
        """Test searching gigs returns multiple matches"""
        service = GigsService(mock_db)

        gig2 = sample_gig.copy()
        gig2['_id'] = ObjectId()
        gig2['title'] = 'Another test gig'

        mock_db.gigs.find.return_value.limit.return_value = [sample_gig, gig2]

        result = service.search('test', {})

        assert result['success'] is True
        assert result['count'] == 2

    def test_create_gig_with_isSeller_flag(self, mock_db, sample_gig, sample_user):
        """Test that a user with isSeller True can create a gig even if role != freelancer"""
        service = GigsService(mock_db)

        sample_user['role'] = 'client'
        sample_user['isSeller'] = True
        mock_db.users.find_one.return_value = sample_user

        result = service.create(str(sample_gig['_id']), str(sample_user['_id']), sample_gig['title'])

        assert result['success'] is True
        assert 'gig_id' in result

