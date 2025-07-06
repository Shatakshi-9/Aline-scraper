
# Aline Scraper 🚀

A scalable, resilient content extractor for building knowledge bases from blogs, PDFs, and more. Built for technical thought leaders who need to import their content into AI-powered comment generation systems.

## ✨ Features

* ✅ **Universal Blog Support** - Works with any blog structure (interviewing.io, quill.co, Substack, etc.)
* 🧠 **Advanced Content Filtering** - Smart extraction of meaningful content, filtering out navigation/ads
* 💾 **Checkpoint Resume Support** - Resume interrupted scraping sessions
* 🛡️ **Secure, Validated Scraping** - Rate limiting, error handling, and respectful crawling
* 🧰 **Configurable via `config.yaml`** - Easy customization without code changes
* 📊 **Structured Logging** - Comprehensive logging for debugging and monitoring
* 🌐 **REST API** - FastAPI-based web service for easy integration
* 📱 **Multiple Interfaces** - CLI, Docker, and REST API support
* 📄 **PDF Processing** - Extract and chunk content from PDF documents
* 🎯 **Standardized Output** - Consistent JSON format for knowledge base integration

## 🌐 Live API

The scraper is deployed and ready to use:

**Base URL:** `https://aline-scraper-api.onrender.com`

### API Endpoints

```bash
# Health check
GET /health

# Scrape a blog or website
GET /scrape?url={blog_url}&team_id={team_id}

# Test endpoint
GET /test
```

### API Usage Examples

```bash
# Scrape interviewing.io blog
curl "https://aline-scraper-api.onrender.com/scrape?url=https://interviewing.io/blog&team_id=aline123"

# Scrape any blog (e.g., quill.co)
curl "https://aline-scraper-api.onrender.com/scrape?url=https://quill.co/blog&team_id=aline123"

# Scrape Substack
curl "https://aline-scraper-api.onrender.com/scrape?url=https://shreycation.substack.com&team_id=aline123"

# Health check
curl "https://aline-scraper-api.onrender.com/health"
```

## 📤 Output Format

The scraper returns data in the standardized knowledge base format:

```json
{
  "team_id": "aline123",
  "items": [
    {
      "title": "How to Ace Technical Interviews",
      "content": "# Technical Interview Guide\n\nMarkdown formatted content here...",
      "content_type": "blog",
      "source_url": "https://example.com/blog/technical-interviews",
      "author": "Jane Smith",
      "user_id": ""
    }
  ]
}
```

### Content Types Supported
- `blog` - Blog posts and articles
- `book` - PDF book chapters
- `podcast_transcript` - Podcast transcriptions
- `call_transcript` - Call recordings
- `linkedin_post` - LinkedIn content
- `reddit_comment` - Reddit discussions
- `other` - General content

## 🧪 Local Usage

### CLI Interface

```bash
# Basic scraping
python main.py --url https://example.com/blog

# Async scraping with resume capability
python main.py --url https://example.com/blog --async --resume

# Custom team ID
python main.py --url https://example.com/blog --team-id custom123

# Verbose logging
python main.py --url https://example.com/blog --verbose
```

### Python Integration

```python
from extractor import AlineExtractor
from formatter import format_for_knowledge_base

# Initialize extractor
extractor = AlineExtractor()

# Scrape content
raw_content = extractor.scrape_url("https://example.com/blog")

# Format for knowledge base
formatted_data = format_for_knowledge_base(raw_content, team_id="aline123")

print(formatted_data)
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t aline-scraper .

# Run with volume mapping
docker run --rm -v $PWD/output:/app/output aline-scraper --url https://example.com/blog

# Run API server
docker run -p 8000:8000 aline-scraper

# Environment variables
docker run -e TEAM_ID=aline123 -e LOG_LEVEL=DEBUG aline-scraper
```

## 🛠️ Installation

### Requirements

```bash
pip install -r requirements.txt
```

### Dependencies

```
Flask==2.3.3
requests==2.31.0
beautifulsoup4==4.12.2
html2text==2020.1.16
lxml>=5.0.0
gunicorn==21.2.0
goose3
pdfminer.six
tqdm
fastapi
uvicorn[standard]
structlog
aiohttp
python-multipart
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_extractor.py
pytest tests/test_api.py
pytest tests/test_async.py

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage

The test suite covers:
- ✅ Multiple blog platforms (interviewing.io, quill.co, Substack)
- ✅ PDF processing and chunking
- ✅ Error handling and edge cases
- ✅ API endpoints and responses
- ✅ Async processing capabilities
- ✅ Resume functionality

## 📂 Project Structure

```
aline-scraper/
├── main.py                 # CLI entry point
├── main_api.py             # FastAPI web service
├── extractor.py            # Core scraper logic
├── async_extractor.py      # Async processing engine
├── formatter.py            # Output formatting
├── utils.py                # Text processing helpers
├── resume_utils.py         # Checkpoint/resume support
├── config.yaml             # Runtime configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── tests/                  # Test suite
│   ├── test_extractor.py
│   ├── test_api.py
│   └── test_async.py
└── output/                 # Scraped content output
```

## ⚙️ Configuration

Customize behavior via `config.yaml`:

```yaml
scraping:
  delay_between_requests: 1.0
  max_retries: 3
  timeout: 30
  user_agent: "Aline-Scraper/2.0"

