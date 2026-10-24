"""What a record's or a contract's text may carry (CR-114).

The rule refuses characters that can add a line to rendered output, or make it
read in an order its bytes do not have. Everything else it accepts — the space
separators included, which the printability test it replaced refused.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import JournalContractError, parse_contract_text
from agentmarshal.journal.records import (
    JournalRecordError,
    create_opened_record,
    create_review_record,
    create_session_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.validate import validate_journal

_REVIEWER = ("qa", "example", "example-model", "reviewer@test.invalid")
_LINE_BREAKERS = ("\n", "\r", "\u2028", "\u2029")
_BIDIRECTIONAL = (
    "\u061c",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
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
    """Parse a header whose `decisions` entry is written as TOML source.

    The entry arrives escaped, which is how a contract file carries a character
    a raw form could not: `tomllib` unescapes it and the rule sees the character
    itself.
    """

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

    record = _review(f"CR-001-F001 - the count is 71{character}415")

    assert record["findings"] == [f"CR-001-F001 - the count is 71{character}415"]


def test_an_unpaired_surrogate_is_refused() -> None:
    """Scenario: an unpaired surrogate is refused."""

    with pytest.raises(JournalRecordError) as refusal:
        _review("F-001\ud800")

    assert "finding id must not contain control characters" in str(refusal.value)


def test_a_private_use_codepoint_is_accepted() -> None:
    """One unknown glyph can neither break a line nor reorder text."""

    record = _review("F-001\ue000")

    assert record["findings"] == ["F-001\ue000"]


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


_TOML_ESCAPES = ("\\n", "\\r", "\\u2028", "\\u2029")


@pytest.mark.parametrize("character", (*_BIDIRECTIONAL, *_TOML_ESCAPES))
def test_the_rule_holds_the_same_on_both_sides(character: str) -> None:
    """Scenario: the rule holds the same on both sides.

    Every class the record side refuses reaches this check too. A line breaker
    reaches it in the escaped form a contract file uses: a raw one would not,
    because the header is split with `str.splitlines()` (`contracts.py:125`),
    which treats U+2028 and U+2029 as line breaks, and TOML refuses a raw
    newline inside a single-line string. Escaped, `tomllib` unescapes it and the
    rule refuses the character itself; the bidirectional characters are valid
    TOML as they stand. An unpaired surrogate is pinned on the record side only:
    TOML refuses its escape as invalid, so no contract file can carry one.
    """

    with pytest.raises(JournalContractError) as refusal:
        _contract(f"ADR-0001{character}x")

    assert "must not contain control characters" in str(refusal.value)


@pytest.mark.parametrize("character", _SPACE_SEPARATORS)
def test_a_contract_entry_keeps_its_space_separator(character: str) -> None:
    """The contract side accepts what the record side accepts.

    The separator goes in an `extensions` entry, which this rule guards; an
    `acceptance` entry does not reach it, and asserting there would pass whatever
    the rule did.
    """

    header = parse_contract_text(
        "+++\n"
        'schema = 2\nid = "CR-001"\n'
        f'title = "Task"\nscope = ["src/"]\nacceptance = []\n'
        f'extensions = ["tool 71{character}415"]\n'
        "+++\n\n# CR-001\n",
        "contract.md",
    )

    assert header.extensions == (f"tool 71{character}415",)


def _hand_written_review(
    repo: Path,
    findings: list[str],
    artifacts: list[dict[str, str]] | None = None,
) -> None:
    """Write a review record the way an earlier release wrote one: schema 2."""

    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    record: dict[str, object] = {
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
        "findings": findings,
    }
    if artifacts is not None:
        record["artifacts"] = artifacts
    (records / f"{generate_ulid()}-review.json").write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )


def test_the_rule_guards_every_place_that_renders_record_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the rule guards every place that renders record text.

    `validate` checks a pinned artifact's reference itself, on the read side.
    Both halves are pinned here: a reference carrying a space separator
    validates, and one carrying a refused character is reported. Without the
    second the check could be dropped unnoticed; without the first it could be
    left stricter than the writer, which is the drift this task removes.
    """

    repo = _project(tmp_path, monkeypatch)
    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    artifacts.mkdir(parents=True)
    accepted_name = "01M0QN0YTPC71EQJM1HRVF9A2K-review\u202fnote.md"
    content = b"reviewer prose\n"
    (artifacts / accepted_name).write_bytes(content)
    _hand_written_review(
        repo,
        ["F-001"],
        [
            {
                "ref": f".agentmarshal/journal/tasks/CR-001/artifacts/{accepted_name}",
                "hash": hashlib.sha256(content).hexdigest(),
            }
        ],
    )

    accepted = validate_journal(repo)

    assert accepted.passed, accepted.lines

    _hand_written_review(
        repo,
        ["F-002"],
        [
            {
                "ref": ".agentmarshal/journal/tasks/CR-001/artifacts/x\u202ey.md",
                "hash": "0" * 64,
            }
        ],
    )

    refused = validate_journal(repo)

    assert not refused.passed
    assert any("contains control characters" in line for line in refused.lines)


