import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from app.services.embedding.local_embedder import LocalEmbedder

@pytest.fixture
def mock_sentence_transformer():
    with patch("sentence_transformers.SentenceTransformer") as mock:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Configure the encode method to return fake numpy arrays
        # The true model returns 384-dim vectors
        def fake_encode(texts, **kwargs):
            # Create deterministic random vectors based on text length for testing
            np.random.seed(len(texts[0]) if texts else 42)
            # Create batch of 384-dim vectors
            batch = np.random.rand(len(texts), 384).astype(np.float32)
            # Normalize them (L2 norm) to simulate normalize_embeddings=True
            norms = np.linalg.norm(batch, axis=1, keepdims=True)
            normalized = batch / norms
            return normalized
            
        mock_instance.encode.side_effect = fake_encode
        mock.return_value = mock_instance
        yield mock

def test_embedder_initialization():
    embedder = LocalEmbedder(model_name="test-model", batch_size=16)
    assert embedder.model_name == "test-model"
    assert embedder.batch_size == 16
    assert embedder._model is None # Should be lazy loaded

def test_lazy_loading(mock_sentence_transformer):
    embedder = LocalEmbedder()
    assert embedder._model is None
    
    # Accessing the property should trigger load
    model = embedder.model
    assert model is not None
    mock_sentence_transformer.assert_called_once_with("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    
    # Accessing again should not trigger another load
    model2 = embedder.model
    assert model is model2
    assert mock_sentence_transformer.call_count == 1

def test_embed_texts(mock_sentence_transformer):
    embedder = LocalEmbedder()
    
    texts = ["Hello world", "This is a test"]
    embeddings = embedder.embed_texts(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384
    
    # Verify encode was called with correct arguments
    embedder.model.encode.assert_called_once_with(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )
    
    # Verify L2 normalization occurred (norm should be ~1.0)
    norm = np.linalg.norm(embeddings[0])
    assert np.isclose(norm, 1.0)

def test_embed_query(mock_sentence_transformer):
    embedder = LocalEmbedder()
    
    query = "Search query"
    embedding = embedder.embed_query(query)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    
    # Verify L2 normalization
    norm = np.linalg.norm(embedding)
    assert np.isclose(norm, 1.0)

def test_empty_input():
    # Shouldn't even load the model if empty
    embedder = LocalEmbedder()
    assert embedder.embed_texts([]) == []
    assert embedder._model is None