content:
  min_content_length: 100
  max_content_length: 50000
  extract_images: false
  preserve_formatting: true

output:
  format: "markdown"
  include_metadata: true
  chunk_size: 2000  # For PDF processing

logging:
  level: "INFO"
  format: "structured"
```

## 🎯 Supported Sources

### Validated Platforms

- ✅ **interviewing.io** - Technical interview content
- ✅ **quill.co** - Blog posts and guides
- ✅ **Substack** - Newsletter platforms
- ✅ **Medium** - Articles and publications
- ✅ **Ghost CMS** - Modern blog platforms
- ✅ **WordPress** - Traditional blog sites
- ✅ **Custom blogs** - Any HTML-based content

### Specific Sources for Aline

- ✅ `https://interviewing.io/blog` - All blog posts
- ✅ `https://interviewing.io/topics#companies` - Company guides
- ✅ `https://interviewing.io/learn#interview-guides` - Interview guides
- ✅ `https://nilmamano.com/blog/category/dsa` - DS&A blog posts
- ✅ PDF book chapters (first 8 chapters)

## 🚀 Performance Features

- **Async Processing** - Handle multiple URLs concurrently
- **Smart Caching** - Avoid re-scraping unchanged content
- **Rate Limiting** - Respectful crawling with configurable delays
- **Resume Capability** - Continue interrupted scraping sessions
- **Batch Processing** - Process multiple sources efficiently
- **Memory Management** - Efficient handling of large content

## 🔧 Advanced Usage

### Batch Processing

```bash
# Process multiple URLs
python main.py --urls urls.txt --batch

# Async batch processing
python main.py --urls urls.txt --batch --async --workers 5
```

### PDF Processing

```bash
# Process PDF with custom chunking
python main.py --pdf book.pdf --chunk-size 2000 --overlap 200

# Extract specific pages
python main.py --pdf book.pdf --pages 1-8
```

### Resume Functionality

```bash
# Start scraping with checkpoint
python main.py --url https://example.com/blog --checkpoint

# Resume from checkpoint
python main.py --resume --checkpoint-file scrape_progress.json
```

## 🛡️ Security & Best Practices

- **Rate Limiting** - Configurable delays between requests
- **User Agent Rotation** - Respectful identification
- **Error Handling** - Graceful failure recovery
- **Input Validation** - Secure URL and parameter handling
- **Content Filtering** - Remove potentially harmful content
- **Privacy Respect** - No personal data collection

## 📊 Monitoring & Logging

```python
import structlog

logger = structlog.get_logger()
logger.info("Scraping started", url=url, team_id=team_id)
logger.error("Scraping failed", error=str(e), url=url)
```

## 🤝 API Integration

### FastAPI Integration

```python
from fastapi import FastAPI
from main_api import app

# The API is ready for integration
# Deployed at: https://aline-scraper-api.onrender.com
```

### Webhook Support

```bash
# Post-processing webhook
curl -X POST https://aline-scraper-api.onrender.com/webhook   -H "Content-Type: application/json"   -d '{"url": "https://example.com/blog", "team_id": "aline123"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Rate Limiting**
   ```yaml
   # Adjust config.yaml
   scraping:
     delay_between_requests: 2.0
   ```

3. **Memory Issues**
   ```bash
   # Use streaming mode
   python main.py --url https://example.com/blog --stream
   ```

### Debug Mode

```bash
# Enable verbose logging
python main.py --url https://example.com/blog --debug --verbose
```

## ✍️ Contributing

We welcome contributions! Please:

1. **Fork the repository**
2. **Create a feature branch**
3. **Add tests for new functionality**
4. **Run the linter**: `black .`
5. **Run tests**: `pytest tests/`
6. **Submit a pull request**

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/aline-scraper.git

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install
```

## 📜 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built for technical thought leaders who need to scale their content for AI-powered engagement tools. Special thanks to the open-source community for the excellent libraries that make this possible.

---

**Ready to scale your content extraction? Start with the live API or deploy your own instance!**

🌐 **Live API**: `https://aline-scraper-api.onrender.com`  
📚 **Documentation**: Available in `/docs` endpoint  
🚀 **Deploy**: One-click deployment on Render, Heroku, or AWS
