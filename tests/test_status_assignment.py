"""Pin the assignment section of the per-task ``status`` view (CR-191).

ADR-0018 decision 3 pairs the contract's declared assignment with what
ran: a schema-3 header's `implementers` and `reviewers` — the fallback
order — and its `independence` rules print beside the implementer
sessions and the reviews, each ran actor outside its role's declared
list marked as not declared for the role, each absent value shown as
absent and never derived. A contract declaring none of the three fields
leaves the detail view byte for byte unchanged.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.records import (
    create_opened_record,
    create_review_record,
    create_session_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatus
from agentmarshal.journal.status_view import print_task_detail

_COMMIT = "a" * 40

_CONTRACT_SCHEMA_1 = """\
+++
schema = 1
id = "CR-001"
title = "Task"
scope = ["src/"]
acceptance = []
+++

# CR-001: Task
"""


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _contract3(
    *,
    implementers: list[str] | None = None,
    reviewers: list[str] | None = None,
    independence: list[str] | None = None,
) -> str:
    """A schema-3 contract carrying exactly the fields given."""

    lines = [
        "+++",
        "schema = 3",
        'id = "CR-001"',
        'title = "Task"',
        'scope = ["src/"]',
        "acceptance = []",
    ]
    for field, value in (
        ("implementers", implementers),
        ("reviewers", reviewers),
        ("independence", independence),
    ):
        if value is not None:
            lines.append(f"{field} = {json.dumps(value)}")
    lines.extend(["+++", "", "# CR-001: Task", ""])
    return "\n".join(lines)


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contract: str) -> Path:
    """A git root with project.json and the task's contract — the floor."""

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    agentmarshal = repo / ".agentmarshal"
    agentmarshal.mkdir()
    (agentmarshal / "project.json").write_text(
        json.dumps({"schema": 1}) + "\n", encoding="utf-8"
    )
    task_directory = agentmarshal / "journal" / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(contract, encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _write(
    repo: Path, record: dict[str, object], record_id: str, created_at: str
) -> None:
    record["created_at"] = created_at
    write_record(_journal(repo), "CR-001", record, record_id=record_id)


def _open(repo: Path) -> None:
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )


def _session(
    repo: Path,
    record_id: str,
    created_at: str,
    *,
    role: str = "implementer",
    actor: str = "devin",
    activity: str = "implementation",
    provider: str | None = "devin-vendor",
    model: str | None = "devin-model",
    fallback_reason: str | None = None,
) -> None:
    """Write a session record; an implementer session by default."""

    _write(
        repo,
        create_session_record(
            "CR-001",
            "1.0",
            role,
            actor,
            activity,
            "implemented",
            1,
            2,
            0,
            usage_provider=provider,
            usage_method="measured" if provider is not None else None,
            model=model,
            fallback_reason=fallback_reason,
        ),
        record_id,
        created_at,
    )


def _review(
    repo: Path,
    record_id: str,
    created_at: str,
    *,
    actor: str | None = "qa-lead",
    vendor: str = "qa-vendor",
    model: str = "qa-model",
) -> None:
    """Write a review record; reviewer fields default to declared values."""

    _write(
        repo,
        create_review_record(
            "CR-001",
            "1.0",
            _COMMIT,
            "approved",
            "qa",
            vendor,
            model,
            "qa@example.invalid",
            [],
            reviewer_actor=actor,
        ),
        record_id,
        created_at,
    )


# -- the section itself ------------------------------------------------------


def test_a_contract_declaring_all_three_prints_the_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a contract declaring all three prints the section — after
    the scope and before the record lines, the declared lists in their
    declared order."""

    repo = _repo(
        tmp_path,
        monkeypatch,
        _contract3(
            implementers=["devin", "codex"],
            reviewers=["qa-lead"],
            independence=["reviewer-not-writer", "distinct-vendor"],
        ),
    )
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        fallback_reason="weekly quota exhausted",
    )
    _review(repo, "00000000000000000000000003", "2026-01-03T00:00:00Z")

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- src/\n"
        "Assignment:\n"
        "- implementers: devin, codex\n"
        "- reviewers: qa-lead\n"
        "- independence: reviewer-not-writer, distinct-vendor\n"
        "- implementer session 00000000000000000000000002: actor=devin "
        "vendor=devin-vendor model=devin-model "
        "fallback_reason=weekly quota exhausted\n"
        "- review 00000000000000000000000003: actor=qa-lead "
        "vendor=qa-vendor model=qa-model\n"
        "Records:\n"
    ) in out


def test_an_undeclared_field_is_shown_as_not_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an undeclared field is shown as not declared — the two
    fields the header does not carry say so rather than being omitted."""

    repo = _repo(
        tmp_path,
        monkeypatch,
        _contract3(implementers=["devin"]),
    )
    _open(repo)

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "Assignment:\n"
        "- implementers: devin\n"
        "- reviewers: (not declared)\n"
        "- independence: (not declared)\n"
    ) in out


