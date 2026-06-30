import logging
import httpx
from bs4 import BeautifulSoup
from typing import AsyncGenerator
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
import uuid

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

    def _clean_html(self, html: str) -> tuple[str, str]:
        """Removes nav, footer, scripts, and extracts clean text and title."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title = "Untitled"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            
        # Remove unwanted tags
        for tag in soup(["nav", "footer", "script", "style", "header", "aside", "noscript"]):
            tag.decompose()
            
        # Get text and clean it
        text = soup.get_text(separator="\n")
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        return text, title

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            
            # Remove fragment/anchor
            full_url = full_url.split('#')[0]
            if full_url:
                links.append(full_url)
        return links

    async def extract(self) -> AsyncGenerator[Document, None]:
        """Crawl the website using BFS."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
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
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Ensure it's HTML
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        continue
                        
                    html_content = response.text
                    clean_text, title = self._clean_html(html_content)
                    
                    if not clean_text:
                        continue
                        
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
                    if depth < self.max_depth:
                        new_links = self._extract_links(html_content, url)
                        for link in new_links:
                            if link not in self.visited:
                                queue.append((link, depth + 1))
                                
                except Exception as e:
                    logger.warning(f"Failed to crawl {url}: {e}")
                    continue
