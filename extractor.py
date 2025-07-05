import os
import time
import hashlib
import logging
import random
from urllib.parse import urlparse, urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, HTTPError
from urllib3.util.retry import Retry

from goose3 import Goose
import html2text
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from utils import chunk_text_by_size
import yaml
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO)
import structlog
logger = structlog.get_logger("SaveAlineScraper")

# Configurable parameters
CONFIG = {
    'min_content_length': 100,
    'max_noise_signals': 3,
    'request_timeout': 10,
    'rate_limit_delay': (1, 3),
    'max_retries': 3,
    'pdf_author': 'Unknown'
}

# Setup retry strategy for session
session = requests.Session()
retries = Retry(
    total=CONFIG['max_retries'],
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

seen_hashes = set()

def _validate_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and parsed.netloc

def _get_content_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def detect_content_type(url):
    url_lower = url.lower()
    if "substack.com" in url_lower:
        return "blog"
    elif "reddit.com" in url_lower:
        return "reddit_comment"
    elif "linkedin.com" in url_lower:
        return "linkedin_post"
    elif "stackoverflow.com" in url_lower:
        return "qa"
    elif "github.com" in url_lower:
        return "code_repository"
    else:
        return "blog"

def is_index_page(url):
    return any(keyword in url for keyword in ['/blog', 'category', 'topics', 'learn'])

def is_content_too_noisy(text):
    noise_signals = ["javascript", "cookie", "advertising", "sign up", "subscribe"]
    noise_count = sum(1 for signal in noise_signals if signal in text.lower())
    words = text.split()
    if not words:
        return True
    unique_words = set(words)
    repetition_score = len(unique_words) / len(words)
    return noise_count >= CONFIG['max_noise_signals'] or repetition_score < 0.3

def extract_from_url(url):
    if not _validate_url(url):
        logger.warning(f"Invalid URL skipped: {url}")
        return []

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SaveAlineBot/1.0)"}
    try:
        response = session.get(url, headers=headers, timeout=CONFIG['request_timeout'])
        response.raise_for_status()
    except (RequestException, Timeout, HTTPError) as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return []

    g = Goose()
    article = g.extract(raw_html=response.text)

    if not article.cleaned_text or len(article.cleaned_text.strip()) < CONFIG['min_content_length']:
        logger.warning(f"Content too short, skipped: {url}")
        return []

    h = html2text.HTML2Text()
    h.ignore_links = False
    markdown_content = h.handle(article.cleaned_article_html)

    if is_content_too_noisy(markdown_content):
        logger.warning(f"Noisy content, skipped: {url}")
        return []

    content_hash = _get_content_hash(markdown_content)
    if content_hash in seen_hashes:
        logger.info(f"Duplicate content detected, skipping: {url}")
        return []
    seen_hashes.add(content_hash)

    soup = BeautifulSoup(response.text, "html.parser")
    meta_author = soup.find("meta", attrs={"name": "author"})
    author = meta_author.get("content", "") if meta_author else article.meta_data.get("author", CONFIG['pdf_author'])

    return [{
        "title": article.title or "Untitled",
        "content": markdown_content.strip(),
        "content_type": detect_content_type(url),
        "source_url": url,
        "author": author,
        "user_id": ""
    }]

def find_article_links(base_url, max_links=20):
    if not _validate_url(base_url):
        logger.warning(f"Invalid base URL skipped: {base_url}")
        return []

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SaveAlineBot/1.0)"}
    try:
        res = session.get(base_url, headers=headers, timeout=CONFIG['request_timeout'])
        res.raise_for_status()
    except (RequestException, Timeout, HTTPError) as e:
        logger.error(f"Failed to crawl index {base_url}: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    article_links = set()

    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag["href"].split('#')[0])  # Strip fragment
        if ("substack.com/p/" in href or
            any(keyword in href.lower() for keyword in ["blog", "post", "article", "story", "interview", "guide"])):
            article_links.add(href)
        if len(article_links) >= max_links:
            break

    return list(article_links)

