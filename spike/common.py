"""Shared spike data: the same 5-case task for both libraries (extract the NCM code)."""

import os
import re

CASES = [
    ("Nota: 10 camisetas de algodão, NCM 6109.10.00, valor R$ 300.", "61091000"),
    ("Venda de arroz polido (NCM 1006.30.21) para supermercado.", "10063021"),
    ("Item: notebook, classificação fiscal 8471.30.12, garantia 1 ano.", "84713012"),
    ("Celular smartphone NCM 85171300 quantidade 2", "85171300"),
    ("Cerveja de malte, código NCM 2203.00.00, caixa com 12 latas", "22030000"),
]
SYSTEM = "Extraia o código NCM do texto. Responda apenas com os 8 dígitos, sem pontos."
MODEL = "databricks-meta-llama-3-3-70b-instruct"


def digits(s: str) -> str:
    m = re.search(r"\d{4}\.?\d{2}\.?\d{2}", s or "")
    return re.sub(r"\D", "", m.group(0)) if m else ""


def databricks_env() -> tuple[str, str]:
    """(base_url, token) for Databricks' OpenAI-compatible endpoint, from the CLI profile."""
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    token = w.config.authenticate()["Authorization"].split(" ", 1)[1]
    return f"{w.config.host}/serving-endpoints", token


if __name__ == "__main__":
    print(os.getcwd())
