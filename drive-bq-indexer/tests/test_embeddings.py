import os
from src.search.embed import embed_texts

def test_stub_embedding_shape():
    os.environ["EMBED_PROVIDER"] = "stub"
    vecs = embed_texts(["hello", "world"])
    assert len(vecs) == 2
    assert all(isinstance(x, list) for x in vecs)
    assert all(isinstance(v, float) for v in vecs[0])
