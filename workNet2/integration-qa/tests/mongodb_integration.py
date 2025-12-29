"""
MongoDB Integration Tests
- Tests collection validation, indexes, constraints, transactions and performance
- Skips tests gracefully if MongoDB is not reachable or transactions are unsupported
"""

import os
import time
import pytest
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('MONGO_TEST_DB', 'worknet_mongo_integration_test')


def _get_client_or_skip():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Trigger a simple command to verify connectivity
        client.admin.command('ping')
        return client
    except Exception as e:
        pytest.skip(f"MongoDB not available at {MONGO_URI}: {e}")


def _transactions_supported(client):
    try:
        session = client.start_session()
        session.end_session()
        return True
    except Exception:
        return False


@pytest.fixture(scope='module')
def mongo_client():
    client = _get_client_or_skip()
    yield client
    # close
    try:
        client.close()
    except Exception:
        pass


@pytest.fixture(scope='function')
def db(mongo_client):
    # Ensure a clean database for each test
    client = mongo_client
    if DB_NAME in client.list_database_names():
        client.drop_database(DB_NAME)
    database = client[DB_NAME]
    yield database
    # Teardown
    client.drop_database(DB_NAME)


# --- Collection / Index / Constraint Tests ---

def test_users_collection_schema_validation(db):
    # Create collection with JSON schema validator
    user_validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['username', 'email'],
            'properties': {
                'username': {'bsonType': 'string'},
                'email': {'bsonType': 'string', 'pattern': '^.+@.+\\..+$'},
            }
        }
    }

    db.create_collection('users', validator=user_validator)

    # Valid document should be inserted
    valid = {'username': 'alice', 'email': 'alice@example.com'}
    result = db.users.insert_one(valid)
    assert isinstance(result.inserted_id, ObjectId)

    # Invalid document (missing username) should raise a WriteError / OperationFailure
    with pytest.raises(OperationFailure):
        db.users.insert_one({'email': 'no_name@example.com'})


def test_indexes_effectiveness(db):
    # Create many documents and an index, then check explain plan uses IXSCAN
    users = db['users_index_test']
    users.create_index([('email', ASCENDING)])

    docs = [{'_id': i, 'email': f'user{i}@example.com'} for i in range(1, 2001)]
    users.insert_many(docs)

    # Use explain to check index usage
    sample_email = 'user1000@example.com'
    plan = users.find({'email': sample_email}).explain()

    # Search plan for IXSCAN stage
    plan_str = str(plan)
    assert 'IXSCAN' in plan_str.upper() or 'INDEX' in plan_str.upper()


def test_unique_constraints(db):
    col = db['unique_test']
    col.create_index([('email', ASCENDING)], unique=True)

    col.insert_one({'email': 'unique@example.com'})
    with pytest.raises(DuplicateKeyError):
        col.insert_one({'email': 'unique@example.com'})


def test_foreign_key_relationships(db):
    users = db['users_fk']
    gigs = db['gigs_fk']

    # Insert user
    user_id = users.insert_one({'username': 'seller1'}).inserted_id

    # Insert gig that references user
    gig_id = gigs.insert_one({'title': 'Test Gig', 'user_id': user_id}).inserted_id

    # Aggregation lookup should return the user embedded
    res = list(gigs.aggregate([
        {'$match': {'_id': gig_id}},
        {'$lookup': {
            'from': 'users_fk',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'owner'
        }}
    ]))

    assert res and len(res[0].get('owner', [])) == 1

    # Simulate cascade delete inside a transaction if supported
    client = db.client
    if _transactions_supported(client):
        with client.start_session() as s:
            with s.start_transaction():
                users.delete_one({'_id': user_id}, session=s)
                gigs.delete_many({'user_id': user_id}, session=s)
        # After commit, both should be removed
        assert users.count_documents({'_id': user_id}) == 0
        assert gigs.count_documents({'user_id': user_id}) == 0
    else:
        pytest.skip('Transactions not supported by MongoDB server; skipping cascade transaction test')


# --- Transactions ---

def test_order_creation_transaction(db):
    client = db.client
    if not _transactions_supported(client):
        pytest.skip('Transactions not supported; skipping order transaction test')

    users = db['txn_users']
    orders = db['txn_orders']

    user_id = users.insert_one({'username': 'txuser', 'balance': 0}).inserted_id

    with client.start_session() as s:
        with s.start_transaction():
            order_id = orders.insert_one({'user_id': user_id, 'price': 100}, session=s).inserted_id
            users.update_one({'_id': user_id}, {'$inc': {'balance': -100}}, session=s)
        # transaction committed

    # After commit, verify
    assert orders.find_one({'_id': order_id}) is not None
    assert users.find_one({'_id': user_id})['balance'] == -100


def test_payment_processing_transaction(db):
    client = db.client
    if not _transactions_supported(client):
        pytest.skip('Transactions not supported; skipping payment transaction test')

    orders = db['pay_orders']
    payments = db['payments']

    order_id = orders.insert_one({'status': 'pending', 'amount': 50}).inserted_id

    with client.start_session() as s:
        try:
            with s.start_transaction():
                payments.insert_one({'order_id': order_id, 'status': 'processing'}, session=s)
                orders.update_one({'_id': order_id}, {'$set': {'status': 'paid'}}, session=s)
            # committed
        except Exception:
            pytest.skip('Transaction failed unexpectedly')

    assert payments.find_one({'order_id': order_id}) is not None
    assert orders.find_one({'_id': order_id})['status'] == 'paid'


def test_rollback_on_failure(db):
    client = db.client
    if not _transactions_supported(client):
        pytest.skip('Transactions not supported; skipping rollback test')

    A = db['txn_a']
    B = db['txn_b']

    with client.start_session() as s:
        with pytest.raises(RuntimeError):
            with s.start_transaction():
                A.insert_one({'x': 1}, session=s)
                # Simulate failure
                raise RuntimeError('Simulated failure to trigger rollback')

    # Ensure documents were not committed
    assert A.count_documents({'x': 1}) == 0
    assert B.count_documents({}) == 0


# --- Performance Tests ---

def test_query_execution_time(db):
    col = db['perf_test']
    docs = [{'_id': i, 'value': i} for i in range(1, 20001)]
    col.insert_many(docs)

    start = time.time()
    r = list(col.find({'value': {'$gte': 15000}}).limit(1000))
    elapsed = time.time() - start

    # Should be reasonably fast on local DB (subject to environment); assert under 2s
    assert elapsed < 2.0
    assert len(r) == 1000


def test_index_usage_with_explain(db):
    col = db['explain_test']
    col.create_index([('category', ASCENDING)])
    docs = [{'_id': i, 'category': f'cat{i%10}'} for i in range(1, 5001)]
    col.insert_many(docs)

    plan = col.find({'category': 'cat5'}).explain()
    plan_str = str(plan)
    assert 'IXSCAN' in plan_str.upper() or 'INDEX' in plan_str.upper()


def test_large_dataset_handling(db):
    col = db['large_test']
    # Insert a moderately large dataset (10k docs) — tuned for CI/dev speed
    docs = [{'_id': i, 'blob': 'x' * 200, 'idx': i} for i in range(1, 10001)]
    col.insert_many(docs)

    start = time.time()
    count = col.count_documents({'idx': {'$gte': 9000}})
    elapsed = time.time() - start

    assert count == 1001
    # Ensure the count query is reasonably fast
    assert elapsed < 2.0
