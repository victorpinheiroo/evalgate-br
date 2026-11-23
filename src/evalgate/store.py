"""runs.sqlite: one row per (run, case). The unit the paired statistics work on.

A run is (suite, model, git sha, prompt versions). Rows are written as cases finish, so an
interrupted run resumes by running only the cases it does not have yet.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  suite TEXT NOT NULL,
  model TEXT NOT NULL,
  git_sha TEXT,
  prompts TEXT,           -- JSON {name: version}
  label TEXT,             -- e.g. "main", "pr-12"
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS results (
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  case_id TEXT NOT NULL,
  correct INTEGER,        -- 1/0; NULL when the case errored
  score REAL,
  answer TEXT,
  error TEXT,
  latency_ms INTEGER,
  meta TEXT,              -- JSON, scorer details
  PRIMARY KEY (run_id, case_id)
);
"""


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self._conn()) as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def ensure_run(
        self,
        run_id: str,
        suite: str,
        model: str,
        git_sha: str | None = None,
        prompts: dict | None = None,
        label: str | None = None,
    ) -> None:
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    suite,
                    model,
                    git_sha,
                    json.dumps(prompts or {}),
                    label,
                    datetime.now(UTC).isoformat(timespec="seconds"),
                ),
            )

    def done_cases(self, run_id: str) -> set[str]:
        """Cases already finished (an errored case is retried on resume)."""
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT case_id FROM results WHERE run_id = ? AND error IS NULL", (run_id,)
            )
            return {r["case_id"] for r in rows}

    def record(
        self,
        run_id: str,
        case_id: str,
        correct: bool | None,
        score: float | None,
        answer: str | None,
        error: str | None,
        latency_ms: int | None,
        meta: dict | None = None,
    ) -> None:
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT OR REPLACE INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    case_id,
                    None if correct is None else int(correct),
                    score,
                    answer,
                    error,
                    latency_ms,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )

    def results(self, run_id: str) -> dict[str, sqlite3.Row]:
        with closing(self._conn()) as c:
            return {
                r["case_id"]: r
                for r in c.execute("SELECT * FROM results WHERE run_id = ?", (run_id,))
            }

    def runs(self, suite: str | None = None) -> list[sqlite3.Row]:
        with closing(self._conn()) as c:
            q = (
                "SELECT * FROM runs"
                + (" WHERE suite = ?" if suite else "")
                + " ORDER BY created_at"
            )
            return list(c.execute(q, (suite,) if suite else ()))
