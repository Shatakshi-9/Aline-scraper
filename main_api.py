from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from io import BytesIO
from pdfminer.high_level import extract_text
import asyncio
import aiohttp
from goose3 import Goose
import structlog

app = FastAPI(title="Aline Scraper API", version="2.0")
logging.basicConfig(level=logging.INFO)

class ScrapedItem(BaseModel):
    title: str
    content: str
    content_type: str
    source_url: Optional[str] = None
    author: str = ""
    user_id: str = ""

class ScrapedResponse(BaseModel):
    team_id: str
    items: List[ScrapedItem]

class BlogScraper:
    def __init__(self):
        self.html2text_converter = html2text.HTML2Text()
        self.html2text_converter.ignore_links = False
        self.html2text_converter.ignore_images = False
        self.html2text_converter.body_width = 0
        self.goose = Goose()

    def get_page_content(self, url: str) -> BeautifulSoup:
        """Get page content with proper error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logging.error(f"Failed to fetch {url}: {e}")
            raise Exception(f"Failed to fetch {url}: {e}")

    def find_blog_post_urls(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Find all blog post URLs from a blog homepage"""
        urls = set()
        base_domain = urlparse(base_url).netloc
        
        # Common blog URL patterns
        blog_patterns = [
            r'/blog/[^/]+/?$',
            r'/post/[^/]+/?$',
            r'/article/[^/]+/?$',
            r'/\d{4}/\d{2}/\d{2}/',
            r'/p/[^/]+/?$',  # Substack
            r'/guides/[^/]+/?$',  # Interview guides
            r'/topics/[^/]+/?$',  # Company topics
            r'/learn/[^/]+/?$',   # Learning materials
        ]
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Only include URLs from the same domain
            if parsed_url.netloc != base_domain:
                continue
            
            # Check if URL matches blog patterns
            for pattern in blog_patterns:
                if re.search(pattern, parsed_url.path):
                    urls.add(full_url)
                    break
        
        # Special handling for different platforms
        if 'substack.com' in base_url:
            urls.update(self._find_substack_urls(soup, base_url))
        elif 'interviewing.io' in base_url:
            urls.update(self._find_interviewing_io_urls(soup, base_url))
        
        return list(urls)

    def _find_substack_urls(self, soup: BeautifulSoup, base_url: str) -> set:
        """Find Substack-specific post URLs"""
        urls = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if '/p/' in href:
                urls.add(urljoin(base_url, href))
        return urls

    def _find_interviewing_io_urls(self, soup: BeautifulSoup, base_url: str) -> set:
        """Find interviewing.io specific URLs"""
        urls = set()
        
        # Look for various content types
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if any(pattern in href for pattern in ['/blog/', '/guides/', '/topics/', '/learn/']):
                full_url = urljoin(base_url, href)
                if full_url != base_url:  # Don't include the base URL itself
                    urls.add(full_url)
        
        return urls

    def extract_content_with_goose(self, url: str) -> Optional[ScrapedItem]:
        """Extract content using Goose3 for better accuracy"""
        try:
            article = self.goose.extract(url=url)
            if article.cleaned_text and len(article.cleaned_text.strip()) > 100:
                return ScrapedItem(
                    title=article.title or "Untitled",
                    content=article.cleaned_text,
                    content_type="blog",
                    source_url=url,
                    author=article.authors[0] if article.authors else ""
                )
        except Exception as e:
            logging.error(f"Goose extraction failed for {url}: {e}")
        return None

    def extract_content_fallback(self, url: str, soup: BeautifulSoup) -> Optional[ScrapedItem]:
        """Fallback content extraction using BeautifulSoup"""
        try:
            # Try to find main content area
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.blog-post', '.post-body'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                # Use the body as fallback
                content_element = soup.find('body')
            
            if content_element:
                # Find title
                title_element = soup.find(['h1', 'h2']) or content_element.find(['h1', 'h2'])
                title = title_element.get_text(strip=True) if title_element else "Untitled"
                
                # Convert to markdown
                markdown_content = self.html2text_converter.handle(str(content_element))
                
                if len(markdown_content.strip()) > 100:
                    return ScrapedItem(
                        title=title,
                        content=markdown_content.strip(),
                        content_type="blog",
                        source_url=url,
                        author=""
                    )
        except Exception as e:
            logging.error(f"Fallback extraction failed for {url}: {e}")
        
        return None

    def scrape_single_url(self, url: str) -> Optional[ScrapedItem]:
        """Scrape content from a single URL"""
        # First try with Goose3
        item = self.extract_content_with_goose(url)
        if item:
            return item
        
        # Fallback to BeautifulSoup
        try:
            soup = self.get_page_content(url)
            return self.extract_content_fallback(url, soup)
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            return None

    def scrape_blog(self, url: str, team_id: str = "aline123", max_pages: int = 50) -> dict:
        """Main blog scraping method"""
        try:
            soup = self.get_page_content(url)
            
            # Find all blog post URLs
            post_urls = self.find_blog_post_urls(url, soup)
            
            items = []
            
            if not post_urls:
                # If no post URLs found, try to scrape the main page
                item = self.scrape_single_url(url)
                if item:
                    items.append(item)
            else:
                # Limit the number of pages
                post_urls = post_urls[:max_pages]
                
                for post_url in post_urls:
                    item = self.scrape_single_url(post_url)
                    if item:
                        items.append(item)
            
            return {
                "team_id": team_id,
                "items": [item.dict() for item in items]
            }
            
        except Exception as e:
            logging.error(f"Blog scraping failed: {e}")
            raise Exception(f"Failed to scrape blog: {e}")

    def scrape_pdf(self, url: str, team_id: str = "aline123") -> dict:
        """Scrape PDF content"""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            pdf_bytes = BytesIO(response.content)
            text = extract_text(pdf_bytes)
            
            # Chunk the text for better processing
            chunks = self.chunk_text(text)
            
            items = []
            for i, chunk in enumerate(chunks[:8]):  # First 8 chapters as requested
                items.append(ScrapedItem(
                    title=f"PDF Document - Chapter {i+1}",
                    content=chunk,
                    content_type="book",
                    source_url=url,
                    author=""
                ))
            
            return {
                "team_id": team_id,
                "items": [item.dict() for item in items]
            }
            
        except Exception as e:
            logging.error(f"PDF scraping failed: {e}")
            raise Exception(f"Failed to extract PDF: {e}")

    def chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

