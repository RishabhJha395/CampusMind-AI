import os
import tempfile
import yaml
import pytest
from ingestion.config_loader import ConfigLoader
from ingestion.models.schemas import Document, DocumentMetadata, Chunk, ChunkMetadata
from ingestion.connectors.base import BaseConnector

def test_document_schema():
    meta = DocumentMetadata(
        university_id="test",
        source_url="http://test.com",
        title="Test Title",
        extracted_at="2026-06-28T00:00:00Z"
    )
    doc = Document(id="doc1", content="Hello", metadata=meta)
    
    assert doc.id == "doc1"
    assert doc.metadata.university_id == "test"

def test_chunk_schema():
    meta = ChunkMetadata(
        university_id="test",
        source_url="http://test.com",
        title="Test Title",
        doc_type="webpage",
        category="general",
        chunk_index=0,
        content_hash="hash123"
    )
    chunk = Chunk(id="chunk1", document_id="doc1", content="Hello", metadata=meta)
    
    assert chunk.id == "chunk1"
    assert chunk.document_id == "doc1"

def test_config_loader():
    valid_config = {
        "university_id": "test_uni",
        "university_name": "Test University"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid yaml file
        file_path = os.path.join(tmpdir, "test_uni.yaml")
        with open(file_path, "w") as f:
            yaml.dump(valid_config, f)
            
        loader = ConfigLoader(config_dir=tmpdir)
        config = loader.load_config("test_uni")
        
        assert config["university_id"] == "test_uni"
        assert config["university_name"] == "Test University"

def test_config_loader_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = ConfigLoader(config_dir=tmpdir)
        with pytest.raises(FileNotFoundError):
            loader.load_config("nonexistent")

@pytest.mark.asyncio
async def test_base_connector_abstract():
    # BaseConnector cannot be instantiated directly
    with pytest.raises(TypeError):
        BaseConnector()
    
    class DummyConnector(BaseConnector):
        async def extract(self):
            yield "dummy"
            
    connector = DummyConnector()
    results = [x async for x in connector.extract()]
    assert results == ["dummy"]