def test_a_contract_declaring_none_prints_todays_view_byte_for_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a contract declaring none prints today's view byte for
    byte — a schema-3 header that could carry the fields and does not is
    indistinguishable from a header that cannot carry them."""

    repo = _repo(tmp_path, monkeypatch, _CONTRACT_SCHEMA_1)
    _open(repo)
    _session(repo, "00000000000000000000000002", "2026-01-02T00:00:00Z")
    _review(repo, "00000000000000000000000003", "2026-01-03T00:00:00Z")

    assert main(["status", "CR-001"]) == 0
    schema_1_out = capsys.readouterr().out
    assert "Assignment" not in schema_1_out

    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    contract.write_text(_contract3(), encoding="utf-8")
    assert main(["status", "CR-001"]) == 0
    schema_3_out = capsys.readouterr().out
    assert "Assignment" not in schema_3_out
    assert schema_3_out == schema_1_out


# -- what ran: implementer sessions ------------------------------------------


def test_an_implementer_sessions_line_shows_what_ran(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an implementer session's line shows what ran — actor,
    the vendor from usage.provider, model and fallback_reason."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin", "codex"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="codex",
        provider="openai",
        model="gpt-5",
        fallback_reason="provider-limit",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- implementer session 00000000000000000000000002: actor=codex "
        "vendor=openai model=gpt-5 fallback_reason=provider-limit\n"
    ) in out


def test_the_vendor_is_read_from_usage_provider_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the vendor is read from usage.provider alone — an actor
    string shaped like `vendor/model` is never split for a guess."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["openai/gpt-5"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="openai/gpt-5",
        provider=None,
        model="gpt-5",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- implementer session 00000000000000000000000002: "
        "actor=openai/gpt-5 vendor=(absent) model=gpt-5\n"
    ) in out


def test_an_absent_session_value_is_shown_as_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an absent value is shown as absent — a session carrying
    no `model` shows it as absent rather than derived."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        model=None,
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert "model=(absent)" in out


def test_an_absent_actor_is_shown_as_absent_and_unmarked(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an absent value is shown as absent — a session carrying
    no actor shows the absent value and no mark, even with a declared
    list: there is no name to check against it."""

    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=3,
            id="CR-001",
            title="Task",
            scope=(),
            acceptance=(),
            implementers=("devin",),
        ),
        records=(
            {
                "id": "r-session",
                "record_type": "session",
                "created_at": "t0",
                "role": "implementer",
                "usage": {"provider": "devin-vendor", "method": "measured"},
                "model": "devin-model",
            },
        ),
        state="open",
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        "- implementer session r-session: actor=(absent) "
        "vendor=devin-vendor model=devin-model\n"
    ) in out


def test_fallback_reason_prints_only_when_the_record_carries_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: fallback_reason prints only when the record carries it —
    a run with none recorded claims none."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin", "codex"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        fallback_reason="provider-limit",
    )
    _session(
        repo,
        "00000000000000000000000003",
        "2026-01-03T00:00:00Z",
        actor="codex",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    first = next(
        line
        for line in out.splitlines()
        if line.startswith("- implementer session 00000000000000000000000002")
    )
    second = next(
        line
        for line in out.splitlines()
        if line.startswith("- implementer session 00000000000000000000000003")
    )
    assert "fallback_reason=provider-limit" in first
    assert "fallback_reason" not in second


def test_an_actor_not_in_the_declared_list_is_marked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an actor not in the declared list is marked — shown, not
    refused (ADR-0018 decision 3)."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin", "codex"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="claude",
        provider="anthropic",
        model="opus-5",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- implementer session 00000000000000000000000002: actor=claude "
        "vendor=anthropic model=opus-5 (not declared for the role)\n"
    ) in out


def test_an_actor_in_the_declared_list_carries_no_mark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an actor in the declared list carries no mark — casing
    cannot move one out of it, the same normalisation the gate applies."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["Devin", "codex"]))
    _open(repo)
    _session(repo, "00000000000000000000000002", "2026-01-02T00:00:00Z")

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    line = next(
        line for line in out.splitlines() if line.startswith("- implementer session")
    )
    assert "actor=devin" in line
    assert "not declared for the role" not in line


