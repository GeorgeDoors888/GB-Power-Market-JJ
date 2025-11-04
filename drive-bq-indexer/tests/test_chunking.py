from src.chunking import into_chunks

def test_into_chunks_basic():
    text = "Lorem ipsum dolor sit amet, " * 200
    chunks = list(into_chunks(text, size=500, overlap=50))
    assert len(chunks) > 1
    total_len = sum(len(c) for _, c, _ in chunks)
    assert total_len > 500
    assert all(isinstance(tok, int) for _, _, tok in chunks)
