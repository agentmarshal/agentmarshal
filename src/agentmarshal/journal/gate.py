"""The merge gate: verifies a candidate against contract, review and attestation.

The gate reads trusted inputs from the base side of the candidate range
(the contract comes from the merge-base tree, so a candidate cannot
widen its own scope) and evidence from the journal records of the
invoking checkout, per ADR-0001/0003/0004. Review records are written by
the launcher into the journal working tree and stay uncommitted until
the completion transaction — a review therefore never has to be part of
the very diff it attests. Record provenance and CI wiring are later
slices; running the gate on a trusted checkout is the operator's
responsibility in this slice.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.actors import finding_reviewer_identity_refusal
from agentmarshal.journal.artifacts import artifact_path as artifact_path
from agentmarshal.journal.capture import (
    CaptureError,
    _acknowledgement_mark,
    decode_diff_per_file,
    private_markers_from_project,
    render_leak_hits,
    render_undecodable_files,
    scan_diff_for_leaks,
)
from agentmarshal.journal.contracts import (
    ContractHeader,
    JournalContractError,
    contract_sha256,
    parse_contract_text,
    scope_covers,
)
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifest,
    ExtensionManifestError,
    ExtensionManifestMissing,
    extension_directory_manifest_path,
    extension_manifest_path,
    parse_extension_manifest_text,
    read_extension_manifest,
)
from agentmarshal.journal.records import (
    JournalRecordError,
    read_records,
    validate_record_content,
)
from agentmarshal.journal.status import (
    TaskStatusError,
    load_task_status,
    projected_state_of,
    record_type_is_admitted_after_terminal,
)
from agentmarshal.project import (
    PROJECT_CONFIG_RELPATH,
    project_file_path,
    read_project_file,
)
from agentmarshal.settings import changes_required_threshold, require_agreement
from agentmarshal.switches import (
    SWITCHES_RELPATH,
    Switch,
    SwitchesError,
    parse_switches,
)

_JOURNAL_PREFIX = ".agentmarshal/journal/"
_EXTENSIONS_PREFIX = ".agentmarshal/extensions/"
# Twenty, because this line is one line of a document people read: a marker
# present in two hundred files used to render as one category token and now
# renders as two hundred records. Enough hits to act on are shown and the rest
# are counted. The bound is the transcript's, which is why it lives here and
# not in the renderer — `agentmarshal leak-scan` passes none.
_LEAK_HIT_RENDER_LIMIT = 20


class GateError(Exception):
    """Raised when the gate cannot evaluate a candidate at all.

    The message is refusal text a caller prints as it stands, and it can
    carry a value the gate did not write — a candidate's ref or path echoed
    in a failed git command, a record or contract value inside an
    exception's text, git's own error output — so it is escaped here the
    way a transcript line is escaped at ``say``: nothing it carries can add
    a line or reorder one, a raise added later cannot forget the escape,
    and a wrapper that re-quotes the text (a lifecycle or a review error)
    carries the escaped form. A message holding no refused character is
    unchanged.
    """

    def __init__(self, message: str) -> None:
        super().__init__(escape_for_display(message))


@dataclass(frozen=True)
class GateReport:
    """The outcome of a gate evaluation."""

    passed: bool
    lines: list[str]
    resolved_commit: str
    resolved_finding: str | None = None
    # True when the review-bound checks were reported as not examined because
    # the caller asked to judge without a review. It says nothing about the
    # other lines this gate can report as not examined — a caller that needs
    # those reads the transcript, which names each one.
    review_not_examined: bool = False
    # The id of the review the gate passed on — the approving latest review
    # of the resolved commit, or the non-approving one an acceptance
    # covered — set where the verdict check decides it, never recomputed;
    # None when the gate passed on no review, and always None on the
    # findings lane, which judges no commit's review. `complete` reads the
    # advisory findings needing a disposition from the record carrying this
    # id, so a review appended after the gate ran cannot change which are
    # owed (ADR-0016 decision 1).
    resolved_review: str | None = None


def run_findings_gate(journal_root: Path, task_id: str) -> GateReport:
    """Evaluate a task's latest finding without offering a merge candidate."""

    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise GateError(str(error)) from error

    lines: list[str] = []
    violations = 0

    def say(message: str) -> None:
        # Escaping the finished line is the one choice a line added later
        # cannot forget: the line interpolates values taken from records and
        # contracts, and the escaped set is exactly the forgeable-text
        # rule's, so the tool's own fixed text passes through unchanged.
        lines.append(escape_for_display(message))

    def check(passed: bool, message: str) -> None:
        nonlocal violations
        say(f"{'PASS' if passed else 'FAIL'}: {message}")
        if not passed:
            violations += 1

    if task.state == "open":
        say(f"PASS: task {task_id} is not closed")
    else:
        check(False, f"task {task_id} is already closed (state: {task.state})")
    if task.contract.scope:
        check(
            False,
            "findings lane requires an empty scope; declared scope: "
            + ", ".join(task.contract.scope),
        )
    else:
        say("NOT EXAMINED: scope diff (findings lane has no candidate)")

    if task.contract.documents or task.contract.extensions:
        # This lane has no candidate to examine, so the contract's naming is
        # all it needs to say so; it reads no manifest and refuses nothing.
        say("NOT EXAMINED: named documents (findings lane has no candidate)")

    findings = [record for record in task.records if record["record_type"] == "finding"]
    latest_finding = findings[-1] if findings else None
    if latest_finding is None:
        check(False, "findings lane requires at least one finding record")
        finding_id = ""
    else:
        finding_id = cast(str, latest_finding["id"])

    reviews = [record for record in task.records if record["record_type"] == "review"]
    latest_review = reviews[-1] if reviews else None
    review_matches = (
        latest_review is not None
        and latest_review.get("reviewed_finding") == finding_id
    )
    if latest_review is None:
        check(False, f"no review record for latest finding {finding_id or '(none)'}")
    elif not review_matches:
        check(
            False,
            f"latest review binds to finding "
            f"{latest_review.get('reviewed_finding', '(commit)')}, not latest finding "
            f"{finding_id or '(none)'}",
        )
    elif latest_review.get("verdict") == "approved":
        check(True, f"latest review of finding {finding_id} is approved")
    else:
        # Only an acceptance over findings counts — the pause and
        # operational forms bind `accepted_commit` and carry no `findings`,
        # so the field's presence is what the latest-acceptance judgment is
        # taken over.
        acceptances = [
            record
            for record in task.records
            if record["record_type"] == "acceptance"
            and record.get("accepted_finding") == finding_id
            and "findings" in record
        ]
        acceptance = acceptances[-1] if acceptances else None
        reviewed = cast(list[str], latest_review["findings"])
        accepted = (
            cast(list[str], acceptance["findings"]) if acceptance is not None else []
        )
        if acceptance is not None and set(accepted) == set(reviewed):
            say(
                f"PASS: accepted over findings {', '.join(accepted)} by "
                f"{acceptance['accepted_by']}; not an approving review"
            )
        else:
            check(
                False,
                f"latest review of finding {finding_id} is "
                f"{latest_review.get('verdict')}; blocking findings: "
                + ", ".join(reviewed),
            )

    if latest_finding is not None and latest_review is not None:
        reviewer = latest_review.get("reviewer")
        email = reviewer.get("email") if isinstance(reviewer, dict) else None
        identity_refusal = finding_reviewer_identity_refusal(
            journal_root.parents[1],
            latest_finding,
            email if isinstance(email, str) else None,
        )
        check(
            identity_refusal is None,
            identity_refusal
            or "declared reviewer identity differs from the finding recorder's "
            "declared git identities",
        )

    verified = 0
    if latest_finding is not None:
        for artifact in cast(list[dict[str, str]], latest_finding["artifacts"]):
            reference = artifact["ref"]
            path = artifact_path(journal_root.parents[1], reference)
            if path is None:
                say(f"NOT VERIFIED: artifact {reference} does not resolve locally")
                continue
            verified += 1
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as error:
                check(False, f"artifact {reference} could not be read: {error}")
                continue
            check(
                digest == artifact["hash"],
                f"artifact {reference} matches its recorded sha256"
                if digest == artifact["hash"]
                else f"artifact {reference} does not match its recorded sha256",
            )
        check(
            verified > 0,
            "at least one finding artifact resolves under the journal project root",
        )

    say("NOT EXAMINED: pipeline attestation (findings lane has no pipeline)")
    say("NOT EXAMINED: candidate diff (findings lane has no candidate)")
    try:
        tampered = _sidecar_tampered_records(journal_root)
    except GateError as error:
        raise GateError(f"cannot examine journal history: {error}") from error
    check(
        not tampered,
        "evidence records are append-only"
        if not tampered
        else "append-only violation, records modified, deleted or renamed: "
        + ", ".join(tampered),
    )
    # load_task_status above reads every record from the journal working tree,
    # validates its shape, and projects the complete lifecycle.
    check(True, "added records are valid (journal working tree examined)")
    say("NOT EXAMINED: record-path collisions (findings lane has no candidate or base)")
    check(True, "task lifecycle records are consistent (journal working tree examined)")
    say("NOT EXAMINED: advisory leak scan (findings lane has no diff)")
    return GateReport(violations == 0, lines, "", finding_id or None)


