"""Append-only journal evidence records."""

from __future__ import annotations

import json
import re
import secrets
import threading
import time
import unicodedata
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

from agentmarshal.journal.actors import resolve_recorded_by

# Reuse the hardened no-follow exclusive creator from project.py so record
# files get the same symlink/race guarantees as the project file.
from agentmarshal.journal.attestation import (
    RECORD_TYPES,
    SOURCE_LIVE,
    SOURCE_VALUES,
    is_registered_record_type,
)

# The signature ids an acknowledgement's `signature` may name are the scan's
# own — read from its table, never listed a second time (ADR-0021).
from agentmarshal.journal.capture import _LEAK_PATTERNS
from agentmarshal.project import UnsafeProjectPathError, _create_exclusive

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RANDOM_MASK = (1 << 80) - 1
_TASK_ID_PATTERN = re.compile(r"CR-[0-9]+$")
_RECORD_FILENAME_PATTERN = re.compile(
    r"(?P<record_id>[0-7][0123456789ABCDEFGHJKMNPQRSTVWXYZ]{25})-"
    r"(?P<record_type>[a-z]+)\.json$"
)
_RECORD_FIELDS = {
    "opened": frozenset(
        {"schema", "record_type", "task", "created_at", "tool_version"}
    ),
    "review": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reviewed_commit",
            "reviewed_finding",
            "verdict",
            "reviewer",
            "findings",
            "advisory_findings",
        }
    ),
    "acceptance": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "accepted_commit",
            "accepted_finding",
            "accepted_by",
            "findings",
            "reason",
        }
    ),
    "completed": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "completed_commit",
            "completed_finding",
        }
    ),
    "abandoned": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reason",
        }
    ),
    "reopened": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reason",
        }
    ),
    "amendment": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reason",
        }
    ),
    "session": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "role",
            "actor",
            "activity",
            "outcome",
            "tokens",
        }
    ),
    "finding": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "summary",
        }
    ),
    "check": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
        }
    ),
    "acknowledgement": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
        }
    ),
}
# Schema 2 adds provenance (ADR-0005): a required ``source`` and optional
# ``artifacts`` references. They are permitted on schema 2 and above — a
# schema 1 record carrying them is rejected as an unexpected field.
# ``recorded_by`` names the actor that created the record and
# ``recorded_by_source`` says where that name came from (ADR-0006). Both are
# optional, so every record written before they existed stays valid. They are
# declarations, not authentication.
_SCHEMA_2_FIELDS = frozenset(
    {"source", "artifacts", "recorded_by", "recorded_by_source"}
)
_SCHEMA_2_SESSION_FIELDS = frozenset({"usage"})
_RECORDED_BY_SOURCES = frozenset({"project-actor", "git-identity", "override"})
# Schema 7 (ADR-0022) is the schema the 0.5.0 record model arrives under.
# Its remaining field families and record types register in the tasks that
# introduce them; a record stamped 7 without a registered family may carry
# only what the earlier schemas admit, and a writer stamps 7 only when the
# record it builds carries a field a schema-7 family admits.
_SUPPORTED_SCHEMAS = frozenset({1, 2, 3, 4, 5, 6, 7})
_SCHEMA_4_FIELDS = frozenset(
    {"reviewed_finding", "accepted_finding", "completed_finding"}
)
_SCHEMA_5_FIELDS = frozenset({"reviewed_contract"})
# What a session produced and with what (ADR-0022 section 2): the commit
# the run produced, the model it ran, an external trace link, the CLI
# session a resume needs, the report-ready flag and the fallback reason.
_SCHEMA_7_SESSION_FIELDS = frozenset(
    {"commit", "model", "trace", "cli_session", "report_ready", "fallback_reason"}
)
# The contract hash the records that establish a contract carry (ADR-0018
# decision 1, ADR-0022 section 2): `opened` and `amendment` may carry the
# sha256 of the contract text they establish.
_SCHEMA_7_CONTRACT_FIELDS = frozenset({"contract"})
# What a pipeline check found on a commit (ADR-0017 decision 1, ADR-0022
# section 3): the commit it ran on, the check's name and result, and
# optionally the step that failed, a bounded excerpt and a link to the run.
_CHECK_RECORD_SCHEMA = 7
_SCHEMA_7_CHECK_FIELDS = frozenset(
    {"commit", "name", "result", "failed_step", "excerpt", "run_url"}
)
_CHECK_RESULTS = frozenset({"passed", "failed", "error", "skipped"})
_CHECK_EXCERPT_BYTE_LIMIT = 4 * 1024
# What a reviewed leak-scan hit leaves (ADR-0021, ADR-0022 section 3): the
# candidate's commit, the file exactly as the scan prints it — masked, so the
# record can never carry a marker's value — the hit's identification (a
# signature id or the marker's position, never the matched text) and a
# bounded reason. The signature ids are the scan's own, read from its table
# so a signature the scan gains joins the vocabulary the record admits.
_ACKNOWLEDGEMENT_RECORD_SCHEMA = 7
_SCHEMA_7_ACKNOWLEDGEMENT_FIELDS = frozenset(
    {"commit", "file", "signature", "marker", "reason"}
)
_ACKNOWLEDGEMENT_REASON_CHAR_LIMIT = 1000
_LEAK_SIGNATURE_IDS = frozenset(name for name, _pattern in _LEAK_PATTERNS)
# The two forms an acceptance takes from schema 7 beside ADR-0007's
# acceptance over findings (ADR-0013 decisions 5 and 17, ADR-0022 section
# 2): `accepted_pause` — the acceptance of an extension pause, an object
# carrying exactly `extension` — and `operational` — the acceptance of an
# operational CR, carrying only `true`. Both bind by `accepted_commit`;
# neither carries `findings`.
_SCHEMA_7_ACCEPTANCE_FIELDS = frozenset({"accepted_pause", "operational"})
_ACCEPTANCE_FORMS = frozenset({"findings", "accepted_pause", "operational"})
# What a review links and classifies (ADR-0016 decisions 2 and 3,
# ADR-0022 section 2): `previous_review` — the id of the task's previous
# review, so the task's reviews form a chain — and `classes` — a class
# for each finding the record names. `actor` inside `reviewer`
# (ADR-0018 decision 3) is the family's third field but a key of the
# reviewer object rather than of the record, so the family names the two
# top-level fields and `reviewer.actor` is admitted where the object's
# closed keys are checked.
_SCHEMA_7_REVIEW_FIELDS = frozenset({"previous_review", "classes"})
_SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}$")
_REVIEWED_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}$")
_REVIEW_VERDICTS = frozenset({"approved", "changes_required", "blocked", "rejected"})
_SESSION_ACTIVITIES = frozenset({"implementation", "review", "other", "coordination"})
_COORDINATION_SESSION_SCHEMA = 6
_SESSION_USAGE_METHODS = frozenset({"measured", "reported"})
_ulid_lock = threading.Lock()
_last_timestamp = -1
_last_randomness = 0


class JournalRecordError(ValueError):
    """Raised when a journal record is malformed."""


def validate_task_id(task_id: str) -> None:
    """Raise when *task_id* is not a canonical journal task identifier."""

    if _TASK_ID_PATTERN.fullmatch(task_id) is None:
        raise JournalRecordError("task id must match CR-<number>")


def _encode_base32(value: int, length: int) -> str:
    characters = ["0"] * length
    for index in range(length - 1, -1, -1):
        characters[index] = _CROCKFORD_BASE32[value & 31]
        value >>= 5
    return "".join(characters)


def generate_ulid() -> str:
    """Return a lexicographically sortable ULID-class identifier."""

    global _last_randomness, _last_timestamp
    timestamp = time.time_ns() // 1_000_000
    with _ulid_lock:
        if timestamp > _last_timestamp:
            randomness = secrets.randbits(80)
        else:
            timestamp = _last_timestamp
            randomness = _last_randomness + 1
            if randomness > _ULID_RANDOM_MASK:
                timestamp += 1
                randomness = secrets.randbits(80)
        _last_timestamp = timestamp
        _last_randomness = randomness
    return _encode_base32(timestamp, 10) + _encode_base32(randomness, 16)


def _is_ulid(value: str) -> bool:
    return (
        len(value) == 26
        and value[0] in "01234567"
        and all(character in _CROCKFORD_BASE32 for character in value)
    )


