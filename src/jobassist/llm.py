"""Única porta de saída para o LLM. Todo texto enviado à API passa por aqui."""
import json
import sys
import threading

from openai import OpenAI

from .config import load_config

_USAGE = {"calls": 0, "input": 0, "output": 0}
_LOCK = threading.Lock()


def reset_usage() -> None:
    with _LOCK:
        _USAGE.update(calls=0, input=0, output=0)


def _add_usage(resp, output: bool = True) -> None:
    u = getattr(resp, "usage", None)
    if u is None:
        return
    with _LOCK:
        _USAGE["calls"] += 1
        _USAGE["input"] += getattr(u, "prompt_tokens", None) or getattr(u, "total_tokens", 0) or 0
        _USAGE["output"] += (getattr(u, "completion_tokens", 0) or 0) if output else 0


def usage() -> dict:
    """Consumo desde o último reset. `cost_usd` só existe se os preços estiverem no .env."""
    cfg = load_config()
    with _LOCK:
        out = dict(_USAGE)
    out["cost_usd"] = None
    if cfg.price_in is not None and cfg.price_out is not None:
        out["cost_usd"] = out["input"] / 1e6 * cfg.price_in + out["output"] / 1e6 * cfg.price_out
    return out


def usage_summary() -> str | None:
    u = usage()
    if not u["calls"]:
        return None
    s = f"{u['calls']} chamada(s) à API, {u['input']} tokens de entrada e {u['output']} de saída"
    if u["cost_usd"] is not None:
        s += f" (≈ US$ {u['cost_usd']:.4f}, pelos preços do .env)"
    return s


def _client() -> OpenAI:
    cfg = load_config()
    if not cfg.api_key:
        raise RuntimeError("OPENAI_API_KEY ausente. Copie .env.example para .env e preencha.")
    return OpenAI(api_key=cfg.api_key)


def embeddings_openai(texts: list[str], model: str) -> list[list[float]]:
    print(f"[llm] enviando {sum(map(len, texts))} caracteres para {model} (embeddings)", file=sys.stderr)
    resp = _client().embeddings.create(model=model, input=texts)
    _add_usage(resp, output=False)
    return [d.embedding for d in resp.data]


def complete(prompt: str, system: str | None = None, schema: dict | None = None):
    """Devolve texto, ou dict se `schema` (JSON Schema) for dado."""
    cfg = load_config()
    if not cfg.model:
        raise RuntimeError("OPENAI_MODEL ausente no .env.")
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    kwargs = {}
    if schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "saida", "strict": True, "schema": schema},
        }
    # Transparência de privacidade: avisa o que está saindo da máquina.
    sent = sum(len(m["content"]) for m in messages)
    print(f"[llm] enviando {sent} caracteres para {cfg.model}", file=sys.stderr)
    # sem `temperature`: modelos GPT-5 só aceitam o padrão
    resp = _client().chat.completions.create(model=cfg.model, messages=messages, **kwargs)
    _add_usage(resp)
    text = resp.choices[0].message.content
    return json.loads(text) if schema else text
