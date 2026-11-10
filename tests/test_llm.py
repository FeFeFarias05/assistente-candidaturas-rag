from types import SimpleNamespace

import pytest

from jobassist import llm


def fake_client(reply):
    def create(**kw):
        create.kw = kw
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])
    c = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return c, create


def test_text(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "m")
    c, create = fake_client("ola")
    monkeypatch.setattr(llm, "_client", lambda: c)
    assert llm.complete("oi", system="s") == "ola"
    assert create.kw["messages"][0]["role"] == "system"
    assert "response_format" not in create.kw


def test_json(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "m")
    c, create = fake_client('{"a": 1}')
    monkeypatch.setattr(llm, "_client", lambda: c)
    assert llm.complete("oi", schema={"type": "object"}) == {"a": 1}
    assert create.kw["response_format"]["type"] == "json_schema"


def test_sem_modelo(monkeypatch):
    monkeypatch.setattr(llm, "load_config", lambda: SimpleNamespace(model=None, api_key="k"))
    with pytest.raises(RuntimeError, match="OPENAI_MODEL"):
        llm.complete("oi")


def test_sem_chave(monkeypatch):
    monkeypatch.setattr(llm, "load_config", lambda: SimpleNamespace(model="m", api_key=None))
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm._client()


def _with_usage(reply, prompt_tokens, completion_tokens):
    def create(**kw):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=reply))],
            usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        )
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_consumo_soma_chamadas_e_zera(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "m")
    monkeypatch.delenv("PRICE_IN_PER_1M", raising=False)
    monkeypatch.delenv("PRICE_OUT_PER_1M", raising=False)
    monkeypatch.setattr(llm, "_client", lambda: _with_usage("ok", 100, 20))
    llm.reset_usage()
    assert llm.usage_summary() is None  # nada gasto, nada a mostrar
    llm.complete("a")
    llm.complete("b")
    u = llm.usage()
    assert (u["calls"], u["input"], u["output"], u["cost_usd"]) == (2, 200, 40, None)
    assert "2 chamada(s)" in llm.usage_summary() and "US$" not in llm.usage_summary()
    llm.reset_usage()
    assert llm.usage()["calls"] == 0


def test_custo_so_aparece_com_os_dois_precos(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "m")
    monkeypatch.setattr(llm, "_client", lambda: _with_usage("ok", 1_000_000, 500_000))
    monkeypatch.setenv("PRICE_IN_PER_1M", "0,50")  # vírgula decimal também vale
    monkeypatch.delenv("PRICE_OUT_PER_1M", raising=False)
    llm.reset_usage()
    llm.complete("a")
    assert llm.usage()["cost_usd"] is None  # só um preço: sem estimativa
    monkeypatch.setenv("PRICE_OUT_PER_1M", "2")
    assert llm.usage()["cost_usd"] == pytest.approx(0.5 + 1.0)
    assert "US$ 1.5000" in llm.usage_summary()


def test_resposta_sem_usage_nao_quebra(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "m")
    c, _ = fake_client("ola")  # o cliente simulado antigo não tem `usage`
    monkeypatch.setattr(llm, "_client", lambda: c)
    llm.reset_usage()
    assert llm.complete("oi") == "ola" and llm.usage()["calls"] == 0


def test_embeddings_openai_conta_so_entrada(monkeypatch):
    resp = SimpleNamespace(data=[SimpleNamespace(embedding=[1.0])], usage=SimpleNamespace(prompt_tokens=None, total_tokens=7))
    monkeypatch.setattr(llm, "_client", lambda: SimpleNamespace(embeddings=SimpleNamespace(create=lambda **k: resp)))
    llm.reset_usage()
    llm.embeddings_openai(["x"], "m")
    assert (llm.usage()["input"], llm.usage()["output"]) == (7, 0)


def test_modelo_pode_ser_trocado_so_numa_chamada(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gerador")
    usados = []

    def create(**kw):
        usados.append(kw["model"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    monkeypatch.setattr(llm, "_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    llm.complete("a")
    llm.complete("b", model="juiz")
    llm.complete("c")
    assert usados == ["gerador", "juiz", "gerador"]  # a troca não vaza para as chamadas seguintes
