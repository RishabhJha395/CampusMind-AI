import logging
import httpx
import os
import uuid
import tempfile
from typing import AsyncGenerator
from datetime import datetime, timezone
from urllib.parse import urlparse

from ingestion.connectors.base import BaseConnector
from ingestion.models.schemas import Document, DocumentMetadata
from ingestion.processors.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

class PDFConnector(BaseConnector):
    def __init__(
        self,
        university_id: str,
        pdf_urls: list[str],
        ocr_languages: list[str] = None
    ):
        self.university_id = university_id
        self.pdf_urls = pdf_urls
        self.processor = PDFProcessor(languages=ocr_languages)

    async def _download_pdf(self, client: httpx.AsyncClient, url: str, temp_dir: str) -> str:
        """Downloads a PDF to a temporary directory."""
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            # Simple filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename.endswith('.pdf'):
                filename = f"{uuid.uuid4()}.pdf"
                
            local_path = os.path.join(temp_dir, filename)
            
            with open(local_path, "wb") as f:
                f.write(response.content)
                
            return local_path
            
        except Exception as e:
            logger.warning(f"Failed to download PDF {url}: {e}")
            return ""

    async def extract(self) -> AsyncGenerator[Document, None]:
        """Downloads, processes, and yields documents for each PDF URL."""
        if not self.pdf_urls:
            return
            
        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                for url in self.pdf_urls:
                    logger.info(f"Processing PDF: {url}")
                    
                    local_path = await self._download_pdf(client, url, temp_dir)
                    if not local_path:
                        continue
                        
                    try:
                        # Extract text
                        extracted_text = self.processor.process_pdf(local_path)
                        
                        if not extracted_text.strip():
                            logger.warning(f"No text extracted from {url}")
                            continue
                            
                        # Try to get a clean title from the filename
                        title = os.path.basename(urlparse(url).path).replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
                        
                        metadata = DocumentMetadata(
                            university_id=self.university_id,
                            source_url=url,
                            title=title if title else "Untitled PDF",
                            doc_type="pdf",
                            category="general",
                            extracted_at=datetime.now(timezone.utc).isoformat()
                        )
                        
                        doc = Document(
                            id=str(uuid.uuid4()),
                            content=extracted_text,
                            metadata=metadata
                        )
                        
                        yield doc
                        
                    except Exception as e:
                        logger.error(f"Error yielding PDF document for {url}: {e}")
                    finally:
                        # Ensure cleanup after processing
                        if os.path.exists(local_path):
                            os.remove(local_path)
                            logger.debug(f"Deleted local temporary file: {local_path}")
