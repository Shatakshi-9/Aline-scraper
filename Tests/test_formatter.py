
from formatter import format_items

def test_format_items_structure():
    raw = [{"title": "Test", "content": "Body"}]
    formatted = format_items(raw)
    assert formatted[0]["title"] == "Test"
    assert "content_type" in formatted[0]
