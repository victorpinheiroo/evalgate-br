"""Spike: the NCM task in Inspect (inspect_ai). Inspect runs the model itself."""

import os
import time

from common import CASES, MODEL, SYSTEM, databricks_env, digits
from inspect_ai import Task, eval, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState, generate, system_message


@scorer(metrics=[accuracy(), stderr()])
def ncm_exact():
    async def score(state: TaskState, target: Target) -> Score:
        got = digits(state.output.completion)
        return Score(value=CORRECT if got == target.text else INCORRECT, answer=got)

    return score


@task
def ncm():
    return Task(
        dataset=[Sample(input=t, target=e) for t, e in CASES],
        solver=[system_message(SYSTEM), generate(cache=True)],
        scorer=ncm_exact(),
    )


if __name__ == "__main__":
    base, token = databricks_env()
    os.environ["DATABRICKS_BASE_URL"] = base
    os.environ["DATABRICKS_API_KEY"] = token
    t0 = time.perf_counter()
    logs = eval(
        ncm(),
        model=f"openai-api/databricks/{MODEL}",
        max_connections=2,
        log_dir="logs-inspect",
        display="none",
    )
    log = logs[0]
    print("status", log.status, "seconds", round(time.perf_counter() - t0, 1))
    for s in log.results.scores:
        print(s.name, {k: round(v.value, 3) for k, v in s.metrics.items()})
    print("samples", [(s.id, s.scores["ncm_exact"].answer) for s in log.samples])
