"""Tests for the capture policy and leak scanner (ADR-0005 Decision 2)."""

from __future__ import annotations

import pytest

from agentmarshal.journal.capture import (
    CaptureClass,
    CaptureError,
    CaptureLevel,
    CapturePolicy,
    assert_no_leaks,
    capture_policy_from_project,
    scan_for_leaks,
)

# --- presets and resolution ----------------------------------------------


@pytest.mark.parametrize(
    ("preset", "expected"),
    [
        (
            "minimal",
            {
                CaptureClass.ECONOMICS: CaptureLevel.OFF,
                CaptureClass.REVIEWS: CaptureLevel.OFF,
                CaptureClass.SESSIONS: CaptureLevel.OFF,
            },
        ),
        (
            "attested",
            {
                CaptureClass.ECONOMICS: CaptureLevel.COMMIT,
                CaptureClass.REVIEWS: CaptureLevel.HASH,
                CaptureClass.SESSIONS: CaptureLevel.HASH,
            },
        ),
        (
            "full",
            {
                CaptureClass.ECONOMICS: CaptureLevel.COMMIT,
                CaptureClass.REVIEWS: CaptureLevel.COMMIT,
                CaptureClass.SESSIONS: CaptureLevel.HASH,
            },
        ),
    ],
)
def test_preset_resolved_levels(
    preset: str, expected: dict[CaptureClass, CaptureLevel]
) -> None:
    policy = capture_policy_from_project({"capture": {"preset": preset}})
    for capture_class, level in expected.items():
        assert policy.level_for(capture_class) == level


def test_full_preset_keeps_sessions_private() -> None:
    # Even at full, sessions never exceed HASH by preset.
    policy = capture_policy_from_project({"capture": {"preset": "full"}})
    assert policy.level_for(CaptureClass.SESSIONS) == CaptureLevel.HASH


def test_default_preset_when_capture_absent() -> None:
    policy = capture_policy_from_project({"schema": 1})
    assert policy.preset == "attested"
    assert policy.level_for(CaptureClass.ECONOMICS) == CaptureLevel.COMMIT


def test_override_beats_preset() -> None:
    policy = capture_policy_from_project(
        {"capture": {"preset": "attested", "overrides": {"reviews": "commit"}}}
    )
    assert policy.level_for(CaptureClass.REVIEWS) == CaptureLevel.COMMIT
    # Non-overridden classes keep the preset.
    assert policy.level_for(CaptureClass.ECONOMICS) == CaptureLevel.COMMIT


# --- fail-closed parsing --------------------------------------------------


@pytest.mark.parametrize(
    "section",
    [
        {"preset": "aggressive"},
        {"preset": 2},
        {"overrides": {"reviews": "publish"}},
        {"overrides": {"telemetry": "commit"}},
        {"overrides": {"sessions": "commit"}},
        {"overrides": "commit-everything"},
        {"allow_public_sessions": "yes"},
        {"unknown_field": 1},
    ],
)
def test_malformed_capture_config_fails_closed(section: object) -> None:
    with pytest.raises(CaptureError):
        capture_policy_from_project({"capture": section})


def test_capture_section_must_be_object() -> None:
    with pytest.raises(CaptureError):
        capture_policy_from_project({"capture": "attested"})


# --- session privacy guard ------------------------------------------------


def test_public_session_needs_both_opt_ins() -> None:
    without = CapturePolicy(preset="full", allow_public_sessions=False)
    assert not without.may_commit_session_publicly(per_operation_flag=True)

    configured = CapturePolicy(preset="full", allow_public_sessions=True)
    # Config alone is not enough; the per-operation flag alone is not enough.
    assert not configured.may_commit_session_publicly(per_operation_flag=False)
    assert configured.may_commit_session_publicly(per_operation_flag=True)


def test_session_commit_override_is_rejected() -> None:
    # A session COMMIT is not expressible as a capture override; it fails
    # closed so no configuration path can leak a raw session.
    with pytest.raises(CaptureError, match="sessions cannot be set to 'commit'"):
        CapturePolicy(
            preset="full", overrides={CaptureClass.SESSIONS: CaptureLevel.COMMIT}
        )
    with pytest.raises(CaptureError):
        capture_policy_from_project(
            {"capture": {"preset": "full", "overrides": {"sessions": "commit"}}}
        )


