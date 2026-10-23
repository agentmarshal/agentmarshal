"""The launcher writing a verdict's ``verification``/``evidence`` markup.

ADR-0017 decision 4 names what the reviewer ran, read and could not run;
decision 5 names the evidence reference behind each finding and the
"unconfirmed" advisory rule. The record layer's shapes live in
``records.py``'s ``review-fields-7`` rule — the launcher reduces the
verdict's raw values to what those rules admit, dropping each malformed
part with a warning, never refusing the paid verdict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import review
from agentmarshal.settings import DEFAULT_FINDING_CLASSES
from test_review_launcher import (
    _finding_args,
    _record_finding,
    _review_repo,
    _reviewer_stub,
    _run_review,
)
from test_review_links_and_classes import _reviews

_VALID_VERIFICATION = {
    "executed": [{"what": "pytest tests/test_api.py", "result": "12 passed"}],
    "read": ["src/api.py lines 40-80", "docs/contract.md"],
    "not_run": [{"what": "deploy smoke test", "why": "no staging credentials"}],
}


def _verdict_with_fields(
    commit: str,
    verdict: str,
    findings: list[str],
    *,
    advisory_findings: list[str] | None = None,
    verification: Any = ...,
    evidence: Any = ...,
) -> str:
    """A commit verdict carrying deliberately malformed optional markup."""

    data: dict[str, object] = {
        "reviewed_commit": commit,
        "verdict": verdict,
        "findings": findings,
    }
    if advisory_findings is not None:
        data["advisory_findings"] = advisory_findings
    if verification is not ...:
        data["verification"] = verification
    if evidence is not ...:
        data["evidence"] = evidence
    return f"AGENTMARSHAL_VERDICT_BEGIN\n{json.dumps(data)}\nAGENTMARSHAL_VERDICT_END\n"


def _launch_with_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    verdict: str = "changes_required",
    findings: list[str] | None = None,
    *,
    advisory_findings: list[str] | None = None,
    verification: Any = ...,
    evidence: Any = ...,
) -> tuple[Path, str]:
    """Stand up the review repo, stub a verdict for the real commit, launch."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = _verdict_with_fields(
        commit,
        verdict,
        findings if findings is not None else ["F-1"],
        advisory_findings=advisory_findings,
        verification=verification,
        evidence=evidence,
    )
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )
    assert _run_review(commit) == 0
    return repo, commit


def test_a_verification_object_is_admitted_by_the_protocol() -> None:
    """Scenario: a verification object is admitted by the protocol."""

    output = _verdict_with_fields(
        "a" * 40,
        "changes_required",
        ["F-1"],
        verification=_VALID_VERIFICATION,
    )

    parsed = review._parse_verdict(output, preserve_output=False)

    assert parsed[6] == _VALID_VERIFICATION


def test_an_evidence_object_is_admitted_by_the_protocol() -> None:
    """Scenario: an evidence object is admitted by the protocol."""

    evidence = {"F-1": "pytest tests/test_api.py: 12 passed"}
    output = _verdict_with_fields(
        "a" * 40, "changes_required", ["F-1"], evidence=evidence
    )

    parsed = review._parse_verdict(output, preserve_output=False)

    assert parsed[7] == evidence


def test_the_prompt_asks_for_the_sections_and_states_the_unconfirmed_rule() -> None:
    """Scenario: the prompt asks for the sections and states the unconfirmed rule."""

    prompt = review._review_prompt(
        "CONTRACT", "DIFF", "b" * 40, DEFAULT_FINDING_CLASSES
    )

    assert '"executed"' in prompt
    assert '"read"' in prompt
    assert '"not_run"' in prompt
    assert "- evidence: an object naming, for each finding id you report" in prompt
    assert '"unconfirmed"' in prompt
    assert "advisory_findings" in prompt


def test_the_commit_prompt_asks_where_each_criterion_is_met() -> None:
    """Scenario: the commit prompt asks where each criterion is met."""

    prompt = review._review_prompt(
        "CONTRACT", "DIFF", "b" * 40, DEFAULT_FINDING_CLASSES
    )

    assert "acceptance criterion" in prompt
    assert "where the diff meets it" in prompt
    assert "which test demonstrates it" in prompt


def test_the_finding_prompt_asks_for_the_same_sections() -> None:
    """Scenario: the finding prompt asks for the same sections."""

    prompt = review._finding_review_prompt(
        "CONTRACT",
        "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "Conclusion",
        (),
        (),
        DEFAULT_FINDING_CLASSES,
    )

    assert '"executed"' in prompt
    assert '"not_run"' in prompt
    assert "- evidence: an object naming, for each finding id you report" in prompt
    assert '"unconfirmed"' in prompt
    # A finding review has no diff — the criterion-coverage ask stays commit-only.
    assert "where the diff meets it" not in prompt


def test_the_verification_sections_are_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the verification sections are recorded."""

    repo, _commit = _launch_with_verdict(
        tmp_path, monkeypatch, verification=_VALID_VERIFICATION
    )

    (record,) = _reviews(repo)
    assert record["verification"] == _VALID_VERIFICATION
    assert record["schema"] == 7
    assert "note:" not in capsys.readouterr().err


def test_a_section_outside_the_three_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a section outside the three is dropped with a warning."""

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        verification={
            "executed": [{"what": "pytest", "result": "pass"}],
            "screenshots": ["img.png"],
        },
    )

    (record,) = _reviews(repo)
    assert record["verification"] == {
        "executed": [{"what": "pytest", "result": "pass"}]
    }
    err = capsys.readouterr().err
    assert "screenshots" in err
    assert "dropped" in err


