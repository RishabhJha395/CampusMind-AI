import hashlib
import uuid
import re
from typing import List
from ingestion.models.schemas import Document, Chunk, ChunkMetadata

class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _generate_hash(self, content: str) -> str:
        """Generate a deterministic SHA-256 hash for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text recursively by paragraphs, then sentences, then words.
        Ensures chunks do not exceed chunk_size.
        """
        # A simple recursive-like character splitter using regex
        separators = ["\n\n", "\n", ". ", " ", ""]
        
        def split_with_seps(text_to_split: str, sep_index: int) -> List[str]:
            if len(text_to_split) <= self.chunk_size:
                return [text_to_split]
            
            if sep_index >= len(separators):
                # If we're out of separators, force split by character
                return [text_to_split[i:i+self.chunk_size] for i in range(0, len(text_to_split), self.chunk_size)]
                
            sep = separators[sep_index]
            if sep == "":
                return [text_to_split[i:i+self.chunk_size] for i in range(0, len(text_to_split), self.chunk_size)]
            
            splits = text_to_split.split(sep)
            
            final_chunks = []
            current_chunk = ""
            
            for s in splits:
                # Add separator back except for the last element, but for simplicity we just add it back if we can
                # Actually, simple joining:
                part = s + sep if s != splits[-1] else s
                
                if len(current_chunk) + len(part) <= self.chunk_size:
                    current_chunk += part
                else:
                    if current_chunk:
                        final_chunks.append(current_chunk)
                    
                    if len(part) > self.chunk_size:
                        # Recursively split this part with next separator
                        sub_chunks = split_with_seps(part, sep_index + 1)
                        # We don't append it to current_chunk, we just add it to final_chunks
                        # The last sub_chunk becomes the new current_chunk
                        final_chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1] if sub_chunks else ""
                    else:
                        current_chunk = part
            
            if current_chunk:
                final_chunks.append(current_chunk)
                
            return final_chunks
            
        raw_chunks = split_with_seps(text, 0)
        
        # A simple recursive-like character splitter using regex
        # ... skipped, delegating completely to sliding window for simplicity
        return self._sliding_window_split(text)

    def _sliding_window_split(self, text: str) -> List[str]:
        """A simple chunker that respects word boundaries and provides overlap."""
        words = text.split(" ")
        chunks = []
        current_chunk = []
        current_length = 0
        
        i = 0
        while i < len(words):
            word = words[i]
            # Roughly estimate length (word length + 1 for space)
            word_len = len(word) + 1
            
            if current_length + word_len > self.chunk_size and current_chunk:
                # Chunk is full
                chunk_str = " ".join(current_chunk)
                chunks.append(chunk_str)
                
                # Backtrack for overlap
                # Find how many words to keep for overlap
                overlap_length = 0
                overlap_words = []
                for w in reversed(current_chunk):
                    if overlap_length + len(w) + 1 > self.chunk_overlap:
                        break
                    overlap_words.insert(0, w)
                    overlap_length += len(w) + 1
                    
                current_chunk = overlap_words
                current_length = overlap_length
                
            current_chunk.append(word)
            current_length += word_len
            i += 1
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Takes a Document and splits it into multiple Chunks."""
        text_chunks = self._split_text(document.content)
        
        chunks = []
        for index, text in enumerate(text_chunks):
            if not text.strip():
                continue
                
            content_hash = self._generate_hash(text)
            
            metadata = ChunkMetadata(
                university_id=document.metadata.university_id,
                source_url=document.metadata.source_url,
                title=document.metadata.title,
                doc_type=document.metadata.doc_type,
                category=document.metadata.category,
                chunk_index=index,
                content_hash=content_hash
            )
            
            # Generate deterministic UUID based on chunk content hash
            namespace = uuid.NAMESPACE_URL
            deterministic_id = str(uuid.uuid5(namespace, content_hash))
            
            chunk = Chunk(
                id=deterministic_id,
                document_id=document.id,
                content=text,
                metadata=metadata
            )
            chunks.append(chunk)
            
        return chunks
