import logging
from typing import AsyncGenerator
from urllib.parse import urlparse
from datetime import datetime, timezone
import uuid

from crawl4ai import AsyncWebCrawler
from ingestion.connectors.base import BaseConnector
from ingestion.models.schemas import Document, DocumentMetadata

logger = logging.getLogger(__name__)

class WebCrawler(BaseConnector):
    def __init__(
        self,
        university_id: str,
        start_urls: list[str],
        max_depth: int = 2,
        max_pages: int = 50,
        exclude_paths: list[str] = None
    ):
        self.university_id = university_id
        self.start_urls = start_urls
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.exclude_paths = exclude_paths or []
        self.visited = set()
        self.discovered_pdfs = set()

    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL should be crawled."""
        try:
            parsed = urlparse(url)
            if not parsed.netloc.endswith(base_domain):
                return False
            
            # Check exclusions
            for exclude in self.exclude_paths:
                if exclude in parsed.path:
                    return False
                    
            # Discover PDFs but do not crawl them as HTML
            if parsed.path.lower().endswith('.pdf'):
                self.discovered_pdfs.add(url)
                return False
                
            # Ignore other files
            if any(parsed.path.lower().endswith(ext) for ext in ['.jpg', '.png', '.zip', '.exe', '.doc', '.docx']):
                return False
                
            return True
        except Exception:
            return False

    async def extract(self) -> AsyncGenerator[Document, None]:
        """Crawl the website using BFS with Crawl4AI."""
        async with AsyncWebCrawler(verbose=True) as crawler:
            queue = [(url, 0) for url in self.start_urls]
            pages_crawled = 0
            
            while queue and pages_crawled < self.max_pages:
                url, depth = queue.pop(0)
                
                if url in self.visited:
                    continue
                    
                # We need the base domain to restrict crawling scope
                base_domain = urlparse(self.start_urls[0]).netloc
                base_domain = base_domain.replace("www.", "")
                
                if not self._is_valid_url(url, base_domain):
                    continue
                    
                if depth > self.max_depth:
                    continue
                    
                self.visited.add(url)
                
                try:
                    logger.info(f"Crawling {url}...")
                    result = await crawler.arun(url=url)
                    
                    if not result.success:
                        logger.warning(f"Failed to crawl {url}: {result.error_message}")
                        continue
                        
                    clean_text = result.markdown
                    # Sometimes markdown is empty if the page is just an image or error
                    if not clean_text or len(clean_text.strip()) < 10:
                        continue
                        
                    # Extract title (Crawl4AI usually puts # Title at the top)
                    first_line = clean_text.split('\n')[0].replace('#', '').strip()
                    title = first_line if len(first_line) > 3 else "Untitled"
                    
                    # Create document
                    metadata = DocumentMetadata(
                        university_id=self.university_id,
                        source_url=url,
                        title=title,
                        doc_type="webpage",
                        category="general",
                        extracted_at=datetime.now(timezone.utc).isoformat()
                    )
                    
                    doc = Document(
                        id=str(uuid.uuid4()),
                        content=clean_text,
                        metadata=metadata
                    )
                    
                    yield doc
                    pages_crawled += 1
                    
                    # Add new links to queue
                    if depth < self.max_depth and hasattr(result, 'links') and isinstance(result.links, dict):
                        internal_links = result.links.get("internal", [])
                        for link_obj in internal_links:
                            link = link_obj.get("href")
                            if link and link not in self.visited:
                                # Remove fragment/anchor
                                clean_link = link.split('#')[0]
                                if clean_link and clean_link not in self.visited:
                                    queue.append((clean_link, depth + 1))
                                
                except Exception as e:
                    logger.warning(f"Unexpected error crawling {url}: {e}")
                    continue
