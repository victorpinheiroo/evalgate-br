Half-day spike for ADR 0001 (docs/adr/0001-evaluation-library.md). Not part of the package.

    uv venv spike/.venv-inspect && uv pip install -p spike/.venv-inspect inspect-ai openai databricks-sdk
    uv venv spike/.venv-deepeval && uv pip install -p spike/.venv-deepeval deepeval httpx databricks-sdk
    spike/.venv-inspect/Scripts/python spike/with_inspect.py
    DEEPEVAL_TELEMETRY_OPT_OUT=YES spike/.venv-deepeval/Scripts/python spike/with_deepeval.py
