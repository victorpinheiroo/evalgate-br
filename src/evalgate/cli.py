"""evalgate command line.

evalgate run --suite evalgate.suites.ncm:NcmSuite --model databricks/databricks-gpt-oss-20b
evalgate run --suite evalgate.suites.ncm:NcmSuite --all-models
evalgate runs
"""

from __future__ import annotations

import argparse
import sys

from evalgate.providers import all_models
from evalgate.runner import DB, load_suite, run
from evalgate.store import Store


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="evalgate")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a suite against one or more models (resumes)")
    r.add_argument("--suite", required=True, help="module:Class")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--model", action="append", help="provider/model (repeatable)")
    g.add_argument("--all-models", action="store_true")
    r.add_argument("--provider", help="with --all-models: only this provider")
    r.add_argument("--label")
    r.add_argument("--limit", type=int)
    sub.add_parser("runs", help="list recorded runs")
    a = p.parse_args(argv)

    if a.cmd == "runs":
        for row in Store(DB).runs():
            print(
                row["run_id"],
                row["suite"],
                row["model"],
                row["git_sha"],
                row["label"] or "",
                row["created_at"],
            )
        return 0

    suite = load_suite(a.suite)
    models = a.model or all_models(a.provider)
    failed = 0
    for m in models:
        try:
            res = run(suite, m, a.label, limit=a.limit)
        except Exception as e:  # one provider down must not stop the others
            print(f"{m}: FAILED {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
            continue
        print(
            f"{m}: {res.correct}/{res.total} correct, {res.errors} errors "
            f"(ran {res.ran}, run {res.run_id})"
        )
    return 1 if failed == len(models) else 0


if __name__ == "__main__":
    sys.exit(main())
