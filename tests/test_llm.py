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
