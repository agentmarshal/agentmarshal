"""Tests for the economics backfill mapping (ADR-0005 Decision 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentmarshal.journal.backfill import (
    BackfillError,
    backfill_task_sessions,
    session_record_from_stat,
)


def _lead_stat(**overrides: object) -> dict[str, object]:
    stat: dict[str, object] = {
        "schema": 1,
        "id": "RUN-20260719T075212Z-lead-3514f554",
        "recorded_at": "2026-07-19T09:22:04.349Z",
        "task": "CR-011",
        "role": "lead",
        "vendor": "claude",
        "model": "claude-fable-5",
        "activity": "implementation",
        "outcome": "completed",
        "input_tokens": 413,
        "output_tokens": 192141,
        "cache_creation_input_tokens": 239348,
        "cache_read_input_tokens": 152669474,
    }
    stat.update(overrides)
    return stat


def _qa_stat(**overrides: object) -> dict[str, object]:
    stat: dict[str, object] = {
        "schema": 1,
        "id": "RUN-20260719T031008Z-qa-f2feae23",
        "recorded_at": "2026-07-19T03:10:08Z",
        "task": "CR-011",
        "role": "qa",
        "vendor": "codex",
        "model": "gpt-5.6-sol",
        "activity": "review",
        "outcome": "approved",
        "input_tokens": 700000,
        "output_tokens": 3000,
        "cache_read_input_tokens": 320000,
    }
    stat.update(overrides)
    return stat


def _write(stats_dir: Path, name: str, stat: dict[str, object]) -> None:
    stats_dir.mkdir(parents=True, exist_ok=True)
    (stats_dir / name).write_text(json.dumps(stat), encoding="utf-8")


# --- mapping --------------------------------------------------------------


def test_lead_stat_maps_to_imported_session() -> None:
    record = session_record_from_stat(_lead_stat())
    assert record["schema"] == 2
    assert record["record_type"] == "session"
    assert record["source"] == "imported-from-host"
    assert record["created_at"] == "2026-07-19T09:22:04.349Z"  # original, not now
    assert record["task"] == "CR-011"
    assert record["role"] == "lead"
    assert record["actor"] == "claude/claude-fable-5"
    assert record["activity"] == "implementation"
    assert record["outcome"] == "completed"
    # cache sums read + creation so no token is dropped.
    assert record["tokens"] == {
        "input": 413,
        "output": 192141,
        "cache": 152669474 + 239348,
    }


def test_qa_stat_maps_review_activity() -> None:
    record = session_record_from_stat(_qa_stat())
    assert record["activity"] == "review"
    assert record["actor"] == "codex/gpt-5.6-sol"
    # cache-creation absent defaults to zero.
    tokens = record["tokens"]
    assert isinstance(tokens, dict)
    assert tokens["cache"] == 320000


def test_unknown_activity_normalizes_to_other() -> None:
    record = session_record_from_stat(_lead_stat(activity="planning"))
    assert record["activity"] == "other"


# --- fail-closed ----------------------------------------------------------


def test_missing_field_fails_closed() -> None:
    stat = _lead_stat()
    del stat["output_tokens"]
    with pytest.raises(BackfillError, match="output_tokens"):
        session_record_from_stat(stat)


def test_negative_tokens_fail_closed() -> None:
    with pytest.raises(BackfillError):
        session_record_from_stat(_lead_stat(input_tokens=-1))


def test_bad_task_id_fails_closed() -> None:
    with pytest.raises(BackfillError):
        session_record_from_stat(_lead_stat(task="not-a-task"))


# --- directory selection --------------------------------------------------


def test_per_task_selector_filters_and_orders(tmp_path: Path) -> None:
    stats = tmp_path / "stats"
    _write(
        stats,
        "RUN-20260719T075212Z-lead-3514f554.json",
        _lead_stat(recorded_at="2026-07-19T09:22:04.349Z"),
    )
    _write(
        stats,
        "RUN-20260719T031008Z-qa-f2feae23.json",
        _qa_stat(recorded_at="2026-07-19T03:10:08Z"),
    )
    _write(
        stats,
        "RUN-20260720T000000Z-lead-othertask.json",
        _lead_stat(task="CR-012", recorded_at="2026-07-20T00:00:00Z"),
    )
    # An unrelated file must be ignored.
    (stats / "README.md").write_text("not a stat\n", encoding="utf-8")

    records = backfill_task_sessions(stats, "CR-011")

    assert [record["role"] for record in records] == ["qa", "lead"]  # by timestamp
    assert all(record["task"] == "CR-011" for record in records)
    assert all(record["source"] == "imported-from-host" for record in records)


def test_selector_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(BackfillError):
        backfill_task_sessions(tmp_path / "absent", "CR-011")
