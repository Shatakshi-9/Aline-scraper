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


from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class BlogScraper:
    def __init__(self):
        self.html2text_converter = html2text.HTML2Text()
        self.html2text_converter.ignore_links = False
        self.html2text_converter.ignore_images = False
        self.html2text_converter.body_width = 0
        
    def get_page_content(self, url: str):
        """Fetch and parse a web page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_blog_posts_from_index(self, soup: BeautifulSoup, base_url: str):
        """Extract individual blog post URLs from a blog index page"""
        post_urls = []
        
        # Enhanced patterns for blog post links
        link_selectors = [
            'a[href*="/blog/"]',
            'a[href*="/post/"]', 
            'a[href*="/article/"]',
            'a[href*="/guide/"]',
            'a[href*="/tutorial/"]',
            'article a',
            '.post-title a',
            '.entry-title a',
            '.article-title a',
            'h2 a',
            'h3 a',
            '.blog-post a',
            '.post-link',
            '.entry-link',
            'a[href*="/20"]',  # Year-based URLs
            'a[href*="-"]',    # Slug-based URLs
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self.is_likely_blog_post(full_url, base_url):
                        post_urls.append(full_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in post_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def is_likely_blog_post(self, url: str, base_url: str) -> bool:
        """Determine if a URL is likely a blog post"""
        parsed_base = urlparse(base_url)
        parsed_url = urlparse(url)
        
        # Must be from the same domain
        if parsed_url.netloc != parsed_base.netloc:
            return False
        
        path = parsed_url.path.lower()
        
        # Skip common non-post pages
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/archive/',
            '/page/', '/search/', '/login/', '/register/',
            '/contact/', '/about/', '/privacy/', '/terms/',
            '/feed/', '/rss/', '/sitemap/', '/admin/',
            '/wp-admin/', '/wp-login/',
            '.xml', '.json', '.pdf', '.jpg', '.png', '.gif',
            '.css', '.js', '.ico', '.svg'
        ]
        
        for pattern in skip_patterns:
            if pattern in path:
                return False
        
        # Look for positive indicators
        positive_patterns = [
            '/blog/', '/post/', '/article/', '/guide/', '/tutorial/',
            '/20', '/news/', '/story/', '/how-to/', '/learn/',
            '/insights/', '/resources/', '/tips/'
        ]
        
        for pattern in positive_patterns:
            if pattern in path:
                return True
        
        # If path has multiple segments and doesn't end with /, likely a post
        path_segments = [seg for seg in path.split('/') if seg]
        if len(path_segments) >= 2 and not path.endswith('/'):
            return True
        
        return False
    
    def extract_article_content(self, soup: BeautifulSoup, source_url: str = ""):
        """Extract title, content, and metadata from an article page"""
        # Find main article content with priority order
        content_selectors = [
            'article',
            '[role="main"]',
            '.post-content',
            '.entry-content', 
            '.article-content',
            '.blog-post-content',
            '.post-body',
            '.article-body',
            '.content',
            '.main-content',
            'main',
            '.single-post',
            '.post-text'
        ]
        
        article_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                article_content = elements[0]
                break
        
        if not article_content:
            # Fallback to body
            article_content = soup.find('body')
        
        # Extract metadata
        title = self.extract_title(soup)
        author = self.extract_author(soup)
        content = self.clean_and_convert_content(article_content)
        
        return {
            'title': title,
            'content': content,
            'author': author,
            'source_url': source_url
        }
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the article title"""
        title_selectors = [
            'h1',
            '.post-title',
            '.entry-title',
            '.article-title',
            '.page-title',
            '.title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                # Filter out site names and very short titles
                if title and len(title) > 5 and len(title) < 200:
                    return title
        
        return "Untitled"
    
    def extract_author(self, soup: BeautifulSoup) -> str:
        """Extract the article author"""
        author_selectors = [
            '.author',
            '.post-author',
            '.entry-author',
            '.article-author',
            '.byline',
            '[rel="author"]',
            '.author-name',
            '.by-author'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text().strip()
                # Clean up common author prefixes
                author = re.sub(r'^(by|author|written by|posted by)\s*:?\s*', '', author, flags=re.IGNORECASE)
                if author and len(author) < 100:  # Reasonable author name length
                    return author
        
        return ""
    
    def clean_and_convert_content(self, content_element) -> str:
        """Clean HTML content and convert to markdown"""
        if not content_element:
            return ""
        
        # Remove unwanted elements
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside', '.sidebar',
            '.navigation', '.menu', '.social-share', '.comments',
            '.related-posts', '.advertisement', '.ads', '.popup',
            '.social-media', '.share-buttons', '.author-bio',
            '.newsletter', '.subscription', '.promo',
            'script', 'style', 'noscript',
            'iframe[src*="ads"]', 'iframe[src*="tracking"]'
        ]
        
        # Create a copy to avoid modifying original
        content_copy = BeautifulSoup(str(content_element), 'html.parser')
        
        for selector in unwanted_selectors:
            for element in content_copy.select(selector):
                element.decompose()
        
        # Convert to markdown
        html_content = str(content_copy)
        markdown_content = self.html2text_converter.handle(html_content)
        
        # Clean up the markdown
        markdown_content = self.clean_markdown(markdown_content)
        
        return markdown_content
    
    def clean_markdown(self, markdown: str) -> str:
        """Clean up markdown content"""
        # Remove excessive whitespace
        markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
        
        # Remove empty markdown elements
        markdown = re.sub(r'^\s*\*\s*$', '', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^\s*-\s*$', '', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^\s*\d+\.\s*$', '', markdown, flags=re.MULTILINE)
        
        # Clean up markdown formatting
        markdown = re.sub(r'\*\*\s*\*\*', '', markdown)
        markdown = re.sub(r'__\s*__', '', markdown)
        markdown = re.sub(r'\[\s*\]', '', markdown)
        
        # Remove excessive line breaks at start/end
        markdown = markdown.strip()
        
        return markdown
    
    def scrape_blog(self, blog_url: str, team_id: str = "aline123"):
        """Main scraping function that returns properly formatted output"""
        logging.info(f"Starting to scrape: {blog_url}")
        
        soup = self.get_page_content(blog_url)
        if not soup:
            return {
                "team_id": team_id,
                "items": [],
                "error": "Failed to fetch the blog page"
            }
        
        # Extract individual blog post URLs
        post_urls = self.extract_blog_posts_from_index(soup, blog_url)
        logging.info(f"Found {len(post_urls)} potential blog posts")
        
        articles = []
        
        if not post_urls:
            # If no individual posts found, try to scrape current page as single post
            logging.info("No individual posts found, treating page as single article")
            article_data = self.extract_article_content(soup, blog_url)
            articles = [article_data]
        else:
            # Scrape individual posts (limit to prevent timeout)
            max_posts = 20  # Reasonable limit
            for i, post_url in enumerate(post_urls[:max_posts]):
                logging.info(f"Scraping post {i+1}/{min(len(post_urls), max_posts)}: {post_url}")
                
                post_soup = self.get_page_content(post_url)
                if post_soup:
                    article_data = self.extract_article_content(post_soup, post_url)
                    articles.append(article_data)
        
        # Format output according to assignment requirements
        items = []
        for article in articles:
            content = article.get('content', '').strip()
            
            # Filter out very short or empty content
            if content and len(content) > 100:
                item = {
                    "title": article.get('title', 'Untitled'),
                    "content": content,
                    "content_type": "blog",
                    "source_url": article.get('source_url', blog_url),
                    "author": article.get('author', ''),
                    "user_id": ""
                }
                items.append(item)
        
        logging.info(f"Successfully extracted {len(items)} articles")
        
        return {
            "team_id": team_id,
            "items": items
        }

# Initialize scraper
scraper = BlogScraper()

@app.route('/scrape', methods=['GET'])
def scrape_endpoint():
    """Main scraping endpoint"""
    url = request.args.get('url')
    team_id = request.args.get('team_id', 'aline123')
    
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        result = scraper.scrape_blog(url, team_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        return jsonify({
            "team_id": team_id,
            "items": [],
            "error": f"Scraping failed: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with sample URLs"""
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
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
