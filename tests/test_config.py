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


def test_precos_opcionais(monkeypatch):
    monkeypatch.delenv("PRICE_IN_PER_1M", raising=False)
    monkeypatch.setenv("PRICE_OUT_PER_1M", "abc")
    c = load_config()
    assert c.price_in is None and c.price_out is None  # ausente ou inválido = sem estimativa
    monkeypatch.setenv("PRICE_IN_PER_1M", "0.25")
    monkeypatch.setenv("PRICE_OUT_PER_1M", "2,5")
    c = load_config()
    assert (c.price_in, c.price_out) == (0.25, 2.5)
