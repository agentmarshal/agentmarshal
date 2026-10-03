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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.actors import finding_reviewer_identity_refusal
from agentmarshal.journal.artifacts import artifact_path as artifact_path
from agentmarshal.journal.brief import (
    append_amendment_history,
    render_amendment_history,
)
from agentmarshal.journal.capture import (
    CaptureError,
    CaptureLevel,
    decode_diff_per_file,
    render_undecodable_files,
    review_capture_level_from_journal,
)
from agentmarshal.journal.contracts import contract_sha256, parse_contract_text
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifestError,
    ExtensionManifestMissing,
    read_extension_manifest,
)
from agentmarshal.journal.gate import (
    GateError,
    markers_from_config,
    markers_from_tree,
)

# The allowed verdicts have one definition, in records.py, which validation
# uses. The prompt renders that same set so it cannot drift from what the
# record layer will accept. (Module-private today; worth making public the
# next time records.py is opened.)
from agentmarshal.journal.records import (
    _REVIEW_VERDICTS as REVIEW_VERDICTS,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.journal.submit_review import (
    ReviewSubmitError,
    submit_review,
)

_VERDICT_BEGIN = "AGENTMARSHAL_VERDICT_BEGIN"
_VERDICT_END = "AGENTMARSHAL_VERDICT_END"
# Embedded content is presented, not quoted verbatim: a pinned artifact may
# itself hold a complete verdict block, and the diff path is immune to that only
# because every diff line already carries a prefix.  An empty line takes the bar
# alone, so the prompt never carries trailing whitespace.
_ARTIFACT_CONTENT_PREFIX = "|"
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

{diff_note}Diff:
{diff}
"""
_FINDING_REVIEW_PROMPT = (
    "You are a read-only reviewer. Review the supplied task contract\n"
    "and verified finding artifacts.\n"
    "Do not modify files. Your reviewed finding is {finding}.\n"
    "\n"
    "Finding claim:\n"
    "{summary}\n"
    "\n"
    "Each embedded artifact-content line begins with `{content_prefix}`; that "
    "prefix presents the content and is not part of the file.\n"
    "The verified artifacts are also files in your working directory, at the "
    "paths named below, so one whose content is not embedded can still be "
    "read there.\n"
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
    """A recorded review plus notes the operator should read.

    ``diagnostics_note`` carries what survived a successful command's error
    stream, and anything else the launch must not drop in silence — files
    the diff decode could not fully read are named through it.
    """

    record_path: Path
    artifact_ref: str | None
    diagnostics_note: str | None
    prose_note: str | None


@dataclass(frozen=True)
class _VerifiedArtifact:
    """A locally resolved finding artifact, read and hashed before review."""

    reference: str
    digest: str
    content: bytes
    snapshot_reference: Path


def _named_contract_material(
    decisions: tuple[str, ...],
    documents: tuple[str, ...],
    absent_extensions: tuple[str, ...],
    *,
    absent_extensions_phrase: str,
    preamble: str = "",
) -> str:
    """Render the contract names shared by commit and finding review prompts.

    ``preamble`` is said only when there is material to say it about: a
    research task usually names none, and telling a reviewer that unsupplied
    material exists invites a finding about its absence.
    """

    if not (decisions or documents or absent_extensions):
        return ""
    lines = [preamble] if preamble else []
    lines.append("Named contract material:")
    if decisions:
        lines.append("Decisions:")
        lines.extend(f"- {escape_for_display(decision)}" for decision in decisions)
        lines.append("A finding may cite a contradiction with a named decision.")
    if documents:
        lines.append("Documents:")
        lines.extend(f"- {escape_for_display(document)}" for document in documents)
    if absent_extensions:
        # A removal candidate deletes its manifest (ADR-0010 D5); the review
        # still launches, and the reviewer is told what is absent.
        lines.append(absent_extensions_phrase)
        lines.extend(f"- {escape_for_display(name)}" for name in absent_extensions)
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


def _run_git_bytes(project_root: Path, arguments: list[str]) -> bytes:
    """Run git and return its standard output as bytes, or raise a launcher error.

    Bytes, not text: a diff is not wholly UTF-8 when a file's content or path
    is not, and even diagnostics can carry a path's raw bytes. Callers decode
    for their own purpose — the diff per file section — rather than a strict
    whole-stream decode here raising mid-launch (proposal 037).
    """

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        # Error text can quote a path whose bytes are not UTF-8; escaping
        # keeps that path printable instead of mangling it or raising.
        detail = (
            result.stderr.decode("utf-8", "backslashreplace").strip()
            or result.stdout.decode("utf-8", "backslashreplace").strip()
        )
        raise ReviewLaunchError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _run_git(project_root: Path, arguments: list[str]) -> str:
    """Run git and return its standard output, or raise a launcher error.

    Decoded with escapes: a SHA is unaffected, while a non-UTF-8 path in a
    listing is named ``\\xNN``-escaped rather than raising UnicodeDecodeError.
    """

    return _run_git_bytes(project_root, arguments).decode("utf-8", "backslashreplace")


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
    undecodable_files: tuple[str, ...] = (),
) -> str:
    """Build the reviewer prompt with its required machine-verdict protocol.

    ``undecodable_files`` names the diff sections the per-file decode could
    not fully read: the reviewer still sees what decoded — U+FFFD marks the
    content bytes that did not — but is told, so the marked spans are not
    mistaken for the file's real content.
    """

    contract_material = append_amendment_history(contract, amendment_history)
    diff_note = ""
    if undecodable_files:
        diff_note = (
            "Diff sections that did not decode as UTF-8 — what decoded is "
            "shown below, with U+FFFD marking each content byte that did not "
            "and \\xNN escapes in the header lines: "
            + ", ".join(escape_for_display(name) for name in undecodable_files)
            + "\n\n"
        )
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
        diff_note=diff_note,
        diff=diff,
    )


def _finding_review_prompt(
    contract: str,
    finding: str,
    summary: str,
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
        artifact_heading = (
            f"Verified artifact: {escape_for_display(artifact.reference)}\n"
        )
        if artifact.snapshot_reference.as_posix() != artifact.reference:
            artifact_heading += (
                "Snapshot path: "
                f"{escape_for_display(artifact.snapshot_reference.as_posix())}\n"
            )
        try:
            text = artifact.content.decode("utf-8")
        except UnicodeDecodeError:
            artifact_sections.append(
                artifact_heading + f"Recorded sha256: {artifact.digest}\n"
                f"Content not embedded: the verified artifact is not valid UTF-8 "
                f"({len(artifact.content)} bytes)."
            )
        else:
            # splitlines(), not split("\n"): the verdict parser reads lines
            # the way str.splitlines() does, so content separated by a lone
            # \r — a measurement log with progress output — would otherwise
            # arrive as one prefixed chunk with unprefixed sentinel lines
            # inside it. The terminators are normalised in the presentation;
            # the recorded hash is what pins the bytes.
            prefixed_text = "\n".join(
                f"{_ARTIFACT_CONTENT_PREFIX} {line}"
                if line
                else _ARTIFACT_CONTENT_PREFIX
                for line in text.splitlines()
            )
            artifact_sections.append(
                artifact_heading + f"Recorded sha256: {artifact.digest}\n"
                f"Content (each line is prefixed):\n{prefixed_text}"
            )
    if unresolved_references:
        artifact_sections.append(
            "Unverified references (not fetched):\n"
            + "\n".join(
                f"- {escape_for_display(reference)}"
                for reference in unresolved_references
            )
        )

    return _FINDING_REVIEW_PROMPT.format(
        content_prefix=_ARTIFACT_CONTENT_PREFIX,
        finding=escape_for_display(finding),
        summary=escape_for_display(summary),
        named_material=_named_contract_material(
            decisions,
            documents,
            absent_extensions,
            absent_extensions_phrase=(
                "Extensions whose manifest is absent in the project:"
            ),
            preamble=(
                "The named contract material below is named, not supplied in "
                "this snapshot; only the pinned artifacts were verified."
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


class _LocalStateUnavailable(Exception):
    """The clone's local state cannot take a kept file this run."""


def _local_state_output(
    journal_project_root: Path,
    *,
    prefix: str,
    event: str,
    task: str | None,
    output: bytes,
) -> Path:
    """Keep bytes under the journal repository's local state and say where.

    The file lands in ``log/files/`` under the clone's local state — the
    process-log area — and an event names the file and its sha256.
    ``journal_project_root`` is the repository that holds the journal, so in
    a sidecar the file and the event land in the sidecar's own state and the
    host never enters the call (ADR-0014 decision 5). Every failure on this
    path — git cannot name the common directory, a directory cannot be
    created, an event cannot be appended — reaches the caller as a
    ``_LocalStateUnavailable`` carrying the reason, so the temporary-file
    fallback is one catch.

    The imports are deferred: ``agentmarshal.journal``'s package init
    imports this module, and the pin that forbids the gate importing
    ``agentmarshal.process_log`` would break if they sat at the top.
    """

    from agentmarshal.journal.placement import PlacementError, resolve_placement
    from agentmarshal.localstate import LocalStateError, local_state
    from agentmarshal.process_log import (
        ProcessLogError,
        open_writer,
        write_event,
        write_payload,
    )

    try:
        state = local_state(resolve_placement(journal_project_root))
        kept = write_payload(state, prefix, output)
        write_event(
            open_writer(state),
            event,
            task=task,
            path=str(kept),
            sha256=hashlib.sha256(output).hexdigest(),
        )
    except (LocalStateError, PlacementError, ProcessLogError, OSError) as error:
        reason = (
            error.strerror or str(error) if isinstance(error, OSError) else str(error)
        )
        raise _LocalStateUnavailable(reason) from error
    return kept


def _preserve_accepted_output(output: bytes) -> Path:
    """Write kept output to a local temporary file — the fallback path.

    Kept output goes under the clone's local state now; a temporary file is
    where it lands when the local state cannot be used. The file is
    deliberately not cleaned up; removing it is the caller's decision.
    """

    descriptor, name = tempfile.mkstemp(
        prefix="agentmarshal-reviewer-output-", suffix=".txt"
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(output)
    return Path(name)


def _preserve_reviewer_diagnostics(output: bytes) -> Path:
    """Write successful reviewer stderr to a temporary file — the fallback.

    Diagnostics go under the clone's local state now, never journal
    evidence; a temporary file is where they land when the local state
    cannot be used.  A wrapper may use stderr for a warning despite
    returning zero; naming the path tells the operator without mixing that
    output into the command's parseable stdout.
    """

    descriptor, name = tempfile.mkstemp(
        prefix="agentmarshal-reviewer-stderr-", suffix=".txt"
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(output)
    return Path(name)


def _keep_accepted_output(
    journal_project_root: Path, task_id: str, output: bytes
) -> str:
    """Keep an accepted verdict's output outside the journal and say where.

    At ``hash`` the journal holds nothing about the prose: the bytes live in
    a file under the local state's process-log area and a ``review-prose``
    event names the file and its sha256 (ADR-0014 decisions 1 and 11,
    ADR-0022 section 7). When the local state cannot be used the output
    falls back to a temporary file and the note says why; a verdict the
    reviewer already produced is never discarded because preservation
    failed.
    """

    try:
        kept = _local_state_output(
            journal_project_root,
            prefix="agentmarshal-reviewer-output-",
            event="review-prose",
            task=task_id,
            output=output,
        )
    except _LocalStateUnavailable as error:
        try:
            kept = _preserve_accepted_output(output)
        except OSError as inner:
            return (
                f"reviewer prose could not be kept locally ({inner}); the "
                f"clone's local state could not be used either ({error})"
            )
        return (
            f"reviewer output kept at {kept} (capture level: hash); the "
            f"clone's local state could not be used ({error})"
        )
    return f"reviewer output kept at {kept} (capture level: hash)"


def _keep_diagnostics(
    output: bytes,
    *,
    journal_project_root: Path | None = None,
    task_id: str | None = None,
) -> str | None:
    """Say where nonempty successful-command stderr went, or leave silence silent.

    The bytes are kept under the journal repository's local state — the
    process-log area — and a ``review-diagnostics`` event names the file and
    its sha256, whatever the capture level (ADR-0014 decisions 1 and 11).
    ``journal_project_root`` is the repository holding the journal; ``None``
    keeps the temporary-file path for a caller that has no journal. When the
    local state cannot be used the output falls back to a temporary file and
    the note says why. Preservation is best effort, exactly as before: a
    failure to keep the bytes lands in the note rather than costing the
    verdict.
    """

    if not output:
        return None
    reason: str | None = None
    if journal_project_root is not None:
        try:
            kept = _local_state_output(
                journal_project_root,
                prefix="agentmarshal-reviewer-stderr-",
                event="review-diagnostics",
                task=task_id,
                output=output,
            )
        except _LocalStateUnavailable as error:
            reason = str(error)
        else:
            return f"reviewer diagnostics kept at {kept}"
    try:
        kept = _preserve_reviewer_diagnostics(output)
    except OSError as error:
        # The file was the way to keep a long warning out of the caller's
        # parseable output. Without it the note itself carries the bytes:
        # losing the warning is the defect proposal 021 reported.
        detail = output.decode("utf-8", errors="replace")
        if reason is not None:
            return (
                "reviewer diagnostics could not be kept under the clone's "
                f"local state ({reason}) or in a temporary file ({error}); "
                f"they follow:\n{detail}"
            )
        return (
            f"reviewer diagnostics could not be kept ({error}); they follow:\n{detail}"
        )
    if reason is not None:
        return (
            f"reviewer diagnostics kept at {kept}; the clone's local state "
            f"could not be used ({reason})"
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
    expected_field: str | None = None,
    preserve_output: bool = True,
) -> tuple[str, str, str, list[str], list[str]]:
    """Parse a verdict for one of the accepted review-subject field sets.

    ``subject_fields`` is what the parser will read; ``expected_field`` is what
    the caller asked the reviewer for. A finding launch reads both shapes so a
    commit-shaped verdict can be named in the refusal, and must not invite one:
    the refusal names the field the prompt asked for.
    """

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
            f"reviewer verdict must name {expected_field}"
            if expected_field is not None
            else "reviewer verdict must name exactly one of "
            + " or ".join(sorted(subject_fields))
        )
    # An unknown key is still refused — a verdict we do not understand must not
    # be recorded — but the message names it, instead of reporting a shape
    # failure the reviewer cannot act on.
    unknown = keys - required - subject_fields - _VERDICT_OPTIONAL
    if unknown:
        raise reject(
            "reviewer verdict has unsupported field(s): "
            + ", ".join(escape_for_display(key) for key in sorted(unknown)),
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
        detail = result.stderr.decode("utf-8", "backslashreplace").strip()
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
    project_root: Path,
    reviewer_model: str | None,
    *,
    journal_root: Path | None = None,
) -> tuple[str, str | None]:
    """Exercise the configured reviewer without writing to any journal.

    The command runs where a recorded review runs it: in a snapshot, so a
    relative path in the template resolves as it will in earnest. The tree is
    the current ``HEAD`` rather than a commit the operator names, which is a
    departure from this change's design note and is recorded there.
    ``journal_root`` is the journal directory a recorded review would write
    against — the diagnostics land in that repository's process log; left
    ``None`` it resolves under ``project_root``, the same default
    ``launch_review`` applies when its own caller names no journal.
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
        # The diagnostics belong to the journal repository's log like a
        # recorded run's, and the journal resolves the way a recorded run
        # resolves one its caller does not name — under the project the
        # command runs against, never the working directory. A caller
        # holding a resolved placement passes the journal root itself, so a
        # sidecar's diagnostics land in the sidecar's log and the host is
        # never consulted.
        journal_root = journal_root or project_root / ".agentmarshal" / "journal"
        diagnostics_note = _keep_diagnostics(
            raw_diagnostics, journal_project_root=journal_root.parents[1]
        )
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
                    f"{escape_for_display(reviewed_commit)}"
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
    drifted: list[str] = []
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
                f"finding artifact {escape_for_display(reference)} could not be "
                f"read: {escape_for_display(str(error))}"
            ) from error
        digest = hashlib.sha256(content).hexdigest()
        if digest != artifact["hash"]:
            drifted.append(reference)
            continue
        reference_path = Path(reference)
        snapshot_reference = (
            path.relative_to(project_root.resolve())
            if reference_path.is_absolute()
            else reference_path
        )
        verified.append(
            _VerifiedArtifact(reference, digest, content, snapshot_reference)
        )
    if drifted:
        raise ReviewLaunchError(
            "finding artifact(s) do not match their recorded sha256: "
            + ", ".join(escape_for_display(reference) for reference in drifted)
        )
    if not verified:
        finding_id = cast(str, finding["id"])
        raise ReviewLaunchError(
            f"finding {escape_for_display(finding_id)} has no artifacts that "
            "could be verified locally"
        )
    return tuple(verified), tuple(unresolved)


def _extract_finding_snapshot(
    artifacts: tuple[_VerifiedArtifact, ...], snapshot: Path
) -> None:
    """Materialize verified bytes at their referenced paths in the snapshot."""

    snapshot.mkdir()
    resolved_snapshot = snapshot.resolve()
    for artifact in artifacts:
        # References, rather than resolved artifact paths, are the paths the
        # prompt tells the reviewer to use.  A symlink is deliberately copied
        # as its verified bytes at its link spelling.  Retain confinement here
        # even though ``artifact_path`` already verified the source path.
        destination = snapshot / artifact.snapshot_reference
        try:
            destination.resolve().relative_to(resolved_snapshot)
        except (OSError, ValueError) as error:
            raise ReviewLaunchError(
                "finding artifact reference escapes the snapshot: "
                f"{escape_for_display(artifact.reference)}"
            ) from error
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(artifact.content)
        except OSError as error:
            # Same class as the manifest failure this task already closed: an
            # I/O error here left `launch_review` as a bare OSError, and the
            # CLI catches only ReviewLaunchError.
            raise ReviewLaunchError(
                f"finding artifact {escape_for_display(artifact.reference)} "
                "could not be placed in the review snapshot: "
                f"{escape_for_display(str(error))}"
            ) from error


def _launch_review_tail(
    journal_root: Path,
    task_id: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    *,
    snapshot_builder: Callable[[Path], None],
    prompt_builder: Callable[[Path], tuple[str, str]],
    subject_fields: frozenset[str],
    expected_subject_field: str,
    expected_subject: str,
    subject_mismatch: Callable[[str, str], str],
    reviewed_commit: str | None = None,
    reviewed_finding: str | None = None,
    prose_capture_level: CaptureLevel,
    operator_note: str | None = None,
) -> LaunchedReview:
    """Run, parse, and record either kind of review after its setup is known.

    ``operator_note`` is something the launch already knows the operator
    should read — the diff decode naming files it could not fully read. It
    rides the diagnostics channel so it survives both a recorded review and
    every later rejection.
    """

    raw_output = b""
    reviewer_output = ""
    with tempfile.TemporaryDirectory(
        prefix="agentmarshal-review-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        try:
            snapshot_builder(snapshot)
            prompt, contract = prompt_builder(snapshot)
            prompt_file.write_text(prompt, encoding="utf-8")
            raw_output, raw_diagnostics = _run_reviewer(
                _reviewer_command(reviewer_model, prompt_file), snapshot, prompt
            )
        except ReviewLaunchError as error:
            # A bare re-raise when there is no note: _with_diagnostics would
            # return the same object, and `raise error from error` makes an
            # exception its own cause.
            if operator_note is None:
                raise
            raise _with_diagnostics(error, operator_note) from error
        diagnostics_note = _keep_diagnostics(
            raw_diagnostics,
            journal_project_root=journal_root.parents[1],
            task_id=task_id,
        )
        if operator_note is not None:
            diagnostics_note = (
                f"{operator_note}\n{diagnostics_note}"
                if diagnostics_note is not None
                else operator_note
            )
        # The verdict is parsed from a decoded copy; the artifact pins the
        # bytes the reviewer wrote, so nothing is normalised on the way.
        reviewer_output = raw_output.decode("utf-8", errors="replace")
        try:
            (
                subject_field,
                subject,
                verdict,
                findings,
                advisory,
            ) = _parse_verdict(
                reviewer_output,
                subject_fields=subject_fields,
                expected_field=expected_subject_field,
            )
        except ReviewLaunchError as error:
            if diagnostics_note is None:
                raise
            raise _with_diagnostics(error, diagnostics_note) from error
        if subject_field != expected_subject_field or subject != expected_subject:
            raise _with_diagnostics(
                _reject(
                    reviewer_output,
                    subject_mismatch(subject_field, subject),
                ),
                diagnostics_note,
            )
    try:
        submitted = submit_review(
            journal_root,
            task_id,
            reviewed_commit,
            verdict,
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
            findings,
            advisory or None,
            prose=raw_output if prose_capture_level is CaptureLevel.COMMIT else None,
            reviewed_finding=reviewed_finding,
            reviewed_contract=contract_sha256(
                contract.encode("utf-8"), f"task {task_id} contract"
            ),
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
    prose_note: str | None = None
    if prose_capture_level is CaptureLevel.HASH:
        prose_note = _keep_accepted_output(journal_root.parents[1], task_id, raw_output)
    elif prose_capture_level is CaptureLevel.OFF:
        prose_note = "reviewer prose was not kept (capture level: off)"
    return LaunchedReview(
        submitted.record_path,
        submitted.artifact_ref,
        diagnostics_note,
        prose_note,
    )


def _launch_finding_review(
    project_root: Path,
    journal_root: Path,
    task_id: str,
    reviewed_finding: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    prose_capture_level: CaptureLevel,
) -> LaunchedReview:
    """Review verified finding artifacts and bind the resulting record to it."""

    try:
        task = load_task_for_record(journal_root, task_id, "review")
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
            f"reviewed finding {escape_for_display(reviewed_finding)} is not a "
            f"finding of task {escape_for_display(task_id)}"
        )
    latest_finding = task_findings[-1]
    latest_finding_id = cast(str, latest_finding["id"])
    if reviewed_finding != latest_finding_id:
        raise ReviewLaunchError(
            f"reviewed finding {escape_for_display(reviewed_finding)} is not the "
            f"latest finding of task {escape_for_display(task_id)}; latest "
            f"finding is {escape_for_display(latest_finding_id)}"
        )
    if task.contract.scope:
        raise ReviewLaunchError(
            "findings lane requires an empty scope; declared scope: "
            + ", ".join(escape_for_display(entry) for entry in task.contract.scope)
        )
    identity_refusal = finding_reviewer_identity_refusal(
        project_root, finding, reviewer_email, launching=True
    )
    if identity_refusal is not None:
        raise ReviewLaunchError(identity_refusal)

    verified, unresolved = _verified_finding_artifacts(project_root, finding)
    contract_path = journal_root / "tasks" / task.task_id / "contract.md"
    try:
        contract = contract_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ReviewLaunchError(
            f"cannot read task contract for review: {error}"
        ) from error
    # The status projection parsed this same file; the commit path parses a
    # second time only because its contract comes from the reviewed snapshot.
    header = task.contract
    documents = list(header.documents)
    absent: list[str] = []
    for name in header.extensions:
        try:
            documents.extend(read_extension_manifest(project_root, name).documents)
        except ExtensionManifestMissing:
            absent.append(name)
        except ExtensionManifestError as error:
            # A malformed manifest refuses the launch on both paths; the commit
            # path reaches that through its ValueError wrapper. Without this the
            # exception left the CLI as a traceback.
            raise ReviewLaunchError(str(error)) from error

    prompt = _finding_review_prompt(
        contract,
        reviewed_finding,
        cast(str, finding["summary"]),
        verified,
        unresolved,
        decisions=header.decisions,
        documents=tuple(dict.fromkeys(documents)),
        absent_extensions=tuple(absent),
        amendment_history=render_amendment_history(task.records),
    )
    return _launch_review_tail(
        journal_root,
        task_id,
        reviewer_role,
        reviewer_vendor,
        reviewer_model,
        reviewer_email,
        snapshot_builder=lambda snapshot: _extract_finding_snapshot(verified, snapshot),
        prompt_builder=lambda _snapshot: (prompt, contract),
        subject_fields=frozenset({"reviewed_commit", "reviewed_finding"}),
        expected_subject_field="reviewed_finding",
        expected_subject=reviewed_finding,
        subject_mismatch=lambda subject_field, subject: (
            "reviewer verdict subject does not match requested finding "
            f"{escape_for_display(reviewed_finding)}: verdict named "
            f"{escape_for_display(subject_field)} {escape_for_display(subject)}"
        ),
        reviewed_finding=reviewed_finding,
        prose_capture_level=prose_capture_level,
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
    try:
        prose_capture_level = review_capture_level_from_journal(journal_root)
    except (CaptureError, OSError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    if reviewed_finding is not None and (commit is not None or base is not None):
        # One binding per review is the record rule (records.py); a public
        # caller handed both would otherwise have the finding judged silently.
        # A base belongs to the commit path too: there is nothing to compare a
        # finding against, and accepting it silently would drop it.
        given = ", ".join(
            name
            for name, value in (("commit", commit), ("base", base))
            if value is not None
        )
        raise ReviewLaunchError(
            f"a review names one subject: a reviewed finding was given with {given}"
        )
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
            prose_capture_level,
        )
    if commit is None or base is None:
        raise ReviewLaunchError("a commit review requires both commit and base")
    try:
        task = load_task_for_record(journal_root, task_id, "review")
    except (OSError, TaskStatusError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    resolved_commit = _resolve_commit(project_root, commit)
    merge_base = _run_git(project_root, ["merge-base", base, resolved_commit]).strip()
    # The diff is bytes decoded one file section at a time by the helper the
    # leak scan already uses: a strict whole-stream decode made one file's
    # non-UTF-8 bytes cost the whole review (proposal 037). The section
    # prefixes are pinned — the name parser strips "b/", which a repo's
    # diff.mnemonicPrefix or diff.dstPrefix would otherwise bend — while the
    # rendering stays what it was: no --text, so a binary file still arrives
    # as "Binary files differ", which already tells the reviewer what it is.
    # The reviewer reads every line of the decoded text, so every section
    # that lost bytes is named — the scan's narrower rule covers only the
    # added bytes and headers it reads.
    diff, undecodable = decode_diff_per_file(
        _run_git_bytes(
            project_root,
            [
                "diff",
                "--src-prefix=a/",
                "--dst-prefix=b/",
                f"{merge_base}..{resolved_commit}",
            ],
        ),
        name_all_losses=True,
    )
    diff_note = None
    if undecodable:
        # The names print on the operator's stderr, where the leak scan's
        # rule applies: a path can itself be the secret, so the configured
        # markers mask them exactly as the gate's warning does — read from
        # the same trusted source (a sidecar's own config, else the
        # merge-base tree). Naming is required, so a marker read that fails
        # refuses rather than prints the names unmasked. The prompt's names
        # are not masked — they must match the names inside the diff text the
        # reviewer is shown — but they go through escape_for_display like
        # every value the prompt places into a line.
        try:
            markers = (
                markers_from_config(journal_root.parents[1])
                if sidecar_journal is not None
                else markers_from_tree(project_root, merge_base)
            )
        except (CaptureError, GateError, ValueError) as error:
            raise ReviewLaunchError(
                f"cannot read configured private markers: {error}"
            ) from error
        diff_note = (
            "diff sections that did not decode as UTF-8 (the reviewer is "
            "shown what decoded and told): "
            + render_undecodable_files(undecodable, markers, limit=None)
        )

    def prompt_builder(snapshot: Path) -> tuple[str, str]:
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
        except (OSError, UnicodeDecodeError) as error:
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
            undecodable_files=tuple(undecodable),
        )
        return prompt, contract

    return _launch_review_tail(
        journal_root,
        task_id,
        reviewer_role,
        reviewer_vendor,
        reviewer_model,
        reviewer_email,
        snapshot_builder=lambda snapshot: _extract_snapshot(
            project_root, resolved_commit, snapshot
        ),
        prompt_builder=prompt_builder,
        subject_fields=frozenset({"reviewed_commit"}),
        expected_subject_field="reviewed_commit",
        expected_subject=resolved_commit,
        subject_mismatch=lambda _subject_field, _subject: (
            "reviewer verdict reviewed_commit does not match commit"
        ),
        reviewed_commit=resolved_commit,
        prose_capture_level=prose_capture_level,
        operator_note=diff_note,
    )