def extract_from_blog_index(index_url, max_articles=20):
    logger.info(f"Crawling index: {index_url}")
    links = find_article_links(index_url, max_articles)
    logger.info(f"Found {len(links)} links")

    all_items = []
    for link in tqdm(links, desc='Extracting articles'):
        logger.info(f"Processing {link}")
        try:
            time.sleep(random.uniform(*CONFIG['rate_limit_delay']))
            items = extract_from_url(link)
            all_items.extend(items)
        except Exception as e:
            logger.error(f"Unhandled error while extracting: {e}", exc_info=True)
    return all_items

def extract_from_pdf(pdf_path, max_pages=50):
    logger.info(f"Extracting PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return []

    try:
        text = extract_text(pdf_path, maxpages=max_pages)
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return []

    chunks = chunk_text_by_size(text, max_chars=1500, overlap=200)
    return [{
        "title": f"Beyond Cracking the Coding Interview - Chunk {i+1}",
        "content": chunk.strip(),
        "content_type": "book",
        "source_url": "",
        "author": CONFIG['pdf_author'],
        "user_id": ""
    } for i, chunk in enumerate(chunks)]

SITE_CONFIGS = {
    'substack.com': {'delay': (2, 4), 'max_articles': 50},
    'medium.com': {'delay': (1, 2), 'max_articles': 30},
    'github.com': {'delay': (0.5, 1), 'max_articles': 20},
    'default': {'delay': (1, 3), 'max_articles': 20}
}

def get_site_config(url):
    domain = urlparse(url).netloc
    for site, config in SITE_CONFIGS.items():
        if site in domain:
            return config
    return SITE_CONFIGS['default']

import urllib.robotparser

def can_fetch(url, user_agent="*"):
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return True

def load_config(config_file="config.yaml"):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        config['rate_limit_delay'] = tuple(config.get('rate_limit_delay', [1, 3]))
        return config
    except:
        return CONFIG  # fallback

def detect_content_type_advanced(url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check for schema.org structured data
    schema = soup.find(attrs={"itemtype": True})
    if schema and "Article" in schema.get("itemtype", ""):
        return "article"

    # Check Open Graph type
    og_type = soup.find("meta", property="og:type")
    if og_type and og_type.get("content"):
        return og_type["content"]

    # Check Twitter card type
    twitter_type = soup.find("meta", attrs={"name": "twitter:card"})
    if twitter_type and twitter_type.get("content"):
        return twitter_type["content"]

    return detect_content_type(url)

def extract_from_blog_index_batched(index_url, max_articles=20, batch_size=10):
    logger.info(f"Batched crawl: {index_url}")
    links = find_article_links(index_url, max_articles)
    all_items = []

    for i in range(0, len(links), batch_size):
        batch = links[i:i+batch_size]
        for link in batch:
            try:
                time.sleep(random.uniform(*CONFIG['rate_limit_delay']))
                items = extract_from_url(link)
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"Batch extraction failed: {e}")
        import gc
        gc.collect()

    return all_items

def extract_with_fallback(url, max_attempts=3):
    extractors = [extract_from_url, fallback_bs4_extract]
    for attempt, extractor in enumerate(extractors):
        try:
            result = extractor(url)
            if result and len(result[0]['content']) > CONFIG['min_content_length']:
                return result
        except Exception as e:
            logger.warning(f"Extractor {attempt+1} failed for {url}: {e}")
    return []

def validate_and_sanitize_url(url):
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL format")

    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Only HTTP/HTTPS URLs allowed")

    if any(blocked in parsed.netloc.lower() for blocked in ['localhost', '127.0.0.1', '192.168.', '10.', '172.']):
        raise ValueError("Internal network URLs not allowed")

    return url

def setup_structured_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def fallback_bs4_extract(url):
    """Fallback extractor using BeautifulSoup when Goose fails"""
    if not _validate_url(url):
        logger.warning(f"Invalid URL skipped: {url}")
        return []

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SaveAlineBot/1.0)"}
    try:
        response = session.get(url, headers=headers, timeout=CONFIG['request_timeout'])
        response.raise_for_status()
    except Exception as e:
        logger.error(f"BS4 fallback failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text() for p in soup.find_all("p")]
    content = "\n\n".join(paragraphs)

    if len(content) < CONFIG['min_content_length']:
        return []

    return [{
        "title": soup.title.string if soup.title else "Untitled",
        "content": content,
        "content_type": detect_content_type(url),
        "source_url": url,
        "author": "",
        "user_id": ""
    }]
