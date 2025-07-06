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


        def scrape_pdf(self, url: str, team_id: str = "aline123") -> dict:
        from io import BytesIO
        from pdfminer.high_level import extract_text

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            pdf_bytes = BytesIO(response.content)
            text = extract_text(pdf_bytes)
        except Exception as e:
            raise Exception(f"Failed to extract PDF: {e}")

        markdown = self.html2text_converter.handle(text)

        return {
            "team_id": team_id,
            "items": [
                {
                    "title": "PDF Document",
                    "content": markdown.strip(),
                    "content_type": "book",
                    "source_url": url,
                    "author": "",
                    "user_id": ""
                }
            ]
        }

    def scrape_topic_page(self, url: str, team_id: str) -> dict:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            raise Exception(f"Failed to load topic page: {e}")

        article_sections = soup.find_all("article")
        items = []

        for section in article_sections:
            title_tag = section.find(["h1", "h2"])
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            raw_html = str(section)
            markdown = self.html2text_converter.handle(raw_html)

            items.append({
                "title": title,
                "content": markdown.strip(),
                "content_type": "topic_guide",
                "source_url": url,
                "author": "",
                "user_id": ""
            })

        return {
            "team_id": team_id,
            "items": items
        }

    def scrape_interview_guides(self, url: str, team_id: str) -> dict:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            raise Exception(f"Failed to load interview guide: {e}")

        guide_sections = soup.find_all("section")
        items = []

        for section in guide_sections:
            title_tag = section.find(["h1", "h2"])
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            raw_html = str(section)
            markdown = self.html2text_converter.handle(raw_html)

            items.append({
                "title": title,
                "content": markdown.strip(),
                "content_type": "interview_guide",
                "source_url": url,
                "author": "",
                "user_id": ""
            })

        return {
            "team_id": team_id,
            "items": items
        }