def test_a_timestamp_carrying_a_refused_character_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: a timestamp carrying a refused character is refused.

    `datetime.fromisoformat` accepts any single character as the date-time
    separator, so `created_at` and the session's `started_at`, `ended_at`
    and `resets_at` could each carry a refused character through the parse —
    a newline for `created_at`, U+200E standing in for `started_at`'s
    separator, U+2028 for `ended_at`'s and a surrogate for `resets_at`.
    Each refusal names the field and leaves nothing behind.
    """

    journal_root = tmp_path / "journal"

    opened = create_opened_record("CR-001", "test")
    opened["created_at"] = "2026-10-01T10:00\n:00Z"
    with pytest.raises(JournalRecordError, match=r"'created_at'.*control characters"):
        write_record(journal_root, "CR-001", opened)

    for field, value in (
        ("started_at", "2026-10-01\u200e10:00:00Z"),
        ("ended_at", "2026-10-01T11:00\u202800Z"),
        ("resets_at", "2026-10-02T00:00:00\ud800Z"),
    ):
        record = create_session_record(
            "CR-001",
            "test",
            "implementer",
            "agent",
            "implementation",
            "provider-limit",
            1,
            2,
            3,
            started_at="2026-10-01T10:00:00Z",
            ended_at="2026-10-01T11:00:00Z",
            resets_at="2026-10-02T00:00:00Z",
        )
        record[field] = value
        with pytest.raises(JournalRecordError, match=rf"'{field}'.*control characters"):
            write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_an_artifact_ref_carrying_a_refused_character_is_refused_at_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an artifact ref carrying a refused character is refused at write.

    The gate's path — `validate_record_content` — refuses the reference
    before a candidate record could be added, while a record an earlier
    release wrote still reads and is reported by `validate`, never refused
    on read (ADR-0015).
    """

    repo = _project(tmp_path, monkeypatch)
    ref = ".agentmarshal/journal/tasks/CR-001/artifacts/x\nPASS: forged.md"
    record = create_review_record(
        "CR-001",
        "0.0.0-test",
        "a" * 40,
        "approved",
        *_REVIEWER,
        [],
        artifacts=[{"ref": ref, "hash": "0" * 64}],
    )

    with pytest.raises(
        JournalRecordError,
        match="artifact field 'ref' must not contain control characters",
    ):
        validate_record_content(
            f"{generate_ulid()}-review.json", json.dumps(record, ensure_ascii=False)
        )

    _hand_written_review(repo, ["F-001"], [{"ref": ref, "hash": "0" * 64}])

    stored = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    artifacts = stored["artifacts"]
    assert isinstance(artifacts, list)
    artifact = artifacts[0]
    assert isinstance(artifact, dict)
    assert artifact["ref"] == ref
    report = validate_journal(repo)
    assert not report.passed
    assert any("control characters" in line for line in report.lines)


def test_a_failure_while_encoding_leaves_no_file(tmp_path: Path) -> None:
    """Scenario: a failure while encoding leaves no file.

    A session's `outcome` is free text the forgeable-text rule does not
    reach, so an unpaired surrogate inside it passes validation and fails
    where the record encodes — ahead of the file's exclusive creation now,
    so nothing is left behind.
    """

    journal_root = tmp_path / "journal"
    record = create_session_record(
        "CR-001",
        "test",
        "implementer",
        "agent",
        "implementation",
        "stalled\ud800",
        1,
        2,
        3,
    )

    with pytest.raises(UnicodeEncodeError):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()
