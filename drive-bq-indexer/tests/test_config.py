import os, tempfile, yaml
from src.config import load_settings

def test_env_expansion(tmp_path):
    os.environ["TEST_VAL"] = "works"
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text("key: ${TEST_VAL}")
    cfg = load_settings(str(cfg_file))
    assert cfg["key"] == "works"
