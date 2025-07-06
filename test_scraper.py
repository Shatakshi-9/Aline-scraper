'''from extractor import extract_from_blog_index, extract_from_url, is_index_page

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
    run_tests()'''

import requests
import json

def test_your_api():
    # Test your local API
    url = "http://localhost:5000/scrape?url=https://interviewing.io/blog"
    
    print("🧪 Testing your updated API...")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print("✅ API Response received")
        print(f"📊 Status Code: {response.status_code}")
        
        # Check required fields
        if "team_id" in data:
            print("✅ team_id field present")
        else:
            print("❌ team_id field missing")
            
        if "items" in data and isinstance(data["items"], list):
            print(f"✅ items array present with {len(data['items'])} items")
            
            # Check first item structure
            if data["items"]:
                item = data["items"][0]
                required_fields = ["title", "content", "content_type", "source_url", "author", "user_id"]
                
                for field in required_fields:
                    if field in item:
                        print(f"✅ {field} field present")
                    else:
                        print(f"❌ {field} field missing")
                
                # Check content quality
                if len(item.get("content", "")) > 100:
                    print("✅ Content has good length")
                else:
                    print("❌ Content too short")
                    
                # Check if content looks like markdown
                content = item.get("content", "")
                if any(indicator in content for indicator in ["#", "*", "**", "\n\n"]):
                    print("✅ Content appears to be markdown")
                else:
                    print("❌ Content doesn't look like markdown")
        else:
            print("❌ items array missing or invalid")
            
        # Print sample output
        print("\n📄 Sample output:")
        print(json.dumps(data, indent=2)[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_your_api()
