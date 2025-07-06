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
import re
from urllib.parse import urljoin, urlparse
import time
import html2text
from datetime import datetime
import logging
from typing import List, Dict, Optional
import traceback

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalBlogScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        
    def scrape_blog(self, url: str) -> Dict:
        """Main scraping function that handles different blog platforms"""
        try:
            logger.info(f"Starting to scrape: {url}")
            
            # Get the main page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract blog posts using multiple strategies
            blog_posts = self._extract_blog_posts(soup, url)
            
            # Format output according to assignment requirements
            result = {
                "team_id": "aline123",
                "items": blog_posts
            }
            
            logger.info(f"Successfully scraped {len(blog_posts)} items from {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "team_id": "aline123",
                "items": [],
                "error": str(e)
            }
    
    def _extract_blog_posts(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract blog posts using multiple strategies"""
        posts = []
        found_posts = set()
        
        # Strategy 1: Look for article elements and common blog post containers
        article_selectors = [
            'article',
            '.post',
            '.blog-post',
            '.entry',
            '.post-item',
            '.article-item',
            '.story',
            '.post-content',
            '[class*="post"]',
            '[class*="article"]',
            '[class*="story"]',
            '.hentry'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                post_data = self._extract_post_from_element(element, base_url)
                if post_data and post_data.get('title'):
                    post_key = post_data.get('source_url', '') or post_data.get('title', '')
                    if post_key and post_key not in found_posts:
                        posts.append(post_data)
                        found_posts.add(post_key)
        
        # Strategy 2: Look for links that might be blog posts
        if len(posts) < 3:  # If we didn't find enough posts
            link_posts = self._extract_from_links(soup, base_url)
            for post in link_posts:
                post_key = post.get('source_url', '') or post.get('title', '')
                if post_key and post_key not in found_posts:
                    posts.append(post)
                    found_posts.add(post_key)
        
        # Strategy 3: Platform-specific handling
        if len(posts) < 2:
            platform_posts = self._handle_special_platforms(soup, base_url)
            for post in platform_posts:
                post_key = post.get('source_url', '') or post.get('title', '')
                if post_key and post_key not in found_posts:
                    posts.append(post)
                    found_posts.add(post_key)
        
        # Limit results and ensure quality
        return self._clean_and_limit_posts(posts)
    
    def _extract_post_from_element(self, element, base_url: str) -> Optional[Dict]:
        """Extract post data from a single element"""
        try:
            # Find title
            title_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '.title', '.post-title', '.entry-title', '.article-title',
                'a[href]'
            ]
            
            title = None
            title_element = None
            
            for selector in title_selectors:
                title_element = element.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    if title and len(title) > 5 and len(title) < 200:
                        break
            
            if not title:
                return None
            
            # Find URL
            url = None
            if title_element and title_element.get('href'):
                url = urljoin(base_url, title_element['href'])
            else:
                # Look for any link in the element
                link = element.select_one('a[href]')
                if link:
                    url = urljoin(base_url, link['href'])
            
            # Extract content
            content = self._extract_content_from_element(element)
            
            # Find author
            author = self._extract_author_from_element(element)
            
            # If we have a URL, try to get full content
            if url and self._is_valid_post_url(url):
                full_content = self._scrape_full_article(url)
                if full_content and len(full_content) > len(content):
                    content = full_content
            
            return {
                "title": title,
                "content": self._clean_content(content),
                "content_type": "blog",
                "source_url": url or "",
                "author": author,
                "user_id": ""
            }
            
        except Exception as e:
            logger.warning(f"Error extracting post from element: {str(e)}")
            return None
    
    def _extract_content_from_element(self, element) -> str:
        """Extract content from an element"""
        # Remove unwanted elements
        for unwanted in element.select('script, style, nav, footer, header, .nav, .footer'):
            unwanted.decompose()
        
        # Try to find main content area
        content_selectors = [
            '.content', '.post-content', '.entry-content', '.article-content',
            '.excerpt', '.summary', '.description', 'p'
        ]
        
        content = ""
        for selector in content_selectors:
            content_elem = element.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                if len(content) > 50:
                    break
        
        if not content:
            content = element.get_text(strip=True)
        
        return content
    
    def _extract_author_from_element(self, element) -> str:
        """Extract author from an element"""
        author_selectors = [
            '.author', '.by', '.post-author', '.entry-author',
            '[class*="author"]', '[class*="by"]'
        ]
        
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                if author and len(author) < 100:
                    return author
        
        return ""
    
    def _extract_from_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract posts by finding links that match blog post patterns"""
        posts = []
        found_urls = set()
        
        # Blog post URL patterns
        patterns = [
            r'/blog/[^/]+/?$',
            r'/post/[^/]+/?$',
            r'/article/[^/]+/?$',
            r'/\d{4}/\d{2}/[^/]+/?$',
            r'/p/[^/]+/?$',  # Substack
            r'/[^/]+/$',     # Generic post pattern
        ]
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if URL matches patterns
            if any(re.search(pattern, href) for pattern in patterns):
                if full_url not in found_urls and self._is_valid_post_url(full_url):
                    title = link.get_text(strip=True)
                    if title and len(title) > 5 and len(title) < 200:
                        posts.append({
                            "title": title,
                            "content": self._scrape_full_article(full_url),
                            "content_type": "blog",
                            "source_url": full_url,
                            "author": "",
                            "user_id": ""
                        })
                        found_urls.add(full_url)
                        
                        if len(posts) >= 10:
                            break
        
        return posts
    
    def _handle_special_platforms(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Handle special platforms"""
        if 'substack.com' in base_url:
            return self._handle_substack(soup, base_url)
        elif 'medium.com' in base_url:
            return self._handle_medium(soup, base_url)
        elif 'interviewing.io' in base_url:
            return self._handle_interviewing_io(soup, base_url)
        elif 'nilmamano.com' in base_url:
            return self._handle_nilmamano(soup, base_url)
        
        return []
    
    def _handle_substack(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Handle Substack blogs"""
        posts = []
        
        # Substack specific selectors
        selectors = [
            '.post-preview',
            '.post',
            '[class*="post"]',
            'article'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                post = self._extract_post_from_element(element, base_url)
                if post:
                    posts.append(post)
        
        return posts
    
    def _handle_medium(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Handle Medium blogs"""
        posts = []
        
        elements = soup.select('article, .postArticle, [data-testid="post-preview"]')
        for element in elements:
            post = self._extract_post_from_element(element, base_url)
            if post:
                posts.append(post)
        
        return posts
    
    def _handle_interviewing_io(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Handle interviewing.io specific structure"""
        posts = []
        
        # Look for blog post links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if '/blog/' in href or '/post/' in href:
                full_url = urljoin(base_url, href)
                title = link.get_text(strip=True)
                if title and len(title) > 5:
                    posts.append({
                        "title": title,
                        "content": self._scrape_full_article(full_url),
                        "content_type": "blog",
                        "source_url": full_url,
                        "author": "",
                        "user_id": ""
                    })
        
        return posts
    
    def _handle_nilmamano(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Handle nilmamano.com blog"""
        posts = []
        
        # Look for blog post elements
        elements = soup.select('article, .post, .blog-post, h2, h3')
        for element in elements:
            post = self._extract_post_from_element(element, base_url)
            if post:
                posts.append(post)
        
        return posts
    
    def _scrape_full_article(self, url: str) -> str:
        """Scrape full content from an article URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', '.nav', '.footer']):
                element.decompose()
            
            # Find main content
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content',
                '.content',
                '.post-body',
                'main',
                '.article-body',
                '.post'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem
                    break
            
            if not content:
                content = soup.find('body')
            
            if content:
                # Convert to markdown
                html_content = str(content)
                markdown_content = self.html_converter.handle(html_content)
                return markdown_content
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error scraping full article {url}: {str(e)}")
            return ""
    
    def _is_valid_post_url(self, url: str) -> bool:
        """Check if URL looks like a valid blog post"""
        if not url:
            return False
        
        skip_patterns = [
            'javascript:', 'mailto:', '#', '/tag/', '/category/', '/author/',
            '/search', '/login', '/register', '/privacy', '/terms', '/about',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns)
    
    def _clean_content(self, content: str) -> str:
        """Clean and format content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        content = content.strip()
        
        # Limit length
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        return content
    
    def _clean_and_limit_posts(self, posts: List[Dict]) -> List[Dict]:
        """Clean and limit posts"""
        # Remove duplicates and invalid posts
        cleaned_posts = []
        seen_titles = set()
        
        for post in posts:
            title = post.get('title', '').strip()
            if title and len(title) > 5 and title not in seen_titles:
                # Ensure all required fields are present
                post['title'] = title
                post['content'] = post.get('content', '')
                post['content_type'] = 'blog'
                post['source_url'] = post.get('source_url', '')
                post['author'] = post.get('author', '')
                post['user_id'] = ''
                
                cleaned_posts.append(post)
                seen_titles.add(title)
        
        return cleaned_posts[:20]  # Limit to 20 posts

# Initialize scraper
scraper = UniversalBlogScraper()

@app.route('/')
def home():
    return jsonify({"message": "Aline Scraper API is live. Use /scrape?url=https://..."})

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({"error": "Invalid URL format"}), 400
        
        # Scrape the blog
        result = scraper.scrape_blog(url)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        return jsonify({
            "team_id": "aline123",
            "items": [],
            "error": str(e)
        }), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
