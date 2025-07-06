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
        except Exception as e:
            raise Exception(f"Failed to fetch topic page: {e}")

        soup = BeautifulSoup(response.text, "html.parser")

        sections = soup.find_all(["section", "article", "div"], class_=lambda x: x and 'topic' in x.lower())
        items = []

        for section in sections:
            title_tag = section.find(["h1", "h2", "h3"])
            title = title_tag.get_text(strip=True) if title_tag else "Untitled Topic"
            markdown = self.html2text_converter.handle(str(section))

            items.append({
                "title": title,
                "content": markdown.strip(),
                "content_type": "guide",
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
        except Exception as e:
            raise Exception(f"Failed to fetch guide page: {e}")

        soup = BeautifulSoup(response.text, "html.parser")

        guides = soup.find_all("article")
        if not guides:
            guides = soup.find_all("div", class_=lambda x: x and "guide" in x.lower())

        items = []

        for guide in guides:
            title_tag = guide.find(["h1", "h2", "h3"])
            title = title_tag.get_text(strip=True) if title_tag else "Interview Guide"
            markdown = self.html2text_converter.handle(str(guide))

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
