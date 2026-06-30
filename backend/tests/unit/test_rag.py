import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.rag.orchestrator import RAGService

@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    # Return mock results
    mock_result = MagicMock()
    mock_result.score = 0.95
    mock_result.payload = {
        "content": "DTU is in Delhi.",
        "url": "https://dtu.ac.in",
        "title": "About DTU"
    }
    store.search.return_value = [mock_result]
    return store

@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1, 0.2, 0.3]
    return embedder

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate_response = AsyncMock(return_value="Yes, DTU is located in Delhi.")
    
    async def mock_stream(*args, **kwargs):
        yield "Yes, "
        yield "DTU is "
        yield "located in Delhi."
    
    llm.generate_response_stream = mock_stream
    return llm

@pytest.fixture
def rag_service(mock_vector_store, mock_embedder, mock_llm):
    return RAGService(
        vector_store=mock_vector_store,
        embedder=mock_embedder,
        llm_service=mock_llm
    )

@pytest.fixture
def mock_registry():
    with patch("app.services.rag.orchestrator.registry.get_university") as mock:
        mock_uni = MagicMock()
        mock_uni.vector_store.collection_name = "dtu_vectors"
        mock_uni.university_name = "DTU"
        mock_uni.branding.welcome_message = "Welcome to DTU"
        mock.return_value = mock_uni
        yield mock

def test_retrieve_context(rag_service, mock_registry):
    texts, sources = rag_service.retrieve_context("dtu", "Where is DTU?")
    
    assert len(texts) == 1
    assert texts[0] == "DTU is in Delhi."
    assert len(sources) == 1
    assert sources[0]["title"] == "About DTU"
    
    # Check that embedder was called
    rag_service.embedder.embed_query.assert_called_once_with("Where is DTU?")
    
    # Check vector search was called with correct filter
    rag_service.vector_store.search.assert_called_once_with(
        collection_name="dtu_vectors",
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        filters={"university_id": "dtu"}
    )

@pytest.mark.asyncio
async def test_chat_non_streaming(rag_service, mock_registry):
    response = await rag_service.chat("dtu", "Where is DTU?", stream=False)
    
    assert "answer" in response
    assert response["answer"] == "Yes, DTU is located in Delhi."
    assert "sources" in response
    assert len(response["sources"]) == 1

@pytest.mark.asyncio
async def test_chat_streaming(rag_service, mock_registry):
    chunks = []
    async for chunk in rag_service.chat_stream("dtu", "Where is DTU?"):
        chunks.append(chunk)
        
    assert len(chunks) == 5
    # First chunk is sources
    assert chunks[0].startswith("data: {\"type\": \"sources\"")
    # Next chunks are text
    assert "Yes, " in chunks[1]
    assert "DTU is " in chunks[2]
    assert "located in Delhi." in chunks[3]
    # Last chunk is DONE
    assert chunks[4] == "data: [DONE]\n\n"