def test_the_mark_appears_only_when_implementers_is_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the mark appears only when implementers is declared —
    with no declared list there is nothing to be outside of."""

    repo = _repo(tmp_path, monkeypatch, _contract3(reviewers=["qa-lead"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="claude",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert "- implementers: (not declared)\n" in out
    assert (
        "- implementer session 00000000000000000000000002: actor=claude "
        "vendor=devin-vendor model=devin-model\n"
    ) in out
    assert "not declared for the role" not in out


def test_a_session_of_another_role_prints_no_implementer_session_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a session of another role prints no implementer-session
    line — a coordination session is not implementer work."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin"]))
    _open(repo)
    _session(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        role="coordinator",
        actor="ops",
        activity="coordination",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert "Assignment:\n" in out
    assert "implementer session" not in out
    # The session still renders its own record line below.
    assert "- 00000000000000000000000002 session 2026-01-02T00:00:00Z\n" in out


# -- what ran: reviews --------------------------------------------------------


def test_a_reviews_line_shows_what_ran(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a review's line shows what ran — the reviewer's actor,
    vendor and model."""

    repo = _repo(tmp_path, monkeypatch, _contract3(reviewers=["qa-lead"]))
    _open(repo)
    _review(repo, "00000000000000000000000002", "2026-01-02T00:00:00Z")

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- review 00000000000000000000000002: actor=qa-lead "
        "vendor=qa-vendor model=qa-model\n"
    ) in out


def test_an_absent_reviewer_actor_is_shown_as_absent_and_unmarked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an absent reviewer value is shown as absent — a review
    carrying no `reviewer.actor` shows the absent value and no mark, even
    with a declared reviewers list."""

    repo = _repo(tmp_path, monkeypatch, _contract3(reviewers=["qa-lead"]))
    _open(repo)
    _review(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor=None,
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- review 00000000000000000000000002: actor=(absent) "
        "vendor=qa-vendor model=qa-model\n"
    ) in out


def test_a_reviewer_actor_not_in_the_declared_list_is_marked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a reviewer actor not in the declared list is marked —
    shown, not refused (ADR-0018 decision 3)."""

    repo = _repo(tmp_path, monkeypatch, _contract3(reviewers=["qa-lead"]))
    _open(repo)
    _review(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="other-reviewer",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- review 00000000000000000000000002: actor=other-reviewer "
        "vendor=qa-vendor model=qa-model (not declared for the role)\n"
    ) in out


def test_the_mark_appears_only_when_reviewers_is_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the mark appears only when reviewers is declared — with
    no declared list there is nothing to be outside of."""

    repo = _repo(tmp_path, monkeypatch, _contract3(implementers=["devin"]))
    _open(repo)
    _review(
        repo,
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
        actor="other-reviewer",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert "- reviewers: (not declared)\n" in out
    assert (
        "- review 00000000000000000000000002: actor=other-reviewer "
        "vendor=qa-vendor model=qa-model\n"
    ) in out
    assert "not declared for the role" not in out


# -- escaping -----------------------------------------------------------------


def test_section_values_that_could_forge_a_line_print_escaped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value that could forge a line prints escaped — a
    declared entry or a record field carrying a refused character prints
    each as its escape and stays on its own line, the section pinned
    byte for byte."""

    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=3,
            id="CR-001",
            title="Task",
            scope=(),
            acceptance=(),
            implementers=("de\nvin", "code\u202ex"),
            reviewers=("qa\u202elead",),
            independence=("distinct-vendor",),
        ),
        records=(
            {
                "id": "r-session",
                "record_type": "session",
                "created_at": "t0",
                "role": "implementer",
                "actor": "de\nvin",
                "usage": {"provider": "pro\nvider", "method": "measured"},
                "model": "m\u202e1",
                "fallback_reason": "quota\nhit",
            },
            {
                "id": "r-review",
                "record_type": "review",
                "created_at": "t1",
                "verdict": "ok",
                "reviewed_commit": _COMMIT,
                "findings": [],
                "reviewer": {
                    "actor": "ra\u202ector",
                    "vendor": "ven\ndor",
                    "model": "mo\tdel",
                },
            },
        ),
        state="open",
    )

    print_task_detail(tmp_path, task, tmp_path)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- (none)\n"
        "Assignment:\n"
        "- implementers: de\\nvin, code\\u202ex\n"
        "- reviewers: qa\\u202elead\n"
        "- independence: distinct-vendor\n"
        "- implementer session r-session: actor=de\\nvin vendor=pro\\nvider "
        "model=m\\u202e1 fallback_reason=quota\\nhit\n"
        "- review r-review: actor=ra\\u202ector vendor=ven\\ndor "
        "model=mo\\tdel (not declared for the role)\n"
        "Records:\n"
        "- r-session session t0\n"
        "- r-review review t1 reviewed_commit=aaaaaaa verdict=ok "
        "findings=0 advisory=0\n"
        "No agreement with the contract is recorded\n"
    )
