import requests
import json
import time

def test_api_endpoint(base_url, endpoint, params=None):
    """Test a specific API endpoint"""
    try:
        url = f"{base_url}{endpoint}"
        print(f"\n🧪 Testing: {url}")
        
        if params:
            response = requests.get(url, params=params, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request successful")
            return data
        else:
            print(f"❌ Request failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def validate_scraper_output(data, expected_items_min=1):
    """Validate the scraper output format"""
    print("\n🔍 Validating output format...")
    
    if not data:
        print("❌ No data received")
        return False
    
    # Check required fields
    required_fields = ["team_id", "items"]
    for field in required_fields:
        if field in data:
            print(f"✅ {field} field present")
        else:
            print(f"❌ {field} field missing")
            return False
    
    # Check items array
    items = data.get("items", [])
    if not isinstance(items, list):
        print("❌ items is not a list")
        return False
    
    if len(items) < expected_items_min:
        print(f"❌ Expected at least {expected_items_min} items, got {len(items)}")
        return False
    
    print(f"✅ Found {len(items)} items")
    
    # Check first item structure
    if items:
        item = items[0]
        required_item_fields = ["title", "content", "content_type", "source_url", "author", "user_id"]
        
        for field in required_item_fields:
            if field in item:
                print(f"✅ {field} field present")
            else:
                print(f"❌ {field} field missing")
                return False
        
        # Check content quality
        content = item.get("content", "")
        if len(content) > 100:
            print("✅ Content has good length")
        else:
            print("❌ Content too short")
            return False
        
        # Check if content looks like markdown
        if any(indicator in content for indicator in ["#", "*", "**", "\n\n", "```"]):
            print("✅ Content appears to be markdown")
        else:
            print("⚠️  Content doesn't clearly look like markdown")
        
        # Print sample content
        print(f"\n📄 Sample title: {item.get('title', 'N/A')}")
        print(f"📝 Content preview: {content[:200]}...")
        
    return True

def test_multiple_blogs(base_url):
    """Test scraping multiple different blog platforms"""
    test_cases = [
        {
            "name": "Interviewing.io Blog",
            "url": "https://interviewing.io/blog",
            "expected_min_items": 1
        },
        {
            "name": "Quill Blog",
            "url": "https://quill.co/blog",
            "expected_min_items": 1
        },
        {
            "name": "Nil's DS&A Blog",
            "url": "https://nilmamano.com/blog/category/dsa",
            "expected_min_items": 1
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🌐 Testing {test_case['name']}...")
        
        params = {
            "url": test_case["url"],
            "team_id": "aline123",
            "max_pages": 10
        }
        
        data = test_api_endpoint(base_url, "/scrape", params)
        
        if data:
            is_valid = validate_scraper_output(data, test_case["expected_min_items"])
            results[test_case["name"]] = {
                "success": is_valid,
                "items_found": len(data.get("items", [])),
                "url": test_case["url"]
            }
        else:
            results[test_case["name"]] = {
                "success": False,
                "error": "Request failed"
            }
        
        # Small delay between requests
        time.sleep(2)
    
    return results

def test_your_api():
    """Main test function"""
    # Test both local and deployed versions
    test_urls = [
        "http://localhost:10000",  # Local development
        "https://aline-scraper-api.onrender.com"  # Deployed version
    ]
    
    for base_url in test_urls:
        print(f"\n🚀 Testing API at: {base_url}")
        print("=" * 60)
        
        # Test health endpoint
        health_data = test_api_endpoint(base_url, "/health")
        if not health_data:
            print(f"❌ Health check failed for {base_url}")
            continue
        
        # Test root endpoint
        root_data = test_api_endpoint(base_url, "/")
        if not root_data:
            print(f"❌ Root endpoint failed for {base_url}")
            continue
        
        # Test scraping functionality
        print(f"\n📊 Testing scraping functionality...")
        results = test_multiple_blogs(base_url)
        
        # Summary
        print(f"\n📈 Summary for {base_url}:")
        successful_tests = sum(1 for r in results.values() if r["success"])
        total_tests = len(results)
        
        print(f"✅ Successful tests: {successful_tests}/{total_tests}")
        
        for name, result in results.items():
            if result["success"]:
                print(f"✅ {name}: {result['items_found']} items scraped")
            else:
                print(f"❌ {name}: Failed")
        
        # Test the test endpoint
        print(f"\n🔧 Testing validation endpoint...")
        test_data = test_api_endpoint(base_url, "/test")
        if test_data:
            print("✅ Test endpoint working")
            print(f"📊 Test results: {json.dumps(test_data, indent=2)}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_your_api()
