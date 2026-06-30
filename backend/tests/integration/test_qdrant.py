import os
import uuid
import pytest
from app.services.vector_store.qdrant_store import QdrantStore

# Using memory mode for tests to avoid requiring Docker
QDRANT_URL = os.getenv("QDRANT_URL", ":memory:")
TEST_COLLECTION = "test_collection_qdrant"

@pytest.fixture(scope="module")
def qdrant_store():
    store = QdrantStore(url=QDRANT_URL)
    # Ensure collection is clean before tests
    store.delete_collection(TEST_COLLECTION)
    yield store
    # Cleanup after tests
    store.delete_collection(TEST_COLLECTION)

def test_qdrant_health(qdrant_store):
    assert qdrant_store.check_health() is True

def test_create_collection(qdrant_store):
    result = qdrant_store.create_collection(TEST_COLLECTION, vector_size=4)
    assert result is True

def test_upsert_and_search(qdrant_store):
    # Collection should be created first
    qdrant_store.create_collection(TEST_COLLECTION, vector_size=4)
    
    point_id = str(uuid.uuid4())
    points = [
        {
            "id": point_id,
            "vector": [0.1, 0.2, 0.3, 0.4],
            "payload": {
                "university_id": "test_uni",
                "content": "Test content",
                "category": "test"
            }
        }
    ]
    
    # Upsert
    assert qdrant_store.upsert(TEST_COLLECTION, points) is True
    
    # Search without filter
    results = qdrant_store.search(TEST_COLLECTION, [0.1, 0.2, 0.3, 0.4], limit=1)
    assert len(results) == 1
    assert results[0].id == point_id
    assert results[0].payload["university_id"] == "test_uni"
    
    # Search with filter match
    filtered_results = qdrant_store.search(
        TEST_COLLECTION, 
        [0.1, 0.2, 0.3, 0.4], 
        limit=1,
        filters={"category": "test"}
    )
    assert len(filtered_results) == 1
    
    # Search with filter no match
    no_match_results = qdrant_store.search(
        TEST_COLLECTION, 
        [0.1, 0.2, 0.3, 0.4], 
        limit=1,
        filters={"category": "wrong"}
    )
    assert len(no_match_results) == 0

def test_delete_points(qdrant_store):
    point_id = str(uuid.uuid4())
    points = [
        {
            "id": point_id,
            "vector": [0.1, 0.1, 0.1, 0.1],
            "payload": {}
        }
    ]
    qdrant_store.upsert(TEST_COLLECTION, points)
    
    # Verify it exists
    results = qdrant_store.search(TEST_COLLECTION, [0.1, 0.1, 0.1, 0.1], limit=1)
    assert len(results) == 1
    
    # Delete it
    assert qdrant_store.delete(TEST_COLLECTION, [point_id]) is True
    
    # Verify it is deleted (this is a bit flaky in real-time sometimes, but Qdrant is quite fast)
    # Actually, in Qdrant it might take a moment to be completely invisible, but typically for tests it's synchronous enough
    results = qdrant_store.search(TEST_COLLECTION, [0.1, 0.1, 0.1, 0.1], limit=1)
    assert len(results) == 0 or (len(results) > 0 and results[0].id != point_id)
