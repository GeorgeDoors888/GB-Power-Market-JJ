from __future__ import annotations
import os, yaml
from dotenv import load_dotenv

load_dotenv()

def load_settings(path: str = "config/settings.yaml") -> dict:
    """Load YAML config with environment variable expansion."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    def _expand(v):
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            return os.getenv(v[2:-1], "")
        return v

    def _walk(x):
        if isinstance(x, dict):
            return {k: _walk(_expand(v)) for k, v in x.items()}
        if isinstance(x, list):
            return [_walk(v) for v in x]
        return _expand(x)

    return _walk(raw)
