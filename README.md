# evalgate-br

A free-model leaderboard for real Portuguese-language data tasks, and the CI gate that blocks a
pull request when a prompt change makes things measurably worse.

> Status: milestone 1. Evaluation library chosen by spike (Inspect, see
> [docs/adr/0001-evaluation-library.md](docs/adr/0001-evaluation-library.md)); runner with
> per-provider limits, cache, and resume through `runs.sqlite`; Databricks Free Edition models
> wired, Gemini free tier wired and waiting for a key.

## Quickstart

```bash
uv sync
uv run evalgate run --suite evalgate.suites.ncm:NcmSuite --model databricks/databricks-gpt-oss-20b
uv run evalgate runs
uv run pytest            # offline: Inspect's mockllm model
```

Databricks uses the CLI profile (`databricks auth login`). Gemini reads `GEMINI_API_KEY` from the
environment or a git-ignored `.env` (see `.env.example`).
