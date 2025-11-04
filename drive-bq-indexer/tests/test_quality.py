from src.quality.auto_tune import suggest_settings

def test_tune_recommendations(monkeypatch):
    monkeypatch.setattr("src.quality.auto_tune.fetch_metrics", lambda _: {"avg_chars": 700, "ocr_like_rate": 0.7})
    s = suggest_settings("dummy")
    assert s["CHUNK_SIZE"] > 1200
    assert s["OCR_MODE"] == "force"
