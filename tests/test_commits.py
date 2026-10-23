"""`agentmarshal.commits.resolve_commit` — one place decides what a `--commit`
reference resolves to.

The four commands that bind a record to a commit resolve through this one
function: `git rev-parse --verify <rev>^{commit}`, never through a shell, in
the repository the caller's root names. What resolves is the full
40-character commit id; what does not is refused, the refusal naming the
reference and the repository the caller said was asked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.commits import CommitResolutionError, resolve_commit


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, message: str = "commit") -> str:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path) -> Path:
    """A git root with one committed file — the floor resolution needs."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    (repo / "notes.txt").write_text("notes\n", encoding="utf-8")
    _commit(repo, "initial")
    return repo


def test_a_full_commit_id_resolves_to_itself(tmp_path: Path) -> None:
    """A 40-hex id the repository holds resolves — to that same id."""

    repo = _repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD")

    assert resolve_commit(repo, head, repository="the journal's repository") == head


def test_an_abbreviated_id_resolves_to_the_full_id(tmp_path: Path) -> None:
    """A short id and a symbolic name resolve to the full 40-hex id."""

    repo = _repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD")

    assert resolve_commit(repo, head[:8], repository="the journal's repository") == head
    assert resolve_commit(repo, "HEAD", repository="the journal's repository") == head


def test_a_name_of_a_non_commit_object_is_refused(tmp_path: Path) -> None:
    """A name resolving to no commit — a tree, a blob — is refused."""

    repo = _repo(tmp_path)
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    blob = _git(repo, "rev-parse", "HEAD:notes.txt")

    for name in (tree, blob):
        with pytest.raises(CommitResolutionError, match="does not resolve to a commit"):
            resolve_commit(repo, name, repository="the journal's repository")


def test_an_unknown_name_is_refused(tmp_path: Path) -> None:
    """A reference the repository does not hold is refused naming it."""

    repo = _repo(tmp_path)

    for name in ("0" * 40, "no-such-ref"):
        with pytest.raises(
            CommitResolutionError, match="does not resolve to a commit"
        ) as raised:
            resolve_commit(repo, name, repository="the journal's repository")
        assert name in str(raised.value)


def test_the_refusal_names_the_repository_the_caller_names(tmp_path: Path) -> None:
    """The message ends on the caller's own phrase for the repository asked."""

    repo = _repo(tmp_path)

    with pytest.raises(CommitResolutionError) as raised:
        resolve_commit(repo, "no-such-ref", repository="the scanned repository")

    assert str(raised.value).startswith(
        "--commit no-such-ref does not resolve to a commit in the scanned repository"
    )


def test_the_reference_and_gits_error_text_are_escaped(tmp_path: Path) -> None:
    """A reference that could forge a line prints escaped in the refusal."""

    repo = _repo(tmp_path)

    with pytest.raises(CommitResolutionError) as raised:
        resolve_commit(repo, "no\nsuch", repository="the journal's repository")

    message = str(raised.value)
    assert "\n" not in message
    assert "--commit no\\nsuch does not resolve" in message


def test_git_that_cannot_be_started_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An OSError launching git lands as `cannot run git: <error>`."""

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("git is not installed")

    monkeypatch.setattr(subprocess, "run", _fail)

    with pytest.raises(CommitResolutionError) as raised:
        resolve_commit(tmp_path, "HEAD", repository="the journal's repository")

    assert str(raised.value) == "cannot run git: git is not installed"
