"""Spike: the NCM task in DeepEval. DeepEval scores outputs; generating them is our loop."""

import time

import httpx
from common import CASES, MODEL, SYSTEM, databricks_env, digits
from deepeval import evaluate
from deepeval.evaluate.configs import DisplayConfig
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class NcmExact(BaseMetric):
    threshold = 1.0

    def __init__(self):
        self.score = 0.0

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        self.score = float(digits(test_case.actual_output) == test_case.expected_output)
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "NCM exact"


if __name__ == "__main__":
    base, token = databricks_env()
    http = httpx.Client(timeout=60, headers={"Authorization": f"Bearer {token}"})
    t0 = time.perf_counter()
    cases = []
    for text, expected in CASES:  # our own generation loop (no rate limit / cache from the lib)
        r = http.post(
            f"{base}/{MODEL}/invocations",
            json={
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
            },
        )
        out = r.json()["choices"][0]["message"]["content"]
        cases.append(LLMTestCase(input=text, actual_output=out, expected_output=expected))
    res = evaluate(
        test_cases=cases,
        metrics=[NcmExact()],
        display_config=DisplayConfig(print_results=False, show_indicator=False),
    )
    passed = sum(all(m.success for m in tr.metrics_data) for tr in res.test_results)
    print("seconds", round(time.perf_counter() - t0, 1), "passed", passed, "/", len(cases))