def test_direct_constructor_validates_preset_and_overrides() -> None:
    # The public constructor fails closed on the same malformed inputs the
    # parser rejects, so level_for cannot later raise or return a non-level.
    with pytest.raises(CaptureError, match="unknown capture preset"):
        CapturePolicy(preset="aggressive")
    with pytest.raises(CaptureError, match="must be a CaptureLevel"):
        CapturePolicy(
            preset="full",
            overrides={CaptureClass.REVIEWS: "commit"},  # type: ignore[dict-item]
        )
    with pytest.raises(CaptureError, match="must be a CaptureClass"):
        CapturePolicy(
            preset="full",
            overrides={"reviews": CaptureLevel.HASH},  # type: ignore[dict-item]
        )


def test_overrides_are_defensively_copied() -> None:
    # Mutating the source mapping after construction must not change the
    # policy: a frozen dataclass does not freeze the referenced mapping, so
    # the policy copies it. Injecting a session COMMIT afterwards is inert.
    source: dict[CaptureClass, CaptureLevel] = {}
    policy = CapturePolicy(preset="full", overrides=source)
    source[CaptureClass.SESSIONS] = CaptureLevel.COMMIT

    assert policy.level_for(CaptureClass.SESSIONS) == CaptureLevel.HASH
    assert (
        policy.resolve_session_disposition(per_operation_flag=False)
        == CaptureLevel.HASH
    )


def test_both_opt_ins_must_be_strict_booleans() -> None:
    # A truthy non-boolean must never authorize a public session.
    with pytest.raises(CaptureError, match="allow_public_sessions must be a boolean"):
        CapturePolicy(preset="full", allow_public_sessions="false")  # type: ignore[arg-type]

    policy = CapturePolicy(preset="full", allow_public_sessions=True)
    with pytest.raises(CaptureError, match="per-operation session flag"):
        policy.may_commit_session_publicly(per_operation_flag=1)  # type: ignore[arg-type]
    with pytest.raises(CaptureError, match="per-operation session flag"):
        policy.resolve_session_disposition(per_operation_flag="yes")  # type: ignore[arg-type]


def test_resolve_session_disposition_gated_by_two_opt_ins() -> None:
    # The authoritative session API returns COMMIT only with both opt-ins.
    default = capture_policy_from_project({"capture": {"preset": "full"}})
    assert (
        default.resolve_session_disposition(per_operation_flag=True)
        == CaptureLevel.HASH
    )

    configured = CapturePolicy(preset="full", allow_public_sessions=True)
    assert (
        configured.resolve_session_disposition(per_operation_flag=False)
        == CaptureLevel.HASH
    )
    assert (
        configured.resolve_session_disposition(per_operation_flag=True)
        == CaptureLevel.COMMIT
    )

    minimal = capture_policy_from_project({"capture": {"preset": "minimal"}})
    assert (
        minimal.resolve_session_disposition(per_operation_flag=True) == CaptureLevel.OFF
    )


# --- leak scanning --------------------------------------------------------


@pytest.mark.parametrize(
    "secret",
    [
        "-----BEGIN OPENSSH PRIVATE KEY-----\nx",
        "-----BEGIN PRIVATE KEY-----\nx",
        "-----BEGIN ENCRYPTED PRIVATE KEY-----\nx",
        "-----BEGIN PGP PRIVATE KEY BLOCK-----\nx",
        "aws key AKIAIOSFODNN7EXAMPLE here",
        "temp creds ASIAIOSFODNN7EXAMPLE session",
        "token ghp_" + "a" * 36,
        "github_pat_" + "a" * 30,
        "glpat-" + "a" * 20,
        "xoxb-123456789012-abcdefghijkl",
        "AIza" + "b" * 35,
        "sk-" + "c" * 40,
        "sk-proj-" + "A" * 48,
        "sk-svcacct-" + "B" * 40,
        "Authorization: Bearer sometoken",
    ],
)
def test_scan_detects_secrets(secret: str) -> None:
    hits = scan_for_leaks(secret)
    assert hits
    with pytest.raises(CaptureError):
        assert_no_leaks(secret)


def test_scan_detects_configured_private_marker() -> None:
    text = "connecting to coordinator.internal.example for the run"
    assert scan_for_leaks(text, private_markers=("coordinator.internal.example",)) == [
        "private-marker"
    ]
    with pytest.raises(CaptureError):
        assert_no_leaks(text, private_markers=("coordinator.internal.example",))


def test_scan_passes_clean_text() -> None:
    text = "The review found no blocking issues; the diff is within scope."
    assert scan_for_leaks(text) == []
    assert_no_leaks(text)  # does not raise
