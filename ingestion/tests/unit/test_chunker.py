import pytest
from ingestion.chunking.text_chunker import TextChunker
from ingestion.models.schemas import Document, DocumentMetadata

def test_hash_generation():
    chunker = TextChunker()
    hash1 = chunker._generate_hash("Hello World")
    hash2 = chunker._generate_hash("Hello World")
    hash3 = chunker._generate_hash("Hello Universe")
    
    assert hash1 == hash2
    assert hash1 != hash3

def test_sliding_window_split():
    # chunk_size refers to characters, overlap to characters
    chunker = TextChunker(chunk_size=20, chunk_overlap=5)
    
    text = "one two three four five six seven eight nine ten"
    chunks = chunker._sliding_window_split(text)
    
    # Check max length
    for c in chunks:
        assert len(c) <= 25  # 20 + length of the word that pushed it over roughly
        
    # Check overlap (last words of chunks[0] should be in chunks[1])
    assert "four" in chunks[0]
    assert "four" in chunks[1]

def test_chunk_document():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    
    meta = DocumentMetadata(
        university_id="test",
        source_url="http://test",
        title="Title",
        doc_type="webpage",
        category="gen",
        extracted_at="2026-06-28"
    )
    doc = Document(id="doc1", content="A very long text that will definitely be split into multiple chunks because it exceeds the fifty character limit easily.", metadata=meta)
    
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) > 1
    assert chunks[0].document_id == "doc1"
    assert chunks[0].metadata.university_id == "test"
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[1].metadata.chunk_index == 1
    assert chunks[0].metadata.content_hash != chunks[1].metadata.content_hash
