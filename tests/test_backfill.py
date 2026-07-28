"""Tests for the economics backfill mapping (ADR-0005 Decision 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentmarshal.journal.backfill import (
    BackfillError,
    backfill_task_sessions,
    session_record_from_stat,
    source_hash,
)

_IMPORTED_AT = "2026-07-28T08:00:00Z"


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


def _map(stat: dict[str, object], **overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "source_ref": "RUN-20260719T075212Z-lead-3514f554",
        "source_digest": "a" * 64,
        "imported_at": _IMPORTED_AT,
    }
    kwargs.update(overrides)
    return session_record_from_stat(stat, **kwargs)  # type: ignore[arg-type]


def _write(stats_dir: Path, name: str, stat: dict[str, object]) -> None:
    stats_dir.mkdir(parents=True, exist_ok=True)
    (stats_dir / name).write_text(json.dumps(stat), encoding="utf-8")


# --- mapping --------------------------------------------------------------


def test_lead_stat_maps_to_imported_session() -> None:
    record = _map(_lead_stat())
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


def test_provenance_pins_source_hash_and_import_time() -> None:
    record = _map(_lead_stat(), source_digest="b" * 64)
    artifacts = record["artifacts"]
    assert isinstance(artifacts, list) and len(artifacts) == 1
    entry = artifacts[0]
    assert entry["hash"] == "b" * 64
    assert "imported-at=2026-07-28T08:00:00Z" in entry["ref"]
    assert "RUN-20260719T075212Z-lead-3514f554" in entry["ref"]


def test_source_hash_changes_with_source_bytes() -> None:
    assert source_hash(b"one") != source_hash(b"two")
    assert len(source_hash(b"one")) == 64


def test_qa_stat_maps_review_activity() -> None:
    record = _map(_qa_stat())
    assert record["activity"] == "review"
    assert record["actor"] == "codex/gpt-5.6-sol"
    tokens = record["tokens"]
    assert isinstance(tokens, dict)
    assert tokens["cache"] == 320000  # cache-creation absent defaults to zero


def test_unknown_activity_normalizes_to_other() -> None:
    record = _map(_lead_stat(activity="planning"))
    assert record["activity"] == "other"


# --- fail-closed ----------------------------------------------------------


def test_missing_field_fails_closed() -> None:
    stat = _lead_stat()
    del stat["output_tokens"]
    with pytest.raises(BackfillError, match="output_tokens"):
        _map(stat)


def test_negative_tokens_fail_closed() -> None:
    with pytest.raises(BackfillError):
        _map(_lead_stat(input_tokens=-1))


def test_bad_task_id_fails_closed() -> None:
    with pytest.raises(BackfillError):
        _map(_lead_stat(task="not-a-task"))


def test_missing_import_metadata_fails_closed() -> None:
    with pytest.raises(BackfillError, match="imported_at"):
        _map(_lead_stat(), imported_at="")
    with pytest.raises(BackfillError, match="source_ref"):
        _map(_lead_stat(), source_ref="")


@pytest.mark.parametrize(
    "imported_at",
    [
        "not-a-timestamp",
        "2026-07-28T08:00:00",  # timezone-naive
        "2026-07-28T08:00:00+02:00",  # non-UTC
    ],
)
def test_malformed_import_time_fails_closed(imported_at: str) -> None:
    with pytest.raises(BackfillError, match="imported_at"):
        _map(_lead_stat(), imported_at=imported_at)


def test_utc_import_time_is_accepted() -> None:
    # Both the Z form and an explicit +00:00 offset are valid UTC.
    assert _map(_lead_stat(), imported_at="2026-07-28T08:00:00Z")
    assert _map(_lead_stat(), imported_at="2026-07-28T08:00:00+00:00")


def test_leak_in_stat_field_fails_closed() -> None:
    # A secret smuggled into a free-text field is refused, not restored.
    with pytest.raises(BackfillError, match="leak"):
        _map(_lead_stat(outcome="token ghp_" + "a" * 36))


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

    records = backfill_task_sessions(stats, "CR-011", _IMPORTED_AT)

    assert [record["role"] for record in records] == ["qa", "lead"]  # by timestamp
    assert all(record["task"] == "CR-011" for record in records)
    assert all(record["source"] == "imported-from-host" for record in records)
    # The hash is over the real file bytes (64 hex).
    for record in records:
        artifacts = record["artifacts"]
        assert isinstance(artifacts, list)
        assert len(artifacts[0]["hash"]) == 64


def test_selector_orders_by_instant_not_text(tmp_path: Path) -> None:
    # Fractional seconds make lexical order disagree with chronological
    # order: "...00.500Z" (later) sorts before "...00Z" (earlier) as text.
    # The selector must order by the parsed instant.
    stats = tmp_path / "stats"
    _write(
        stats,
        "RUN-20260719T090000Z-lead-later0000.json",
        _lead_stat(recorded_at="2026-07-19T09:00:00.500Z", outcome="later"),
    )
    _write(
        stats,
        "RUN-20260719T090000Z-lead-earlier00.json",
        _lead_stat(recorded_at="2026-07-19T09:00:00Z", outcome="earlier"),
    )

    records = backfill_task_sessions(stats, "CR-011", _IMPORTED_AT)

    assert [record["outcome"] for record in records] == ["earlier", "later"]


def test_selector_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(BackfillError):
        backfill_task_sessions(tmp_path / "absent", "CR-011", _IMPORTED_AT)


def test_symlinked_stat_file_is_refused(tmp_path: Path) -> None:
    # A RUN-*.json symlink must not let the importer hash bytes from outside
    # the retained stats directory and attribute them to an in-directory ref.
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(_lead_stat()), encoding="utf-8")
    stats = tmp_path / "stats"
    stats.mkdir()
    link = stats / "RUN-20260719T090000Z-lead-evil0000.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unsupported on this platform")

    with pytest.raises(BackfillError, match=r"symlink|regular file"):
        backfill_task_sessions(stats, "CR-011", _IMPORTED_AT)
