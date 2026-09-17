"""Read-only launcher for trusted task reviews."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shlex
import string
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.artifacts import artifact_path
from agentmarshal.journal.brief import (
    append_amendment_history,
    render_amendment_history,
)
from agentmarshal.journal.contracts import parse_contract_text
from agentmarshal.journal.extensions import (
    ExtensionManifestMissing,
    read_extension_manifest,
)
from agentmarshal.journal.gate import finding_reviewer_identity_refusal

# The allowed verdicts have one definition, in records.py, which validation
# uses. The prompt renders that same set so it cannot drift from what the
# record layer will accept. (Module-private today; worth making public the
# next time records.py is opened.)
from agentmarshal.journal.records import (
    _REVIEW_VERDICTS as REVIEW_VERDICTS,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status
from agentmarshal.journal.submit_review import (
    ReviewSubmitError,
    submit_review,
)

_VERDICT_BEGIN = "AGENTMARSHAL_VERDICT_BEGIN"
_VERDICT_END = "AGENTMARSHAL_VERDICT_END"
_VERDICT_REQUIRED = {"reviewed_commit", "verdict", "findings"}
# advisory_findings is in the record schema and create_review_record accepts it;
# accepting it here is what makes it reachable through the protocol at all.
_VERDICT_OPTIONAL = {"advisory_findings"}
_DRY_RUN_COMMIT = "0" * 40
_DRY_RUN_CONTRACT = (
    "# Example task\n\nThis synthetic contract exercises the reviewer command."
)
_DRY_RUN_DIFF = "diff --git a/example.py b/example.py\n+print('example')\n"
_REVIEW_PROMPT = """You are a read-only code reviewer. Review the supplied task contract
and diff.
Do not modify files. Your reviewed commit is {commit}.

{named_material}{prose_instruction}

{verdict_protocol}

No other key is accepted.

Task contract:
{contract}

