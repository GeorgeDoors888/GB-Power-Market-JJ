import pytest
from src.chunking import into_chunks, tokenize_est

def test_tokenize_est():
    assert tokenize_est("hello world") > 0
    assert tokenize_est("a" * 100) == 25

def test_into_chunks():
    text = "word " * 500
    chunks = into_chunks(text, size=100, overlap=20)
    assert len(chunks) > 1
    for i, chunk, tok in chunks:
        assert isinstance(i, int)
        assert isinstance(chunk, str)
        assert tok > 0
