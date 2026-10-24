#!/usr/bin/env python3
"""Release audit gate.

Usage: ``check_release_audit.py <tag>`` (the pushed tag, e.g. ``v0.6.0``).

Reads ``release/audit-<version>.toml`` — where ``<version>`` is the tag
without its leading ``v`` — from the tagged tree and refuses, one line per
cause, unless the audit is recorded, was run by an allowlisted model on an
ancestor of the tagged commit, every blocking finding it lists was dealt
with, and nothing but those fixes and the release notes landed between the
audited commit and the tag.

Standard library and git only: the release job runs this before the
project's own environment exists, so nothing here may import the product.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

# The only models whose audit accepts a release. CONTRIBUTING.md's release
# section states the same list for the operator running the audit.
ALLOWED_MODELS = ("gpt-6-astra",)

# Paths that may always differ between the audited commit and the tag: the
# journal evidence of the fixes themselves, the audit file, the release
# notes and the version bump.
ALWAYS_ALLOWED = (
    ".agentmarshal/journal/",
    "release/",
    "CHANGELOG.md",
    "UPGRADING.md",
    "pyproject.toml",
    "uv.lock",
    "src/agentmarshal/__init__.py",
)

_TASKS = ".agentmarshal/journal/tasks"

_FULL_COMMIT = re.compile(r"[0-9a-f]{40}")
_TASK_ID = re.compile(r"CR-[0-9]+")
_DISPOSITIONS = ("fixed", "deferred", "rejected")


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        capture_output=True,
        encoding="utf-8",
    )


def _git_show(repo: Path, commit: str, path: str) -> str | None:
    """Return ``path``'s content at ``commit``, or ``None`` when absent."""

    result = _git(repo, "show", f"{commit}:{path}")
    return result.stdout if result.returncode == 0 else None


def _covered(scope: tuple[str, ...] | list[str], path: str) -> bool:
    """Whether an exact entry or trailing-slash prefix covers ``path``.

    The same rule ``agentmarshal.journal.contracts.scope_covers`` applies to
    contract scopes, so the gate reads a task's scope the way the scope was
    granted.
    """

    for entry in scope:
        if entry.endswith("/"):
            if path == entry.rstrip("/") or path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def _contract_scope(repo: Path, tagged: str, task: str) -> list[str] | None:
    """The ``scope`` list of ``task``'s contract in the tagged tree.

    ``None`` when the contract is missing or its TOML header or ``scope``
    array cannot be read.
    """

    raw = _git_show(repo, tagged, f"{_TASKS}/{task}/contract.md")
    if raw is None:
        return None
    lines = raw.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "+++":
        return None
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "+++"
        )
    except StopIteration:
        return None
    try:
        header = tomllib.loads("\n".join(lines[1:end]))
    except tomllib.TOMLDecodeError:
        return None
    scope = header.get("scope")
    if not isinstance(scope, list) or not all(
        isinstance(entry, str) for entry in scope
    ):
        return None
    return scope


def _has_completed_record(repo: Path, tagged: str, task: str) -> bool:
    """Whether ``task`` has a parseable ``completed`` record in the tagged tree."""

    listing = _git(
        repo,
        "ls-tree",
        "-r",
        "-z",
        "--name-only",
        tagged,
        "--",
        f"{_TASKS}/{task}/records/",
    )
    if listing.returncode != 0:
        return False
    for path in listing.stdout.split("\0"):
        if not path.endswith("-completed.json"):
            continue
        raw = _git_show(repo, tagged, path)
        if raw is None:
            continue
        try:
            record: Any = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("record_type") == "completed":
            return True
    return False