Diff:
{diff}
"""
_FINDING_REVIEW_PROMPT = (
    "You are a read-only reviewer. Review the supplied task contract\n"
    "and verified finding artifacts.\n"
    "Do not modify files. Your reviewed finding is {finding}.\n"
    "\n"
    "The named contract material is named, not supplied in this snapshot; only the "
    "pinned artifacts below were verified.\n"
    "\n"
    "{named_material}{prose_instruction}\n"
    "\n"
    "{verdict_protocol}\n"
    "\n"
    "No other key is accepted.\n"
    "\n"
    "Task contract:\n"
    "{contract}\n"
    "\n"
    "Finding artifacts:\n"
    "{artifacts}\n"
)


class ReviewLaunchError(Exception):
    """Raised when a read-only review cannot be launched or recorded."""


@dataclass(frozen=True)
class LaunchedReview:
    """A recorded review plus any successful-command diagnostics kept locally."""

    record_path: Path
    artifact_ref: str | None
    diagnostics_note: str | None


@dataclass(frozen=True)
class _VerifiedArtifact:
    """A locally resolved finding artifact, read and hashed before review."""

    reference: str
    digest: str
    path: Path
    content: bytes


def _named_contract_material(
    decisions: tuple[str, ...],
    documents: tuple[str, ...],
    absent_extensions: tuple[str, ...],
    *,
    absent_extensions_phrase: str,
) -> str:
    """Render the contract names shared by commit and finding review prompts."""

    if not (decisions or documents or absent_extensions):
        return ""
    lines = ["Named contract material:"]
    if decisions:
        lines.append("Decisions:")
        lines.extend(f"- {decision}" for decision in decisions)
        lines.append("A finding may cite a contradiction with a named decision.")
    if documents:
        lines.append("Documents:")
        lines.extend(f"- {document}" for document in documents)
    if absent_extensions:
        # A removal candidate deletes its manifest (ADR-0010 D5); the review
        # still launches, and the reviewer is told what is absent.
        lines.append(absent_extensions_phrase)
        lines.extend(f"- {name}" for name in absent_extensions)
    return "\n".join(lines) + "\n\n"


def _prose_instruction() -> str:
    """Return the shared request for human-readable finding explanations."""

    return (
        "For each blocking or advisory finding id you report, print one line of "
        "prose\n"
        "before the verdict block, naming what is wrong and where. The ids are labels\n"
        "for the machine; the prose is what a human will read."
    )


def _verdict_protocol(subject_field: str, subject_description: str) -> str:
    """Render the shared machine-verdict protocol for one review binding."""

    verdicts = ", ".join(sorted(REVIEW_VERDICTS))
    return (
        "At the end, print exactly one JSON object between lines containing "
        "exactly\n"
        f"{_VERDICT_BEGIN} and {_VERDICT_END}. The object must contain:\n"
        f"- {subject_field}: {subject_description}\n"
        f"- verdict: exactly one of: {verdicts}\n"
        "- findings: an array of unique finding-id strings; empty only for "
        '"approved",\n'
        "  and non-empty for every other verdict\n"
        "and may additionally contain:\n"
        "- advisory_findings: an array of unique non-blocking finding-id strings,\n"
        '  disjoint from findings; allowed with any verdict, including "approved"'
    )


def _run_git(project_root: Path, arguments: list[str]) -> str:
    """Run git and return its standard output, or raise a launcher error."""

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReviewLaunchError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _resolve_commit(project_root: Path, commit: str) -> str:
    resolved = _run_git(
        project_root, ["rev-parse", "--verify", f"{commit}^{{commit}}"]
    ).strip()
    if len(resolved) != 40:
        raise ReviewLaunchError(f"commit did not resolve to a full SHA: {commit}")
    return resolved


def _review_prompt(
    contract: str,
    diff: str,
    commit: str,
    *,
    decisions: tuple[str, ...] = (),
    documents: tuple[str, ...] = (),
    absent_extensions: tuple[str, ...] = (),
    amendment_history: str = "",
) -> str:
    """Build the reviewer prompt with its required machine-verdict protocol."""

    contract_material = append_amendment_history(contract, amendment_history)
    return _REVIEW_PROMPT.format(
        commit=commit,
        named_material=_named_contract_material(
            decisions,
            documents,
            absent_extensions,
            absent_extensions_phrase=(
                "Extensions whose manifest is absent in the reviewed tree:"
            ),
        ),
        prose_instruction=_prose_instruction(),
        verdict_protocol=_verdict_protocol(
            "reviewed_commit", "the exact reviewed commit SHA"
        ),
        contract=contract_material,
        diff=diff,
    )


def _finding_review_prompt(
    contract: str,
    finding: str,
    artifacts: tuple[_VerifiedArtifact, ...],
    unresolved_references: tuple[str, ...],
    *,
    decisions: tuple[str, ...] = (),
    documents: tuple[str, ...] = (),
    absent_extensions: tuple[str, ...] = (),
    amendment_history: str = "",
) -> str:
    """Build the distinct reviewer prompt for a hash-pinned finding."""

    artifact_sections: list[str] = []
    for artifact in artifacts:
        try:
            text = artifact.content.decode("utf-8")
        except UnicodeDecodeError:
            artifact_sections.append(
                f"Verified artifact: {artifact.reference}\n"
                f"Recorded sha256: {artifact.digest}\n"
                f"Content not embedded: the verified artifact is not valid UTF-8 "
                f"({len(artifact.content)} bytes)."
            )
        else:
            artifact_sections.append(
                f"Verified artifact: {artifact.reference}\n"
                f"Recorded sha256: {artifact.digest}\n"
                f"Content:\n{text}"
            )
    if unresolved_references:
        artifact_sections.append(
            "Unverified references (not fetched):\n"
            + "\n".join(f"- {reference}" for reference in unresolved_references)
        )

    return _FINDING_REVIEW_PROMPT.format(
        finding=finding,
        named_material=_named_contract_material(
            decisions,
            documents,
            absent_extensions,
            absent_extensions_phrase=(
                "Extensions whose manifest is absent in the project:"
            ),
        ),
        prose_instruction=_prose_instruction(),
        verdict_protocol=_verdict_protocol(
            "reviewed_finding", "the exact reviewed finding id"
        ),
        contract=append_amendment_history(contract, amendment_history),
        artifacts="\n\n".join(artifact_sections),
    )


def _names_model(template: str) -> bool:
    """Whether the template has a model field, however it is formatted."""

    try:
        fields = [token for _, token, _, _ in string.Formatter().parse(template)]
    except ValueError:
        return False
    return "model" in fields


def _dry_run_prompt() -> str:
    """Build the real reviewer prompt around a fixed, synthetic example."""

    return _review_prompt(_DRY_RUN_CONTRACT, _DRY_RUN_DIFF, _DRY_RUN_COMMIT)


def _unsupported_placeholder(template: str, known: set[str]) -> str | None:
    """Return the first formatter field not accepted by the template rule."""

    for _literal, token, specification, _conversion in string.Formatter().parse(
        template
    ):
        if token is None:
            continue
        if token not in known:
            return token
        if specification:
            nested = _unsupported_placeholder(specification, known)
            if nested is not None:
                return nested
    return None


def _reviewer_command(model: str, prompt_file: Path) -> list[str]:
    """Build the reviewer command from ``AGENTMARSHAL_REVIEWER_CMD``.

    AgentMarshal is model-agnostic and bundles no reviewer: the operator
    supplies the command that runs their reviewer of choice. It receives the
    review prompt on stdin and must print the machine-verdict block.
    Placeholders ``{model}`` and ``{prompt_file}`` are substituted.
    """

    template_text = os.environ.get("AGENTMARSHAL_REVIEWER_CMD")
    if template_text is None:
        raise ReviewLaunchError(
            "no reviewer command configured: set AGENTMARSHAL_REVIEWER_CMD to the "
            "command that runs your reviewer (AgentMarshal bundles none — it is "
            "model-agnostic). The command reads the prompt on stdin and prints the "
            "machine-verdict block; placeholders {model} and {prompt_file} are "
            "substituted. Example (Codex): "
            "'codex exec --sandbox read-only --model {model} -'. "
            "Alternatively, record a verdict directly with `agentmarshal "
            "submit-review`."
        )
    try:
        template = tuple(shlex.split(template_text))
    except ValueError as error:
        raise ReviewLaunchError(
            f"invalid AGENTMARSHAL_REVIEWER_CMD: {error}"
        ) from error
    if not template:
        raise ReviewLaunchError("AGENTMARSHAL_REVIEWER_CMD must not be empty")
    replacements = {"model": model, "prompt_file": str(prompt_file)}
    try:
        for element in template:
            token = _unsupported_placeholder(element, set(replacements))
            if token is not None:
                named = token if token else "{} (an auto-numbered field)"
                raise ReviewLaunchError(
                    f"AGENTMARSHAL_REVIEWER_CMD has an unsupported placeholder: {named}"
                )
        return [element.format(**replacements) for element in template]
    except (KeyError, IndexError, ValueError) as error:
        # What reaches here is a template the scan passes and the formatter does
        # not — a bad format specification such as {model:d} — or one neither
        # could parse, such as a brace left unclosed by a quoting accident.
        # Neither has a field name to report, and the value is not echoed: a
        # vendor template often carries a token, and this would be the one place
        # the tool prints it. The position of the last opening brace is what the
        # operator needs to find it, and it discloses nothing.
        position = template_text.rfind("{")
        where = (
            f"; the last opening brace is at character {position}"
            if position >= 0
            else ""
        )
        raise ReviewLaunchError(
            f"AGENTMARSHAL_REVIEWER_CMD has an invalid placeholder ({error}){where}"
        ) from error


def _run_reviewer(
    command: list[str], snapshot: Path, prompt: str
) -> tuple[bytes, bytes]:
    """Execute the reviewer adapter against the metadata-free snapshot.

    Process-level isolation belongs to the reviewer command's own vendor
    sandbox (ADR-0001; a Codex command, for example, passes
    ``--sandbox read-only``). The
    launcher's own guarantee is the snapshot: a plain copy of the
    reviewed tree with no repository metadata, so nothing the reviewer
    writes through it reaches the repository. ``AGENTMARSHAL_REVIEWER_CMD``
    is a test/ops seam; whoever configures it owns that command's
    isolation.
    """

    # Bytes, not text: the output is pinned as the reviewer's prose "as
    # received", and text mode would fold a CRLF into LF before the pin.
    try:
        result = subprocess.run(
            command,
            cwd=snapshot,
            capture_output=True,
            input=prompt.encode("utf-8"),
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run reviewer: {error}") from error
    if result.returncode != 0:
        detail = (
            result.stderr.decode("utf-8", errors="replace").strip()
            or result.stdout.decode("utf-8", errors="replace").strip()
        )
        message = f"reviewer exited with status {result.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise ReviewLaunchError(message)
    return result.stdout, result.stderr


def _preserve_output(output: str) -> Path:
    """Write a reviewer's raw output where the caller can still read it.

    A verdict that fails validation used to take the whole run with it: the
    launcher prints only the record path, so the analysis the reviewer was paid
    to produce had nowhere to survive. The file is deliberately not cleaned up;
    removing it is the caller's decision.
    """

    descriptor, name = tempfile.mkstemp(
        prefix="agentmarshal-rejected-verdict-", suffix=".txt"
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(output)
    return Path(name)


def _preserve_reviewer_diagnostics(output: bytes) -> Path:
    """Keep successful reviewer stderr beside rejected-verdict copies.

    Diagnostics are deliberately a local temporary artifact, not journal
    evidence.  A wrapper may use stderr for a warning despite returning zero;
    naming the path tells the operator without mixing that output into the
    command's parseable stdout.
    """

    descriptor, name = tempfile.mkstemp(
        prefix="agentmarshal-reviewer-stderr-", suffix=".txt"
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(output)
    return Path(name)


def _keep_diagnostics(output: bytes) -> str | None:
    """Say where nonempty successful-command stderr went, or leave silence silent.

    Preservation is best effort and this is where that is decided: the note
    says where the bytes were kept, or that they could not be kept and why.
    A verdict the reviewer already produced is never discarded because a
    temporary file could not be written — the operator is told instead, the
    way :func:`_reject` degrades when it cannot keep raw output.
    """

    if not output:
        return None
    try:
        kept = _preserve_reviewer_diagnostics(output)
    except OSError as error:
        # The file was the way to keep a long warning out of the caller's
        # parseable output. Without it the note itself carries the bytes:
        # losing the warning is the defect proposal 021 reported.
        detail = output.decode("utf-8", errors="replace")
        return (
            f"reviewer diagnostics could not be kept ({error}); they follow:\n{detail}"
        )
    return f"reviewer diagnostics kept at {kept}"


def _with_diagnostics(error: ReviewLaunchError, note: str | None) -> ReviewLaunchError:
    """Carry the zero-exit diagnostics note on every later rejection path."""

    if note is None:
        return error
    return ReviewLaunchError(f"{error}; {note}")


def _reject(
    output: str, reason: str, *, preserve_output: bool = True
) -> ReviewLaunchError:
    """Build a rejection that names where the reviewer's raw output was kept."""

    if not preserve_output:
        return ReviewLaunchError(reason)
    try:
        kept = _preserve_output(output)
    except OSError as error:  # pragma: no cover - preservation is best effort
        return ReviewLaunchError(f"{reason} (raw output could not be kept: {error})")
    return ReviewLaunchError(f"{reason}; reviewer output kept at {kept}")


