"""Tests for ``.github/scripts/check_release_audit.py`` — the release gate.

Each test builds a small git repository under ``tmp_path`` and calls the
script's ``audit_release`` (imported by path: the script lives outside the
package and runs in the release job before the product is installed).
"""

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "scripts"
    / "check_release_audit.py"
)

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("check_release_audit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_release_audit: Any = _load()


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    _write(repo, "pyproject.toml", '[project]\nversion = "1.0.0"\n')
    return repo


def _journal_task(
    repo: Path,
    task: str,
    scope: tuple[str, ...],
    *,
    completed: bool = True,
) -> None:
    """A minimal journal task: a TOML-headed contract plus records."""

    header = (
        "+++\n"
        "schema = 2\n"
        f'id = "{task}"\n'
        'title = "a task"\n'
        f"scope = {json.dumps(list(scope))}\n"
        "+++\n\n# task\n"
    )
    _write(repo, f".agentmarshal/journal/tasks/{task}/contract.md", header)
    if completed:
        _write(
            repo,
            f".agentmarshal/journal/tasks/{task}/records/01TEST-completed.json",
            json.dumps({"record_type": "completed", "task": task}) + "\n",
        )
    else:
        _write(
            repo,
            f".agentmarshal/journal/tasks/{task}/records/01TEST-opened.json",
            json.dumps({"record_type": "opened", "task": task}) + "\n",
        )


def _audit_file(
    repo: Path,
    *,
    version: str = "1.0.0",
    audited_commit: str,
    model: str = "gpt-6-astra",
    findings: tuple[dict[str, str], ...] = (),
) -> None:
    lines = [
        f'version = "{version}"',
        f'audited_commit = "{audited_commit}"',
        f'model = "{model}"',
        "audited_at = 2026-10-24T00:00:00Z",
    ]
    for finding in findings:
        lines.append("")
        lines.append("[[finding]]")
        for key, value in finding.items():
            lines.append(f'{key} = "{value}"')
    _write(repo, f"release/audit-{version}.toml", "\n".join(lines) + "\n")


def _audit(repo: Path, tag: str = "v1.0.0") -> list[str]:
    refusals: list[str] = check_release_audit.audit_release(tag, repo)
    return refusals


def _base_commit(repo: Path) -> str:
    _write(repo, "src/agentmarshal/__init__.py", '__version__ = "1.0.0"\n')
    _write(repo, "src/foo.py", "x = 1\n")
    _write(repo, "CHANGELOG.md", "# changelog\n")
    return _commit_all(repo, "base")


def test_unresolvable_tag_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    # No tag v1.0.0 exists in the repository.

    refusals = _audit(repo)

    assert refusals == ["cannot resolve tag 'v1.0.0' to a commit"]


def test_missing_audit_file_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == ["release/audit-1.0.0.toml is missing from the tagged tree"]


def test_unparseable_audit_file_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    _write(repo, "release/audit-1.0.0.toml", 'version = "1.0.0"\n[[[broken\n')
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert len(refusals) == 1
    assert "not valid TOML" in refusals[0]


def test_missing_required_key_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        f'version = "1.0.0"\naudited_commit = "{audited}"\n'
        "audited_at = 2026-10-24T00:00:00Z\n",
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("missing required key 'model'" in r for r in refusals)


def test_version_mismatch_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # The file names a different release than the tag does.
    _write(
        repo,
        "release/audit-1.0.0.toml",
        f'version = "9.9.9"\naudited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\naudited_at = 2026-10-24T00:00:00Z\n',
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("does not match tag" in r for r in refusals)


def test_non_string_version_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        "version = 1\n"
        f'audited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\n'
        "audited_at = 2026-10-24T00:00:00Z\n",
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: 'version' must be a non-empty string"
    ]


def test_short_audited_commit_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # The natural operator mistake: the abbreviated SHA git prints. The
    # refusal must say a full 40-character commit is required.
    _audit_file(repo, audited_commit=audited[:7])
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: 'audited_commit' must be a full"
        " 40-character hexadecimal commit id"
    ]


