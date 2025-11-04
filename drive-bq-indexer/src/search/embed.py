from __future__ import annotations
import os
import numpy as np

# Optional Vertex AI embedding
_USE_VERTEX = os.getenv("EMBED_PROVIDER", "stub").lower() == "vertex"

if _USE_VERTEX:
    import vertexai
    from vertexai.preview.language_models import TextEmbeddingModel  # textembedding-gecko

    def _vertex_client():
        project = os.getenv("GCP_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "europe-west2")
        vertexai.init(project=project, location=location)
        model_name = os.getenv("VERTEX_EMBED_MODEL", "textembedding-gecko@latest")
        return TextEmbeddingModel.from_pretrained(model_name)

    _MODEL = None

    def embed_texts(texts: list[str], dim: int | None = None) -> list[list[float]]:
        global _MODEL
        if _MODEL is None:
            _MODEL = _vertex_client()
        res = _MODEL.get_embeddings(texts)
        return [e.values for e in res]
else:
    # Fallback stub
    def embed_texts(texts: list[str], dim: int = 384) -> list[list[float]]:
        out = []
        for t in texts:
            rng = np.random.default_rng(abs(hash(t)) % (2**32))
            out.append(rng.random(dim).tolist())
        return out