def _parse_verdict(
    output: str,
    *,
    subject_fields: frozenset[str] = frozenset({"reviewed_commit"}),
    preserve_output: bool = True,
) -> tuple[str, str, str, list[str], list[str]]:
    """Parse a verdict for one of the accepted review-subject field sets."""

    def reject(reason: str) -> ReviewLaunchError:
        return _reject(output, reason, preserve_output=preserve_output)

    lines = output.splitlines()
    begins = [index for index, line in enumerate(lines) if line == _VERDICT_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == _VERDICT_END]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise reject("reviewer output has invalid verdict sentinels")
    try:
        verdict_data = json.loads("\n".join(lines[begins[0] + 1 : ends[0]]))
    except json.JSONDecodeError as error:
        raise reject(f"reviewer verdict is not valid JSON: {error}") from error
    if not isinstance(verdict_data, dict):
        raise reject("reviewer verdict must be a JSON object")
    keys = set(verdict_data)
    required = (
        _VERDICT_REQUIRED - {"reviewed_commit"}
        if "reviewed_finding" in subject_fields
        else _VERDICT_REQUIRED
    )
    missing = required - keys
    if missing:
        raise reject(
            "reviewer verdict is missing required field(s): "
            + ", ".join(sorted(missing)),
        )
    bindings = keys & subject_fields
    if len(bindings) != 1:
        raise reject(
            "reviewer verdict must name exactly one of "
            + " or ".join(sorted(subject_fields))
        )
    # An unknown key is still refused — a verdict we do not understand must not
    # be recorded — but the message names it, instead of reporting a shape
    # failure the reviewer cannot act on.
    unknown = keys - required - subject_fields - _VERDICT_OPTIONAL
    if unknown:
        raise reject(
            "reviewer verdict has unsupported field(s): " + ", ".join(sorted(unknown)),
        )
    subject_field = bindings.pop()
    subject = verdict_data[subject_field]
    verdict = verdict_data["verdict"]
    findings = verdict_data["findings"]
    advisory = verdict_data.get("advisory_findings", [])
    if not isinstance(subject, str) or not isinstance(verdict, str):
        raise reject("reviewer verdict fields must be strings")
    for name, value in (("findings", findings), ("advisory_findings", advisory)):
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise reject(f"reviewer verdict {name} must be an array of strings")
    return (
        subject_field,
        subject,
        verdict,
        cast(list[str], findings),
        cast(list[str], advisory),
    )


