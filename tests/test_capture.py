"""Tests for the capture policy and leak scanner (ADR-0005 Decision 2)."""

from __future__ import annotations

import pytest

from agentmarshal.journal.capture import (
    CaptureClass,
    CaptureError,
    CaptureLevel,
    CapturePolicy,
    LeakHit,
    assert_no_leaks,
    capture_policy_from_project,
    private_markers_from_project,
    render_leak_hits,
    scan_diff_for_leaks,
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


def test_an_artefact_refusal_reports_what_matched_not_where() -> None:
    """Scenario: an artefact refusal reports what matched, not where.

    This scan is handed one artefact the caller already names, so the refusal
    stays a category list; the added-content scan is the one that was given
    many files and has to say which."""

    text = "token AKIAIOSFODNN7EXAMPLE in a captured artefact"

    with pytest.raises(CaptureError) as refused:
        assert_no_leaks(text)

    message = str(refused.value)
    assert "aws-access-key-id" in message
    assert "AKIAIOSFODNN7EXAMPLE" not in message
    # The added-content renderer's "file: what" shape is deliberately absent:
    # the category stands alone.
    assert message.endswith("(aws-access-key-id)")


def test_scan_passes_clean_text() -> None:
    text = "The review found no blocking issues; the diff is within scope."
    assert scan_for_leaks(text) == []
    assert_no_leaks(text)  # does not raise


def test_scan_diff_scans_only_added_lines() -> None:
    diff = (
        "diff --git a/f b/f\n"
        "--- a/f\n"
        "+++ b/f\n"
        "@@ -1,2 +1,2 @@\n"
        " context AKIAIOSFODNN7EXAMPLE stays unscanned on a context line\n"
        "-removed AKIAIOSFODNN7EXAMPLE on a removed line is ignored\n"
        "+added token AKIAIOSFODNN7EXAMPLE now present\n"
    )
    # Only the '+' line (not the '+++' header, not context, not '-') is scanned.
    assert scan_diff_for_leaks(diff) == [LeakHit("f", "aws-access-key-id")]


def test_scan_diff_ignores_file_header_plus_plus_plus() -> None:
    diff = "--- a/x\n+++ b/AKIAIOSFODNN7EXAMPLE\n@@ -0,0 +1 @@\n+clean line\n"
    # The '+++' destination header is outside any hunk, so it is not content.
    assert scan_diff_for_leaks(diff) == []


def test_scan_diff_catches_added_line_starting_with_plus() -> None:
    # An added line whose content itself starts with '+' is emitted as
    # '+++...' in the diff; hunk-aware parsing must still scan it so a secret
    # cannot hide behind leading plus signs.
    diff = (
        "diff --git a/f b/f\n"
        "--- a/f\n"
        "+++ b/f\n"
        "@@ -0,0 +1 @@\n"
        "+++AKIAIOSFODNN7EXAMPLE trailing\n"
    )
    assert scan_diff_for_leaks(diff) == [LeakHit("f", "aws-access-key-id")]


def test_scan_diff_honours_private_markers() -> None:
    diff = "+++ b/f\n@@ -0,0 +1 @@\n+HOST = internal.example.invalid\n"
    assert scan_diff_for_leaks(diff, ("internal.example.invalid",)) == [
        LeakHit("f", "private-marker #1")
    ]


def test_scan_diff_multi_file_without_diff_git_header() -> None:
    # Two file patches separated only by ---/+++ headers (no 'diff --git').
    # Hunk line counts end each body, so the second file's '+++' header is
    # never scanned as added content — no false positive on a legit diff.
    diff = (
        "--- a/one\n"
        "+++ b/one\n"
        "@@ -0,0 +1 @@\n"
        "+clean one\n"
        "--- a/two\n"
        "+++ b/AKIAIOSFODNN7EXAMPLE\n"
        "@@ -0,0 +1 @@\n"
        "+clean two\n"
    )
    assert scan_diff_for_leaks(diff) == []


def test_scan_diff_counts_added_line_that_looks_like_a_hunk_header() -> None:
    # An added content line beginning with '@@' must be consumed by the hunk
    # counter, not treated as a new hunk header.
    diff = (
        "@@ -0,0 +2 @@\n"
        "+@@ not a real header AKIAIOSFODNN7EXAMPLE\n"
        "+second added line\n"
    )
    assert scan_diff_for_leaks(diff) == [LeakHit("(unknown file)", "aws-access-key-id")]


def test_a_built_in_signature_names_its_file_and_itself() -> None:
    """Scenario: a built-in signature names its file and itself."""

    secret = "AKIAIOSFODNN7EXAMPLE"
    diff = (
        "diff --git a/src/keys.py b/src/keys.py\n"
        "--- a/src/keys.py\n"
        "+++ b/src/keys.py\n"
        "@@ -0,0 +1 @@\n"
        f"+KEY = '{secret}'\n"
    )

    rendered = render_leak_hits(scan_diff_for_leaks(diff))

    assert rendered == "src/keys.py: aws-access-key-id"
    assert secret not in rendered


def test_a_path_that_carries_a_marker_is_not_printed_either() -> None:
    """Scenario: a path that carries a marker is described, not printed.

    A repository can name a directory after an internal host, and then the path
    is the secret; naming the file would disclose what naming the marker
    refused to."""

    diff = (
        "--- a/configs/internal.corp.invalid/app.json\n"
        "+++ b/configs/internal.corp.invalid/app.json\n"
        "@@ -0,0 +1 @@\n"
        '+{"host": "internal.corp.invalid"}\n'
    )

    hits = scan_diff_for_leaks(diff, ("internal.corp.invalid",))

    rendered = render_leak_hits(hits)
    assert "internal.corp.invalid" not in rendered
    assert "private marker #1" in rendered


def test_a_path_that_is_itself_a_key_is_described_not_printed() -> None:
    """Scenario: a path that is itself a key is described, not printed.

    A file can be named after the key it holds. The rendering says which
    signature the path matched — that name is public — and never the
    characters that matched it."""

    diff = (
        "--- a/keys/AKIAIOSFODNN7EXAMPLE\n"
        "+++ b/keys/AKIAIOSFODNN7EXAMPLE\n"
        "@@ -0,0 +1 @@\n"
        "+rotated on Tuesday AKIAIOSFODNN7EXAMPLE\n"
    )

    hits = scan_diff_for_leaks(diff)

    rendered = render_leak_hits(hits)
    assert "AKIAIOSFODNN7EXAMPLE" not in rendered
    # Only the span that is the key is replaced; the directory still says where.
    assert "keys/<aws-access-key-id>: aws-access-key-id" in rendered


def test_two_leaking_files_under_one_marker_directory_stay_two_hits() -> None:
    """A masked path keeps what is not the secret, so files stay distinct.

    Describing the whole path made both files render identically, and the hits
    are a set: the operator saw one place to look instead of two."""

    diff = (
        "--- a/configs/internal.corp.invalid/one.json\n"
        "+++ b/configs/internal.corp.invalid/one.json\n"
        "@@ -0,0 +1 @@\n"
        '+{"host": "internal.corp.invalid"}\n'
        "--- a/configs/internal.corp.invalid/two.json\n"
        "+++ b/configs/internal.corp.invalid/two.json\n"
        "@@ -0,0 +1 @@\n"
        '+{"host": "internal.corp.invalid"}\n'
    )

    hits = scan_diff_for_leaks(diff, ("internal.corp.invalid",))

    rendered = render_leak_hits(hits)
    assert "internal.corp.invalid" not in rendered
    assert len(hits) == 2
    assert "configs/<private marker #1>/one.json" in rendered
    assert "configs/<private marker #1>/two.json" in rendered


def test_added_lines_of_a_dev_null_destination_are_still_scanned() -> None:
    """A scanner with no name for the file must not stop scanning.

    A destination of /dev/null left no path, and the added lines of that hunk
    were dropped — fail-open in the one direction that matters."""

    diff = "--- a/gone\n+++ /dev/null\n@@ -0,0 +1 @@\n+AKIAIOSFODNN7EXAMPLE\n"

    hits = scan_diff_for_leaks(diff)

    assert hits == [LeakHit("(unknown file)", "aws-access-key-id")]


def test_a_rendered_warning_is_bounded_and_counts_the_rest() -> None:
    """The merge transcript is read by people; the line cannot be unbounded."""

    hits = [LeakHit(f"file{index:03d}", "aws-access-key-id") for index in range(25)]

    rendered = render_leak_hits(hits)

    assert rendered.count("aws-access-key-id") == 20
    assert rendered.endswith(", and 5 more not shown")


def test_a_signature_split_across_added_lines_is_still_found() -> None:
    """A signature may span a wrapped header; matching line by line lost it."""

    # The authorization-header signature allows whitespace between the header
    # and its value, so a wrapped header matches the file's added text and not
    # either line alone.
    diff = (
        "--- a/src/client.py\n"
        "+++ b/src/client.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+Authorization:\n"
        "+  Bearer abcdefghijklmnopqrstuvwxyz0123456789\n"
    )

    hits = scan_diff_for_leaks(diff)

    assert [hit.identification for hit in hits] == ["authorization-header"]


def test_the_declaration_path_is_not_reported_beside_a_real_occurrence() -> None:
    """Where a marker is defined is not where it leaked."""

    diff = (
        "--- a/.agentmarshal/project.json\n"
        "+++ b/.agentmarshal/project.json\n"
        "@@ -0,0 +1 @@\n"
        '+{"leak_scan": {"private_markers": ["acme-internal"]}}\n'
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -0,0 +1 @@\n"
        '+HOST = "acme-internal"\n'
    )

    hits = scan_diff_for_leaks(diff, ("acme-internal",))

    assert [hit.path for hit in hits] == ["src/app.py"]


def test_a_private_marker_is_named_by_position_not_by_value() -> None:
    """Scenario: a private marker is named by position, not by value."""

    marker = "private-coordinator.example.invalid"
    diff = (
        "diff --git a/src/config.py b/src/config.py\n"
        "--- a/src/config.py\n"
        "+++ b/src/config.py\n"
        "@@ -0,0 +1 @@\n"
        f"+HOST = '{marker}'\n"
    )

    rendered = render_leak_hits(scan_diff_for_leaks(diff, (marker,)))

    assert rendered == "src/config.py: private-marker #1"
    assert marker not in rendered


def test_a_change_to_the_marker_list_does_not_trip_on_itself() -> None:
    """Scenario: a change to the marker list does not trip on itself."""

    marker = "private-coordinator.example.invalid"
    diff = (
        "diff --git a/.agentmarshal/project.json b/.agentmarshal/project.json\n"
        "--- a/.agentmarshal/project.json\n"
        "+++ b/.agentmarshal/project.json\n"
        "@@ -0,0 +1 @@\n"
        f'+{{"leak_scan": {{"private_markers": ["{marker}"]}}}}\n'
    )

    assert scan_diff_for_leaks(diff, (marker,)) == []


def test_a_marker_elsewhere_in_the_same_content_is_still_reported() -> None:
    """Scenario: a marker elsewhere in the same content is still reported."""

    marker = "private-coordinator.example.invalid"
    diff = (
        "diff --git a/.agentmarshal/project.json b/.agentmarshal/project.json\n"
        "--- a/.agentmarshal/project.json\n"
        "+++ b/.agentmarshal/project.json\n"
        "@@ -0,0 +1 @@\n"
        f'+{{"leak_scan": {{"private_markers": ["{marker}"]}}}}\n'
        "diff --git a/src/config.py b/src/config.py\n"
        "--- a/src/config.py\n"
        "+++ b/src/config.py\n"
        "@@ -0,0 +1 @@\n"
        f"+HOST = '{marker}'\n"
    )

    hits = scan_diff_for_leaks(diff, (marker,))

    assert LeakHit("src/config.py", "private-marker #1") in hits


def test_private_markers_absent_section_is_empty() -> None:
    assert private_markers_from_project({}) == ()


def test_private_markers_parsed_from_list() -> None:
    data = {"leak_scan": {"private_markers": ["a.example", "b.example"]}}
    assert private_markers_from_project(data) == ("a.example", "b.example")


def test_private_markers_reject_non_object_section() -> None:
    with pytest.raises(CaptureError):
        private_markers_from_project({"leak_scan": ["not-an-object"]})


def test_private_markers_reject_unsupported_field() -> None:
    with pytest.raises(CaptureError):
        private_markers_from_project({"leak_scan": {"bogus": 1}})


def test_private_markers_reject_non_list() -> None:
    with pytest.raises(CaptureError):
        private_markers_from_project({"leak_scan": {"private_markers": "x"}})


def test_private_markers_reject_empty_or_non_string_entry() -> None:
    with pytest.raises(CaptureError):
        private_markers_from_project({"leak_scan": {"private_markers": [""]}})
    with pytest.raises(CaptureError):
        private_markers_from_project({"leak_scan": {"private_markers": [3]}})
