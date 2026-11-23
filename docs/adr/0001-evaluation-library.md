# ADR 0001: build on Inspect, not DeepEval

Date: 2026-11-23. Status: accepted.

## Context

The scope document asks for a half-day spike between DeepEval and Inspect before writing the
runner. Evalgate needs: several providers with free-tier rate limits (Databricks Free Edition,
Gemini free tier), caching, retries, resuming an interrupted run, per-sample records for paired
statistics, deterministic scorers first and an LLM judge only where needed, and a CLI that CI can
call.

## Spike

`spike/` runs the same 5-case Portuguese task (extract the NCM code from an invoice line) with a
deterministic exact-match scorer and `databricks-meta-llama-3-3-70b-instruct`, in both libraries
(inspect-ai 0.3.292, deepeval 4.3.4).

| | Inspect | DeepEval |
| --- | --- | --- |
| Result | 5/5 | 5/5 |
| Who calls the model | the library: OpenAI-compatible (Databricks), Google, Ollama providers built in | us: DeepEval scores outputs we generate |
| Concurrency / retries on 429 | built in (`max_connections`, backoff) | ours to write |
| Cache | built in (`generate(cache=True)`) | ours to write |
| Resume an interrupted run | `inspect eval-retry`, `eval-set` | none |
| Per-sample records | full log per sample (input, output, score, timing), viewer | aggregated results |
| Generic scorers / judge | match, includes, model-graded QA | strong LLM-judge metrics (G-Eval, faithfulness) |
| Footprint | 209 MB venv | 59 MB venv |
| Telemetry / cloud | none by default | telemetry on by default, pushes its hosted platform |

## Decision

Use **Inspect** as the harness: tasks, samples, scorers, model providers, concurrency, cache,
retries, logs. Evalgate's own code is what Inspect does not have:

- the adapter contract that A and C implement (their pipelines run as Inspect solvers);
- per-provider free-tier settings (concurrency, retry budget) in one config file;
- `runs.sqlite`: one row per (run, case, model) with the git sha and prompt versions, the input to
  the paired statistics;
- the paired diff (McNemar, confidence intervals, case-by-case flips), the PR comment and the gate;
- the leaderboard published to GitHub Pages.

## Consequences

- Inspect's model abstraction is used directly for single-call tasks; for A and C, whose answers
  come from a whole pipeline (retrieval, tools, verification), the adapter is a solver that calls
  the project's own pipeline with the model under test. A and C keep their `LLMClient`; Gemini is
  added there as a provider.
- DeepEval's judge metrics are not needed: the judge in milestone 4 is calibrated against 30
  hand-labelled cases and can be an Inspect model-graded scorer.
- Heavier install (209 MB); acceptable for a dev/CI tool, not shipped in A or C's runtime images.
