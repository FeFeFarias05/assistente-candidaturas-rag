"""Única porta de saída para o LLM. Todo texto enviado à API passa por aqui."""
import json
import sys

from openai import OpenAI

from .config import load_config


def _client() -> OpenAI:
    cfg = load_config()
    if not cfg.api_key:
        raise RuntimeError("OPENAI_API_KEY ausente. Copie .env.example para .env e preencha.")
    return OpenAI(api_key=cfg.api_key)


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
    text = resp.choices[0].message.content
    return json.loads(text) if schema else text
