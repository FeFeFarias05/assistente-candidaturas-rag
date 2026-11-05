from jobassist.config import load_config


def test_defaults(monkeypatch):
    for k in ("OPENAI_API_KEY", "OPENAI_MODEL", "EMBEDDINGS", "MATERIAL_DIR"):
        monkeypatch.delenv(k, raising=False)
    c = load_config()
    assert c.api_key is None and c.model is None
    assert c.embeddings == "local" and c.material_dir == "data/sample"


def test_reads_env(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "x")
    assert load_config().model == "x"
