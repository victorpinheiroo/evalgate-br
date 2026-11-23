"""Run a suite against a model through Inspect, record every case in runs.sqlite, resume.

    evalgate run --suite evalgate.suites.ncm:NcmSuite --model databricks/databricks-gpt-oss-20b

The run id is derived from (suite, suite version, model, git sha, prompt versions), so running
the same thing twice resumes the same run instead of starting over: only cases without a
successful row are sent to the model.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import Generate, TaskState, generate, solver, system_message

from evalgate.providers import ROOT, prepare, spec
from evalgate.store import Store
from evalgate.suite import Case, Suite

DB = ROOT / "runs" / "runs.sqlite"
LOGS = ROOT / "logs"


def load_suite(path: str) -> Suite:
    """'package.module:ClassName' -> instance."""
    mod, _, cls = path.partition(":")
    return getattr(importlib.import_module(mod), cls)()


def git_sha(cwd: Path | None = None) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_id_for(suite: Suite, model_id: str, sha: str | None, prompts: dict) -> str:
    key = json.dumps([suite.name, suite.version, model_id, sha, prompts], sort_keys=True)
    return hashlib.sha1(key.encode()).hexdigest()[:12]


@dataclass
class RunResult:
    run_id: str
    total: int
    ran: int
    correct: int
    errors: int


def _scorer_for(suite: Suite, by_id: dict[str, Case]):
    @scorer(metrics=[accuracy(), stderr()])
    def suite_scorer():
        async def score(state: TaskState, target: Target) -> Score:
            case = by_id[str(state.sample_id)]
            output = state.metadata.get("pipeline_output", state.output.completion)
            v = suite.score(case, output)
            return Score(
                value=1.0 if v.correct else 0.0,
                answer=v.answer,
                metadata={"detail": v.detail, "score": v.score},
            )

        return score

    return suite_scorer()


def _pipeline_solver(suite, model_id: str):
    @solver
    def run_pipeline():
        async def solve(state: TaskState, generate: Generate) -> TaskState:
            case = Case(
                id=str(state.sample_id),
                input=state.input_text,
                target=None,
                meta=state.metadata.get("case_meta", {}),
            )
            state.metadata["pipeline_output"] = await suite.solve(case, model_id)
            return state

        return solve

    return run_pipeline()


def run(
    suite: Suite,
    model_id: str,
    label: str | None = None,
    db: Path = DB,
    limit: int | None = None,
    project_dir: Path | None = None,
) -> RunResult:
    s = spec(model_id)
    prepare(model_id)
    prompts = suite.prompts()
    sha = git_sha(project_dir)
    rid = run_id_for(suite, model_id, sha, prompts)
    store = Store(db)
    store.ensure_run(rid, f"{suite.name}@{suite.version}", model_id, sha, prompts, label)

    cases = suite.cases()[:limit] if limit else suite.cases()
    by_id = {c.id: c for c in cases}
    todo = [c for c in cases if c.id not in store.done_cases(rid)]
    if todo:
        samples = [
            Sample(
                id=c.id,
                input=c.input,
                target=json.dumps(c.target, ensure_ascii=False),
                metadata={"case_meta": c.meta},
            )
            for c in todo
        ]
        is_pipeline = hasattr(suite, "solve")
        solvers = (
            [_pipeline_solver(suite, model_id)]
            if is_pipeline
            else [system_message(suite.system), generate(cache=True)]
        )
        task = Task(
            dataset=samples, solver=solvers, scorer=_scorer_for(suite, by_id), name=suite.name
        )
        logs = inspect_eval(
            task,
            model=s.inspect_model,
            log_dir=str(LOGS / suite.name),
            display="none",
            max_connections=s.max_connections,
            max_samples=s.max_connections,
            fail_on_error=False,
            max_retries=s.max_retries,
            temperature=0,
        )
        for sample in logs[0].samples or []:
            sc = (sample.scores or {}).get("suite_scorer")
            err = sample.error.message[:500] if sample.error else None
            latency = int((sample.total_time or 0) * 1000)
            store.record(
                rid,
                str(sample.id),
                None if err or sc is None else sc.value == 1.0,
                None if sc is None else (sc.metadata or {}).get("score"),
                None if sc is None else sc.answer,
                err,
                latency,
                None if sc is None else (sc.metadata or {}).get("detail"),
            )
    rows = store.results(rid)
    return RunResult(
        rid,
        len(cases),
        len(todo),
        sum(1 for r in rows.values() if r["correct"] == 1),
        sum(1 for r in rows.values() if r["error"]),
    )
