"""Runner, store and resume, offline with Inspect's mockllm model."""

from evalgate.runner import run, run_id_for
from evalgate.store import Store
from evalgate.suites.ncm import NcmSuite


def test_mock_run_records_every_case_and_resumes(tmp_path):
    db = tmp_path / "runs.sqlite"
    s = NcmSuite()
    first = run(s, "mockllm/model", db=db, limit=5)
    assert (first.total, first.ran, first.errors) == (5, 5, 0)
    assert first.correct == 0  # mockllm answers a fixed sentence, never an NCM
    rows = Store(db).results(first.run_id)
    assert set(rows) == {"n01", "n02", "n03", "n04", "n05"}
    assert all(r["correct"] == 0 and r["error"] is None for r in rows.values())

    again = run(s, "mockllm/model", db=db, limit=5)
    assert again.run_id == first.run_id and again.ran == 0  # resumed: nothing re-sent


def test_run_identity_changes_with_what_was_evaluated():
    s = NcmSuite()
    base = run_id_for(s, "databricks/x", "abc123", {"p": "1"})
    assert base == run_id_for(s, "databricks/x", "abc123", {"p": "1"})
    assert base != run_id_for(s, "databricks/y", "abc123", {"p": "1"})
    assert base != run_id_for(s, "databricks/x", "def456", {"p": "1"})
    assert base != run_id_for(s, "databricks/x", "abc123", {"p": "2"})


def test_scorer_normalizes_formats():
    s = NcmSuite()
    case = s.cases()[0]  # target 61091000
    assert s.score(case, "6109.10.00").correct
    assert s.score(case, "O NCM é 6109 10 00.").correct
    assert not s.score(case, "61091001").correct
    assert not s.score(case, "").correct
