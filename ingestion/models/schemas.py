from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    university_id: str
    source_url: str
    title: str = "Untitled Document"
    doc_type: str = "webpage"  # or 'pdf', 'notice', etc.
    category: str = "general"
    extracted_at: str
    
class Document(BaseModel):
    id: str
    content: str
    metadata: DocumentMetadata
    
class ChunkMetadata(BaseModel):
    university_id: str
    source_url: str
    title: str
    doc_type: str
    category: str
    chunk_index: int
    content_hash: str

class Chunk(BaseModel):
    id: str  # globally unique id for the chunk
    document_id: str
    content: str
    metadata: ChunkMetadata
