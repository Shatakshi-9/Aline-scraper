
from utils import chunk_text_by_size

def test_chunking():
    text = "A\n\nB\n\nC\n\n" + "D " * 500
    chunks = chunk_text_by_size(text, max_chars=100, overlap=20)
    assert all(len(c) <= 100 for c in chunks)
    assert len(chunks) > 0