# Read-time rules and the schema each applies from (ADR-0015). A rule is a
# named check on a record — over the record type, a field, a field's value,
# or the record against where it lies — raising JournalRecordError.
# `_RULES` registers them in check order; `_RULE_FROM_SCHEMA` binds each to
# the schema it applies from at read time (decision 7): every rule that
# exists today applies from schema 1 (decision 6), except the field gates
# already bound to schemas 2, 4, 5 and 6, which keep their numbers. The two
# structures are deliberate: a rule can be registered without a table entry,
# and that gap is what the completeness test catches. A read path whose
# lookup finds no entry applies no rule — skipping is permissive, never a
# refusal, so it is the completeness test that refuses the missing entry.
# A rule that compares the record with where it lies reads that placement
# from the context the caller passes; a rule whose placement the caller
# cannot supply is not applied there. The schema-version check is not a
# rule: `_validate_record` runs it as an explicit first step, before the
# registry, so no rule — wherever it is registered — can read the record's
# schema before it is checked.
class _RuleContext(TypedDict, total=False):
    """What a rule may compare the record against, beyond the record itself.

    ``task`` is the task the record is written to or read from, with
    ``task_label`` the noun a mismatch message gives that place
    ("destination", "directory"); ``filename_record_type`` is the record
    type the file name declares and ``filename`` the file's display name
    for that message; ``finding_ids`` lazily yields the ids of the task's
    finding records.
    """

    task: str
    task_label: str
    filename: str
    filename_record_type: str
    finding_ids: Callable[[], frozenset[str]]


_RuleCheck = Callable[[Mapping[str, object], _RuleContext], None]
_RULES: dict[str, _RuleCheck] = {}


def _rule(name: str) -> Callable[[_RuleCheck], _RuleCheck]:
    """Register a read-time rule under *name*, in source order."""

    def register(check: _RuleCheck) -> _RuleCheck:
        _RULES[name] = check
        return check

    return register


# The field families a record's own schema admits (ADR-0005, ADR-0011): the
# schema-2 provenance fields on every record, ``usage`` on sessions,
# ``reviewed_contract`` on reviews, and the schema-7 session, contract,
# check, acknowledgement and acceptance fields of ADR-0022 sections 2 and
# 3. The fields rule computes the admitted set from the record's schema; a
# later schema registers its family here.
_FIELD_FAMILIES: tuple[tuple[int, str | None, frozenset[str]], ...] = (
    (2, None, _SCHEMA_2_FIELDS),
    (2, "session", _SCHEMA_2_SESSION_FIELDS),
    (5, "review", _SCHEMA_5_FIELDS),
    (7, "session", _SCHEMA_7_SESSION_FIELDS),
    (7, "opened", _SCHEMA_7_CONTRACT_FIELDS),
    (7, "amendment", _SCHEMA_7_CONTRACT_FIELDS),
    (7, "check", _SCHEMA_7_CHECK_FIELDS),
    (7, "acknowledgement", _SCHEMA_7_ACKNOWLEDGEMENT_FIELDS),
    (7, "acceptance", _SCHEMA_7_ACCEPTANCE_FIELDS),
    (7, "review", _SCHEMA_7_REVIEW_FIELDS),
)


def _allowed_fields(record_type: str, schema: int) -> frozenset[str]:
    fields = _RECORD_FIELDS[record_type]
    for introduced, only_type, family in _FIELD_FAMILIES:
        if schema >= introduced and (only_type is None or record_type == only_type):
            fields = fields | family
    return fields


# The field registrations the shared validators read (ADR-0022 section 8):
# which fields the bounded-text, bounded-text-bytes, bounded-JSON and
# forgeable-text rules guard, and with what bound. Two text bounds because
# the ADR's figures are not all the same measure: ``reason`` is a character
# count and ``excerpt`` a byte count — a text bounded in bytes is measured
# on its UTF-8 encoding, the form a record file and a rendered line carry.
# A registration keys on the record type whose field it guards — ADR-0022's
# ``reason`` bound is for the new record types alone, and a bare field-name
# key could not keep it off the ``reason`` fields acceptance, abandoned,
# reopened and amendment already carry. ``None`` in the record-type slot is
# the explicit "every type" form, for a field the rule guards on every type
# that carries it; a name shared with an older record type is never that
# case. All four tables are dicts, so iteration is registration order and
# the field a refusal names is stable; a field family registers its fields
# into the validators it needs and nothing more. The schema-7 session
# family registers its five string fields below; ADR-0022 section 8 bounds
# no length for them, so the limit tables hold none of the family.
# `commit`'s entry never fires — the 40-lowercase-hex shape rule refuses
# every character the forgeable-text rule would, and runs first — but the
# family registers every string field, so the entry stands beside it. The
# contract family's `contract` registers the same way on each of its two
# record types, its 64-hex shape rule standing first the same way. The
# check family registers its `excerpt` at the ADR's 4 KiB byte bound and
# its four displayed strings under the forgeable-text rule; its `commit`
# hex shape and `result` vocabulary admit no character that rule refuses,
# so they carry no registration. The acknowledgement family registers its
# `reason` at the ADR's 1000-character bound — a character count, as the
# ADR states it — and its two displayed strings under the forgeable-text
# rule; `commit`'s hex shape, the signature vocabulary and `marker`'s
# integer shape admit no character that rule refuses either. The
# acceptance family registers nothing: `accepted_pause` is an object, not
# a displayed string, so the extension name it carries gets the same
# `_reject_control_characters` check the finding ids get inline, inside
# the family's shape rule. The review family registers its
# `previous_review` the same completeness way `commit` registers: the
# ULID shape admits no character the forgeable-text rule refuses, so the
# entry never fires. `classes` is an object and `actor` a key of the
# reviewer object — a table entry would fail-closed on the dict, and a
# top-level key could never reach the nested string — so each takes the
# same `_reject_control_characters` check inside the family's own rule,
# as `accepted_pause`'s `extension` does.
_TEXT_CHAR_LIMITS: dict[tuple[str | None, str], int] = {
    ("acknowledgement", "reason"): _ACKNOWLEDGEMENT_REASON_CHAR_LIMIT,
}
_TEXT_BYTE_LIMITS: dict[tuple[str | None, str], int] = {
    ("check", "excerpt"): _CHECK_EXCERPT_BYTE_LIMIT,
}
_JSON_BYTE_LIMITS: dict[tuple[str | None, str], int] = {}
_FORGEABLE_TEXT_FIELDS: dict[tuple[str | None, str], None] = {
    ("session", "commit"): None,
    ("session", "model"): None,
    ("session", "trace"): None,
    ("session", "cli_session"): None,
    ("session", "fallback_reason"): None,
    ("opened", "contract"): None,
    ("amendment", "contract"): None,
    ("check", "name"): None,
    ("check", "failed_step"): None,
    ("check", "excerpt"): None,
    ("check", "run_url"): None,
    ("acknowledgement", "file"): None,
    ("acknowledgement", "reason"): None,
    ("review", "previous_review"): None,
}


def _check_schema_version(data: Mapping[str, object]) -> None:
    """The explicit first step of validation, ahead of every rule."""

    schema = data.get("schema")
    if type(schema) is not int or schema not in _SUPPORTED_SCHEMAS:
        raise JournalRecordError("record has an unknown or missing schema version")


@_rule("record-type")
def _check_record_type(data: Mapping[str, object], _context: _RuleContext) -> None:
    record_type = data.get("record_type")
    if not isinstance(record_type, str) or record_type not in _RECORD_FIELDS:
        raise JournalRecordError("record has an unknown or missing record type")


