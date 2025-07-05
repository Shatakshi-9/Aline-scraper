
import asyncio
import aiohttp
import logging
import random
import time
from urllib.parse import urlparse
from extractor import (
    can_fetch,
    detect_content_type_advanced,
    _validate_url,
    get_site_config,
    seen_hashes,
    CONFIG,
    _get_content_hash
)
from goose3 import Goose
import html2text
from bs4 import BeautifulSoup

logger = logging.getLogger("AsyncExtractor")

async def fetch_and_extract(session, url, semaphore):
    async with semaphore:
        if not can_fetch(url):
            logger.warning(f"❌ Disallowed by robots.txt: {url}")
            return []

        try:
            async with session.get(url, timeout=CONFIG['request_timeout']) as response:
                html = await response.text()
        except Exception as e:
            logger.error(f"❌ Async fetch failed for {url}: {e}")
            return []

        g = Goose()
        article = g.extract(raw_html=html)

        if not article.cleaned_text or len(article.cleaned_text.strip()) < CONFIG['min_content_length']:
            logger.warning(f"⚠️ Skipped short content: {url}")
            return []

        h = html2text.HTML2Text()
        h.ignore_links = False
        markdown_content = h.handle(article.cleaned_article_html)

        if len(markdown_content) < CONFIG['min_content_length']:
            return []

        content_hash = _get_content_hash(markdown_content)
        if content_hash in seen_hashes:
            logger.info(f"🔁 Duplicate skipped: {url}")
            return []
        seen_hashes.add(content_hash)

        soup = BeautifulSoup(html, "html.parser")
        meta_author = soup.find("meta", attrs={"name": "author"})
        author = meta_author.get("content", "") if meta_author else article.meta_data.get("author", CONFIG['pdf_author'])

        return [{
            "title": article.title or "Untitled",
            "content": markdown_content.strip(),
            "content_type": detect_content_type_advanced(url, html),
            "source_url": url,
            "author": author,
            "user_id": ""
        }]

async def extract_from_urls_async(urls, max_concurrent=5):
    """Extract content from multiple URLs concurrently"""
    if not urls:
        return []

    config = get_site_config(urls[0])
    semaphore = asyncio.Semaphore(max_concurrent)
    all_items = []

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_extract(session, url, semaphore) for url in urls]

        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                all_items.extend(result)

                # Use async sleep instead of blocking time.sleep
                delay = random.uniform(*config['delay'])
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Task failed: {e}")
                continue

    return all_items
