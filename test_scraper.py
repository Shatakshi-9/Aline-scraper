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
import time
from typing import Dict, List

class ScraperTester:
    def __init__(self, base_url: str = "https://aline-scraper-api.onrender.com"):
        self.base_url = base_url
        self.test_results = []
    
    def test_scraper(self, test_url: str, expected_min_items: int = 1) -> Dict:
        """Test the scraper with a specific URL"""
        print(f"\n🧪 Testing: {test_url}")
        
        try:
            # Make request to scraper API
            response = requests.get(
                f"{self.base_url}/scrape",
                params={"url": test_url},
                timeout=60
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response text: {response.text[:200]}...")
                return {
                    "url": test_url,
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:500]
                }
            
            data = response.json()
            
            # Validate response format
            validation_result = self._validate_response_format(data)
            
            # Check if we got items
            items_count = len(data.get('items', []))
            
            result = {
                "url": test_url,
                "status": "PASSED" if items_count >= expected_min_items else "FAILED",
                "items_count": items_count,
                "expected_min": expected_min_items,
                "format_valid": validation_result['valid'],
                "format_errors": validation_result['errors'],
                "sample_item": data.get('items', [{}])[0] if data.get('items') else None,
                "has_error": 'error' in data
            }
            
            # Print results
            if result['status'] == "PASSED":
                print(f"✅ SUCCESS: Found {items_count} items")
                if result['sample_item']:
                    print(f"   Sample title: {result['sample_item'].get('title', 'N/A')[:50]}...")
                    print(f"   Sample content length: {len(result['sample_item'].get('content', ''))}")
            else:
                print(f"❌ FAILED: Found {items_count} items (expected >= {expected_min_items})")
                if validation_result['errors']:
                    print(f"   Format errors: {validation_result['errors']}")
                if result['has_error']:
                    print(f"   API Error: {data.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                "url": test_url,
                "status": "ERROR",
                "error": str(e)
            }
    
    def _validate_response_format(self, data: Dict) -> Dict:
        """Validate that response matches assignment requirements"""
        errors = []
        
        # Check required fields
        if 'team_id' not in data:
            errors.append("Missing 'team_id' field")
        elif data['team_id'] != 'aline123':
            errors.append(f"Invalid team_id: {data['team_id']}")
        
        if 'items' not in data:
            errors.append("Missing 'items' field")
        elif not isinstance(data['items'], list):
            errors.append("'items' should be a list")
        
        # Check item format
        for i, item in enumerate(data.get('items', [])[:3]):  # Check first 3 items
            required_fields = ['title', 'content', 'content_type', 'source_url', 'author', 'user_id']
            for field in required_fields:
                if field not in item:
                    errors.append(f"Item {i}: Missing '{field}' field")
            
            # Check content_type values
            valid_content_types = ['blog', 'podcast_transcript', 'call_transcript', 'linkedin_post', 'reddit_comment', 'book', 'other']
            if item.get('content_type') not in valid_content_types:
                errors.append(f"Item {i}: Invalid content_type '{item.get('content_type')}'")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def run_comprehensive_test(self):
        """Run tests on all required URLs from the assignment"""
        
        print("🚀 Starting Comprehensive Scraper Testing")
        print("=" * 60)
        
        # Test URLs from assignment
        test_cases = [
            # Assignment required URLs
            ("https://interviewing.io/blog", 3),
            ("https://interviewing.io/topics", 2),
            ("https://interviewing.io/learn", 2),
            ("https://nilmamano.com/blog/category/dsa", 2),
            
            # Test case from assignment
            ("https://quill.co/blog", 2),
            
            # Bonus: Substack
            ("https://shreycation.substack.com", 1),
            
            # Additional simple test cases
            ("https://blog.hubspot.com", 2),
        ]
        
        results = []
        
        for url, min_items in test_cases:
            result = self.test_scraper(url, min_items)
            results.append(result)
            time.sleep(3)  # Be respectful with requests
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[Dict]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r.get('status') == 'PASSED')
        failed = sum(1 for r in results if r.get('status') == 'FAILED')
        errors = sum(1 for r in results if r.get('status') == 'ERROR')
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🔥 Errors: {errors}")
        
        if passed + failed + errors > 0:
            print(f"📈 Success Rate: {passed/(passed+failed+errors)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in results:
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌" if result['status'] == 'FAILED' else "🔥"
            print(f"{status_emoji} {result['url']}")
            if result.get('items_count') is not None:
                print(f"   Items: {result['items_count']}")
            if result.get('format_errors'):
                print(f"   Format issues: {result['format_errors']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            if result.get('has_error'):
                print(f"   API reported error")
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS:")
        
        if failed > 0:
            print("- Some sites returned insufficient items. Check content extraction logic.")
        
        if errors > 0:
            print("- Some requests failed. Check error handling and network issues.")
        
        format_issues = any(not r.get('format_valid', True) for r in results)
        if format_issues:
            print("- Fix response format to match assignment requirements.")
        
        print("\n💡 SCORING PREDICTION:")
        if passed >= 5:
            print("🎯 HIGH SCORE: Your scraper works well across different platforms!")
        elif passed >= 3:
            print("🎯 MEDIUM SCORE: Good foundation, but needs improvement for some sites.")
        else:
            print("🎯 LOW SCORE: Major issues need fixing before submission.")

def main():
    print("🔧 Blog Scraper Validation Tool")
    print("Testing your scraper against assignment requirements...")
    
    # Initialize tester
    tester = ScraperTester()
    
    # Run comprehensive tests
    results = tester.run_comprehensive_test()
    
    # Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to 'test_results.json'")

if __name__ == "__main__":
    main()