@_rule("record-type-predicate")
def _check_record_type_predicate(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    # Every accepted record type must be projectable to an in-toto
    # Statement; a type without a registered predicateType could not be,
    # so reject it fail-closed (ADR-0005 Decision 5).
    record_type = cast(str, data["record_type"])
    if not is_registered_record_type(record_type):
        raise JournalRecordError(
            f"record type {record_type!r} has no registered predicateType"
        )


@_rule("reviewed-contract")
def _check_reviewed_contract(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    if "reviewed_contract" in data and cast(int, data["schema"]) < 5:
        raise JournalRecordError("record field 'reviewed_contract' requires schema 5")


@_rule("fields")
def _check_fields(data: Mapping[str, object], _context: _RuleContext) -> None:
    allowed_fields = _allowed_fields(
        cast(str, data["record_type"]), cast(int, data["schema"])
    )
    unexpected_fields = data.keys() - allowed_fields
    if unexpected_fields:
        raise JournalRecordError(
            f"record has unsupported fields: {', '.join(sorted(unexpected_fields))}"
        )


@_rule("required-strings")
def _check_required_strings(data: Mapping[str, object], _context: _RuleContext) -> None:
    for field in ("record_type", "task", "created_at"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"record field {field!r} must be a non-empty string"
            )


@_rule("created-at")
def _check_created_at(data: Mapping[str, object], _context: _RuleContext) -> None:
    try:
        created_at = datetime.fromisoformat(
            cast(str, data["created_at"]).replace("Z", "+00:00")
        )
    except ValueError as error:
        raise JournalRecordError(
            "record field 'created_at' must be an ISO-8601 timestamp"
        ) from error
    if created_at.tzinfo is None or created_at.utcoffset() != UTC.utcoffset(created_at):
        raise JournalRecordError("record field 'created_at' must be a UTC timestamp")


@_rule("tool-version")
def _check_tool_version(data: Mapping[str, object], _context: _RuleContext) -> None:
    tool_version = data.get("tool_version")
    if not isinstance(tool_version, str) or not tool_version:
        raise JournalRecordError(
            "record field 'tool_version' must be a non-empty string"
        )


@_rule("review")
def _check_review_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "review":
        _validate_review_record(data)


@_rule("acceptance")
def _check_acceptance_record(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    if cast(str, data["record_type"]) == "acceptance":
        _validate_acceptance_record(data)


@_rule("completed")
def _check_completed_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "completed":
        _validate_binding(data, "completed", "completed_commit", "completed_finding")


@_rule("finding")
def _check_finding_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "finding":
        _validate_finding_record(data)


@_rule("abandoned")
def _check_abandoned_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "abandoned":
        reason = data.get("reason")
        if not isinstance(reason, str) or not reason:
            raise JournalRecordError(
                "abandoned record field 'reason' must be a non-empty string"
            )


@_rule("reopened")
def _check_reopened_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "reopened":
        reason = data.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise JournalRecordError(
                "reopened record field 'reason' must be a non-empty string"
            )


@_rule("amendment")
def _check_amendment_record(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) == "amendment":
        reason = data.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise JournalRecordError(
                "amendment record field 'reason' must be a non-empty string"
            )


@_rule("check")
def _check_check_schema(data: Mapping[str, object], _context: _RuleContext) -> None:
    # The record-type gate, bound to 1 like `fields` itself: a check
    # record below the schema the type arrived under is refused at write
    # and on read, whatever it carries. The family's fields are admitted
    # only from schema 7, so a check carrying them meets the
    # unsupported-fields refusal first; this rule is what also refuses
    # the type where no field forces it, and no legitimate history can
    # carry it.
    if (
        cast(str, data["record_type"]) == "check"
        and cast(int, data["schema"]) < _CHECK_RECORD_SCHEMA
    ):
        raise JournalRecordError(f"check records require schema {_CHECK_RECORD_SCHEMA}")


@_rule("acknowledgement")
def _check_acknowledgement_schema(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    # The record-type gate, bound to 1 like `check`: an acknowledgement
    # record below the schema the type arrived under is refused at write
    # and on read, whatever it carries — the family's fields already meet
    # the unsupported-fields refusal, this covers the record that carries
    # none of them, and no legitimate history can carry the type.
    if (
        cast(str, data["record_type"]) == "acknowledgement"
        and cast(int, data["schema"]) < _ACKNOWLEDGEMENT_RECORD_SCHEMA
    ):
        raise JournalRecordError(
            f"acknowledgement records require schema {_ACKNOWLEDGEMENT_RECORD_SCHEMA}"
        )


@_rule("session-fields")
def _check_session_fields(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "session":
        return
    for field in ("role", "actor", "outcome"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"session record field {field!r} must be a non-empty string"
            )
    activity = data.get("activity")
    if not isinstance(activity, str) or activity not in _SESSION_ACTIVITIES:
        raise JournalRecordError(
            "session record field 'activity' must be one of "
            + ", ".join(sorted(_SESSION_ACTIVITIES))
        )


@_rule("coordination")
def _check_coordination(data: Mapping[str, object], _context: _RuleContext) -> None:
    if (
        cast(str, data["record_type"]) == "session"
        and data.get("activity") == "coordination"
        and cast(int, data["schema"]) < _COORDINATION_SESSION_SCHEMA
    ):
        raise JournalRecordError(
            f"session activity 'coordination' requires schema "
            f"{_COORDINATION_SESSION_SCHEMA}"
        )


@_rule("session-tokens")
def _check_session_tokens(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "session":
        return
    tokens = data.get("tokens")
    if not isinstance(tokens, dict) or tokens.keys() != {"input", "output", "cache"}:
        raise JournalRecordError(
            "session record field 'tokens' must contain only input, output, and cache"
        )
    for field in ("input", "output", "cache"):
        value = tokens[field]
        if type(value) is not int or value < 0:
            raise JournalRecordError(
                f"session record token {field!r} must be an integer greater "
                "than or equal to zero"
            )


@_rule("session-usage")
def _check_session_usage(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "session" or "usage" not in data:
        return
    usage = data["usage"]
    if not isinstance(usage, dict):
        raise JournalRecordError("session record field 'usage' must be an object")
    expected_fields = {"provider", "method"}
    unexpected_fields = usage.keys() - expected_fields
    if unexpected_fields:
        raise JournalRecordError(
            "session record field 'usage' has unsupported fields: "
            + ", ".join(sorted(str(field) for field in unexpected_fields))
        )
    if usage.keys() != expected_fields:
        raise JournalRecordError(
            "session record field 'usage' must contain provider and method"
        )
    provider = usage["provider"]
    if not isinstance(provider, str) or not provider:
        raise JournalRecordError(
            "session record usage field 'provider' must be a non-empty string"
        )
    method = usage["method"]
    if not isinstance(method, str) or method not in _SESSION_USAGE_METHODS:
        raise JournalRecordError(
            "session record usage field 'method' must be one of measured or reported"
        )


@_rule("session-fields-7")
def _check_session_fields_7(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "session":
        return
    if "commit" in data:
        commit = data["commit"]
        if (
            not isinstance(commit, str)
            or _REVIEWED_COMMIT_PATTERN.fullmatch(commit) is None
        ):
            raise JournalRecordError(
                "session record field 'commit' must be exactly 40 "
                "lowercase hex characters"
            )
    for field in ("model", "trace", "cli_session", "fallback_reason"):
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise JournalRecordError(
                f"session record field {field!r} must be a non-empty string"
            )
    if "report_ready" in data and type(data["report_ready"]) is not bool:
        raise JournalRecordError(
            "session record field 'report_ready' must be a boolean"
        )


@_rule("contract-hash-7")
def _check_contract_hash_7(data: Mapping[str, object], _context: _RuleContext) -> None:
    if "contract" not in data:
        return
    contract = data["contract"]
    if not isinstance(contract, str) or _SHA256_HEX_PATTERN.fullmatch(contract) is None:
        raise JournalRecordError(
            "record field 'contract' must be exactly 64 lowercase hex characters"
        )


@_rule("check-fields-7")
def _check_check_fields_7(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "check":
        return
    commit = data.get("commit")
    if (
        not isinstance(commit, str)
        or _REVIEWED_COMMIT_PATTERN.fullmatch(commit) is None
    ):
        raise JournalRecordError(
            "check record field 'commit' must be exactly 40 lowercase hex characters"
        )
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise JournalRecordError("check record field 'name' must be a non-empty string")
    result = data.get("result")
    if not isinstance(result, str) or result not in _CHECK_RESULTS:
        raise JournalRecordError(
            "check record field 'result' must be one of "
            + ", ".join(sorted(_CHECK_RESULTS))
        )
    for field in ("failed_step", "excerpt", "run_url"):
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise JournalRecordError(
                f"check record field {field!r} must be a non-empty string"
            )


@_rule("acknowledgement-fields-7")
def _check_acknowledgement_fields_7(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    if cast(str, data["record_type"]) != "acknowledgement":
        return
    commit = data.get("commit")
    if (
        not isinstance(commit, str)
        or _REVIEWED_COMMIT_PATTERN.fullmatch(commit) is None
    ):
        raise JournalRecordError(
            "acknowledgement record field 'commit' must be exactly 40 "
            "lowercase hex characters"
        )
    file = data.get("file")
    if not isinstance(file, str) or not file.strip():
        raise JournalRecordError(
            "acknowledgement record field 'file' must be a non-empty string"
        )
    has_signature = "signature" in data
    has_marker = "marker" in data
    if has_signature == has_marker:
        raise JournalRecordError(
            "acknowledgement record must name exactly one of 'signature' or 'marker'"
        )
    if has_signature:
        signature = data["signature"]
        if not isinstance(signature, str) or signature not in _LEAK_SIGNATURE_IDS:
            raise JournalRecordError(
                "acknowledgement record field 'signature' must be one of "
                + ", ".join(sorted(_LEAK_SIGNATURE_IDS))
            )
    else:
        marker = data["marker"]
        if type(marker) is not int or marker < 1:
            raise JournalRecordError(
                "acknowledgement record field 'marker' must be an integer of at least 1"
            )
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise JournalRecordError(
            "acknowledgement record field 'reason' must be a non-empty string"
        )


@_rule("acceptance-fields-7")
def _check_acceptance_fields_7(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    if cast(str, data["record_type"]) != "acceptance":
        return
    new_form = next(iter(sorted(data.keys() & _SCHEMA_7_ACCEPTANCE_FIELDS)), None)
    if new_form is None:
        return
    # Both new forms bind `accepted_commit` alone (ADR-0022 section 2): a
    # pause raises no review finding to bind, and an operational CR carries
    # no review at all — `accepted_finding` is refused on either.
    if "accepted_finding" in data:
        raise JournalRecordError(
            f"acceptance record field {new_form!r} binds by "
            "'accepted_commit', never 'accepted_finding'"
        )
    if "accepted_pause" in data:
        pause = data["accepted_pause"]
        if not isinstance(pause, dict) or pause.keys() != {"extension"}:
            raise JournalRecordError(
                "acceptance record field 'accepted_pause' must be an object "
                "carrying only 'extension'"
            )
        extension = pause["extension"]
        # The name rule an extension manifest applies (extensions.py's
        # `_validate_name`): non-empty, one path component — never `.`,
        # `..`, or a name carrying `/` or `\` — and no character that could
        # forge a line. The rule is replicated rather than imported:
        # extensions.py stands on this module, and an import back would
        # cycle.
        if not isinstance(extension, str):
            raise JournalRecordError(
                "acceptance record 'accepted_pause' field 'extension' must be a string"
            )
        _reject_control_characters(
            extension, "acceptance record 'accepted_pause' field 'extension'"
        )
        if (
            not extension
            or extension in {".", ".."}
            or "/" in extension
            or "\\" in extension
        ):
            raise JournalRecordError(
                "acceptance record 'accepted_pause' field 'extension' must be "
                "one non-empty path component"
            )
    if "operational" in data and data["operational"] is not True:
        raise JournalRecordError("acceptance record field 'operational' must be true")


@_rule("review-fields-7")
def _check_review_fields_7(data: Mapping[str, object], _context: _RuleContext) -> None:
    if cast(str, data["record_type"]) != "review":
        return
    if "previous_review" in data:
        previous = data["previous_review"]
        if not isinstance(previous, str) or not _is_ulid(previous):
            raise JournalRecordError(
                "review record field 'previous_review' must be a "
                "26-character Crockford base32 ULID"
            )
    if "classes" in data:
        classes = data["classes"]
        if not isinstance(classes, dict) or not classes:
            raise JournalRecordError(
                "review record field 'classes' must be a non-empty object "
                "keyed by finding id"
            )
        # A class's key may name only a finding the record itself names;
        # `findings` and `advisory_findings` are inside the record — at
        # hand at write and on read alike — and the `review` rule has
        # already refused a malformed one when this rule runs.
        named: set[object] = set()
        for field in ("findings", "advisory_findings"):
            ids = data.get(field)
            if isinstance(ids, list):
                named.update(ids)
        for finding_id, finding_class in classes.items():
            if finding_id not in named:
                raise JournalRecordError(
                    "review record 'classes' key must name a finding id the "
                    "record carries in 'findings' or 'advisory_findings'"
                )
            if not isinstance(finding_class, str) or not finding_class.strip():
                raise JournalRecordError(
                    "review record 'classes' value must be a non-empty string"
                )
            _reject_control_characters(finding_class, "review record 'classes' value")
    # `reviewer.actor` is a key of the reviewer object: the `review`
    # rule's closed-key check has admitted it here, and this rule checks
    # its shape with the family's.
    reviewer = data.get("reviewer")
    if isinstance(reviewer, dict) and "actor" in reviewer:
        actor = reviewer["actor"]
        if not isinstance(actor, str) or not actor.strip():
            raise JournalRecordError(
                "review record reviewer field 'actor' must be a non-empty string"
            )
        _reject_control_characters(actor, "review record reviewer field 'actor'")


@_rule("provenance")
def _check_provenance(data: Mapping[str, object], _context: _RuleContext) -> None:
    # Provenance was introduced at schema 2 (ADR-0005 Decision 4); the rule
    # keeps its own guard so a schema-1 record stays writable, and the
    # table's 2 keeps a reader from demanding it of older records either.
    if cast(int, data["schema"]) >= 2:
        _validate_provenance(data)


@_rule("recorded-by")
def _check_recorded_by(data: Mapping[str, object], _context: _RuleContext) -> None:
    _validate_recorded_by(data)


@_rule("finding-binding")
def _check_finding_binding(data: Mapping[str, object], _context: _RuleContext) -> None:
    needs_schema_4 = cast(str, data["record_type"]) == "finding" or bool(
        data.keys() & _SCHEMA_4_FIELDS
    )
    if needs_schema_4 and cast(int, data["schema"]) < 4:
        raise JournalRecordError(
            "finding records and finding bindings require schema 4"
        )


@_rule("task-placement")
def _check_task_placement(data: Mapping[str, object], context: _RuleContext) -> None:
    # The record's task against where it lies — the destination on write,
    # the directory on read. A content check has no destination, so it
    # supplies neither and the gate compares task and path itself.
    expected = context.get("task")
    if expected is not None and data["task"] != expected:
        raise JournalRecordError(
            f"record task does not match its {context['task_label']}"
        )


@_rule("filename-record-type")
def _check_filename_record_type(
    data: Mapping[str, object], context: _RuleContext
) -> None:
    declared = context.get("filename_record_type")
    if declared is not None and data["record_type"] != declared:
        where = f": {context['filename']}" if "filename" in context else ""
        raise JournalRecordError("record type does not match its filename" + where)


@_rule("finding-binding-target")
def _check_finding_binding_target(
    data: Mapping[str, object], context: _RuleContext
) -> None:
    # The named finding against the task's findings — a set only the write
    # side supplies, where the author can still fix the input; the read
    # side does not, so what history accepts is unchanged.
    bindings = data.keys() & _SCHEMA_4_FIELDS
    finding_ids = context.get("finding_ids")
    if bindings and finding_ids is not None:
        binding = next(iter(bindings))
        if data[binding] not in finding_ids():
            raise JournalRecordError(
                f"record field {binding!r} must name a finding in the same task"
            )


def _check_text_limits(
    data: Mapping[str, object],
    limits: Mapping[tuple[str | None, str], int],
    measure: Callable[[str], int],
    unit: str,
) -> None:
    record_type = cast(str, data["record_type"])
    for (only_type, field), limit in limits.items():
        if (only_type is not None and record_type != only_type) or field not in data:
            continue
        value = data[field]
        if not isinstance(value, str) or measure(value) > limit:
            raise JournalRecordError(
                f"record field {field!r} must be a string of at most {limit} {unit}"
            )


@_rule("bounded-text")
def _check_bounded_text(data: Mapping[str, object], _context: _RuleContext) -> None:
    _check_text_limits(data, _TEXT_CHAR_LIMITS, len, "characters")


@_rule("bounded-text-bytes")
def _check_bounded_text_bytes(
    data: Mapping[str, object], _context: _RuleContext
) -> None:
    _check_text_limits(
        data,
        _TEXT_BYTE_LIMITS,
        lambda value: len(value.encode("utf-8")),
        "UTF-8 bytes",
    )


@_rule("bounded-json")
def _check_bounded_json(data: Mapping[str, object], _context: _RuleContext) -> None:
    record_type = cast(str, data["record_type"])
    for (only_type, field), limit in _JSON_BYTE_LIMITS.items():
        if (only_type is not None and record_type != only_type) or field not in data:
            continue
        try:
            encoded = _canonical_json(data[field])
        except (TypeError, ValueError) as error:
            raise JournalRecordError(
                f"record field {field!r} must be a JSON value"
            ) from error
        if len(encoded) > limit:
            raise JournalRecordError(
                f"record field {field!r} must encode to at most {limit} bytes"
            )


@_rule("forgeable-text")
def _check_forgeable_text(data: Mapping[str, object], _context: _RuleContext) -> None:
    record_type = cast(str, data["record_type"])
    for only_type, field in _FORGEABLE_TEXT_FIELDS:
        if (only_type is not None and record_type != only_type) or field not in data:
            continue
        value = data[field]
        # Fail-closed like bounded-text: a registered field carrying a
        # non-string is refused here rather than skipped, since the field
        # may carry no shape rule of its own to own the type refusal.
        if not isinstance(value, str):
            raise JournalRecordError(f"record field {field!r} must be a string")
        _reject_control_characters(value, f"record field {field!r}")


# The table ADR-0015 decision 7 asks for: rule → the schema it applies from
# at read time. The write path applies every rule regardless; the read paths
# apply a rule only to records of this schema and above. The shared
# validators are bound to 7 — the schema whose fields they guard — and are
# entries of their own, never folded into a schema-1 rule: a tightening
# hidden inside one would apply to records older schemas wrote. The
# session-fields-7 and contract-hash-7 shape rules take the same binding
# for the same reason.
_RULE_FROM_SCHEMA: dict[str, int] = {
    "record-type": 1,
    "record-type-predicate": 1,
    "reviewed-contract": 5,
    "fields": 1,
    "required-strings": 1,
    "created-at": 1,
    "tool-version": 1,
    "review": 1,
    "acceptance": 1,
    "completed": 1,
    "finding": 1,
    "abandoned": 1,
    "reopened": 1,
    "amendment": 1,
    "check": 1,
    "acknowledgement": 1,
    "session-fields": 1,
    "coordination": 6,
    "session-tokens": 1,
    "session-usage": 1,
    "session-fields-7": 7,
    "contract-hash-7": 7,
    "check-fields-7": 7,
    "acknowledgement-fields-7": 7,
    "acceptance-fields-7": 7,
    "review-fields-7": 7,
    "provenance": 2,
    "recorded-by": 1,
    "finding-binding": 4,
    "task-placement": 1,
    "filename-record-type": 1,
    "finding-binding-target": 1,
    "bounded-text": 7,
    "bounded-text-bytes": 7,
    "bounded-json": 7,
    "forgeable-text": 7,
}


def _validate_record(
    record: Mapping[str, object], *, for_write: bool, context: _RuleContext
) -> dict[str, object]:
    """Check *record* and return it as a dict.

    ADR-0015 decision 1: at write time every rule applies, whatever schema
    the record carries (refusal is in place while the author can still fix
    the input); at read time a record is checked by the rules of its own
    schema and below, so a rule bound to a later schema cannot refuse
    history. *context* carries what the placing rules compare the record
    against — a rule whose placement the caller cannot supply is not
    applied there.
    """

    data = dict(record)
    # An explicit first step, outside the registry: once it has run, the
    # record's number selects which rules a read applies — and a rule
    # registered ahead of the others can never read the schema unchecked.
    _check_schema_version(data)
    schema = cast(int, data["schema"])
    for name, check in _RULES.items():
        if not for_write:
            bound = _RULE_FROM_SCHEMA.get(name)
            if bound is None or bound > schema:
                continue
        check(data, context)
    if for_write and not RECORD_TYPES[cast(str, data["record_type"])].writable:
        # The registry's writable flag, consulted on every write path —
        # validate_record_for_write behind write_record, and the gate's
        # validate_record_content over a record a candidate adds — never
        # on read, where it would refuse a record history already holds.
        raise JournalRecordError(f"record type {data['record_type']!r} is not writable")
    return data


def _canonical_json(value: object) -> bytes:
    """The canonical encoding a byte bound is measured on.

    Sorted keys, compact separators, UTF-8 output with non-ASCII
    unescaped: one byte count for one value, so the bound does not depend
    on how the record happened to be serialized. ``allow_nan=False``
    keeps that promise for non-finite floats: ``NaN`` and ``Infinity``
    are not JSON, so the dumps raises and the rule refuses the value
    rather than measuring a token a strict parser could not read back.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _validate_provenance(data: Mapping[str, object]) -> None:
    """Validate the schema-2 provenance fields (ADR-0005 Decision 4).

    ``source`` is required and names how the evidence was captured;
    ``artifacts`` is an optional list of hash-pinned references to
    supplementary evidence stored outside the record.
    """

    source = data.get("source")
    if not isinstance(source, str) or source not in SOURCE_VALUES:
        raise JournalRecordError(
            f"record field 'source' must be one of {', '.join(sorted(SOURCE_VALUES))}"
        )
    if "artifacts" not in data:
        return
    artifacts = data["artifacts"]
    if not isinstance(artifacts, list):
        raise JournalRecordError("record field 'artifacts' must be an array")
    for artifact in artifacts:
        if not isinstance(artifact, dict) or artifact.keys() != {"ref", "hash"}:
            raise JournalRecordError("each artifact must contain only 'ref' and 'hash'")
        ref = artifact["ref"]
        if not isinstance(ref, str) or not ref:
            raise JournalRecordError("artifact field 'ref' must be a non-empty string")
        digest = artifact["hash"]
        if not isinstance(digest, str) or _SHA256_HEX_PATTERN.fullmatch(digest) is None:
            raise JournalRecordError(
                "artifact field 'hash' must be exactly 64 lowercase hex characters"
            )


def _validate_review_record(data: Mapping[str, object]) -> None:
    _validate_binding(data, "review", "reviewed_commit", "reviewed_finding")
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict not in _REVIEW_VERDICTS:
        raise JournalRecordError(
            "review record field 'verdict' must be one of approved, changes_required, "
            "blocked, or rejected"
        )
    reviewer = data.get("reviewer")
    if not isinstance(reviewer, dict):
        raise JournalRecordError("review record field 'reviewer' must be an object")
    for field in ("role", "vendor", "model", "email"):
        value = reviewer.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"review record reviewer field {field!r} must be a non-empty string"
            )
    email = reviewer["email"]
    if not isinstance(email, str) or "@" not in email:
        raise JournalRecordError(
            "review record reviewer field 'email' must contain '@'"
        )
    # `actor` — the declared reviewer actor the distinct-actor rule
    # compares (ADR-0018 decision 3) — joins the closed object from
    # schema 7 alone (ADR-0022 section 2): the record's own schema
    # decides, so a review stamped below 7 carrying it is refused on
    # read the way it is at write.
    reviewer_keys = {"role", "vendor", "model", "email"}
    admitted = "role, vendor, model, and email"
    if cast(int, data["schema"]) >= 7:
        reviewer_keys = reviewer_keys | {"actor"}
        admitted = "role, vendor, model, email, and actor"
    if reviewer.keys() - reviewer_keys:
        raise JournalRecordError(
            f"review record field 'reviewer' must contain only {admitted}"
        )
    findings = data.get("findings")
    if not isinstance(findings, list) or not all(
        isinstance(finding, str) and finding for finding in findings
    ):
        raise JournalRecordError(
            "review record field 'findings' must be an array of non-empty finding ids"
        )
    for finding in findings:
        _reject_control_characters(finding, "review record finding id")
    if len(set(findings)) != len(findings):
        raise JournalRecordError("review record findings must have unique finding ids")
    if verdict == "approved" and findings:
        raise JournalRecordError("approved review records must have no findings")
    if verdict != "approved" and not findings:
        raise JournalRecordError(
            "non-approved review records must have at least one finding id"
        )
    if "advisory_findings" in data:
        advisory = data["advisory_findings"]
        if not isinstance(advisory, list) or not all(
            isinstance(finding, str) and finding for finding in advisory
        ):
            raise JournalRecordError(
                "review record field 'advisory_findings' must be an array of "
                "non-empty finding ids"
            )
        for finding in advisory:
            _reject_control_characters(finding, "review record advisory finding id")
        if len(set(advisory)) != len(advisory):
            raise JournalRecordError(
                "review record advisory_findings must have unique finding ids"
            )
        # A finding is either blocking or advisory, never both.
        overlap = set(advisory) & set(findings)
        if overlap:
            raise JournalRecordError(
                "review record findings and advisory_findings must be disjoint"
            )
    if "reviewed_contract" in data:
        reviewed_contract = data["reviewed_contract"]
        if (
            not isinstance(reviewed_contract, str)
            or _SHA256_HEX_PATTERN.fullmatch(reviewed_contract) is None
        ):
            raise JournalRecordError(
                "review record field 'reviewed_contract' must be exactly 64 "
                "lowercase hex characters"
            )


def _validate_acceptance_record(data: Mapping[str, object]) -> None:
    _validate_binding(data, "acceptance", "accepted_commit", "accepted_finding")
    for field in ("accepted_by", "reason"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise JournalRecordError(
                f"acceptance record field {field!r} must be a non-empty string"
            )
        _reject_control_characters(value, f"acceptance record field {field!r}")
    # ADR-0007's acceptance over findings is one of three forms from schema
    # 7 (ADR-0013 decisions 5 and 17): an acceptance carries exactly one of
    # `findings`, `accepted_pause` and `operational`. The check sits in the
    # schema-1 rule so a record of an earlier schema without `findings` is
    # refused on read the way it always was; a record of an earlier schema
    # carrying a new field meets the field-admission refusal first.
    if len(data.keys() & _ACCEPTANCE_FORMS) != 1:
        raise JournalRecordError(
            "acceptance record must name exactly one of 'findings', "
            "'accepted_pause' or 'operational'"
        )
    if "findings" not in data:
        return
    findings = data["findings"]
    if (
        not isinstance(findings, list)
        or not findings
        or not all(isinstance(finding, str) and finding for finding in findings)
    ):
        raise JournalRecordError(
            "acceptance record field 'findings' must be a non-empty array of "
            "finding ids"
        )
    for finding in cast(list[str], findings):
        _reject_control_characters(finding, "acceptance record finding id")
    if len(set(findings)) != len(findings):
        raise JournalRecordError(
            "acceptance record findings must have unique finding ids"
        )


def _validate_binding(
    data: Mapping[str, object], record_type: str, commit_field: str, finding_field: str
) -> None:
    """Require exactly one well-formed commit or finding binding."""

    has_commit = commit_field in data
    has_finding = finding_field in data
    if has_commit == has_finding:
        raise JournalRecordError(
            f"{record_type} record must name exactly one of {commit_field!r} "
            f"or {finding_field!r}"
        )
    if has_commit:
        commit = data[commit_field]
        if (
            not isinstance(commit, str)
            or _REVIEWED_COMMIT_PATTERN.fullmatch(commit) is None
        ):
            raise JournalRecordError(
                f"{record_type} record field {commit_field!r} must be exactly 40 "
                "lowercase hex characters"
            )
        return
    finding = data[finding_field]
    if not isinstance(finding, str) or not _is_ulid(finding):
        raise JournalRecordError(
            f"{record_type} record field {finding_field!r} must be a "
            "26-character Crockford base32 ULID"
        )


def _validate_finding_record(data: Mapping[str, object]) -> None:
    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise JournalRecordError(
            "finding record field 'summary' must be a non-empty string"
        )
    _reject_control_characters(summary, "finding record field 'summary'")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise JournalRecordError(
            "finding record field 'artifacts' must be a non-empty array"
        )
    # The findings gate renders each artifact ref as its own transcript line;
    # ``_validate_provenance`` checks the shape, this refuses a ref that could
    # print as a second line.
    for artifact in artifacts:
        if isinstance(artifact, dict) and isinstance(artifact.get("ref"), str):
            _reject_control_characters(artifact["ref"], "finding record artifact 'ref'")


# What a value may not carry, named as a set rather than tested by proxy.
# Cc is the C0/C1 controls, so a newline and a carriage return are in it; Zl is
# U+2028 and Zp is U+2029, the two separators a renderer may treat as a line
# break; Cs is an unpaired surrogate, which cannot be encoded as UTF-8 at all,
# so a record carrying one could not be written back out.
# `str.isprintable()` used to stand in for all of this and was stricter than the
# purpose: it is false for all sixteen Zs space separators except U+0020 — among
# them U+00A0, U+2007, U+2009, U+202F and U+3000 — none of which can end a line
# (CR-114, reported by an adopter whose journal 0.4.0 refused over U+202F).
_FORGEABLE_CATEGORIES = frozenset({"Cc", "Cs", "Zl", "Zp"})
# The bidirectional marks, embeddings, overrides and isolates. All are category
# Cf, so no category rule catches them, and each can make displayed text read in
# an order its bytes do not have: the same harm as forging a line. The rest of
# Cf stays accepted — among them U+00AD, U+200B-U+200D, U+FEFF and the tag block
# U+E0020-U+E007F — as does category Co, a private-use codepoint that renders as
# one unknown glyph. Some of those are invisible; none can break a line or
# reorder text, which is what this rule is for. That boundary is deliberate, and
# stated here because it is the first thing a reader asks about.
_BIDIRECTIONAL_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def forges_rendered_text(value: str) -> bool:
    """Whether *value* could add a line to rendered output or reorder it.

    One predicate for both sides of the journal: records here, contract text in
    ``contracts.py``, which calls this rather than keeping its own test.
    """

    return any(
        unicodedata.category(character) in _FORGEABLE_CATEGORIES
        or character in _BIDIRECTIONAL_CONTROLS
        for character in value
    )


def _reject_control_characters(value: str, what: str) -> None:
    """Refuse a value that could add lines to a rendered transcript.

    The gate, ``status`` and ``report`` all render an acceptance's party, its
    finding ids and its reason inline, a review's finding ids — and, since
    ADR-0009, a finding's summary and its artifact refs. A newline in any of
    them would put extra
    lines into that output — including one that reads as an approval, which is
    the thing ADR-0007 forbids above all. In a single-operator project that is
    self-deception; where two operators share a journal it is one party forging
    what the other reads.

    So the record is refused rather than the display escaped: a value that can
    forge a transcript is not a valid identity, and evidence we cannot render
    faithfully should not be written.
    """

    if forges_rendered_text(value):
        raise JournalRecordError(f"{what} must not contain control characters")


def _record_path(
    journal_root: Path, task_id: str, record_id: str, record_type: str
) -> Path:
    validate_task_id(task_id)
    if not record_type or Path(record_type).name != record_type:
        raise JournalRecordError("record type must be a single path component")
    return (
        journal_root / "tasks" / task_id / "records" / f"{record_id}-{record_type}.json"
    )


def ensure_journal_root_is_real(journal_root: Path) -> None:
    """Reject a journal root reachable through a symlinked ancestor.

    ``journal_root`` must be built from a resolved project root; a resolve
    mismatch means some ancestor (for example the project metadata
    directory itself) is a symlink and evidence I/O would escape the
    repository.
    """

    resolved_root = journal_root.resolve()
    if resolved_root != journal_root:
        raise JournalRecordError(
            "journal root resolves outside its expected location: "
            f"{journal_root} -> {resolved_root}"
        )


def _prepare_record_directory(journal_root: Path, task_id: str) -> Path:
    ensure_journal_root_is_real(journal_root)
    paths = (journal_root, journal_root / "tasks", journal_root / "tasks" / task_id)
    for path in paths:
        if path.is_symlink():
            raise JournalRecordError(f"refusing to write through a symlink: {path}")
        if path.exists() and not path.is_dir():
            raise JournalRecordError(f"record path is not a directory: {path}")
        path.mkdir(exist_ok=True)
    records_directory = paths[-1] / "records"
    if records_directory.is_symlink():
        raise JournalRecordError(
            f"refusing to write through a symlink: {records_directory}"
        )
    if records_directory.exists() and not records_directory.is_dir():
        raise JournalRecordError(f"record path is not a directory: {records_directory}")
    records_directory.mkdir(exist_ok=True)
    resolved_directory = records_directory.resolve()
    if resolved_directory != records_directory:
        raise JournalRecordError(
            "record directory resolves outside its expected location: "
            f"{records_directory} -> {resolved_directory}"
        )
    return records_directory


def _validate_recorded_by(data: Mapping[str, object]) -> None:
    """Check the pair is well-formed and never half-present.

    Presence is what matters, not truthiness: an explicit ``null`` is a record
    that carries the field without naming an actor, which is neither absent nor
    valid. And the source is type-checked before the membership test, because a
    list or dict there would raise TypeError — a validator that crashes on a
    malformed record fails open in practice.
    """

    has_actor = "recorded_by" in data
    has_source = "recorded_by_source" in data
    record_type = cast(str, data["record_type"])
    if RECORD_TYPES[record_type].requires_recorded_by and not (
        has_actor and has_source
    ):
        raise JournalRecordError(
            f"{record_type} record requires a resolvable recorder in "
            "'recorded_by' and 'recorded_by_source'"
        )
    if not has_actor and not has_source:
        return
    if not has_actor or not has_source:
        raise JournalRecordError(
            "record fields 'recorded_by' and 'recorded_by_source' must appear "
            "together or not at all"
        )
    actor = data["recorded_by"]
    origin = data["recorded_by_source"]
    if not isinstance(actor, str) or not actor:
        raise JournalRecordError(
            "record field 'recorded_by' must be a non-empty string"
        )
    if not isinstance(origin, str) or origin not in _RECORDED_BY_SOURCES:
        raise JournalRecordError(
            "record field 'recorded_by_source' must be one of "
            + ", ".join(sorted(_RECORDED_BY_SOURCES))
        )


def _project_root_for(journal_root: Path) -> Path:
    """Find the project a journal belongs to, walking up from the given root.

    The journal root is not always two levels below the project: `open` writes
    the opening record through a staging directory *inside* the journal, so a
    fixed `parent.parent` lands on `.agentmarshal` and misses the project file —
    the opening record of every task would then miss the actors table while its
    later records used it.
    """

    for candidate in (journal_root, *journal_root.parents):
        if (candidate / ".agentmarshal" / "project.json").is_file():
            return candidate
    return journal_root.parent.parent


def validate_record_for_write(
    journal_root: Path,
    task_id: str,
    record: Mapping[str, object],
    *,
    record_id: str | None = None,
) -> dict[str, object]:
    """Apply every record refusal knowable before an exclusive write.

    The returned record includes derived recorder identity. Callers that write
    related evidence first use this preflight so shape, task, finding-binding,
    identity, and identifier failures cannot leave an orphan behind.
    """

    if "recorded_by" in record or "recorded_by_source" in record:
        # The field is derived, never supplied: a caller-provided value would be
        # just another label, and would silently outrank the override.
        raise JournalRecordError(
            "recorded_by is derived from the environment and must not be supplied"
        )
    data = dict(record)
    if type(data.get("schema")) is int and cast(int, data["schema"]) >= 2:
        resolved = resolve_recorded_by(_project_root_for(journal_root))
        if resolved is not None:
            data["recorded_by"], data["recorded_by_source"] = resolved

    def finding_ids() -> frozenset[str]:
        return frozenset(
            cast(str, item["id"])
            for item in read_records(journal_root, task_id)
            if item["record_type"] == "finding"
        )

    data = _validate_record(
        data,
        for_write=True,
        context={
            "task": task_id,
            "task_label": "destination",
            "finding_ids": finding_ids,
        },
    )
    if record_id is not None and not _is_ulid(record_id):
        raise JournalRecordError(
            "record id must be a 26-character Crockford base32 ULID"
        )
    return data


def write_record(
    journal_root: Path,
    task_id: str,
    record: Mapping[str, object],
    *,
    record_id: str | None = None,
) -> Path:
    """Exclusively create an evidence record and return its path.

    Every record passes through here, so this is where the creating actor is
    stamped (ADR-0006) — no record type is missed and no caller has to remember.
    A record that already carries ``recorded_by`` keeps it; one written where no
    identity can be determined carries neither field.
    """

    identifier = generate_ulid() if record_id is None else record_id
    data = validate_record_for_write(
        journal_root, task_id, record, record_id=identifier
    )
    record_type = cast(str, data["record_type"])
    path = _record_path(journal_root, task_id, identifier, record_type)
    _prepare_record_directory(journal_root, task_id)
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    try:
        record_file = _create_exclusive(path)
    except UnsafeProjectPathError as error:
        raise JournalRecordError(str(error)) from error
    with record_file:
        record_file.write(f"{content}\n")
    return path


# The schema a writer stamps (ADR-0004, ADR-0015 decision 2): the base
# record model is schema 3, and whatever a later schema introduced — a
# record type, a field, a value — raises the stamp to the schema that
# introduced it. One derivation for every writer.
_BASELINE_SCHEMA = 3


def _minimum_schema(record: Mapping[str, object]) -> int:
    """The least schema admitting every field and value *record* carries."""

    schema = _BASELINE_SCHEMA
    if record.get("record_type") == "finding" or record.keys() & _SCHEMA_4_FIELDS:
        schema = max(schema, 4)
    if "reviewed_contract" in record:
        schema = max(schema, 5)
    if record.get("activity") == "coordination":
        schema = max(schema, _COORDINATION_SESSION_SCHEMA)
    if record.keys() & _SCHEMA_7_SESSION_FIELDS:
        schema = max(schema, 7)
    if record.keys() & _SCHEMA_7_CONTRACT_FIELDS:
        schema = max(schema, 7)
    if record.keys() & _SCHEMA_7_ACCEPTANCE_FIELDS:
        schema = max(schema, 7)
    if record.keys() & _SCHEMA_7_REVIEW_FIELDS:
        schema = max(schema, 7)
    # `reviewer.actor` is a key of the reviewer object — `record.keys()`
    # never sees it — and needs 7 all the same.
    reviewer = record.get("reviewer")
    if isinstance(reviewer, dict) and "actor" in reviewer:
        schema = max(schema, 7)
    if record.get("record_type") == "check":
        schema = max(schema, _CHECK_RECORD_SCHEMA)
    if record.get("record_type") == "acknowledgement":
        schema = max(schema, _ACKNOWLEDGEMENT_RECORD_SCHEMA)
    return schema


def create_opened_record(
    task_id: str,
    tool_version: str,
    *,
    contract: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the lifecycle record emitted when a task is opened."""

    record: dict[str, object] = {
        "record_type": "opened",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "source": source,
    }
    if contract is not None:
        record["contract"] = contract
    record["schema"] = _minimum_schema(record)
    return record


def create_completed_record(
    task_id: str,
    tool_version: str,
    completed_commit: str | None,
    *,
    completed_finding: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the terminal record emitted when a task is completed."""

    if (completed_commit is None) == (completed_finding is None):
        raise JournalRecordError(
            "completed record must name exactly one of 'completed_commit' or "
            "'completed_finding'"
        )
    record: dict[str, object] = {
        "record_type": "completed",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "source": source,
    }
    if completed_finding is not None:
        record["completed_finding"] = completed_finding
    else:
        record["completed_commit"] = completed_commit
    record["schema"] = _minimum_schema(record)
    return record


def create_finding_record(
    task_id: str,
    tool_version: str,
    summary: str,
    artifacts: list[dict[str, str]],
    *,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build a hash-pinned research finding record."""

    record: dict[str, object] = {
        "record_type": "finding",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "summary": summary,
        "artifacts": artifacts,
        "source": source,
    }
    record["schema"] = _minimum_schema(record)
    return record


def create_abandoned_record(
    task_id: str, tool_version: str, reason: str, *, source: str = SOURCE_LIVE
) -> dict[str, object]:
    """Build the terminal record emitted when a task is abandoned."""

    record: dict[str, object] = {
        "record_type": "abandoned",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "reason": reason,
        "source": source,
    }
    record["schema"] = _minimum_schema(record)
    return record


def create_reopened_record(
    task_id: str, tool_version: str, reason: str, *, source: str = SOURCE_LIVE
) -> dict[str, object]:
    """Build the lifecycle record emitted when a completed task is reopened."""

    record: dict[str, object] = {
        "record_type": "reopened",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "reason": reason,
        "source": source,
    }
    record["schema"] = _minimum_schema(record)
    return record


def create_amendment_record(
    task_id: str,
    tool_version: str,
    reason: str,
    *,
    contract: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the evidence record emitted when a contract is amended."""

    record: dict[str, object] = {
        "record_type": "amendment",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "reason": reason,
        "source": source,
    }
    if contract is not None:
        record["contract"] = contract
    record["schema"] = _minimum_schema(record)
    return record


def session_record_schema(activity: str) -> int:
    """Return the schema a session record with *activity* is written under.

    Backfill asks for the stamp before its record exists; it goes through
    the same minimum-schema derivation the writers apply to the records
    they build.
    """

    return _minimum_schema({"record_type": "session", "activity": activity})


def create_session_record(
    task_id: str,
    tool_version: str,
    role: str,
    actor: str,
    activity: str,
    outcome: str,
    input_tokens: int,
    output_tokens: int,
    cache_tokens: int,
    *,
    usage_provider: str | None = None,
    usage_method: str | None = None,
    commit: str | None = None,
    model: str | None = None,
    trace: str | None = None,
    cli_session: str | None = None,
    report_ready: bool | None = None,
    fallback_reason: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build an attributed work session record."""

    if (usage_provider is None) != (usage_method is None):
        missing = "usage_method" if usage_method is None else "usage_provider"
        raise JournalRecordError(
            f"session record argument {missing!r} is required when its pair is supplied"
        )
    record: dict[str, object] = {
        "record_type": "session",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "role": role,
        "actor": actor,
        "activity": activity,
        "outcome": outcome,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "cache": cache_tokens,
        },
        "source": source,
    }
    if usage_provider is not None:
        record["usage"] = {"provider": usage_provider, "method": usage_method}
    for field, value in (
        ("commit", commit),
        ("model", model),
        ("trace", trace),
        ("cli_session", cli_session),
        ("report_ready", report_ready),
        ("fallback_reason", fallback_reason),
    ):
        if value is not None:
            record[field] = value
    record["schema"] = _minimum_schema(record)
    return record


def create_review_record(
    task_id: str,
    tool_version: str,
    reviewed_commit: str | None,
    verdict: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    findings: list[str],
    *,
    reviewed_finding: str | None = None,
    reviewed_contract: str | None = None,
    advisory_findings: list[str] | None = None,
    artifacts: list[dict[str, str]] | None = None,
    previous_review: str | None = None,
    classes: dict[str, str] | None = None,
    reviewer_actor: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the review evidence record submitted by a reviewer.

    ``advisory_findings`` are non-blocking findings that may accompany any
    verdict, including ``approved``; they never affect the merge decision.
    The field is omitted when empty so records without advisory findings
    stay identical to before. ``previous_review``, ``classes`` and
    ``reviewer_actor`` are the schema-7 fields of ADR-0022 section 2:
    supplied, each lands on the record and raises its stamp to 7.
    """

    if (reviewed_commit is None) == (reviewed_finding is None):
        raise JournalRecordError(
            "review record must name exactly one of 'reviewed_commit' or "
            "'reviewed_finding'"
        )
    reviewer: dict[str, str] = {
        "role": reviewer_role,
        "vendor": reviewer_vendor,
        "model": reviewer_model,
        "email": reviewer_email,
    }
    if reviewer_actor is not None:
        reviewer["actor"] = reviewer_actor
    record: dict[str, object] = {
        "record_type": "review",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "verdict": verdict,
        "reviewer": reviewer,
        "findings": findings,
        "source": source,
    }
    if reviewed_finding is not None:
        record["reviewed_finding"] = reviewed_finding
    else:
        record["reviewed_commit"] = reviewed_commit
    if reviewed_contract is not None:
        record["reviewed_contract"] = reviewed_contract
    if advisory_findings:
        record["advisory_findings"] = advisory_findings
    if artifacts:
        record["artifacts"] = artifacts
    if previous_review is not None:
        record["previous_review"] = previous_review
    if classes is not None:
        record["classes"] = classes
    record["schema"] = _minimum_schema(record)
    return record


def create_acceptance_record(
    task_id: str,
    tool_version: str,
    accepted_commit: str | None,
    accepted_by: str,
    findings: list[str] | None,
    reason: str,
    *,
    accepted_finding: str | None = None,
    accepted_pause: str | None = None,
    operational: bool = False,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build an operator acceptance record.

    The findings form is ADR-0007's acceptance over a review's blocking
    findings; ``accepted_pause`` names the extension whose pause is
    accepted and ``operational`` marks the acceptance of an operational CR
    — the two schema-7 forms of ADR-0013 decisions 5 and 17, which bind
    `accepted_commit` alone.
    """

    if (accepted_commit is None) == (accepted_finding is None):
        raise JournalRecordError(
            "acceptance record must name exactly one of 'accepted_commit' or "
            "'accepted_finding'"
        )
    forms = (findings is not None, accepted_pause is not None, operational)
    if sum(forms) != 1:
        raise JournalRecordError(
            "acceptance record must name exactly one of 'findings', "
            "'accepted_pause' or 'operational'"
        )
    if accepted_finding is not None and (accepted_pause is not None or operational):
        raise JournalRecordError(
            "acceptance record fields 'accepted_pause' and 'operational' bind "
            "by 'accepted_commit', never 'accepted_finding'"
        )
    record: dict[str, object] = {
        "record_type": "acceptance",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "accepted_by": accepted_by,
        "reason": reason,
        "source": source,
    }
    if findings is not None:
        record["findings"] = findings
    elif accepted_pause is not None:
        record["accepted_pause"] = {"extension": accepted_pause}
    else:
        record["operational"] = True
    if accepted_finding is not None:
        record["accepted_finding"] = accepted_finding
    else:
        record["accepted_commit"] = accepted_commit
    record["schema"] = _minimum_schema(record)
    return record


def create_check_record(
    task_id: str,
    tool_version: str,
    commit: str,
    name: str,
    result: str,
    *,
    failed_step: str | None = None,
    excerpt: str | None = None,
    run_url: str | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the measurement record a pipeline check's observer writes.

    The record traces what a check found on a commit — its name, its
    result, and optionally the step that failed, a bounded excerpt and a
    link to the run (ADR-0017 decision 1); the gate decides nothing from
    it.
    """

    record: dict[str, object] = {
        "record_type": "check",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "commit": commit,
        "name": name,
        "result": result,
        "source": source,
    }
    for field, value in (
        ("failed_step", failed_step),
        ("excerpt", excerpt),
        ("run_url", run_url),
    ):
        if value is not None:
            record[field] = value
    record["schema"] = _minimum_schema(record)
    return record


def create_acknowledgement_record(
    task_id: str,
    tool_version: str,
    commit: str,
    file: str,
    reason: str,
    signature: str | None,
    *,
    marker: int | None = None,
    source: str = SOURCE_LIVE,
) -> dict[str, object]:
    """Build the record a reviewed leak-scan hit leaves (ADR-0021).

    Bound to the candidate commit the hit was found in, it names the file
    exactly as the scan prints it — already masked — and the hit's
    identification: a built-in ``signature`` id or the ``marker``'s
    position, never the matched text.
    """

    if (signature is None) == (marker is None):
        raise JournalRecordError(
            "acknowledgement record must name exactly one of 'signature' or 'marker'"
        )
    record: dict[str, object] = {
        "record_type": "acknowledgement",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "commit": commit,
        "file": file,
        "reason": reason,
        "source": source,
    }
    if signature is not None:
        record["signature"] = signature
    else:
        record["marker"] = marker
    record["schema"] = _minimum_schema(record)
    return record


def validate_record_content(filename: str, content: str) -> dict[str, object]:
    """Validate a record file's name and JSON content; return the record.

    A write-side check (ADR-0015 decision 1): the gate runs it on the
    records a candidate adds, and backfill and migrate run it on a record
    they built before writing — in each case the author can still fix the
    input, so every current rule applies whatever schema the record
    carries. History is read through ``read_records``.
    """

    match = _RECORD_FILENAME_PATTERN.fullmatch(filename)
    if match is None:
        raise JournalRecordError(f"record filename is malformed: {filename}")
    try:
        loaded = json.loads(content)
    except json.JSONDecodeError as error:
        raise JournalRecordError(f"invalid JSON record: {filename}") from error
    if not isinstance(loaded, dict):
        raise JournalRecordError(f"record must contain a JSON object: {filename}")
    return _validate_record(
        cast(dict[str, object], loaded),
        for_write=True,
        context={
            "filename": filename,
            "filename_record_type": match["record_type"],
        },
    )


def read_records(journal_root: Path, task_id: str) -> list[dict[str, object]]:
    """Load and validate all evidence records for one task in path order."""

    validate_task_id(task_id)
    ensure_journal_root_is_real(journal_root)
    if journal_root.is_symlink():
        raise JournalRecordError(f"refusing to read through a symlink: {journal_root}")
    tasks_directory = journal_root / "tasks"
    task_directory = tasks_directory / task_id
    for path in (tasks_directory, task_directory):
        if path.is_symlink():
            raise JournalRecordError(f"refusing to read through a symlink: {path}")
    records_directory = journal_root / "tasks" / task_id / "records"
    if records_directory.is_symlink():
        raise JournalRecordError(
            f"refusing to read through a symlink: {records_directory}"
        )
    if not records_directory.exists():
        return []
    if not records_directory.is_dir():
        raise JournalRecordError(
            f"record directory is not a directory: {records_directory}"
        )
    records: list[dict[str, object]] = []
    for path in sorted(records_directory.iterdir()):
        if path.is_symlink():
            raise JournalRecordError(f"refusing to read through a symlink: {path}")
        if not path.is_file():
            raise JournalRecordError(f"record path is not a file: {path}")
        filename = _RECORD_FILENAME_PATTERN.fullmatch(path.name)
        if filename is None:
            raise JournalRecordError(f"record filename is malformed: {path}")
        with path.open("r", encoding="utf-8-sig") as record_file:
            try:
                loaded = json.load(record_file)
            except json.JSONDecodeError as error:
                raise JournalRecordError(f"invalid JSON record: {path}") from error
        if not isinstance(loaded, dict):
            raise JournalRecordError(f"record must contain a JSON object: {path}")
        try:
            record = _validate_record(
                cast(dict[str, object], loaded),
                for_write=False,
                context={
                    "task": task_id,
                    "task_label": "directory",
                    "filename_record_type": filename["record_type"],
                },
            )
        except JournalRecordError as error:
            raise JournalRecordError(f"{error}: {path}") from error
        record["id"] = filename["record_id"]
        records.append(record)
    return records
