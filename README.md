
# Aline Scraper 🚀

A scalable, resilient content extractor for building knowledge bases from blogs, PDFs, and more.

## ✨ Features

- ✅ Sync & Async scraping
- 🧠 Advanced content filtering
- 💾 Checkpoint resume support
- 🛡️ Secure, validated scraping
- 🧰 Configurable via `config.yaml`
- 📊 Structured logging

## 🧪 Usage

```bash
# Sync scrape
python main.py --url https://example.com/blog

# Async + checkpoint
python main.py --url https://example.com/blog --async --resume
```

## 🐳 Docker

```bash
docker build -t aline-scraper .
docker run --rm -v $PWD/output:/app/output aline-scraper --url https://example.com/blog
```

## 🧪 Testing

```bash
pip install pytest
pytest tests/
```

## 📂 Project Structure

- `main.py` - CLI entry point
- `extractor.py` - Core scraper
- `async_extractor.py` - Async engine
- `formatter.py` - Output formatting
- `utils.py` - Text helpers
- `resume_utils.py` - Resume support
- `config.yaml` - Runtime config
- `requirements.txt` - Dependencies

---

## ✍️ Contribution

PRs welcome! Please lint (`black`) and test before submitting.
