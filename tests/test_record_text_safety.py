"""What a record's or a contract's text may carry (CR-114).

The rule refuses characters that can add a line to rendered output, or make it
read in an order its bytes do not have. Everything else it accepts — the space
separators included, which the printability test it replaced refused.
"""

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import JournalContractError, parse_contract_text
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    generate_ulid,
    validate_record_content,
)
from agentmarshal.journal.validate import validate_journal

_REVIEWER = ("qa", "example", "example-model", "reviewer@test.invalid")
_LINE_BREAKERS = ("\n", "\r", "\u2028", "\u2029")
_BIDIRECTIONAL = (
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2069",
)
_SPACE_SEPARATORS = ("\u00a0", "\u2007", "\u2009", "\u202f")


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Task", "--scope", "src/"]) == 0
    return repo


def _review(finding: str) -> dict[str, object]:
    """Build a review record and validate it the way a writer and a reader do."""

    record = create_review_record(
        "CR-001",
        "0.0.0-test",
        "a" * 40,
        "changes_required",
        *_REVIEWER,
        [finding],
    )
    return validate_record_content(
        f"{generate_ulid()}-review.json", json.dumps(record, ensure_ascii=False)
    )


def _contract(entry: str) -> None:
    parse_contract_text(
        "+++\n"
        'schema = 2\nid = "CR-001"\ntitle = "Task"\n'
        f'scope = ["src/"]\nacceptance = []\ndecisions = ["{entry}"]\n'
        "+++\n\n# CR-001\n",
        "contract.md",
    )


@pytest.mark.parametrize("character", _LINE_BREAKERS)
def test_a_newline_in_a_finding_id_is_refused(character: str) -> None:
    """Scenario: a newline in a finding id is refused."""

    with pytest.raises(JournalRecordError) as refusal:
        _review(f"F-001{character}approved")

    assert "review record finding id must not contain control characters" in str(
        refusal.value
    )


@pytest.mark.parametrize("character", _BIDIRECTIONAL)
def test_a_bidirectional_override_is_refused(character: str) -> None:
    """Scenario: a bidirectional override is refused."""

    with pytest.raises(JournalRecordError) as refusal:
        _review(f"F-001{character}text")

    assert "finding id must not contain control characters" in str(refusal.value)


@pytest.mark.parametrize("character", _SPACE_SEPARATORS)
def test_a_space_separator_is_accepted(character: str) -> None:
    """Scenario: a space separator is accepted."""

    record = _review(f"CR-001-F001 — the count is 71{character}415")

    assert record["findings"] == [f"CR-001-F001 — the count is 71{character}415"]


def test_a_journal_an_earlier_release_accepted_stays_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a journal an earlier release accepted stays valid.

    The record is written by hand in the shape an earlier release wrote it —
    schema 2, its own `tool_version` — because that is the case the adopter's
    journal holds and no current writer can produce it.
    """

    repo = _project(tmp_path, monkeypatch)
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    record_id = generate_ulid()
    (records / f"{record_id}-review.json").write_text(
        json.dumps(
            {
                "schema": 2,
                "record_type": "review",
                "task": "CR-001",
                "created_at": "2026-08-23T10:00:00.000000Z",
                "source": "live",
                "tool_version": "0.1.0",
                "reviewed_commit": "b" * 40,
                "verdict": "changes_required",
                "reviewer": {
                    "role": _REVIEWER[0],
                    "vendor": _REVIEWER[1],
                    "model": _REVIEWER[2],
                    "email": _REVIEWER[3],
                },
                "findings": ["CR-001-F001 - the table says 71\u202f415 rows"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = validate_journal(repo)

    assert report.passed, report.lines
    assert any("OK: CR-001" in line for line in report.lines)


@pytest.mark.parametrize("character", _BIDIRECTIONAL)
def test_the_rule_holds_the_same_on_both_sides(character: str) -> None:
    """Scenario: the rule holds the same on both sides.

    A line breaker never reaches this check on the contract side: TOML refuses
    it in a string first. A bidirectional control is valid TOML, so the check is
    what has to refuse it — and it does, by the record side's set.
    """

    with pytest.raises(JournalContractError) as refusal:
        _contract(f"ADR-0001{character}x")

    assert "must not contain control characters" in str(refusal.value)


@pytest.mark.parametrize("character", _SPACE_SEPARATORS)
def test_a_contract_entry_keeps_its_space_separator(character: str) -> None:
    """The contract side accepts what the record side accepts."""

    header = parse_contract_text(
        "+++\n"
        'schema = 2\nid = "CR-001"\n'
        f'title = "Task"\nscope = ["src/"]\nacceptance = ["counts 71{character}415"]\n'
        "+++\n\n# CR-001\n",
        "contract.md",
    )

    assert header.acceptance == (f"counts 71{character}415",)
