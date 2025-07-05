def format_items(raw_items):
    return [{
        "title": item.get("title", ""),
        "content": item.get("content", ""),
        "content_type": item.get("content_type", "other"),
        "source_url": item.get("source_url", ""),
        "author": item.get("author", ""),
        "user_id": item.get("user_id", "")
    } for item in raw_items]