def test_non_hex_audited_commit_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    # Forty characters but not hexadecimal.
    _audit_file(repo, audited_commit="z" * 40)
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: 'audited_commit' must be a full"
        " 40-character hexadecimal commit id"
    ]


def test_model_not_allowlisted_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(repo, audited_commit=audited, model="some-other-model")
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("not in the allowlist" in r for r in refusals)


def test_non_string_model_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        'version = "1.0.0"\n'
        f'audited_commit = "{audited}"\n'
        "model = 1\n"
        "audited_at = 2026-10-24T00:00:00Z\n",
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == ["release/audit-1.0.0.toml: 'model' must be a non-empty string"]


def test_invalid_audited_at_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        'version = "1.0.0"\n'
        f'audited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\n'
        "audited_at = 5\n",
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == ["release/audit-1.0.0.toml: 'audited_at' must be a timestamp"]


def test_audited_commit_not_a_commit_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    _audit_file(repo, audited_commit="0" * 40)
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("is not a commit in this repository" in r for r in refusals)


def test_audited_commit_not_ancestor_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    # A commit that exists in the repository but on a branch that never
    # reached the tag: the audit claims to have run on it.
    _git(repo, "checkout", "--quiet", "-b", "side")
    _git(repo, *_WRITER, "commit", "--allow-empty", "--quiet", "-m", "side")
    side = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "--quiet", "master")
    _audit_file(repo, audited_commit=side)
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("is not an ancestor" in r for r in refusals)


def test_finding_not_an_array_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        'version = "1.0.0"\n'
        f'audited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\n'
        "audited_at = 2026-10-24T00:00:00Z\n"
        'finding = "oops"\n',
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: 'finding' must be an array of tables"
    ]


def test_finding_element_not_a_table_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        "release/audit-1.0.0.toml",
        'version = "1.0.0"\n'
        f'audited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\n'
        "audited_at = 2026-10-24T00:00:00Z\n"
        'finding = ["oops"]\n',
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == ["release/audit-1.0.0.toml: finding[0] is not a table"]


def test_finding_without_id_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # One finding has no 'id' key at all, the other an empty one; both are
    # the same refusal.
    _write(
        repo,
        "release/audit-1.0.0.toml",
        'version = "1.0.0"\n'
        f'audited_commit = "{audited}"\n'
        'model = "gpt-6-astra"\n'
        "audited_at = 2026-10-24T00:00:00Z\n"
        "[[finding]]\n"
        'disposition = "deferred"\n'
        'reason = "no id at all"\n'
        "\n"
        "[[finding]]\n"
        'id = ""\n'
        'disposition = "deferred"\n'
        'reason = "empty id"\n',
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: finding[0] requires a non-empty 'id'",
        "release/audit-1.0.0.toml: finding[1] requires a non-empty 'id'",
    ]


def test_fixed_finding_without_task_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed"},),
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("requires task" in r for r in refusals)


def test_deferred_finding_without_reason_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "deferred"},),
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("requires a non-empty 'reason'" in r for r in refusals)


def test_unknown_disposition_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "ignored", "reason": "not one"},),
    )
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("expected one of" in r for r in refusals)


def test_fixed_task_without_completed_record_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _journal_task(repo, "CR-7", ("src/foo.py",), completed=False)
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed", "task": "CR-7"},),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("no 'completed' record" in r for r in refusals)


def test_reopened_fix_task_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # CR-7 was completed, then reopened: the last lifecycle record is the
    # reopening, so the fix does not count as done.
    _journal_task(repo, "CR-7", ("src/foo.py",))
    _write(
        repo,
        ".agentmarshal/journal/tasks/CR-7/records/02TEST-reopened.json",
        json.dumps({"record_type": "reopened", "task": "CR-7"}) + "\n",
    )
    _write(repo, "src/foo.py", "x = 2\n")
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed", "task": "CR-7"},),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: task CR-7 is listed as fixing a finding"
        " but was reopened in the tagged tree's journal"
    ]


