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


def load_config() -> Config:
    return Config(
        api_key=os.getenv("OPENAI_API_KEY") or None,
        model=os.getenv("OPENAI_MODEL") or None,
        embeddings=os.getenv("EMBEDDINGS", "local"),
        material_dir=os.getenv("MATERIAL_DIR", "data/sample"),
    )