def _check_findings(
    audit_path: str, data: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Validate the ``[[finding]]`` tables; return (refusals, fixed tasks)."""

    refusals: list[str] = []
    fixed_tasks: list[str] = []
    raw_findings = data.get("finding", [])
    if not isinstance(raw_findings, list):
        return [f"{audit_path}: 'finding' must be an array of tables"], []
    for index, finding in enumerate(raw_findings):
        label = f"{audit_path}: finding[{index}]"
        if not isinstance(finding, dict):
            refusals.append(f"{label} is not a table")
            continue
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id:
            refusals.append(f"{label} requires a non-empty 'id'")
        else:
            label = f"{audit_path}: finding {finding_id!r}"
        disposition = finding.get("disposition")
        if disposition not in _DISPOSITIONS:
            refusals.append(
                f"{label} has disposition {disposition!r};"
                f" expected one of: {', '.join(_DISPOSITIONS)}"
            )
            continue
        if disposition == "fixed":
            task = finding.get("task")
            if not isinstance(task, str) or _TASK_ID.fullmatch(task) is None:
                refusals.append(f"{label} is 'fixed' and requires task = \"CR-<n>\"")
            else:
                fixed_tasks.append(task)
        else:
            reason = finding.get("reason")
            if not isinstance(reason, str) or not reason:
                refusals.append(
                    f"{label} is {disposition!r} and requires a non-empty 'reason'"
                )
    return refusals, fixed_tasks


def audit_release(tag: str, repo: Path) -> list[str]:
    """Return every refusal cause for releasing ``tag`` from ``repo``.

    An empty list means the audit accepts the release. ``tag`` is the pushed
    tag (``v0.6.0``); the audit file is ``release/audit-<version>.toml``
    with ``<version>`` the tag without its leading ``v``.
    """

    version = tag.removeprefix("v")
    audit_path = f"release/audit-{version}.toml"

    resolved = _git(repo, "rev-parse", "--verify", f"{tag}^{{commit}}")
    if resolved.returncode != 0:
        return [f"cannot resolve tag {tag!r} to a commit"]
    tagged = resolved.stdout.strip()

    raw = _git_show(repo, tagged, audit_path)
    if raw is None:
        return [f"{audit_path} is missing from the tagged tree"]
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as error:
        return [f"{audit_path} is not valid TOML: {error}"]

    refusals: list[str] = []
    for key in ("version", "audited_commit", "model", "audited_at"):
        if key not in data:
            refusals.append(f"{audit_path}: missing required key {key!r}")

    declared = data.get("version")
    if "version" in data:
        if not isinstance(declared, str) or not declared:
            refusals.append(f"{audit_path}: 'version' must be a non-empty string")
        elif declared != version:
            refusals.append(
                f"{audit_path}: version {declared!r} does not match tag {tag!r}"
            )

    audited = data.get("audited_commit")
    audited_commit: str | None = None
    if "audited_commit" in data:
        if not isinstance(audited, str) or _FULL_COMMIT.fullmatch(audited) is None:
            refusals.append(
                f"{audit_path}: 'audited_commit' must be a 40-character"
                " hexadecimal commit id"
            )
        else:
            audited_commit = audited

    model = data.get("model")
    if "model" in data:
        if not isinstance(model, str) or not model:
            refusals.append(f"{audit_path}: 'model' must be a non-empty string")
        elif model not in ALLOWED_MODELS:
            refusals.append(
                f"{audit_path}: model {model!r} is not in the allowlist"
                f" ({', '.join(ALLOWED_MODELS)})"
            )

    audited_at = data.get("audited_at")
    if "audited_at" in data and not (
        isinstance(audited_at, datetime.date)
        or (isinstance(audited_at, str) and audited_at)
    ):
        refusals.append(f"{audit_path}: 'audited_at' must be a timestamp")

    finding_refusals, fixed_tasks = _check_findings(audit_path, data)
    refusals.extend(finding_refusals)

    scopes: list[str] = []
    for task in dict.fromkeys(fixed_tasks):
        if not _has_completed_record(repo, tagged, task):
            refusals.append(
                f"{audit_path}: task {task} is listed as fixing a finding but"
                " has no 'completed' record in the tagged tree's journal"
            )
        task_scope = _contract_scope(repo, tagged, task)
        if task_scope is None:
            refusals.append(
                f"{audit_path}: cannot read the scope of task {task} from its"
                " contract in the tagged tree"
            )
        else:
            scopes.extend(task_scope)

    ancestor = False
    if audited_commit is not None:
        exists = _git(repo, "cat-file", "-e", f"{audited_commit}^{{commit}}")
        if exists.returncode != 0:
            refusals.append(
                f"{audit_path}: audited_commit {audited_commit} is not a commit"
                " in this repository"
            )
        else:
            ancestry = _git(repo, "merge-base", "--is-ancestor", audited_commit, tagged)
            if ancestry.returncode != 0:
                refusals.append(
                    f"{audit_path}: audited_commit {audited_commit} is not an"
                    f" ancestor of the tagged commit {tagged}"
                )
            else:
                ancestor = True

    if ancestor and audited_commit is not None:
        allowed = list(ALWAYS_ALLOWED) + scopes
        diff = _git(
            repo,
            "diff",
            "--no-renames",
            "--name-only",
            "-z",
            audited_commit,
            tagged,
        )
        for path in diff.stdout.split("\0"):
            if path and not _covered(allowed, path):
                refusals.append(
                    f"{audit_path}: {path} changed between the audited commit"
                    f" {audited_commit} and tag {tag} and is covered neither by"
                    " the release paths nor by the scope of a task listed as"
                    " fixing a finding"
                )

    return refusals


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("usage: check_release_audit.py <tag>", file=sys.stderr)
        return 2
    refusals = audit_release(arguments[0], Path.cwd())
    if not refusals:
        print("release audit: passed")
        return 0
    for refusal in refusals:
        print(f"::error::release audit refused: {refusal}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