# Instantiate scraper
scraper = BlogScraper()

@app.get("/")
async def root():
    return {
        "message": "Aline Scraper API v2.0 is running",
        "endpoints": {
            "scrape": "/scrape?url=<blog_url>&team_id=<team_id>",
            "health": "/health",
            "test": "/test"
        }
    }

@app.get("/scrape")
async def scrape_endpoint(
    url: str = Query(..., description="URL to scrape"),
    team_id: str = Query("aline123", description="Team ID"),
    max_pages: int = Query(50, description="Maximum pages to scrape")
):
    """Scrape content from a URL"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    try:
        result = scraper.scrape_blog(url, team_id, max_pages)
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "team_id": team_id,
                "items": [],
                "error": f"Scraping failed: {str(e)}"
            }
        )

@app.get("/scrape-pdf")
async def scrape_pdf_endpoint(
    url: str = Query(..., description="PDF URL to scrape"),
    team_id: str = Query("aline123", description="Team ID")
):
    """Scrape PDF content from URL"""
    try:
        result = scraper.scrape_pdf(url, team_id)
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"PDF scraping error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "team_id": team_id,
                "items": [],
                "error": f"PDF scraping failed: {str(e)}"
            }
        )

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    team_id: str = "aline123"
):
    """Upload and process PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        content = await file.read()
        text = extract_text(BytesIO(content))
        
        chunks = scraper.chunk_text(text)
        
        items = []
        for i, chunk in enumerate(chunks[:8]):  # First 8 chapters
            items.append(ScrapedItem(
                title=f"{file.filename} - Chapter {i+1}",
                content=chunk,
                content_type="book",
                source_url=None,
                author=""
            ))
        
        return JSONResponse(content={
            "team_id": team_id,
            "items": [item.dict() for item in items]
        })
        
    except Exception as e:
        logging.error(f"PDF upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to validate scraper on multiple blogs"""
    test_urls = [
        "https://interviewing.io/blog",
        "https://quill.co/blog",
        "https://nilmamano.com/blog/category/dsa"
    ]

    results = {}
    for url in test_urls:
        try:
            # Test URL discovery
            soup = scraper.get_page_content(url)
            post_urls = scraper.find_blog_post_urls(url, soup)
            
            # Test content extraction on first URL
            sample_content = None
            if post_urls:
                sample_content = scraper.scrape_single_url(post_urls[0])
            
            results[url] = {
                "success": True,
                "discovered_urls": len(post_urls),
                "sample_urls": post_urls[:3],
                "sample_content_length": len(sample_content.content) if sample_content else 0,
                "sample_title": sample_content.title if sample_content else None
            }
        except Exception as e:
            results[url] = {
                "success": False,
                "error": str(e)
            }

    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