def test_recompleted_after_reopen_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # completed, reopened, completed again: the last lifecycle record is
    # the second completion, so the task counts as done.
    _journal_task(repo, "CR-7", ("src/foo.py",))
    _write(
        repo,
        ".agentmarshal/journal/tasks/CR-7/records/02TEST-reopened.json",
        json.dumps({"record_type": "reopened", "task": "CR-7"}) + "\n",
    )
    _write(
        repo,
        ".agentmarshal/journal/tasks/CR-7/records/03TEST-completed.json",
        json.dumps({"record_type": "completed", "task": "CR-7"}) + "\n",
    )
    _write(repo, "src/foo.py", "x = 2\n")
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed", "task": "CR-7"},),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    assert _audit(repo) == []


def test_fixed_task_without_contract_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _write(
        repo,
        ".agentmarshal/journal/tasks/CR-7/records/01TEST-completed.json",
        json.dumps({"record_type": "completed", "task": "CR-7"}) + "\n",
    )
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed", "task": "CR-7"},),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("cannot read the scope of task CR-7" in r for r in refusals)


def test_change_outside_allowed_paths_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _journal_task(repo, "CR-7", ("src/foo.py",))
    _write(repo, "src/foo.py", "x = 2\n")
    # tools/extra.py is in no fixed task's scope and not a release path.
    _write(repo, "tools/extra.py", "y = 1\n")
    _audit_file(
        repo,
        audited_commit=audited,
        findings=({"id": "F-1", "disposition": "fixed", "task": "CR-7"},),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    refusals = _audit(repo)

    assert any("tools/extra.py changed" in r for r in refusals)


def test_diff_failure_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(repo, audited_commit=audited)
    _commit_all(repo, "audit file")
    _git(repo, "tag", "v1.0.0")

    real_git = check_release_audit._git

    def fake_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        if arguments[0] == "diff":
            return subprocess.CompletedProcess(list(arguments), 1, "", "fatal")
        result: subprocess.CompletedProcess[str] = real_git(repository, *arguments)
        return result

    # A failing post-audit diff must refuse like every other git call, not
    # pass on the empty output it produces.
    monkeypatch.setattr(check_release_audit, "_git", fake_git)

    refusals = _audit(repo)

    assert refusals == [
        "release/audit-1.0.0.toml: git diff between the audited commit"
        f" {audited} and tag v1.0.0 failed"
    ]


def test_passes_with_zero_findings(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    _audit_file(repo, audited_commit=audited)
    _write(repo, "CHANGELOG.md", "# changelog\n\n## 1.0.0\n")
    _commit_all(repo, "release notes and audit file")
    _git(repo, "tag", "v1.0.0")

    assert _audit(repo) == []


def test_passes_with_fixed_finding_covering_change(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audited = _base_commit(repo)
    # The fix: src/foo.py lands after the audit, inside CR-7's scope; the
    # deferred finding needs a reason but no task.
    _journal_task(repo, "CR-7", ("src/foo.py",))
    _write(repo, "src/foo.py", "x = 2\n")
    _audit_file(
        repo,
        audited_commit=audited,
        findings=(
            {"id": "F-1", "disposition": "fixed", "task": "CR-7"},
            {
                "id": "F-2",
                "disposition": "deferred",
                "reason": "documented for next release",
            },
        ),
    )
    _commit_all(repo, "fix and audit file")
    _git(repo, "tag", "v1.0.0")

    assert _audit(repo) == []


def test_main_reports_pass_and_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _base_commit(repo)
    monkeypatch.chdir(repo)
    _git(repo, "tag", "v1.0.0")

    assert check_release_audit.main(["v1.0.0"]) == 1
    captured = capsys.readouterr()
    assert "::error::" in captured.err
    assert "release/audit-1.0.0.toml is missing" in captured.err

    audited = _git(repo, "rev-parse", "HEAD")
    _audit_file(repo, audited_commit=audited)
    _commit_all(repo, "audit file")
    _git(repo, "tag", "-d", "v1.0.0")
    _git(repo, "tag", "v1.0.0")

    assert check_release_audit.main(["v1.0.0"]) == 0
    captured = capsys.readouterr()
    assert "release audit: passed" in captured.out


def test_main_usage_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_release_audit.main([]) == 2
    assert check_release_audit.main(["v1.0.0", "extra"]) == 2
    captured = capsys.readouterr()
    assert captured.err.count("usage: check_release_audit.py <tag>") == 2