def _extract_snapshot(project_root: Path, commit: str, snapshot: Path) -> None:
    """Materialize the reviewed tree as a plain copy without git metadata.

    ``git archive`` piped into stdlib tar extraction: the snapshot
    contains no ``.git`` entry at all, so the reviewer cannot reach the
    repository's metadata through it, and cleanup is the enclosing
    temporary directory's own removal — there is no worktree
    registration to leak.
    """

    try:
        result = subprocess.run(
            ["git", "archive", "--format=tar", commit],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ReviewLaunchError(f"git archive failed: {detail}")
    snapshot.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            archive.extractall(snapshot, filter="data")
    except tarfile.TarError as error:
        # An empty tree archives to a lone pax_global_header, which
        # tarfile rejects; an empty snapshot is then correct. Anything
        # else is a real extraction failure.
        if not _run_git(project_root, ["ls-tree", commit]).strip():
            return
        raise ReviewLaunchError(f"snapshot extraction failed: {error}") from error


def dry_run_review(
    project_root: Path, reviewer_model: str | None
) -> tuple[str, str | None]:
    """Exercise the configured reviewer without writing to any journal.

    The command runs where a recorded review runs it: in a snapshot, so a
    relative path in the template resolves as it will in earnest. The tree is
    the current ``HEAD`` rather than a commit the operator names, which is a
    departure from this change's design note and is recorded there.
    """

    template = os.environ.get("AGENTMARSHAL_REVIEWER_CMD")
    if template is not None and reviewer_model is None and _names_model(template):
        raise ReviewLaunchError(
            "the configured reviewer command names a model, so a dry run needs --model"
        )
    with tempfile.TemporaryDirectory(prefix="agentmarshal-review-dry-run-") as name:
        temporary_root = Path(name)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        prompt = _dry_run_prompt()
        prompt_file.write_text(prompt, encoding="utf-8")
        # A project initialised in a repository with no commit has no tree to
        # copy. The command is still worth exercising; only a relative path in
        # it cannot be, and the caller is told which of the two it got. A git
        # that will not run at all is a different problem and stays an error.
        _run_git(project_root, ["rev-parse", "--git-dir"])
        head = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "HEAD^{commit}"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
        if head.returncode == 0:
            _extract_snapshot(project_root, "HEAD", snapshot)
            tree = "a snapshot of HEAD"
        else:
            snapshot.mkdir()
            tree = "an empty tree, because this repository has no commit yet"
        raw_output, raw_diagnostics = _run_reviewer(
            _reviewer_command(reviewer_model or "", prompt_file), snapshot, prompt
        )
        diagnostics_note = _keep_diagnostics(raw_diagnostics)
        output = raw_output.decode("utf-8", errors="replace")
        try:
            (
                _subject_field,
                reviewed_commit,
                _verdict,
                _findings,
                _advisory,
            ) = _parse_verdict(output, preserve_output=False)
        except ReviewLaunchError as error:
            # The operator is debugging this command; the output is the evidence.
            # It goes beside the rejected-verdict copies, outside any journal.
            try:
                kept = _preserve_output(output)
            except OSError:
                raise _with_diagnostics(
                    ReviewLaunchError(f"reviewer output: {error}"), diagnostics_note
                ) from error
            message = f"reviewer output: {error}; what the command printed is at {kept}"
            raise _with_diagnostics(
                ReviewLaunchError(message), diagnostics_note
            ) from error
        # The recorded path refuses a verdict about another commit, and so does
        # this one: a command that echoes a commit of its own would pass a check
        # that only parsed.
        if reviewed_commit != _DRY_RUN_COMMIT:
            raise _with_diagnostics(
                ReviewLaunchError(
                    "reviewer verdict names a commit the dry run did not ask about: "
                    f"{reviewed_commit}"
                ),
                diagnostics_note,
            )
        return tree, diagnostics_note


def _verified_finding_artifacts(
    project_root: Path, finding: dict[str, object]
) -> tuple[tuple[_VerifiedArtifact, ...], tuple[str, ...]]:
    """Read and hash all locally resolvable artifacts before a reviewer runs."""

    verified: list[_VerifiedArtifact] = []
    unresolved: list[str] = []
    for artifact in cast(list[dict[str, str]], finding["artifacts"]):
        reference = artifact["ref"]
        path = artifact_path(project_root, reference)
        if path is None:
            unresolved.append(reference)
            continue
        try:
            content = path.read_bytes()
        except OSError as error:
            raise ReviewLaunchError(
                f"finding artifact {reference} could not be read: {error}"
            ) from error
        digest = hashlib.sha256(content).hexdigest()
        if digest != artifact["hash"]:
            raise ReviewLaunchError(
                f"finding artifact {reference} does not match its recorded sha256"
            )
        verified.append(_VerifiedArtifact(reference, digest, path, content))
    if not verified:
        finding_id = cast(str, finding["id"])
        raise ReviewLaunchError(
            f"finding {finding_id} has no artifacts that could be verified locally"
        )
    return tuple(verified), tuple(unresolved)


def _extract_finding_snapshot(
    project_root: Path, artifacts: tuple[_VerifiedArtifact, ...], snapshot: Path
) -> None:
    """Materialize the already-verified files under their project-relative paths."""

    snapshot.mkdir()
    resolved_project = project_root.resolve()
    for artifact in artifacts:
        # ``artifact_path`` already established this relationship.  Retaining
        # the check makes a future caller of this helper fail closed rather
        # than accidentally creating a path outside the snapshot.
        try:
            relative = artifact.path.relative_to(resolved_project)
        except ValueError as error:  # pragma: no cover - guarded by resolver
            raise ReviewLaunchError(
                f"finding artifact {artifact.reference} is outside the project root"
            ) from error
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(artifact.content)


def _launch_finding_review(
    project_root: Path,
    journal_root: Path,
    task_id: str,
    reviewed_finding: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
) -> LaunchedReview:
    """Review verified finding artifacts and bind the resulting record to it."""

    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    task_findings = [
        record for record in task.records if record["record_type"] == "finding"
    ]
    finding = next(
        (record for record in task_findings if record.get("id") == reviewed_finding),
        None,
    )
    if finding is None:
        raise ReviewLaunchError(
            f"reviewed finding {reviewed_finding} is not a finding of task {task_id}"
        )
    latest_finding = task_findings[-1]
    latest_finding_id = cast(str, latest_finding["id"])
    if reviewed_finding != latest_finding_id:
        raise ReviewLaunchError(
            f"reviewed finding {reviewed_finding} is not the latest finding of task "
            f"{task_id}; latest finding is {latest_finding_id}"
        )
    identity_refusal = finding_reviewer_identity_refusal(
        project_root, finding, reviewer_email
    )
    if identity_refusal is not None:
        raise ReviewLaunchError(identity_refusal)

    verified, unresolved = _verified_finding_artifacts(project_root, finding)
    contract_path = journal_root / "tasks" / task.task_id / "contract.md"
    try:
        contract = contract_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ReviewLaunchError(
            f"cannot read task contract for review: {error}"
        ) from error
    try:
        header = parse_contract_text(contract, str(contract_path))
        documents = list(header.documents)
        absent: list[str] = []
        for name in header.extensions:
            try:
                documents.extend(read_extension_manifest(project_root, name).documents)
            except ExtensionManifestMissing:
                absent.append(name)
    except ValueError as error:
        raise ReviewLaunchError(str(error)) from error

    prompt = _finding_review_prompt(
        contract,
        reviewed_finding,
        verified,
        unresolved,
        decisions=header.decisions,
        documents=tuple(dict.fromkeys(documents)),
        absent_extensions=tuple(absent),
        amendment_history=render_amendment_history(task.records),
    )
    raw_output = b""
    reviewer_output = ""
    with tempfile.TemporaryDirectory(
        prefix="agentmarshal-review-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        _extract_finding_snapshot(project_root, verified, snapshot)
        prompt_file.write_text(prompt, encoding="utf-8")
        raw_output, raw_diagnostics = _run_reviewer(
            _reviewer_command(reviewer_model, prompt_file), snapshot, prompt
        )
        diagnostics_note = _keep_diagnostics(raw_diagnostics)
        reviewer_output = raw_output.decode("utf-8", errors="replace")
        try:
            (
                subject_field,
                subject,
                verdict,
                blocking_findings,
                advisory,
            ) = _parse_verdict(
                reviewer_output,
                subject_fields=frozenset({"reviewed_commit", "reviewed_finding"}),
            )
        except ReviewLaunchError as error:
            raise _with_diagnostics(error, diagnostics_note) from error
        if subject_field != "reviewed_finding" or subject != reviewed_finding:
            raise _with_diagnostics(
                _reject(
                    reviewer_output,
                    "reviewer verdict subject does not match requested finding "
                    f"{reviewed_finding}: verdict named {subject_field} {subject}",
                ),
                diagnostics_note,
            )
    try:
        submitted = submit_review(
            journal_root,
            task_id,
            None,
            verdict,
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
            blocking_findings,
            advisory or None,
            prose=raw_output,
            reviewed_finding=reviewed_finding,
            reviewed_contract=hashlib.sha256(contract.encode("utf-8")).hexdigest(),
        )
    except ReviewSubmitError as error:
        if error.artifact_ref is not None:
            raise _with_diagnostics(
                ReviewLaunchError(str(error)), diagnostics_note
            ) from error
        raise _with_diagnostics(
            _reject(reviewer_output, str(error)), diagnostics_note
        ) from error
    return LaunchedReview(
        submitted.record_path, submitted.artifact_ref, diagnostics_note
    )


def launch_review(
    project_root: Path,
    task_id: str,
    commit: str | None,
    base: str | None,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    *,
    journal_root: Path | None = None,
    reviewed_finding: str | None = None,
) -> LaunchedReview:
    """Review an exact commit or a hash-pinned finding and record the verdict."""

    sidecar_journal = journal_root
    journal_root = journal_root or project_root / ".agentmarshal" / "journal"
    if reviewed_finding is not None:
        # A sidecar finding belongs to the sidecar project, even though the
        # commit path receives the configured host as ``project_root``.
        return _launch_finding_review(
            journal_root.parents[1],
            journal_root,
            task_id,
            reviewed_finding,
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
        )
    if commit is None or base is None:
        raise ReviewLaunchError("a commit review requires both commit and base")
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    resolved_commit = _resolve_commit(project_root, commit)
    merge_base = _run_git(project_root, ["merge-base", base, resolved_commit]).strip()
    diff = _run_git(project_root, ["diff", f"{merge_base}..{resolved_commit}"])

    review_result: tuple[str, str, list[str], list[str]]
    reviewer_output = ""
    raw_output = b""
    with tempfile.TemporaryDirectory(
        prefix="agentmarshal-review-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        _extract_snapshot(project_root, resolved_commit, snapshot)
        contract_path = (
            journal_root / "tasks" / task.task_id / "contract.md"
            if sidecar_journal is not None
            else snapshot
            / ".agentmarshal"
            / "journal"
            / "tasks"
            / task.task_id
            / "contract.md"
        )
        try:
            contract = contract_path.read_text(encoding="utf-8")
        except OSError as error:
            source = (
                "for review" if sidecar_journal is not None else "from reviewed commit"
            )
            raise ReviewLaunchError(
                f"cannot read task contract {source}: {error}"
            ) from error
        amendment_history = render_amendment_history(task.records)
        try:
            header = parse_contract_text(contract, str(contract_path))
            extension_root = (
                journal_root.parents[1] if sidecar_journal is not None else snapshot
            )
            documents = list(header.documents)
            absent: list[str] = []
            for name in header.extensions:
                try:
                    documents.extend(
                        read_extension_manifest(extension_root, name).documents
                    )
                except ExtensionManifestMissing:
                    absent.append(name)
        except ValueError as error:
            raise ReviewLaunchError(str(error)) from error
        prompt = _review_prompt(
            contract,
            diff,
            resolved_commit,
            decisions=header.decisions,
            documents=tuple(dict.fromkeys(documents)),
            absent_extensions=tuple(absent),
            amendment_history=amendment_history,
        )
        prompt_file.write_text(prompt, encoding="utf-8")
        raw_output, raw_diagnostics = _run_reviewer(
            _reviewer_command(reviewer_model, prompt_file),
            snapshot,
            prompt,
        )
        diagnostics_note = _keep_diagnostics(raw_diagnostics)
        # The verdict is parsed from a decoded copy; the artifact pins the
        # bytes the reviewer wrote, so nothing is normalised on the way.
        output = raw_output.decode("utf-8", errors="replace")
        reviewer_output = output
        try:
            (
                _subject_field,
                reviewed_commit,
                verdict,
                findings,
                advisory,
            ) = _parse_verdict(output)
        except ReviewLaunchError as error:
            raise _with_diagnostics(error, diagnostics_note) from error
        if reviewed_commit != resolved_commit:
            raise _with_diagnostics(
                _reject(
                    output, "reviewer verdict reviewed_commit does not match commit"
                ),
                diagnostics_note,
            )
        review_result = reviewed_commit, verdict, findings, advisory
    try:
        submitted = submit_review(
            journal_root,
            task_id,
            review_result[0],
            review_result[1],
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
            review_result[2],
            review_result[3] or None,
            prose=raw_output,
            reviewed_contract=hashlib.sha256(contract.encode("utf-8")).hexdigest(),
        )
    except ReviewSubmitError as error:
        if error.artifact_ref is not None:
            raise _with_diagnostics(
                ReviewLaunchError(str(error)), diagnostics_note
            ) from error
        # A verdict can parse cleanly and still be refused by record validation —
        # an unknown verdict value, empty findings for a non-approving verdict,
        # duplicates, or advisory ids overlapping findings. That path discarded
        # the analysis too, and it is the one seen most often in practice.
        raise _with_diagnostics(
            _reject(reviewer_output, str(error)), diagnostics_note
        ) from error
    return LaunchedReview(
        submitted.record_path,
        submitted.artifact_ref,
        diagnostics_note,
    )
