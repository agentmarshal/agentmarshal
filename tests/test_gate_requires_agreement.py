"""Tests for the gate's required-agreement check.

One test per scenario of the ``gate-requires-agreement`` change's
contract-governance delta; each docstring opens with the scenario's
heading so the requirement and its demonstration can be traced one to
one.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal import __version__
from agentmarshal.cli import main
from agentmarshal.journal.contracts import contract_sha256
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import create_agreement_record, write_record
from test_gate import (
    GATE_FIXTURES,
    _approve,
    _candidate_head,
    _compare_transcript,
    _embedded_implementation_case,
    _gate_repo,
    _implement,
    _run,
    _run_without_review,
)
from test_placement import _host_and_sidecar

_CONTRACT_PATH = ".agentmarshal/journal/tasks/CR-001/contract.md"


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    An agreement record requires a resolvable recorder; every test that
    needs one names the actor itself rather than inheriting a value.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _require_agreement(repo: Path, value: object) -> None:
    """Write ``contract.require_agreement`` into the working-tree project file.

    Called after the candidate's head commit exists, deliberately:
    ``_commit_all`` sweeps a dirty ``project.json`` into the candidate's
    diff, outside the task's scope. The gate reads the setting from the
    working tree at run time, so an uncommitted edit is the honest way
    to make it.
    """

    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project.setdefault("contract", {})["require_agreement"] = value
    project_path.write_text(json.dumps(project), encoding="utf-8")


def _agree(journal_root: Path, contract_hash: str) -> None:
    write_record(
        journal_root,
        "CR-001",
        create_agreement_record("CR-001", __version__, contract_hash),
    )


def _judged_hash(repo: Path, base: str, head: str) -> str:
    """The hash the embedded gate compares against: the merge-base contract."""

    merge_base = subprocess.run(
        ["git", "merge-base", base, head],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "show", f"{merge_base}:{_CONTRACT_PATH}"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    return contract_sha256(blob, f"{merge_base}:{_CONTRACT_PATH}")


def _working_contract_hash(repo: Path) -> str:
    path = repo / _CONTRACT_PATH
    return contract_sha256(path.read_bytes(), str(path))


def test_a_recorded_agreement_at_the_judged_hash_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a recorded agreement at the judged hash passes."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    _agree(repo / ".agentmarshal" / "journal", _judged_hash(repo, base, head))

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert (
        f"PASS: agreement recorded for contract "
        f"{_judged_hash(repo, base, head)[:7]}" in output
    )


def test_no_recorded_agreement_refuses_the_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: no recorded agreement refuses the candidate."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: no agreement recorded for contract "
        f"{_judged_hash(repo, base, head)[:7]}; "
        "record agreement with 'agentmarshal agree'" in output
    )


def test_an_agreement_for_an_earlier_contract_text_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an agreement for an earlier contract text fails."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    _agree(repo / ".agentmarshal" / "journal", "b" * 64)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: an agreement exists for another hash (bbbbbbb), "
        f"not for the judged contract {_judged_hash(repo, base, head)[:7]}; "
        "record agreement with 'agentmarshal agree'" in output
    )


def test_the_latest_agreement_names_the_other_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the latest agreement names the other hash."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    _agree(repo / ".agentmarshal" / "journal", "b" * 64)
    _agree(repo / ".agentmarshal" / "journal", "c" * 64)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "an agreement exists for another hash (ccccccc)" in output
    assert "bbbbbbb" not in output


def test_any_agreement_carrying_the_hash_satisfies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: any agreement carrying the hash satisfies.

    The matching record is the older of the two — the check is
    existential over the task's records, so a later agreement at a
    stale hash does not unsatisfy what the journal holds.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    judged = _judged_hash(repo, base, head)
    _agree(repo / ".agentmarshal" / "journal", judged)
    _agree(repo / ".agentmarshal" / "journal", "b" * 64)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert f"PASS: agreement recorded for contract {judged[:7]}" in output


def test_any_recorder_satisfies_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: any recorder satisfies the check.

    The project declares no actors at all, so the recorded agreement's
    recorder is nobody the project's table names — agreement is any
    actor's, there are no roles.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "not-a-declared-actor")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    judged = _judged_hash(repo, base, head)
    _agree(repo / ".agentmarshal" / "journal", judged)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert f"PASS: agreement recorded for contract {judged[:7]}" in output


def test_the_hash_compared_is_the_contract_the_gate_judges_against(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the hash compared is the contract the gate judges against.

    The working-tree contract is amended after opening; the merge-base
    text is still what the gate judges, so an agreement at the working
    tree's hash is an agreement for another hash — while one at the
    judged text's hash satisfies.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)
    _approve(repo, head)
    contract_path = repo / _CONTRACT_PATH
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8").replace(
            'title = "Gate task"', 'title = "Amended gate task"'
        ),
        encoding="utf-8",
    )
    drifted = _working_contract_hash(repo)
    _agree(repo / ".agentmarshal" / "journal", drifted)

    judged = _judged_hash(repo, base, head)
    assert drifted != judged
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"an agreement exists for another hash ({drifted[:7]}), "
        f"not for the judged contract {judged[:7]}" in output
    )

    _agree(repo / ".agentmarshal" / "journal", judged)
    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert f"PASS: agreement recorded for contract {judged[:7]}" in output


def test_a_sidecars_required_agreement_is_judged_against_its_own_journals_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a sidecar's required agreement is judged against its own
    journal's contract.

    The host's diff and commits are the candidate; the hash an agreement
    must carry is of the sidecar journal's own contract.md — first shown
    failing with the judged hash named, then passing once a record at
    that hash exists.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    host, sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    _require_agreement(sidecar, True)
    _approve(sidecar, head)
    journal = sidecar / ".agentmarshal" / "journal"
    contract_path = journal / "tasks" / "CR-001" / "contract.md"
    judged = contract_sha256(contract_path.read_bytes(), str(contract_path))

    report = run_gate(host, "CR-001", head, base, head, journal_root=journal)
    output = "\n".join(report.lines)

    assert not report.passed
    assert f"no agreement recorded for contract {judged[:7]}" in output

    _agree(journal, judged)
    report = run_gate(host, "CR-001", head, base, head, journal_root=journal)
    output = "\n".join(report.lines)

    assert report.passed, output
    assert f"PASS: agreement recorded for contract {judged[:7]}" in output


def test_the_check_is_not_review_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the check is not review-bound.

    With ``review_required`` false the review checks are reported not
    examined; the agreement line still judges the records — a FAIL when
    nothing matches, a PASS once a matching record exists.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, True)

    passed, output = _run_without_review(repo, head, base, head)

    assert "NOT EXAMINED: latest review" in output
    assert not passed
    assert (
        f"FAIL: no agreement recorded for contract "
        f"{_judged_hash(repo, base, head)[:7]}" in output
    )

    _agree(repo / ".agentmarshal" / "journal", _judged_hash(repo, base, head))
    passed, output = _run_without_review(repo, head, base, head)

    assert passed, output
    assert (
        f"PASS: agreement recorded for contract "
        f"{_judged_hash(repo, base, head)[:7]}" in output
    )


def test_the_deterministic_lane_prints_no_agreement_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the deterministic lane prints no agreement line.

    The candidate's only change is a journal record — an agreement
    naming the hash that would satisfy the check — so the run takes the
    lane for journal-only transactions. The lane's line appears; the
    required-agreement check is not among the lane's checks.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"

    def add_agreement() -> None:
        _agree(journal, _judged_hash(repo, base, base))

    head = _candidate_head(repo, "agreement-only", base, add_agreement)
    _require_agreement(repo, True)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: journal-only transaction" in output
    assert "agreement recorded" not in output
    assert "contract.require_agreement" not in output


def test_an_absent_or_false_setting_prints_no_agreement_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an absent or false setting prints no agreement line.

    The pinned transcript is the assertion: with the setting absent and
    again with it false the run is the committed fixture byte for byte,
    so no agreement line can have crept into the default output.
    """

    for name, value in (("absent", None), ("false", False)):
        case_root = tmp_path / name
        case_root.mkdir()
        arguments, run_values = _embedded_implementation_case(case_root, monkeypatch)
        if value is not None:
            _require_agreement(case_root / "repo", value)
        capsys.readouterr()
        code = main(arguments)
        transcript = capsys.readouterr()
        _compare_transcript(
            GATE_FIXTURES,
            "embedded-implementation",
            code,
            transcript.out,
            transcript.err,
            run_values,
        )


def test_an_unreadable_setting_is_reported_not_silently_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an unreadable setting is reported, not silently skipped."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_agreement(repo, "yes")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert (
        "WARN: agreement with the contract not examined "
        "(contract.require_agreement unreadable:" in output
    )
    assert "agreement recorded" not in output
    assert "FAIL" not in output