def _run_git_bytes(project_root: Path, arguments: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GateError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        stdout = result.stdout.decode("utf-8", errors="replace")
        detail = stderr.strip() or stdout.strip()
        raise GateError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _run_git(project_root: Path, arguments: list[str]) -> str:
    stdout = _run_git_bytes(project_root, arguments)
    try:
        return stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        # git permits arbitrary non-NUL bytes in path names; a non-UTF-8
        # path is a controlled refusal, never a traceback.
        raise GateError(f"git produced non-UTF-8 output: {error}") from error


def _run_git_lossy(project_root: Path, arguments: list[str]) -> str:
    """Run git like ``_run_git``, decoding what a path may have spoiled.

    For the ``-z`` listings: NUL is the one byte git guarantees a path
    never carries, so the names arrive raw — bytes that are not UTF-8
    included, which a strict decode would refuse the whole run over even
    when the name is one the run never had to read. Undecodable bytes
    decode as low surrogates instead (``surrogateescape``): the name
    keeps its bytes for matching — the surrogate round-trips through
    ``os`` and back to git — and where the gate names it, a surrogate is
    a character the forgeable-text rule refuses, so ``say`` and
    ``GateError`` print it as its ``\\udcXX`` escape.
    """

    return _run_git_bytes(project_root, arguments).decode(
        "utf-8", errors="surrogateescape"
    )


def _resolve_commit(project_root: Path, reference: str) -> str:
    resolved = _run_git(
        project_root, ["rev-parse", "--verify", f"{reference}^{{commit}}"]
    ).strip()
    if len(resolved) != 40:
        raise GateError(f"reference did not resolve to a full SHA: {reference}")
    return resolved


def _changed_with_status(
    project_root: Path, merge_base: str, commit: str
) -> list[tuple[str, str]]:
    """Return (status, path) pairs for the range.

    A rename decomposes into a deletion of its source and an addition of
    its destination, so moving a file out of a protected location is
    seen as removing it there; a copy contributes only the addition.
    """

    output = _run_git_lossy(
        project_root, ["diff", "--name-status", "-z", f"{merge_base}..{commit}"]
    )
    tokens = [token for token in output.split("\0") if token]
    pairs: list[tuple[str, str]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        if status[0] in "RC":
            if index + 2 >= len(tokens):
                raise GateError("unparseable rename entry in candidate diff")
            if status[0] == "R":
                pairs.append(("D", tokens[index + 1]))
            pairs.append(("A", tokens[index + 2]))
            index += 3
        else:
            if index + 1 >= len(tokens):
                raise GateError("unparseable entry in candidate diff")
            pairs.append((status[0], tokens[index + 1]))
            index += 2
    return pairs


def _is_record_path(path: str) -> bool:
    return path.startswith(_JOURNAL_PREFIX) and "/records/" in path


def _record_type_from_record_path(path: str) -> str:
    """Derive a record type from its journal filename without reading it."""

    return (
        path.rsplit("/", maxsplit=1)[-1]
        .removesuffix(".json")
        .rsplit("-", maxsplit=1)[-1]
    )


def _is_append_only_evidence_path(path: str) -> bool:
    """Whether *path* is immutable record or artifact evidence."""

    return _is_record_path(path) or (
        path.startswith(f"{_JOURNAL_PREFIX}tasks/") and "/artifacts/" in path
    )


def _sidecar_history_tampering(project_root: Path, journal_path: str) -> list[str]:
    """Return records that a sidecar commit modified, deleted or renamed.

    The working-tree check below only sees what is not yet committed — and a
    committed journal is the only state in which its history proves anything
    (ADR-0008 Decision 7: append-only *within the sidecar's own history*). A
    substitution that landed in a commit would otherwise be invisible, and the
    transcript would report append-only integrity it never examined.
    """

    # A sidecar with no commits yet is an ordinary state — the first records are
    # written before the first commit — and git log refuses on an unborn HEAD.
    # No history is not a failure to read history; anything else still raises.
    # Whether history exists is asked positively, not read out of an error
    # message: matching text would make a corrupt repository look like an empty
    # one, and reporting append-only integrity we never examined is precisely
    # what this check exists to prevent. rev-list on a repository with no
    # commits succeeds and prints nothing; on a broken one it fails, and that
    # failure propagates.
    if not _run_git(project_root, ["rev-list", "-n", "1", "--all"]).strip():
        return []
    output = _run_git_lossy(
        project_root,
        [
            "log",
            # -m --first-parent: without it git shows no diff for a merge
            # commit, so a record substituted during a merge — content in
            # neither parent — is invisible while every ordinary commit is
            # seen. Verified: an evil merge scores zero without these flags.
            "-m",
            "--first-parent",
            # T: a file replaced by a symlink (or the reverse) is a change to
            # the evidence as much as an edit is.
            "--diff-filter=MDRT",
            "--name-only",
            "--format=",
            # -z: NUL-separated, as the gate's other listings are — git
            # C-quotes a name with a non-ASCII or control character
            # otherwise, and a quoted name is one the evidence-path test
            # cannot see: tampering the check never found.
            "-z",
            "--",
            journal_path,
        ],
    )
    return sorted(
        {
            token
            for token in output.split("\0")
            if token and _is_append_only_evidence_path(token)
        }
    )


def _sidecar_tampered_records(journal_root: Path) -> list[str]:
    """Return sidecar records changed other than by addition.

    Both the working tree and the committed history: a record rewritten before
    a commit and one rewritten by a commit are the same violation, and only the
    pair of checks sees both.
    """

    project_root = journal_root.parents[1]
    output = _run_git_lossy(
        project_root,
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            str(journal_root.relative_to(project_root)),
        ],
    )
    tokens = output.split("\0")
    tampered: set[str] = set()
    index = 0
    while index < len(tokens):
        entry = tokens[index]
        if not entry:
            index += 1
            continue
        status = entry[:2]
        paths = [entry[3:]]
        if "R" in status or "C" in status:
            index += 1
            if index < len(tokens) and tokens[index]:
                paths.append(tokens[index])
        if status != "??" and "A" not in status:
            tampered.update(
                path for path in paths if _is_append_only_evidence_path(path)
            )
        index += 1
    tampered.update(
        _sidecar_history_tampering(
            project_root, str(journal_root.relative_to(project_root))
        )
    )
    return sorted(tampered)


def _range_emails(project_root: Path, merge_base: str, commit: str) -> set[str]:
    output = _run_git(
        project_root, ["log", "--format=%ae%n%ce", f"{merge_base}..{commit}"]
    )
    return {line.strip() for line in output.splitlines() if line.strip()}


def _range_commits(project_root: Path, merge_base: str, commit: str) -> set[str]:
    """The full ids of the candidate range's commits.

    The same ``merge-base..candidate`` enumeration the writer-emails
    comparison uses — the independence rules ask which sessions produced
    commits of this range, so the set is of ids rather than identities.
    """

    output = _run_git(project_root, ["log", "--format=%H", f"{merge_base}..{commit}"])
    return {line.strip() for line in output.splitlines() if line.strip()}


def _extension_name(path: str) -> str | None:
    """Return the name for a manifest at one of its two allowed locations.

    The file form is ``.agentmarshal/extensions/<name>.toml``; the directory
    form's manifest is ``.agentmarshal/extensions/<name>/manifest.toml``.
    Nothing else under ``<name>/`` names a manifest — a deleted ``bin/`` or
    ``lock/`` file is not the extension's removal.
    """

    if not path.startswith(_EXTENSIONS_PREFIX):
        return None
    relative = path.removeprefix(_EXTENSIONS_PREFIX)
    name: str | None = None
    if relative.endswith("/manifest.toml"):
        name = relative.removesuffix("/manifest.toml")
    elif "/" not in relative and relative.endswith(".toml"):
        name = relative.removesuffix(".toml")
    return name if name and "/" not in name else None


def _tree_entry(project_root: Path, tree_ref: str, path: str) -> tuple[str, str] | None:
    """Return the ``(mode, kind)`` of *path*'s entry in *tree_ref*, or None.

    A literal pathspec: a bracket or a star in an extension's name is a
    character, not a glob.
    """

    entry = _run_git_lossy(
        project_root, ["ls-tree", "-z", tree_ref, "--", f":(literal){path}"]
    )
    if not entry.strip("\0"):
        return None
    mode, kind = entry.split("\0", 1)[0].split(" ")[:2]
    return mode, kind


def _manifest_blob_present(
    project_root: Path, tree_ref: str, name: str, path: str
) -> bool:
    """Whether *path* holds a manifest blob in *tree_ref*; refusals raise.

    The entry's mode is part of the answer — a symlink is refused here as
    the filesystem reader refuses one, and so is an entry that is not a
    file.
    """

    entry = _tree_entry(project_root, tree_ref, path)
    if entry is None:
        return False
    mode, kind = entry
    if mode == "120000":
        raise ExtensionManifestError(
            f"refusing to read extension manifest {name!r} through a symlink: "
            f"{tree_ref}:{path}"
        )
    if kind != "blob":
        raise ExtensionManifestError(
            f"extension manifest {name!r} at {tree_ref}:{path} is a {kind}, not a file"
        )
    return True


def _manifest_from_tree(
    project_root: Path, tree_ref: str, name: str
) -> ExtensionManifest:
    """Read a manifest blob from ``tree_ref`` and use the shared validator.

    An extension lives at ``.agentmarshal/extensions/<name>.toml`` — the
    file form — or at ``.agentmarshal/extensions/<name>/manifest.toml`` —
    the directory form of ADR-0013 decision 9 — and the tree read applies
    the rules the working-tree reader applies, said in tree terms: a
    manifest in both places is refused naming both; a link entry at the
    manifest path, or at the ``<name>`` directory itself, is refused as a
    link — in a tree a link resolves to nothing, so the directory entry is
    examined before absence is decided; an entry at a manifest path that
    is not a blob is refused as not a file; and the directory form holds
    only a schema-2 manifest.
    """

    file_path = extension_manifest_path(name)
    directory_path = extension_directory_manifest_path(name)
    container = directory_path.rsplit("/", maxsplit=1)[0]
    file_source = f"{tree_ref}:{file_path}"
    directory_source = f"{tree_ref}:{directory_path}"
    # `source` tracks the path being probed so a git failure is wrapped
    # naming the path the run could not read.
    source = file_source
    try:
        file_present = _manifest_blob_present(project_root, tree_ref, name, file_path)
        source = f"{tree_ref}:{container}"
        container_entry = _tree_entry(project_root, tree_ref, container)
        if container_entry is not None and container_entry[0] == "120000":
            raise ExtensionManifestError(
                f"refusing to read extension manifest {name!r} through a "
                f"symlink: {source}"
            )
        directory_present = (
            container_entry is not None
            and container_entry[1] == "tree"
            and _manifest_blob_present(project_root, tree_ref, name, directory_path)
        )
        if file_present and directory_present:
            raise ExtensionManifestError(
                f"extension {name!r} has a manifest in both the file and the "
                f"directory form: {file_source} and {directory_source}"
            )
        if not file_present and not directory_present:
            raise ExtensionManifestMissing(
                f"extension manifest {name!r} is missing: {file_source}"
            )
        source = file_source if file_present else directory_source
        text = _run_git(project_root, ["show", source])
    except GateError as error:
        # A blob git cannot show as UTF-8 text, or a tree entry that cannot
        # be listed, is a manifest the gate cannot read — a refusal line,
        # not an aborted run.
        raise ExtensionManifestError(
            f"cannot read extension manifest {name!r} at {source}: {error}"
        ) from error
    manifest = parse_extension_manifest_text(text, name, source)
    if directory_present and manifest.schema != 2:
        raise ExtensionManifestError(
            "the directory form requires a manifest of schema 2; "
            f"{name!r} declares schema {manifest.schema}: {source}"
        )
    return manifest


def markers_from_config(project_root: Path) -> tuple[str, ...]:
    """Read ``leak_scan.private_markers`` from a project's working config.

    Used where the trusted side is a working tree rather than a git tree: a
    sidecar's own repository is the operator's private one, so its checked-out
    configuration is the trusted source, while the content being scanned comes
    from the host.
    """

    try:
        data = read_project_file(project_file_path(project_root))
    except (OSError, ValueError) as error:
        raise GateError(f"cannot read project configuration: {error}") from error
    return private_markers_from_project(data)


def markers_from_tree(project_root: Path, tree_ref: str) -> tuple[str, ...]:
    """Read ``leak_scan.private_markers`` from ``project.json`` at a git tree.

    The config is read from a **trusted** tree (the merge base), never the
    candidate working tree, so a candidate cannot weaken its own leak-scan by
    editing ``project.json`` in the very change being scanned — the same
    reason the contract is read from the base side.

    A tree that genuinely has no ``project.json`` yields no markers (the scan
    still runs its built-in secret signatures). That is distinguished from a
    real failure — an unknown ref, or a ``git show`` error on a file that
    does exist — which propagates as :class:`GateError` so the caller can
    surface a visible skip warning instead of silently dropping configured
    markers. A malformed config likewise raises (``ValueError`` /
    :class:`CaptureError`).
    """

    # `ls-tree` distinguishes an absent path (empty output, exit 0) from a
    # bad ref (non-zero -> GateError); only genuine absence returns no markers.
    listing = _run_git(
        project_root, ["ls-tree", "--name-only", tree_ref, "--", PROJECT_CONFIG_RELPATH]
    )
    if not listing.strip():
        return ()
    project_json = _run_git(
        project_root, ["show", f"{tree_ref}:{PROJECT_CONFIG_RELPATH}"]
    )
    data = json.loads(project_json.lstrip("\ufeff"))
    if not isinstance(data, dict):
        raise ValueError("project.json is not a JSON object")
    return private_markers_from_project(data)


def _declared_actor_ids(
    project_root: Path, journal_root: Path, merge_base: str, sidecar: bool
) -> frozenset[str] | None:
    """The actor ids the project's actors table declares, read trusted-side.

    Declared-ness feeds a refusal, so the table is read where the candidate
    cannot edit it — the merge-base tree in the embedded placement, the
    sidecar repository's own working file in the other — the same split the
    contract and the leak-scan markers take. An actor is a key of the
    ``actors`` section, not a value of the identity mapping, so a key with
    no ``git_identities`` counts as declared — the same test
    ``reviewer_actor_note`` runs at submit time. ``None`` reports that the
    table could not be read at all: a rule needing it then says so rather
    than reading every actor as undeclared.
    """

    try:
        if sidecar:
            data = read_project_file(project_file_path(journal_root.parents[1]))
        else:
            # As markers_from_tree: `ls-tree` tells an absent config from a
            # failure; only genuine absence reads as an empty table.
            listing = _run_git(
                project_root,
                [
                    "ls-tree",
                    "--name-only",
                    merge_base,
                    "--",
                    PROJECT_CONFIG_RELPATH,
                ],
            )
            if not listing.strip():
                return frozenset()
            data = json.loads(
                _run_git(
                    project_root,
                    ["show", f"{merge_base}:{PROJECT_CONFIG_RELPATH}"],
                ).lstrip("\ufeff")
            )
    except (OSError, ValueError, GateError):
        return None
    if not isinstance(data, dict):
        return None
    actors = data.get("actors")
    if not isinstance(actors, dict):
        return frozenset()
    return frozenset(actor for actor in actors if isinstance(actor, str))


# The reviewer field each declared independence rule compares, and the
# session field it is compared against. `reviewer-not-writer` is absent:
# it is the gate's existing identity check, run for every candidate whether
# or not the header names it.
_RULE_REVIEWER_FIELD = {
    "distinct-vendor": "vendor",
    "distinct-model": "model",
    "distinct-actor": "actor",
}
_RULE_SESSION_FIELD = {
    "distinct-vendor": "usage.provider",
    "distinct-model": "model",
    "distinct-actor": "actor",
}


def _session_independence_value(rule: str, session: dict[str, object]) -> str | None:
    """The session value ``rule`` compares, or None where it is absent."""

    if rule == "distinct-vendor":
        usage = session.get("usage")
        value = usage.get("provider") if isinstance(usage, dict) else None
    else:
        value = session.get(_RULE_SESSION_FIELD[rule])
    return value if isinstance(value, str) and value.strip() else None


def _judge_independence_rule(
    rule: str,
    reviewer: object,
    sessions: list[dict[str, object]],
    declared_actors: frozenset[str] | None,
) -> tuple[bool | None, str]:
    """Judge one declared independence rule against the in-range sessions.

    Returns ``(None, reason)`` where the rule cannot be judged — no
    implementer session carries a commit in the range, a compared field is
    absent on the review or on a session, or an actor is not declared — the
    caller prints the reason on a NOT CHECKED line. Otherwise it returns
    ``(verdict, message)``. A rule holds only when it holds against every
    session; one equal pair fails it, and a demonstrated failure outranks an
    unjudgeable session — reporting it is never the overclaim that passing
    over an unseen session would be.
    """

    if not sessions:
        return (
            None,
            "no implementer session carries a commit in the candidate's range",
        )
    reviewer_field = _RULE_REVIEWER_FIELD[rule]
    reviewer_value = (
        reviewer.get(reviewer_field) if isinstance(reviewer, dict) else None
    )
    if not isinstance(reviewer_value, str) or not reviewer_value.strip():
        return None, f"the latest review carries no 'reviewer.{reviewer_field}'"
    declared: frozenset[str] | None = None
    if rule == "distinct-actor":
        if declared_actors is None:
            return None, "the project's actors table could not be read"
        # Both labels must be declared for the comparison to say anything:
        # an actor is a declared label, and a pass or fail over a label no
        # actors table vouches for would be a claim the journal cannot
        # stand behind (ADR-0006, ADR-0022 section 3).
        if reviewer_value not in declared_actors:
            return (
                None,
                f"the latest review's actor {reviewer_value!r} is not a declared actor",
            )
        declared = declared_actors
    session_field = _RULE_SESSION_FIELD[rule]
    label = reviewer_field
    first_gap: str | None = None
    for session in sessions:
        session_id = session.get("id")
        session_label = (
            f"implementer session {session_id}"
            if isinstance(session_id, str)
            else "an implementer session"
        )
        session_value = _session_independence_value(rule, session)
        if session_value is None:
            if first_gap is None:
                first_gap = f"{session_label} carries no '{session_field}'"
            continue
        if declared is not None and session_value not in declared:
            if first_gap is None:
                first_gap = (
                    f"{session_label}'s actor {session_value!r} is not a declared actor"
                )
            continue
        # Vendor and model keep the identity check's normalisation — a
        # reviewer controls its own string and must not evade the
        # comparison through casing. An actor id is an exact label — the
        # actors table keys it exactly, and `status` compares it against a
        # declared list exactly — so `distinct-actor` compares without it:
        # two actor ids differing only in case are two declared actors.
        equal = (
            session_value == reviewer_value
            if rule == "distinct-actor"
            else session_value.strip().casefold() == reviewer_value.strip().casefold()
        )
        if equal:
            return (
                False,
                f"declared reviewer {label} {reviewer_value!r} equals "
                f"{session_label}'s declared {label} {session_value!r}",
            )
    if first_gap is not None:
        return None, first_gap
    return (
        True,
        f"declared reviewer {label} {reviewer_value!r} differs from every "
        f"in-range implementer session's declared {label}",
    )


def _extension_names_at_tree(
    project_root: Path, tree_ref: str
) -> tuple[frozenset[str], frozenset[str]]:
    """The shared extension names a tree declares: (every name, directory-form).

    The enumeration half of ``stages.py``'s base read, living beside the
    manifest-at-tree helpers it uses so the gate's operational lane can
    name the shared extensions at the merge base without loading
    manifests: a symlink at ``.agentmarshal``, at ``extensions/`` or at
    an extension's ``<name>`` is refused as a link; a missing or
    non-tree ``extensions/`` is simply no extensions; a ``<name>.toml``
    blob is the file form — a shared extension that declares no
    directory, though a switches entry may still name it.
    """

    agentmarshal_entry = _tree_entry(project_root, tree_ref, ".agentmarshal")
    if agentmarshal_entry is not None and agentmarshal_entry[0] == "120000":
        raise ExtensionManifestError(
            f"refusing to read extensions through a symlink: {tree_ref}:.agentmarshal"
        )
    extensions_entry = _tree_entry(
        project_root, tree_ref, _EXTENSIONS_PREFIX.removesuffix("/")
    )
    if extensions_entry is not None and extensions_entry[0] == "120000":
        raise ExtensionManifestError(
            "refusing to read extensions through a symlink: "
            f"{tree_ref}:{_EXTENSIONS_PREFIX.removesuffix('/')}"
        )
    if agentmarshal_entry is None or agentmarshal_entry[1] != "tree":
        return frozenset(), frozenset()
    if extensions_entry is None or extensions_entry[1] != "tree":
        return frozenset(), frozenset()
    listing = _run_git_lossy(
        project_root, ["ls-tree", "-z", tree_ref, "--", _EXTENSIONS_PREFIX]
    )
    names: set[str] = set()
    directory_names: set[str] = set()
    for item in listing.split("\0"):
        if not item:
            continue
        meta, _, path = item.partition("\t")
        fields = meta.split(" ")
        mode, kind = fields[0], fields[1]
        basename = path.rsplit("/", maxsplit=1)[-1]
        if kind == "tree":
            directory_names.add(basename)
            names.add(basename)
        elif mode == "120000":
            raise ExtensionManifestError(
                f"refusing to read extension {basename!r} through a symlink: "
                f"{tree_ref}:{path}"
            )
        elif basename.endswith(".toml") and basename != ".toml":
            names.add(basename.removesuffix(".toml"))
    return frozenset(names), frozenset(directory_names)


def _operational_contract(
    project_root: Path, task_id: str, merge_base: str, resolved_commit: str
) -> ContractHeader | None:
    """The contract the operational lane is judged under, or ``None``.

    Read from the merge-base tree when the task exists there; when the
    candidate itself opens the task — no ``contract.md`` at the base —
    from the candidate's tree, mirroring how the journal-only lane
    treats an opening transaction. The lane bounds the diff either way,
    so a contract the candidate publishes cannot widen what the lane
    admits. An absent contract, a link or non-blob at its path, a blob
    git cannot read, or text the contract parser refuses each return
    ``None``: not operational, and the regular lane reports the same
    contract's own refusal.
    """

    contract_path = f"{_JOURNAL_PREFIX}tasks/{task_id}/contract.md"
    tree_ref = merge_base
    entry = _tree_entry(project_root, merge_base, contract_path)
    if entry is None:
        tree_ref = resolved_commit
        entry = _tree_entry(project_root, resolved_commit, contract_path)
    if entry is None or entry[0] == "120000" or entry[1] != "blob":
        return None
    try:
        text = _run_git(project_root, ["show", f"{tree_ref}:{contract_path}"])
        return parse_contract_text(text, f"{tree_ref}:{contract_path}")
    except (GateError, JournalContractError):
        return None


def operational_candidate(
    project_root: Path,
    task_id: str,
    merge_base: str,
    resolved_commit: str,
    changes_with_status: list[tuple[str, str]],
) -> ContractHeader | None:
    """The contract an operational candidate's lane is judged under, or ``None``.

    ADR-0013 decision 17 — the lane a change takes when it only switches
    shared extensions: the diff carries ``.agentmarshal/switches.toml``
    and otherwise nothing outside ``.agentmarshal/journal/tasks/<task>/``
    — the task's own subtree, contract included — and the task's
    contract declares ``scope`` exactly that file. Anything else — a
    manifest, any configuration, code — is not operational and takes the
    lane it takes today. ``run_gate`` asks this only in the embedded
    placement; in a sidecar the lane is not offered. The switches
    file's entries are not inspected here: qualification is a property
    of the diff's shape and the contract, so a malformed file fails on
    the lane itself with the file and entry named.
    """

    task_prefix = f"{_JOURNAL_PREFIX}tasks/{task_id}/"
    carries_file = False
    for _status, path in changes_with_status:
        if path == SWITCHES_RELPATH:
            carries_file = True
        elif not path.startswith(task_prefix):
            return None
    if not carries_file:
        return None
    contract = _operational_contract(project_root, task_id, merge_base, resolved_commit)
    if contract is None or contract.scope != (SWITCHES_RELPATH,):
        return None
    return contract


def _switches_at_tree(
    project_root: Path, tree_ref: str, names: frozenset[str]
) -> dict[str, Switch]:
    """The switches a tree declares; a missing file is all-on.

    The candidate read of the operational lane, kept beside
    ``parse_switches``' caller so the file's own ref names every
    refusal: a link or a non-blob at the file's path is not a file —
    the same refusal ``stages.py``'s base read makes.
    """

    source = f"{tree_ref}:{SWITCHES_RELPATH}"
    entry = _tree_entry(project_root, tree_ref, SWITCHES_RELPATH)
    if entry is None:
        return {}
    mode, kind = entry
    if mode == "120000" or kind != "blob":
        raise SwitchesError(f"{source}: not a file")
    data = _run_git_bytes(project_root, ["show", source])
    return parse_switches(data, source, names)


def leak_scan_diff(
    project_root: Path, merge_base: str, commit: str
) -> tuple[str, list[str]]:
    """Return the candidate diff decoded per file, and the files it could not decode.

    The gate's advisory scan and the ``leak-scan`` command share this helper so
    the two cannot degrade differently: ``_run_git_bytes`` captures the diff as
    bytes and :func:`decode_diff_per_file` decodes one file section at a time,
    so a single file's non-UTF-8 bytes no longer discard the whole scan
    (proposal 026's fourth finding).

    Pin raw text patch output: ``--text`` forces content even for files a repo
    marks binary/non-diffable (otherwise git emits "Binary files differ" and
    the added content is never scanned); ``--no-textconv`` / ``--no-ext-diff``
    stop the repo's own diff drivers from rewriting or redacting what the
    scanner sees, which could hide a secret. The prefix flags fix the
    destination prefix the parser strips ("b/"): with diff.mnemonicPrefix the
    header reads "+++ c/…" and with diff.dstPrefix anything at all, and the
    suppression key would stop matching the project file silently. The flags
    win over all four config knobs (noprefix, mnemonicPrefix, srcPrefix,
    dstPrefix), which "-c diff.noprefix=false" alone does not.
    core.quotePath is left alone on purpose: a quoted path still decodes, and
    an unquoted one is escaped per file rather than skipping the whole scan.
    """

    raw = _run_git_bytes(
        project_root,
        [
            "diff",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            "--text",
            "--no-textconv",
            "--no-ext-diff",
            f"{merge_base}..{commit}",
        ],
    )
    return decode_diff_per_file(raw)


ATTESTATION_MODES = ("commit", "ci-required")


def run_gate(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    pipeline_sha: str | None,
    attestation: str = "commit",
    *,
    journal_root: Path | None = None,
    review_required: bool = True,
) -> GateReport:
    """Evaluate a merge candidate; fail closed on every violation.

    ``review_required`` says whether the caller is in a position to have a
    review at all. When it is false and the candidate has no review record,
    the two review-bound checks are reported as not examined rather than
    refused; a candidate that has one is judged by it either way.

    ``attestation`` selects how the pipeline-attestation check is
    satisfied. ``commit`` (the default, Variant 1) requires
    ``pipeline_sha`` to equal the candidate commit — the invoker attests a
    green pipeline. ``ci-required`` (Variant 2) delegates attestation to
    the provider's required checks: the gate runs as one required check
    and the provider blocks the merge until the test check is also green,
    so the gate does not self-attest. It is only sound when the provider
    independently requires the test check for merge.
    """

    if attestation not in ATTESTATION_MODES:
        raise GateError(
            f"unknown attestation mode: {attestation!r} "
            f"(expected one of {', '.join(ATTESTATION_MODES)})"
        )

    lines: list[str] = []
    violations = 0

    def say(message: str) -> None:
        # As in the findings lane: the finished line is escaped, so the
        # record and contract values interpolated into it can neither add a
        # line nor reorder what is read, and a line added later cannot
        # forget the escape.
        lines.append(escape_for_display(message))

    def check(passed: bool, message: str) -> None:
        nonlocal violations
        if passed:
            say(f"PASS: {message}")
        else:
            violations += 1
            say(f"FAIL: {message}")

    sidecar = journal_root is not None
    if journal_root is None:
        journal_root = project_root / ".agentmarshal" / "journal"
    # load_task_status validates that the post-candidate journal is
    # well-formed (single opened record, no record after a terminal one,
    # contract id matches); it raises on an inconsistent projection.
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise GateError(str(error)) from error

    review_not_examined = False
    resolved_review: str | None = None
    resolved_commit = _resolve_commit(project_root, commit)
    base_commit = _resolve_commit(project_root, base)
    merge_base = _run_git(
        project_root, ["merge-base", base_commit, resolved_commit]
    ).strip()
    # One listing defines every path the candidate touches. In particular, the
    # status helper expands a rename to its deleted source and added destination;
    # the scope check, lane choice and empty-range refusal must all see both.
    changes_with_status = _changed_with_status(
        project_root, merge_base, resolved_commit
    )
    changed = list(dict.fromkeys(path for _status, path in changes_with_status))
    if not changed:
        raise GateError("candidate range contains no changes")

    # NUL-separated, as the diff listings are: git C-quotes a path with a
    # non-ASCII or control character otherwise, and a quoted name never
    # equals the raw name the candidate's diff returns — a record-path
    # collision the check could not see.
    base_tree = {
        path
        for path in _run_git_lossy(
            project_root, ["ls-tree", "-r", "--name-only", "-z", base_commit]
        ).split("\0")
        if path
    }

    # The candidate's per-path change statuses also drive the measurements
    # lane below and the append-only / validity checks later. A rename
    # decomposes into a deletion plus an addition, so a move is never seen as a
    # pure addition.
    # A removal is a candidate that deletes a base-side manifest (ADR-0010
    # D5). In a sidecar the manifest lives in the sidecar, not in the host's
    # history, so a host path deletion says nothing about this journal's
    # extensions; how a sidecar removal is recognised awaits an amendment to
    # ADR-0010, and until then no removal line prints there.
    deleted_extensions = (
        []
        if sidecar
        else sorted(
            {
                name
                for status, path in changes_with_status
                if status == "D" and (name := _extension_name(path)) is not None
            }
        )
    )
    evidence_changes = [
        (status, path)
        for status, path in changes_with_status
        if _is_append_only_evidence_path(path)
    ]
    record_changes = [
        (status, path) for status, path in changes_with_status if _is_record_path(path)
    ]
    added_records = [path for status, path in record_changes if status == "A"]
    if sidecar:
        # One rule, applied once: in a sidecar no host path is ever a journal
        # path. The evidence lives in the sidecar and the candidate is a host
        # change, so a host that keeps an .agentmarshal/ of its own must not
        # drive record validity, path collisions or duplicate-opened detection
        # — those would decide this task from a different journal's records
        # (ADR-0008 Decision 2). Carving out one check at a time left the rest
        # reading host paths as evidence, which is how this was wrong twice.
        evidence_changes = []
        record_changes = []
        added_records = []
        base_tree = {path for path in base_tree if not path.startswith(_JOURNAL_PREFIX)}
    journal_only = all(path.startswith(_JOURNAL_PREFIX) for path in changed)
    if sidecar:
        # The deterministic lane exists because a journal-only change carries no
        # work to review. In a sidecar the evidence lives elsewhere, so a host
        # candidate is work whatever paths it touches — and a host that keeps a
        # journal of its own would otherwise reach the lane and skip scope,
        # review and independence on an unreviewed change.
        journal_only = False
    # ADR-0013 decision 17's lane is offered only in the embedded placement: in
    # a sidecar a host diff spelling the same paths is work like any other.
    # A journal-only candidate cannot carry the switches file, so asking the
    # predicate then would only spend git reads.
    operational_contract = (
        operational_candidate(
            project_root, task_id, merge_base, resolved_commit, changes_with_status
        )
        if not sidecar and not journal_only
        else None
    )

    # "Open" is decided from the base tree, never the candidate: opening,
    # implementation and completion candidates all merge onto a task that
    # is not yet closed there, so a legitimate open->terminal completion
    # passes while work merged onto an already-closed task is refused.
    task_records_prefix = f"{_JOURNAL_PREFIX}tasks/{task_id}/records/"
    task_dir_prefix = f"{_JOURNAL_PREFIX}tasks/{task_id}/"
    # Closed-ness is the *latest* lifecycle record at base, not the presence of
    # a terminal one: a task may be reopened after completion (CR-067), and a
    # check that stopped at "a -completed.json exists" would refuse every
    # candidate on a task the projection calls open. Record identifiers are
    # monotonic and lead the file name, so the latest is the greatest name and
    # this stays a comparison over names — no record is read here.
    lifecycle_at_base = sorted(
        path
        for path in base_tree
        if path.startswith(task_records_prefix)
        and path.endswith(("-completed.json", "-abandoned.json", "-reopened.json"))
    )
    closed_at_base = bool(lifecycle_at_base) and not lifecycle_at_base[-1].endswith(
        "-reopened.json"
    )
    if sidecar:
        # The host carries no journal, so lifecycle_at_base is empty there and
        # this check would assert "not closed" about every task, including ones
        # the sidecar journal projects as done — a false PASS in a transcript
        # whose whole purpose is to not overstate. The journal is not versioned
        # alongside the host, so its own projection is the only truthful
        # source; if the host happens to be an AgentMarshal project of its own,
        # its records belong to a different journal entirely (ADR-0008
        # Decision 2) and must not decide anything here.
        closed_at_base = task.state != "open"
        lifecycle_at_base = []
    # A task closed at base still admits only the record types its projection
    # admits after that terminal state. Every candidate change remains an
    # addition in this task's own subtree: a modification or deletion of an
    # existing file (contract.md, an artifact, anything) cannot be authorized
    # by appended evidence.
    # Only a closed task has a terminal state to ask about; when the latest
    # lifecycle record is a reopening the task is open and there is none.
    terminal_state_at_base = (
        projected_state_of(_record_type_from_record_path(lifecycle_at_base[-1]))
        if closed_at_base and lifecycle_at_base
        else None
    )
    added_record_types = [_record_type_from_record_path(path) for path in added_records]
    admitted_records_only = (
        bool(added_records)
        and all(
            status == "A" and path.startswith(task_dir_prefix)
            for status, path in changes_with_status
        )
        and terminal_state_at_base is not None
        and all(
            path.startswith(task_records_prefix)
            and record_type_is_admitted_after_terminal(
                record_type, terminal_state_at_base
            )
            for path, record_type in zip(added_records, added_record_types, strict=True)
        )
    )
    if not closed_at_base:
        say(f"PASS: task {task_id} is not closed at base")
    elif admitted_records_only:
        if "reopened" in added_record_types:
            say(
                "PASS: reopening append to a task completed at base "
                "(reopening is admitted post-terminal)"
            )
        else:
            say(
                "PASS: measurements-only append to a task closed at base "
                "(session records accrue post-terminal)"
            )
    else:
        check(
            False,
            f"task {task_id} is already closed at base (candidate state: {task.state})",
        )

    if journal_only:
        say("PASS: journal-only transaction (deterministic lane; review not required)")
    elif operational_contract is not None:
        contract = operational_contract
        say("PASS: operational transaction (operational lane; review not required)")
        # ADR-0013 decision 17's lane check: the candidate's file parses
        # against the shared extension names the base declares, and every
        # entry it adds or changes relative to the base names this task.
        # A removal is judged by the candidate having no entry — switching
        # an extension back on is as operational as switching it off — so
        # the base's entries decide nothing and a base file that cannot be
        # parsed is simply no entries.
        extension_names = _extension_names_at_tree(project_root, merge_base)[0]
        try:
            base_switches = _switches_at_tree(project_root, merge_base, extension_names)
        except SwitchesError:
            base_switches = {}
        candidate_source = f"{resolved_commit}:{SWITCHES_RELPATH}"
        candidate_switches: dict[str, Switch] | None
        try:
            candidate_switches = _switches_at_tree(
                project_root, resolved_commit, extension_names
            )
        except SwitchesError as error:
            check(False, str(error))
            candidate_switches = None
        if candidate_switches is not None:
            misnamed = sorted(
                name
                for name, switch in candidate_switches.items()
                if switch.task != task_id and base_switches.get(name) != switch
            )
            removed = [name for name in base_switches if name not in candidate_switches]
            detail = f"every added or changed switch entry names {task_id}"
            if removed:
                detail += (
                    f"; {len(removed)} removed "
                    f"{'entry' if len(removed) == 1 else 'entries'} allowed"
                )
            check(
                not misnamed,
                detail
                if not misnamed
                else f"{candidate_source}: switch entries naming another task: "
                + ", ".join(
                    f"{name!r} (task {candidate_switches[name].task})"
                    for name in misnamed
                ),
            )
        say("NOT EXAMINED: agreement (the operational lane requires none)")
        named_manifests: dict[str, ExtensionManifest] = {}
        for name in dict.fromkeys(contract.extensions):
            try:
                # The trusted side, as on the regular lane: the merge-base
                # tree the candidate cannot edit.
                named_manifests[name] = _manifest_from_tree(
                    project_root, merge_base, name
                )
            except ExtensionManifestError as error:
                check(False, f"named extension {name!r} manifest unreadable: {error}")
        named_documents = list(contract.documents)
        for name in contract.extensions:
            named_manifest = named_manifests.get(name)
            if named_manifest is not None:
                named_documents.extend(named_manifest.documents)
        named_documents = list(dict.fromkeys(named_documents))
        if named_documents:
            named = tuple(named_documents)
            touched_documents = sorted(
                {
                    path
                    for _status, path in changes_with_status
                    if scope_covers(named, path)
                }
            )
            check(
                bool(touched_documents),
                "named documents touched (" + ", ".join(touched_documents) + ")"
                if touched_documents
                else "named documents untouched: " + ", ".join(named_documents),
            )
        say("NOT EXAMINED: latest review (the operational lane requires none)")
        say("NOT EXAMINED: reviewer independence (the operational lane requires none)")
        for rule in contract.independence:
            if rule != "reviewer-not-writer":
                say(
                    f"NOT EXAMINED: independence rule {rule!r} "
                    "(the operational lane requires no review)"
                )
        if contract.reviewers:
            say(
                "NOT EXAMINED: declared reviewers "
                "(the operational lane requires no review)"
            )
        # The declared implementers check is not review-bound, so the lane
        # still runs it — the same in-range session rule and the same lines
        # as on the regular lane.
        if contract.implementers:
            records = read_records(journal_root, task_id)
            candidate_range = _range_commits(project_root, merge_base, resolved_commit)
            lane_sessions = [
                record
                for record in records
                if record.get("record_type") == "session"
                and record.get("commit") in candidate_range
            ]
            if not lane_sessions:
                say(
                    "NOT CHECKED: declared implementers (no implementer "
                    "session carries a commit in the candidate's range)"
                )
            else:
                nonmember_sessions = [
                    session
                    for session in lane_sessions
                    if session.get("actor") not in contract.implementers
                ]
                if nonmember_sessions:
                    check(
                        False,
                        "in-range implementer session actors outside the "
                        f"contract's declared implementers "
                        f"({', '.join(contract.implementers)}): "
                        + ", ".join(
                            f"{session.get('actor')!r} (implementer session "
                            f"{session.get('id')})"
                            for session in nonmember_sessions
                        ),
                    )
                else:
                    check(
                        True,
                        "every in-range implementer session's actor is in "
                        "the contract's declared implementers",
                    )
    else:
        # The contract is read from the merge-base tree: the trusted
        # side, so the candidate cannot widen its own scope.
        contract_path = f"{_JOURNAL_PREFIX}tasks/{task_id}/contract.md"
        if sidecar:
            # The host deliberately has no journal tree. The sidecar's projected
            # contract is the trusted side of this comparison; only the diff and
            # commit identities come from the host.
            contract = task.contract
        else:
            try:
                contract_text = _run_git(
                    project_root, ["show", f"{merge_base}:{contract_path}"]
                )
            except GateError:
                raise GateError(
                    f"contract for {task_id} is not present in the base tree; "
                    "the opening transaction must merge before implementation"
                ) from None
            try:
                contract = parse_contract_text(contract_text, contract_path)
            except JournalContractError as error:
                raise GateError(
                    f"contract in the base tree is invalid: {error}"
                ) from error
        manifests: dict[str, ExtensionManifest] = {}
        for name in dict.fromkeys((*contract.extensions, *deleted_extensions)):
            try:
                # The trusted side, as for the contract: the sidecar working
                # tree, or the merge-base tree the candidate cannot edit.
                loaded_manifest = (
                    read_extension_manifest(journal_root.parents[1], name)
                    if sidecar and journal_root is not None
                    else _manifest_from_tree(project_root, merge_base, name)
                )
            except ExtensionManifestError as error:
                if name in contract.extensions:
                    check(
                        False,
                        f"named extension {name!r} manifest unreadable: {error}",
                    )
                else:
                    # The candidate deleted a file at a manifest's path, but the
                    # base holds no valid manifest there: nothing declares a
                    # footprint, so there is no removal to verify — and no
                    # refusal the candidate could repair from its side.
                    say(
                        f"NOT EXAMINED: removal of extension {name!r} (base-side "
                        f"file is not a valid manifest: {error})"
                    )
                continue
            manifests[name] = loaded_manifest

        effective_scope = list(contract.scope)
        contributors: list[str] = []
        for name in dict.fromkeys(contract.extensions):
            named_manifest = manifests.get(name)
            if named_manifest is not None:
                effective_scope.extend(named_manifest.footprint)
                if named_manifest.footprint:
                    contributors.append(name)
        effective = tuple(effective_scope)
        outside = [path for path in changed if not scope_covers(effective, path)]
        # The embedded gate reads the contract from the base tree, so a
        # candidate cannot widen its own scope. A sidecar's contract is not in
        # the host's history at all — the candidate cannot reach it, but nor is
        # it pinned to a commit, so what is compared is the working copy. That
        # is a weaker provenance than embedded and the transcript says so
        # rather than letting the two lines read alike.
        if outside:
            scope_message = (
                f"paths outside contract scope: {', '.join(sorted(outside))}"
            )
            if contributors:
                scope_message += (
                    " (effective scope includes extensions: "
                    + ", ".join(contributors)
                    + ")"
                )
        else:
            scope_details: list[str] = []
            if sidecar:
                scope_details.append(
                    "contract read from the sidecar working tree, not pinned to a "
                    "commit"
                )
            if contributors:
                scope_details.append("extensions: " + ", ".join(contributors))
            scope_message = "diff within contract scope"
            if scope_details:
                scope_message += f" ({'; '.join(scope_details)})"
        check(not outside, scope_message)

        # ADR-0018 decision 2 / ADR-0022 section 6: a project whose rules
        # demand agreement makes the record a merge requirement. The
        # setting is read from the journal repository's project file —
        # the same working-tree read the changes_required threshold
        # makes — and an unreadable setting is reported on a WARN line
        # the way an unreadable threshold is: reported, neither refused
        # nor silently skipped.
        try:
            agreement_required = require_agreement(journal_root.parents[1])
        except (OSError, ValueError) as error:
            say(
                "WARN: agreement with the contract not examined "
                f"(contract.require_agreement unreadable: {error})"
            )
            agreement_required = False
        if agreement_required:
            # The hash an agreement must carry is of the contract the
            # gate judges against — the merge-base tree's text just
            # applied to the diff in the embedded placement, the sidecar
            # working tree's in the other — so a candidate's own contract
            # edit moves nothing. `contract_sha256` is the one way any
            # place that hashes a contract computes it.
            if sidecar:
                trusted_contract = journal_root / "tasks" / task_id / "contract.md"
                try:
                    judged_hash = contract_sha256(
                        trusted_contract.read_bytes(), str(trusted_contract)
                    )
                except (JournalContractError, OSError) as error:
                    raise GateError(f"cannot hash the contract: {error}") from error
            else:
                judged_hash = contract_sha256(
                    contract_text.encode("utf-8"),
                    f"{merge_base}:{contract_path}",
                )
            agreed = [
                cast(str, record["contract"])
                for record in task.records
                if record.get("record_type") == "agreement"
            ]
            if judged_hash in agreed:
                check(True, f"agreement recorded for contract {judged_hash[:7]}")
            elif agreed:
                check(
                    False,
                    f"an agreement exists for another hash ({agreed[-1][:7]}), "
                    f"not for the judged contract {judged_hash[:7]}; record "
                    "agreement with 'agentmarshal agree'",
                )
            else:
                check(
                    False,
                    f"no agreement recorded for contract {judged_hash[:7]}; "
                    "record agreement with 'agentmarshal agree'",
                )

        named_documents = list(contract.documents)
        for name in contract.extensions:
            named_manifest = manifests.get(name)
            if named_manifest is not None:
                named_documents.extend(named_manifest.documents)
        named_documents = list(dict.fromkeys(named_documents))
        if named_documents:
            named = tuple(named_documents)
            # From the status pairs: a rename decomposes into a deletion and
            # an addition there, and a deleted document counts as touched.
            touched_documents = sorted(
                {
                    path
                    for _status, path in changes_with_status
                    if scope_covers(named, path)
                }
            )
            check(
                bool(touched_documents),
                "named documents touched (" + ", ".join(touched_documents) + ")"
                if touched_documents
                else "named documents untouched: " + ", ".join(named_documents),
            )

        if deleted_extensions:
            # NUL-separated, as the diff listings are: git C-quotes a path
            # with a non-ASCII or control character otherwise, and a quoted
            # path is one the matcher cannot see — a false "removal complete".
            candidate_tree = {
                path
                for path in _run_git_lossy(
                    project_root,
                    ["ls-tree", "-r", "--name-only", "-z", resolved_commit],
                ).split("\0")
                if path
            }
            for name in deleted_extensions:
                removed_manifest = manifests.get(name)
                if removed_manifest is None:
                    # Its read failure is already a refusal above; without the
                    # trusted footprint there is no removal claim to make.
                    continue
                remaining = sorted(
                    path
                    for path in candidate_tree
                    if scope_covers(removed_manifest.footprint, path)
                )
                check(
                    not remaining,
                    f"extension {name!r} removal complete (no footprint paths remain)"
                    if not remaining
                    else f"extension {name!r} removal incomplete; footprint paths "
                    f"remain: {', '.join(remaining)}",
                )

        records = read_records(journal_root, task_id)
        reviews = [
            record
            for record in records
            if record.get("record_type") == "review"
            and record.get("reviewed_commit") == resolved_commit
        ]
        latest = reviews[-1] if reviews else None
        approved = latest is not None and latest.get("verdict") == "approved"
        acceptances = [
            record
            for record in records
            if record.get("record_type") == "acceptance"
            and record.get("accepted_commit") == resolved_commit
            and "findings" in record
        ]
        # The latest acceptance over findings, judged as it stands — never the
        # best-fitting one. A pause or operational acceptance carries no
        # `findings` and is not judged here: one written after an acceptance
        # over findings does not shadow it, and one standing alone satisfies
        # nothing. Searching a record set for whichever entry justifies a
        # merge is the opposite of what a merge authority does, and it would
        # let a stale or hand-written record be rescued by an older one. This
        # mirrors the review rule above: the last record wins and is then held
        # to the requirement.
        acceptance = acceptances[-1] if acceptances else None
        valid_acceptance: tuple[str, list[str]] | None = None
        if latest is not None and not approved and acceptance is not None:
            review_findings = cast(list[str], latest["findings"])
            acceptance_findings = cast(list[str], acceptance["findings"])
            if set(acceptance_findings) == set(review_findings):
                valid_acceptance = (
                    cast(str, acceptance["accepted_by"]),
                    acceptance_findings,
                )
        # The review the gate passed on is the one this verdict check just
        # judged — the approving latest review, or the non-approving one a
        # covering acceptance stood in for. The report carries its id so
        # `complete` reads the advisory findings of the review actually
        # judged: a review appended after the gate ran names a different id
        # and cannot change which dispositions are owed (ADR-0016
        # decision 1).
        if latest is not None and (approved or valid_acceptance is not None):
            resolved_review = cast(str, latest["id"])
        if valid_acceptance is not None:
            accepted_by, accepted_findings = valid_acceptance
            findings = ", ".join(accepted_findings)
            say(
                f"PASS: accepted over findings {findings} by {accepted_by}; "
                "not an approving review"
            )
        elif acceptance is not None and latest is not None and not approved:
            # An operator who has just recorded an acceptance and sees only
            # "latest review is approved: FAIL" learns nothing about why the
            # mechanism they used did not count. Findings can grow between an
            # acceptance and a gate run, and that is the usual reason.
            outstanding = sorted(set(cast(list[str], latest["findings"])))
            accepted = sorted(set(cast(list[str], acceptance["findings"])))
            check(
                False,
                f"acceptance of {resolved_commit[:12]} does not cover the latest "
                f"review's findings (outstanding: {', '.join(outstanding)}; "
                f"accepted: {', '.join(accepted)})",
            )
        elif latest is None and not review_required:
            # The caller has said it cannot yet have a review — a provider's CI
            # runs on a head that no review can name, because a review names a
            # commit only after that commit exists. Absence is reported as
            # absence; it is not a pass, and it is not a refusal either. A
            # candidate that *has* a review is judged below whatever the caller
            # asked for, so this cannot turn a refusal into a pass.
            review_not_examined = True
            say(
                "NOT EXAMINED: latest review "
                f"(no review record for {resolved_commit[:12]}, and this run "
                "was asked to judge without one)"
            )
            say(
                "NOT EXAMINED: reviewer independence (no review record to "
                "compare against the candidate's writers)"
            )
            # The declared rules are review-bound too: with no review to
            # judge them against, each reports not examined the same way.
            for rule in contract.independence:
                if rule != "reviewer-not-writer":
                    say(
                        f"NOT EXAMINED: independence rule {rule!r} (no "
                        "review record to compare against the implementer "
                        "sessions)"
                    )
            # So is the declared reviewers membership: with no review to
            # judge it reports not examined beside them.
            if contract.reviewers:
                say(
                    "NOT EXAMINED: declared reviewers (no review record to "
                    "judge the reviewer's actor against the list)"
                )
        else:
            check(
                approved,
                f"latest review of {resolved_commit[:12]} is approved"
                if latest is not None
                else f"no review record for {resolved_commit[:12]}",
            )

        # The declared implementers check and the declared independence
        # rules judge the same sessions — the session records whose
        # `commit` names a commit of the candidate's range — but only the
        # rules are review-bound: implementer membership is judged with no
        # review at all, so the set is computed ahead of the review-bound
        # block whenever a contract declaration needs it.
        declared_rules = [
            rule for rule in contract.independence if rule != "reviewer-not-writer"
        ]
        range_commits: set[str] = set()
        implementer_sessions: list[dict[str, object]] = []
        if contract.implementers or (latest is not None and declared_rules):
            range_commits = _range_commits(project_root, merge_base, resolved_commit)
            # An implementer session is a session record whose `commit`
            # names a commit of the candidate's range — the field records
            # the commit the implementer run produced.
            implementer_sessions = [
                record
                for record in records
                if record.get("record_type") == "session"
                and record.get("commit") in range_commits
            ]

        if latest is not None:
            reviewer = latest.get("reviewer")
            reviewer_email = (
                reviewer.get("email") if isinstance(reviewer, dict) else None
            )
            # Identity comparison is case-insensitive: the reviewer
            # controls its own identity string and must not evade the
            # check through casing.
            normalized_reviewer = (
                reviewer_email.strip().casefold()
                if isinstance(reviewer_email, str)
                else ""
            )
            writer_emails = {
                email.strip().casefold()
                for email in _range_emails(project_root, merge_base, resolved_commit)
            }
            check(
                bool(normalized_reviewer) and normalized_reviewer not in writer_emails,
                "declared reviewer identity differs from the candidate's "
                "declared writers",
            )

            # The contract's declared independence rules (ADR-0018
            # decision 3, ADR-0022 section 5): one line per declared rule
            # other than `reviewer-not-writer`, which is the check above —
            # the header naming it adds no second line. A rule the run
            # cannot judge reports NOT CHECKED rather than passing or
            # failing on nothing.
            if declared_rules:
                actors = (
                    _declared_actor_ids(project_root, journal_root, merge_base, sidecar)
                    if "distinct-actor" in declared_rules
                    else None
                )
                for rule in declared_rules:
                    judged, detail = _judge_independence_rule(
                        rule, reviewer, implementer_sessions, actors
                    )
                    if judged is None:
                        say(f"NOT CHECKED: independence rule {rule!r} ({detail})")
                    else:
                        check(judged, f"independence rule {rule!r} ({detail})")

            # ADR-0018 decision 3 and the operator decision of 2026-10-23:
            # a contract naming its reviewers gets the latest review's
            # `reviewer.actor` held against the list — by exact equality,
            # the way `status` compares an actor — and a review carrying
            # none is refused rather than unchecked: membership is what
            # the contract claims and without an actor it cannot be shown.
            if contract.reviewers:
                reviewer_actor = (
                    reviewer.get("actor") if isinstance(reviewer, dict) else None
                )
                if not isinstance(reviewer_actor, str) or not reviewer_actor.strip():
                    check(
                        False,
                        "the latest review carries no 'reviewer.actor'; "
                        "membership in the declared reviewers cannot be "
                        "shown — the review is recorded with --actor",
                    )
                elif reviewer_actor in contract.reviewers:
                    check(
                        True,
                        f"reviewer actor {reviewer_actor!r} is in the "
                        "contract's declared reviewers",
                    )
                else:
                    check(
                        False,
                        f"reviewer actor {reviewer_actor!r} is not in the "
                        f"contract's declared reviewers: "
                        f"{', '.join(contract.reviewers)}",
                    )

        # ADR-0018 decision 3: a contract naming its implementers gets the
        # actor of every in-range implementer session held against the
        # list by the same exact equality. The check is not review-bound —
        # the sessions are the candidate's, not the review's — so a
        # provider's CI run is judged too, and one holding no session in
        # the range reports NOT CHECKED rather than a pass over nothing.
        if contract.implementers:
            if not implementer_sessions:
                say(
                    "NOT CHECKED: declared implementers (no implementer "
                    "session carries a commit in the candidate's range)"
                )
            else:
                nonmembers = [
                    session
                    for session in implementer_sessions
                    if session.get("actor") not in contract.implementers
                ]
                if nonmembers:
                    check(
                        False,
                        "in-range implementer session actors outside the "
                        f"contract's declared implementers "
                        f"({', '.join(contract.implementers)}): "
                        + ", ".join(
                            f"{session.get('actor')!r} (implementer session "
                            f"{session.get('id')})"
                            for session in nonmembers
                        ),
                    )
                else:
                    check(
                        True,
                        "every in-range implementer session's actor is in "
                        "the contract's declared implementers",
                    )

    if attestation == "ci-required":
        say(
            "PASS: pipeline attestation delegated to the provider's required "
            "checks (the test check must also be required for merge)"
        )
    else:
        attested = pipeline_sha is not None and pipeline_sha == resolved_commit
        check(
            attested,
            f"pipeline attested for {resolved_commit[:12]}"
            if attested
            else "pipeline attestation missing or for a different commit",
        )

    # Evidence records are append-only for every candidate: any
    # modification, deletion or rename of an existing record rewrites
    # history at the merge boundary and is refused (ADR-0004). The record
    # changes were computed once above for the measurements lane.
    tampered = (
        _sidecar_tampered_records(journal_root)
        if sidecar
        else sorted(path for status, path in evidence_changes if status != "A")
    )
    check(
        not tampered,
        "evidence records are append-only"
        if not tampered
        else "append-only violation, records modified, deleted or renamed: "
        + ", ".join(tampered),
    )

    invalid: list[str] = []
    for path in added_records:
        try:
            content = _run_git(project_root, ["show", f"{resolved_commit}:{path}"])
            record = validate_record_content(Path(path).name, content)
        except (GateError, JournalRecordError) as error:
            invalid.append(f"{path}: {error}")
            continue
        expected_task = path.removeprefix(f"{_JOURNAL_PREFIX}tasks/").split("/", 1)[0]
        if record.get("task") != expected_task:
            invalid.append(f"{path}: record task does not match its directory")
    if invalid:
        check(False, f"invalid added records: {'; '.join(sorted(invalid))}")
    else:
        # In a sidecar there are no added records to validate: the candidate is
        # a host change and the host carries no journal. Saying so beats a PASS
        # that reports a check nothing exercised.
        check(
            True,
            "added records are valid (none examined: a host journal is not "
            "this journal's evidence)"
            if sidecar
            else "added records are valid",
        )

    # Collisions are checked against the merge target's tip: a record
    # path independently created on both sides would collide at merge.
    colliding = [
        path for status, path in evidence_changes if status == "A" and path in base_tree
    ]
    if colliding:
        check(
            False,
            f"record paths already exist on the base: {', '.join(sorted(colliding))}",
        )
    else:
        check(
            True,
            "no record-path collisions (none examined: the candidate adds no "
            "record to this journal)"
            if sidecar
            else "no record-path collisions with the base tree",
        )

    # A single record is valid in isolation yet corrupts the lifecycle
    # projection in aggregate — a second 'opened' record makes the task
    # unreadable after merge. Reject a task ending up with more than one
    # opened record across the target tip and the candidate's additions.
    def _task_of(path: str) -> str:
        return path.removeprefix(f"{_JOURNAL_PREFIX}tasks/").split("/", 1)[0]

    duplicate_opened: set[str] = set()
    affected_tasks = {_task_of(path) for path in added_records}
    for affected in affected_tasks:
        prefix = f"{_JOURNAL_PREFIX}tasks/{affected}/records/"
        opened_paths = {
            path
            for path in base_tree
            if path.startswith(prefix) and path.endswith("-opened.json")
        }
        opened_paths.update(
            path
            for path in added_records
            if path.startswith(prefix) and path.endswith("-opened.json")
        )
        if len(opened_paths) > 1:
            duplicate_opened.add(affected)
    check(
        not duplicate_opened,
        "task lifecycle records are consistent"
        if not duplicate_opened
        else "multiple opened records after merge for: "
        + ", ".join(sorted(duplicate_opened)),
    )

    # Proposal 035's disposition: `open` and `amend` are the events that must
    # arrive on the base in a transaction naming their own task, and a
    # transaction staging outside its task swept other tasks' records in —
    # more than a quarter of one adopter's journal transactions carried
    # them. The record stays valid evidence; what was wrong is which
    # transaction carried it, so this warns and refuses nothing. Only the
    # agreement events warn: a review or a session riding the wrong
    # transaction is bookkeeping noise the reporter's measurements call
    # the common case, not the one that cost a round.
    other_agreement_records: dict[str, set[str]] = {}
    for path in added_records:
        if not path.startswith(f"{_JOURNAL_PREFIX}tasks/"):
            continue
        record_type = _record_type_from_record_path(path)
        other = _task_of(path)
        if other != task_id and record_type in ("opened", "amendment"):
            other_agreement_records.setdefault(other, set()).add(record_type)
    if other_agreement_records:
        say(
            "WARN: candidate adds opened/amendment records of other tasks "
            "(the records stay valid evidence): "
            + "; ".join(
                f"{other} ({', '.join(sorted(kinds))})"
                for other, kinds in sorted(other_agreement_records.items())
            )
        )

    # Advisory leak-scan (ADR-0005, CR-041): best-effort and never
    # fail-closed. The scanner is heuristic — a clean result is not proof of
    # safety and a hit is not proof of a leak — so it warns but does not
    # block, and it never touches `violations`. Marker config is read from
    # the merge-base tree (the trusted side), so a candidate cannot weaken
    # its own scan; a malformed config or a git failure degrades to a warning
    # rather than refusing every merge. Only the candidate's added lines are
    # scanned, so accepted historical residuals already in the tree are not
    # re-flagged.
    try:
        # Markers come from the trusted side. In a sidecar that is the
        # operator's own journal repository, not the host: reading them from
        # the host means a host without a project.json silently disables the
        # operator's configured guard while the scan still reports success.
        markers = (
            markers_from_config(journal_root.parents[1])
            if sidecar and journal_root is not None
            else markers_from_tree(project_root, merge_base)
        )
        # The pinned diff comes back as text decoded file section by file
        # section (leak_scan_diff carries the flag rationale); a file whose
        # section did not decode is named in `undecodable`, and only a git
        # failure itself still skips the whole scan.
        diff_text, undecodable = leak_scan_diff(
            project_root, merge_base, resolved_commit
        )
        # The declaration that a marker may match is the project file the
        # markers were read from. In a sidecar that file is the sidecar's and
        # the diff is the host's, so no path in the diff is it, and nothing is
        # suppressed — which is the safe direction.
        leak_hits = scan_diff_for_leaks(
            diff_text,
            markers,
            config_path=PROJECT_CONFIG_RELPATH if not sidecar else "",
        )
    except (ValueError, CaptureError, GateError) as error:
        say(f"WARN: leak-scan skipped ({error})")
    else:
        if leak_hits:
            # ADR-0021 decisions 2 and 3: the task's `acknowledgement`
            # records bound to this commit mark the hits they name —
            # acknowledged, by whom and why — the same mark `leak-scan`
            # builds for the same hit through the same helper. The mark
            # rides the hit's own entry inside the bound the line
            # already had: an acknowledgement neither removes a hit nor
            # changes which are shown or their order, and one bound to
            # another commit marks nothing.
            acknowledgements = [
                record
                for record in task.records
                if record.get("record_type") == "acknowledgement"
                and record.get("commit") == resolved_commit
            ]
            marks = [
                _acknowledgement_mark(hit, acknowledgements, markers)
                for hit in leak_hits
            ]
            say(
                "WARN: possible leak in candidate additions "
                "(advisory, not blocking): "
                + render_leak_hits(leak_hits, limit=_LEAK_HIT_RENDER_LIMIT, marks=marks)
            )
        if undecodable:
            say(
                "WARN: leak-scan could not decode as UTF-8 "
                "(added bytes still searched): "
                + render_undecodable_files(
                    undecodable, markers, limit=_LEAK_HIT_RENDER_LIMIT
                )
            )

    if not journal_only and operational_contract is None:
        # ADR-0016 decision 4: the count of changes_required verdicts over
        # the whole task — every review of the task's candidates, whatever
        # commit it names; a review bound to a research finding (ADR-0009)
        # is not a candidate's return and is not counted — is the signal to
        # stop and revisit the contract. It closes the transcript and
        # reports; it is never a check, so it cannot add a violation,
        # change the exit status or refuse a merge. The journal-only lane
        # carries no work to review and prints nothing; the operational
        # lane has no review loop to signal and prints nothing either.
        count = sum(
            1
            for record in task.records
            if record.get("record_type") == "review"
            and record.get("verdict") == "changes_required"
            and record.get("reviewed_finding") is None
        )
        try:
            threshold = changes_required_threshold(journal_root.parents[1])
        except (OSError, ValueError) as error:
            # A malformed setting is reported on the line, not refused:
            # ProjectSettingsError is a ValueError, and the same catch
            # covers an unreadable or unparseable project.json.
            say(
                f"WARN: changes_required verdicts for {task_id}: {count} "
                f"(threshold unreadable: {error})"
            )
        else:
            if count >= threshold:
                say(
                    f"WARN: changes_required verdicts for {task_id}: {count} "
                    f"(threshold {threshold} reached — stop and revisit the "
                    "contract)"
                )
            else:
                say(
                    f"INFO: changes_required verdicts for {task_id}: {count} "
                    f"(threshold {threshold})"
                )

    return GateReport(
        passed=violations == 0,
        lines=lines,
        resolved_commit=resolved_commit,
        review_not_examined=review_not_examined,
        resolved_review=resolved_review,
    )
