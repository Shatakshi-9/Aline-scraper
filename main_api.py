'''from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from extractor import extract_from_url, extract_from_blog_index
from urllib.parse import urlparse

app = FastAPI(title="Aline Scraper API")

@app.get("/")
def root():
    return {"message": "Aline Scraper API is live. Use /scrape?url=https://..."}

@app.get("/scrape")
def scrape(url: str = Query(..., description="URL to scrape (blog post or blog index)")):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return JSONResponse(status_code=400, content={"error": "Invalid URL."})

    try:
        if "/blog" in url or "category" in url or "topics" in url or "learn" in url:
            items = extract_from_blog_index(url)
        else:
            items = extract_from_url(url)
        return {"success": True, "count": len(items), "items": items}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})'''


from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class BlogScraper:
    def __init__(self):
        self.html2text_converter = html2text.HTML2Text()
        self.html2text_converter.ignore_links = False
        self.html2text_converter.ignore_images = False
        self.html2text_converter.body_width = 0
        
    # All your scraper methods here (unchanged)
    # Paste the entire BlogScraper class as-is...
    # --- [TRUNCATED HERE FOR BREVITY] ---
    # Keep everything from your original BlogScraper class

# Instantiate scraper
scraper = BlogScraper()

@app.get("/scrape")
async def scrape(url: str, team_id: str = "aline123"):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    try:
        result = scraper.scrape_blog(url, team_id)
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        return JSONResponse(status_code=500, content={
            "team_id": team_id,
            "items": [],
            "error": f"Scraping failed: {str(e)}"
        })

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }

@app.get("/test")
async def test_endpoint():
    test_urls = [
        "https://interviewing.io/blog",
        "https://quill.co/blog"
    ]
    
    results = {}
    for url in test_urls:
        try:
            result = scraper.scrape_blog(url)
            results[url] = {
                "success": True,
                "post_count": len(result.get('items', [])),
                "sample_titles": [item.get('title') for item in result.get('items', [])[:3]]
            }
        except Exception as e:
            results[url] = {
                "success": False,
                "error": str(e)
            }
    
    return results

