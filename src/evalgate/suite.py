"""The contract a project implements to be evaluated (adapters live in A and C, not here).

Two shapes:
- PromptSuite: one model call per case (system prompt + input); Inspect calls the model, with
  its provider, cache, concurrency and retries.
- PipelineSuite: the project's own pipeline answers each case with the model under test
  (retrieval, tools, verification...). Evalgate still owns cases, scoring, records and stats.
Scoring is deterministic by default; `Verdict.detail` carries what the scorer saw.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Case:
    id: str
    input: str
    target: Any
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Verdict:
    correct: bool
    score: float
    answer: str
    detail: dict = field(default_factory=dict)


class Suite(Protocol):
    name: str
    version: str  # bump when cases or scoring change; part of every run's identity

    def cases(self) -> list[Case]: ...

    def score(self, case: Case, output: Any) -> Verdict: ...


class PromptSuite(Suite, Protocol):
    system: str

    def prompts(self) -> dict[str, str]:  # {prompt name: version}, recorded with the run
        ...


class PipelineSuite(Suite, Protocol):
    async def solve(self, case: Case, model_id: str) -> Any:
        """Run the project's pipeline for `case` with `model_id`; return what `score` reads."""
        ...

    def prompts(self) -> dict[str, str]: ...
