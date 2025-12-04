from typing import Dict, Any

def resolve_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Turn UI filters into resolved dict (placeholder for now).

    Supports:
      - mode: ALL | VLP_ONLY | BESS_ONLY
      - gsp: single GSP id or None
      - dno: single DNO id or None
    """
    out = dict(filters)
    mode = (filters.get("mode") or "ALL").upper()
    if mode not in {"ALL", "VLP_ONLY", "BESS_ONLY"}:
        mode = "ALL"
    out["mode"] = mode
    return out
