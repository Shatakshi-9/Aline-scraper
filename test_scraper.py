from extractor import extract_from_blog_index, extract_from_url, is_index_page

def test_single_url(url):
    print(f"\n🧪 Testing: {url}")
    if is_index_page(url):
        items = extract_from_blog_index(url, max_articles=5)
    else:
        items = extract_from_url(url)

    print(f"✅ Extracted {len(items)} items")
    for item in items[:1]:
        print(f"Title: {item['title']}")
        print(f"Source: {item['source_url']}")
        print(f"Content sample:\n{item['content'][:300]}\n")

def run_tests():
    with open("test_sites.txt") as f:
        urls = [line.strip() for line in f if line.strip()]
    for url in urls:
        test_single_url(url)

if __name__ == "__main__":
    run_tests()
