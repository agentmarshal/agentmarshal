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
from pathlib import Path
from typing import cast

from agentmarshal.journal.brief import (
    append_amendment_history,
    render_amendment_history,
)
from agentmarshal.journal.contracts import parse_contract_text
from agentmarshal.journal.extensions import (
    ExtensionManifestMissing,
    read_extension_manifest,
)

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
    SubmittedReview,
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

{named_material}For each blocking or advisory finding id you report, print one line of \
prose
before the verdict block, naming what is wrong and where. The ids are labels
for the machine; the prose is what a human will read.

At the end, print exactly one JSON object between lines containing exactly
{verdict_begin} and {verdict_end}. The object must contain:
- reviewed_commit: the exact reviewed commit SHA
- verdict: exactly one of: {verdicts}
- findings: an array of unique finding-id strings; empty only for "approved",
  and non-empty for every other verdict
and may additionally contain:
- advisory_findings: an array of unique non-blocking finding-id strings,
  disjoint from findings; allowed with any verdict, including "approved"

No other key is accepted.

Task contract:
{contract}

Diff:
{diff}
"""


class ReviewLaunchError(Exception):
    """Raised when a read-only review cannot be launched or recorded."""


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

    verdicts = ", ".join(sorted(REVIEW_VERDICTS))
    named_material = ""
    if decisions or documents or absent_extensions:
        lines = ["Named contract material:"]
        if decisions:
            lines.append("Decisions:")
            lines.extend(f"- {decision}" for decision in decisions)
            lines.append("A finding may cite a contradiction with a named decision.")
        if documents:
            lines.append("Documents:")
            lines.extend(f"- {document}" for document in documents)
        if absent_extensions:
            # A removal candidate deletes its manifest (ADR-0010 D5); the
            # review still launches, and the reviewer is told what is absent.
            lines.append("Extensions whose manifest is absent in the reviewed tree:")
            lines.extend(f"- {name}" for name in absent_extensions)
        named_material = "\n".join(lines) + "\n\n"
    contract_material = append_amendment_history(contract, amendment_history)
    return _REVIEW_PROMPT.format(
        commit=commit,
        named_material=named_material,
        verdict_begin=_VERDICT_BEGIN,
        verdict_end=_VERDICT_END,
        verdicts=verdicts,
        contract=contract_material,
        diff=diff,
    )


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
        # could parse, such as a brace left unclosed by a quoting accident. There
        # is no field name to report in either case, so the refusal quotes the
        # template: the operator needs something to search for.
        raise ReviewLaunchError(
            f"AGENTMARSHAL_REVIEWER_CMD has an invalid placeholder ({error}) in: "
            f"{template_text}"
        ) from error


def _run_reviewer(command: list[str], snapshot: Path, prompt: str) -> bytes:
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
    return result.stdout


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
    output: str, *, preserve_output: bool = True
) -> tuple[str, str, list[str], list[str]]:
    """Parse a verdict, preserving rejected recorded-review output when asked."""

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
    missing = _VERDICT_REQUIRED - keys
    if missing:
        raise reject(
            "reviewer verdict is missing required field(s): "
            + ", ".join(sorted(missing)),
        )
    # An unknown key is still refused — a verdict we do not understand must not
    # be recorded — but the message names it, instead of reporting a shape
    # failure the reviewer cannot act on.
    unknown = keys - _VERDICT_REQUIRED - _VERDICT_OPTIONAL
    if unknown:
        raise reject(
            "reviewer verdict has unsupported field(s): " + ", ".join(sorted(unknown)),
        )
    reviewed_commit = verdict_data["reviewed_commit"]
    verdict = verdict_data["verdict"]
    findings = verdict_data["findings"]
    advisory = verdict_data.get("advisory_findings", [])
    if not isinstance(reviewed_commit, str) or not isinstance(verdict, str):
        raise reject("reviewer verdict fields must be strings")
    for name, value in (("findings", findings), ("advisory_findings", advisory)):
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise reject(f"reviewer verdict {name} must be an array of strings")
    return (
        reviewed_commit,
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


def dry_run_review(project_root: Path, reviewer_model: str | None) -> None:
    """Exercise the configured reviewer without writing to any journal.

    The command runs where a recorded review runs it: in a snapshot, so a
    relative path in the template resolves as it will in earnest. The tree is
    the current ``HEAD`` rather than a commit the operator names, which is a
    departure from this change's design note and is recorded there.
    """

    template = os.environ.get("AGENTMARSHAL_REVIEWER_CMD")
    if template is not None and "{model}" in template and reviewer_model is None:
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
        # it cannot be, and the caller is told which of the two it got.
        try:
            _run_git(project_root, ["rev-parse", "--verify", "HEAD^{commit}"])
        except ReviewLaunchError:
            snapshot.mkdir()
        else:
            _extract_snapshot(project_root, "HEAD", snapshot)
        output = _run_reviewer(
            _reviewer_command(reviewer_model or "", prompt_file), snapshot, prompt
        ).decode("utf-8", errors="replace")
        try:
            verdict = _parse_verdict(output, preserve_output=False)
        except ReviewLaunchError as error:
            # The operator is debugging this command; the output is the evidence.
            # It goes beside the rejected-verdict copies, outside any journal.
            try:
                kept = _preserve_output(output)
            except OSError:
                raise ReviewLaunchError(f"reviewer output: {error}") from error
            raise ReviewLaunchError(
                f"reviewer output: {error}; what the command printed is at {kept}"
            ) from error
        # The recorded path refuses a verdict about another commit, and so does
        # this one: a command that echoes a commit of its own would pass a check
        # that only parsed.
        if verdict[0] != _DRY_RUN_COMMIT:
            raise ReviewLaunchError(
                "reviewer verdict names a commit the dry run did not ask about: "
                f"{verdict[0]}"
            )


def launch_review(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    *,
    journal_root: Path | None = None,
) -> SubmittedReview:
    """Review an exact commit in a temporary metadata-free snapshot and record it."""

    sidecar_journal = journal_root
    journal_root = journal_root or project_root / ".agentmarshal" / "journal"
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
        raw_output = _run_reviewer(
            _reviewer_command(reviewer_model, prompt_file),
            snapshot,
            prompt,
        )
        # The verdict is parsed from a decoded copy; the artifact pins the
        # bytes the reviewer wrote, so nothing is normalised on the way.
        output = raw_output.decode("utf-8", errors="replace")
        reviewer_output = output
        reviewed_commit, verdict, findings, advisory = _parse_verdict(output)
        if reviewed_commit != resolved_commit:
            raise _reject(
                output, "reviewer verdict reviewed_commit does not match commit"
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
            raise ReviewLaunchError(str(error)) from error
        # A verdict can parse cleanly and still be refused by record validation —
        # an unknown verdict value, empty findings for a non-approving verdict,
        # duplicates, or advisory ids overlapping findings. That path discarded
        # the analysis too, and it is the one seen most often in practice.
        raise _reject(reviewer_output, str(error)) from error
    return submitted
