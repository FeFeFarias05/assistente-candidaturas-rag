import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(override=True)  # o .env do projeto vale mais que variáveis do shell


@dataclass(frozen=True)
class Config:
    api_key: str | None
    model: str | None
    embeddings: str
    material_dir: str
    price_in: float | None = None  # US$ por 1 milhão de tokens de entrada (opcional)
    price_out: float | None = None  # idem, de saída


def _float(name: str) -> float | None:
    try:
        return float(os.getenv(name, "").replace(",", "."))
    except ValueError:
        return None  # vazio ou inválido: sem estimativa de custo


def load_config() -> Config:
    return Config(
        api_key=os.getenv("OPENAI_API_KEY") or None,
        model=os.getenv("OPENAI_MODEL") or None,
        embeddings=os.getenv("EMBEDDINGS", "local"),
        material_dir=os.getenv("MATERIAL_DIR", "data/sample"),
        price_in=_float("PRICE_IN_PER_1M"),
        price_out=_float("PRICE_OUT_PER_1M"),
    )