@pytest.mark.parametrize("bad_section", [[], "not-an-array", {"a": 1}, 5])
def test_a_section_that_is_not_a_non_empty_array_is_dropped_with_a_warning(
    bad_section: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a section that is not a non-empty array is dropped with a warning."""

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        verification={"executed": bad_section, "read": ["contract.md"]},
    )

    (record,) = _reviews(repo)
    assert record["verification"] == {"read": ["contract.md"]}
    err = capsys.readouterr().err
    assert "executed" in err
    assert "dropped" in err


def test_a_malformed_verification_entry_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed verification entry is dropped with a warning."""

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        verification={
            "executed": [
                {"what": "pytest", "result": "pass"},
                {"what": "missing the result key"},
                {"what": "line1\nline2 forged", "result": "x"},
            ],
            "read": ["contract.md", 5, " "],
        },
    )

    (record,) = _reviews(repo)
    assert record["verification"] == {
        "executed": [{"what": "pytest", "result": "pass"}],
        "read": ["contract.md"],
    }
    err = capsys.readouterr().err
    assert "entry 1" in err
    assert "entry 2" in err
    assert "item 1" in err
    assert "item 2" in err


def test_a_section_with_no_usable_entry_lands_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a section with no usable entry lands nothing."""

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        verification={
            "read": [5, " "],
            "executed": [{"what": "only-what"}],
        },
    )

    (record,) = _reviews(repo)
    assert "verification" not in record
    err = capsys.readouterr().err
    assert "no usable entries" in err


@pytest.mark.parametrize("bad", ["a-string", 5, ["x"], None])
def test_a_verification_that_is_not_an_object_is_dropped_whole_with_a_warning(
    bad: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a verification that is not an object is dropped whole with a
    warning."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch, verification=bad)

    (record,) = _reviews(repo)
    assert "verification" not in record
    assert "is not an object" in capsys.readouterr().err


def test_an_empty_verification_object_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an empty verification object is dropped with a warning."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch, verification={})

    (record,) = _reviews(repo)
    assert "verification" not in record
    assert "empty object" in capsys.readouterr().err


def test_a_verdict_without_verification_records_exactly_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a verdict without verification records exactly as before."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch)

    (record,) = _reviews(repo)
    assert "verification" not in record
    assert "verification" not in capsys.readouterr().err


def test_evidence_for_the_verdicts_ids_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: evidence for the verdict's ids is recorded."""

    evidence = {
        "F-1": "pytest tests/test_api.py: 12 passed",
        "A-1": "src/api.py:42",
    }
    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        advisory_findings=["A-1"],
        evidence=evidence,
    )

    (record,) = _reviews(repo)
    assert record["evidence"] == evidence
    assert record["schema"] == 7
    assert "note:" not in capsys.readouterr().err


def test_evidence_for_an_unknown_id_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario:
    an evidence entry for an id the verdict does not carry is dropped with a warning.
    """

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        evidence={"F-1": "src/api.py:42", "G-9": "ghost evidence"},
    )

    (record,) = _reviews(repo)
    assert record["evidence"] == {"F-1": "src/api.py:42"}
    err = capsys.readouterr().err
    assert "G-9" in err
    assert "dropped" in err


@pytest.mark.parametrize("bad_value", [5, " ", {"a": 1}, "line1\nline2 forged"])
def test_an_evidence_entry_the_record_could_not_hold_is_dropped_with_a_warning(
    bad_value: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an evidence entry the record could not hold is dropped with a
    warning."""

    repo, _commit = _launch_with_verdict(
        tmp_path,
        monkeypatch,
        findings=["F-1", "F-2"],
        evidence={"F-1": "src/api.py:42", "F-2": bad_value},
    )

    (record,) = _reviews(repo)
    assert record["evidence"] == {"F-1": "src/api.py:42"}
    err = capsys.readouterr().err
    assert "F-2" in err
    assert "dropped" in err


@pytest.mark.parametrize("bad", ["a-string", 5, ["x"], None])
def test_an_evidence_that_is_not_an_object_is_dropped_whole_with_a_warning(
    bad: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an evidence that is not an object is dropped whole with a warning."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch, evidence=bad)

    (record,) = _reviews(repo)
    assert "evidence" not in record
    assert "is not an object" in capsys.readouterr().err


def test_an_empty_evidence_object_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an empty evidence object is dropped with a warning."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch, evidence={})

    (record,) = _reviews(repo)
    assert "evidence" not in record
    assert "empty object" in capsys.readouterr().err


def test_a_verdict_without_evidence_records_exactly_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a verdict without evidence records exactly as before."""

    repo, _commit = _launch_with_verdict(tmp_path, monkeypatch)

    (record,) = _reviews(repo)
    assert "evidence" not in record
    assert "evidence" not in capsys.readouterr().err


def test_a_finding_review_records_verification_and_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The finding binding runs the same tail: the fields land identically."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    finding = _record_finding(repo, [("evidence/log.txt", b"conclusion\n")])
    output = (
        "AGENTMARSHAL_VERDICT_BEGIN\n"
        + json.dumps(
            {
                "reviewed_finding": finding,
                "verdict": "changes_required",
                "findings": ["F-1"],
                "verification": {"read": ["artifact content"]},
                "evidence": {"F-1": "evidence/log.txt"},
            }
        )
        + "\nAGENTMARSHAL_VERDICT_END\n"
    )
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )

    assert main(_finding_args(finding)) == 0

    (record,) = _reviews(repo)
    assert record["verification"] == {"read": ["artifact content"]}
    assert record["evidence"] == {"F-1": "evidence/log.txt"}
    assert record["schema"] == 7
    assert "note:" not in capsys.readouterr().err
