"""Model ids ("databricks/<endpoint>", "google/<model>") -> Inspect models, credentials, limits.

Credentials never live in code or config: Databricks comes from the CLI profile
(~/.databrickscfg, `databricks auth login`), Gemini from GEMINI_API_KEY in the environment or a
git-ignored .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "providers.yml"


@dataclass(frozen=True)
class ModelSpec:
    id: str  # "databricks/databricks-qwen35-122b-a10b"
    provider: str
    name: str
    inspect_model: str
    max_connections: int
    max_retries: int


@lru_cache(maxsize=1)
def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def spec(model_id: str) -> ModelSpec:
    provider, _, name = model_id.partition("/")
    cfg = config().get(provider)
    if cfg is None or not name:
        raise ValueError(
            f"unknown model id {model_id!r}; use '<provider>/<model>' from providers.yml"
        )
    return ModelSpec(
        id=model_id,
        provider=provider,
        name=name,
        inspect_model=f"{cfg['inspect_prefix']}/{name}",
        max_connections=cfg["max_connections"],
        max_retries=cfg["max_retries"],
    )


def all_models(provider: str | None = None) -> list[str]:
    return [f"{p}/{m}" for p, c in config().items() if provider in (None, p) for m in c["models"]]


def prepare(model_id: str) -> None:
    """Put the provider's credentials where Inspect expects them."""
    s = spec(model_id)
    if s.provider == "databricks":
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        os.environ["DATABRICKS_BASE_URL"] = f"{w.config.host}/serving-endpoints"
        os.environ["DATABRICKS_API_KEY"] = w.config.authenticate()["Authorization"].split(" ", 1)[1]
    elif s.provider == "google":
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set (see .env.example)")
        os.environ["GOOGLE_API_KEY"] = key
