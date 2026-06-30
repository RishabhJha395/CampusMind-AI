import pytest
from unittest.mock import patch, MagicMock
from ingestion.connectors.web_crawler import WebCrawler
import httpx

@pytest.fixture
def web_crawler():
    return WebCrawler(
        university_id="test",
        start_urls=["https://test.edu"],
        max_depth=1,
        max_pages=2
    )

def test_is_valid_url(web_crawler):
    # Valid
    assert web_crawler._is_valid_url("https://test.edu/about", "test.edu") is True
    # Invalid domain
    assert web_crawler._is_valid_url("https://other.edu", "test.edu") is False
    # Invalid extension
    assert web_crawler._is_valid_url("https://test.edu/file.pdf", "test.edu") is False

def test_clean_html(web_crawler):
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Menu</nav>
            <main>
                <h1>Welcome</h1>
                <p>This is the main content.</p>
            </main>
            <footer>Copyright</footer>
            <script>alert('hi')</script>
        </body>
    </html>
    """
    text, title = web_crawler._clean_html(html)
    assert title == "Test Page"
    assert "Welcome" in text
    assert "This is the main content." in text
    assert "Menu" not in text
    assert "Copyright" not in text
    assert "alert" not in text

def test_extract_links(web_crawler):
    html = """
    <a href="/about">About</a>
    <a href="https://external.com">External</a>
    <a href="/contact#form">Contact</a>
    """
    links = web_crawler._extract_links(html, "https://test.edu")
    
    assert "https://test.edu/about" in links
    assert "https://external.com" in links
    assert "https://test.edu/contact" in links  # anchor removed

@pytest.mark.asyncio
async def test_crawler_extract(web_crawler):
    # Mock httpx.AsyncClient.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = """
    <html><head><title>Test</title></head><body>Hello World!</body></html>
    """
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        docs = []
        async for doc in web_crawler.extract():
            docs.append(doc)
            
        # Since we mock the same response for everything, it'll just hit max_pages if there were links
        # But our mock HTML has no links, so it should only crawl the start URL
        assert len(docs) == 1
        assert docs[0].metadata.title == "Test"
        assert docs[0].content == "Test\nHello World!"
        assert docs[0].metadata.source_url == "https://test.edu"
