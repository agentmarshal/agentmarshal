"""Tests for the 0.5.0 project settings reader."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from agentmarshal.settings import (
    DEFAULT_FINDING_CLASSES,
    ProjectSettingsError,
    changes_required_threshold,
    finding_classes,
    read_project_settings,
    require_agreement,
)


def write_project(repo: Path, data: dict[str, object]) -> None:
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir(parents=True, exist_ok=True)
    project_file.write_text(json.dumps(data) + "\n", encoding="utf-8")


def test_project_with_no_keys_gets_every_default(tmp_path: Path) -> None:
    """Scenario: a project with none of the keys gets every default."""

    write_project(tmp_path, {"schema": 1})

    settings = read_project_settings(tmp_path)

    assert settings.finding_classes == (
        "correctness",
        "contract-mismatch",
        "claim-accuracy",
        "scope",
        "test-gap",
        "security",
        "style",
    )
    assert settings.changes_required_threshold == 3
    assert settings.require_agreement is False


def test_absent_key_falls_back_beside_present_ones(tmp_path: Path) -> None:
    """Scenario: an absent key falls back beside present ones."""

    write_project(
        tmp_path,
        {
            "schema": 1,
            "review": {"changes_required_threshold": 5},
            "contract": {"require_agreement": True},
        },
    )
    settings = read_project_settings(tmp_path)
    assert settings.finding_classes == DEFAULT_FINDING_CLASSES
    assert settings.changes_required_threshold == 5
    assert settings.require_agreement is True

    write_project(
        tmp_path,
        {
            "schema": 1,
            "review": {"finding_classes": ["scope"]},
        },
    )
    settings = read_project_settings(tmp_path)
    assert settings.finding_classes == ("scope",)
    assert settings.changes_required_threshold == 3
    assert settings.require_agreement is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("correctness", "non-empty list of distinct non-empty strings"),
        ([], "non-empty list of distinct non-empty strings"),
        (["scope", 3], "non-empty list of distinct non-empty strings"),
        (["scope", ""], "non-empty list of distinct non-empty strings"),
        (["scope", "scope"], "non-empty list of distinct non-empty strings"),
        (["scope", "style\nforged-line"], "must not contain control characters"),
        (["scope", "style\tforged-cell"], "must not contain control characters"),
    ],
    ids=[
        "not-a-list",
        "empty-list",
        "non-string-entry",
        "empty-entry",
        "repeated-entry",
        "newline-entry",
        "tab-entry",
    ],
)
def test_malformed_vocabulary_is_named(
    tmp_path: Path, value: object, expected: str
) -> None:
    """Scenario: a malformed vocabulary is named."""

    write_project(tmp_path, {"schema": 1, "review": {"finding_classes": value}})

    with pytest.raises(ProjectSettingsError) as raised:
        read_project_settings(tmp_path)

    message = str(raised.value)
    assert "review.finding_classes" in message
    assert expected in message


@pytest.mark.parametrize(
    "value",
    [True, "3", 0, -2, 2.5, [3]],
    ids=["boolean", "string", "zero", "negative", "float", "list"],
)
def test_malformed_threshold_is_named(tmp_path: Path, value: object) -> None:
    """Scenario: a malformed threshold is named."""

    write_project(
        tmp_path, {"schema": 1, "review": {"changes_required_threshold": value}}
    )

    with pytest.raises(ProjectSettingsError) as raised:
        read_project_settings(tmp_path)

    message = str(raised.value)
    assert "review.changes_required_threshold" in message
    assert "an integer of at least 1" in message


@pytest.mark.parametrize("value", ["yes", 1, [True]], ids=["string", "int", "list"])
def test_malformed_agreement_flag_is_named(tmp_path: Path, value: object) -> None:
    """Scenario: a malformed agreement flag is named."""

    write_project(tmp_path, {"schema": 1, "contract": {"require_agreement": value}})

    with pytest.raises(ProjectSettingsError) as raised:
        read_project_settings(tmp_path)

    message = str(raised.value)
    assert "contract.require_agreement" in message
    assert "a boolean" in message


@pytest.mark.parametrize(
    ("data", "key"),
    [
        ({"review": None}, "review.finding_classes"),
        ({"review": {"finding_classes": None}}, "review.finding_classes"),
        (
            {"review": {"changes_required_threshold": None}},
            "review.changes_required_threshold",
        ),
        ({"contract": None}, "contract.require_agreement"),
        ({"contract": {"require_agreement": None}}, "contract.require_agreement"),
    ],
    ids=[
        "null-review-section",
        "null-vocabulary",
        "null-threshold",
        "null-contract-section",
        "null-agreement-flag",
    ],
)
def test_present_null_is_malformed_not_absent(
    tmp_path: Path, data: dict[str, object], key: str
) -> None:
    """Scenario: a present null is malformed, not absent."""

    write_project(tmp_path, {"schema": 1, **data})

    with pytest.raises(ProjectSettingsError) as raised:
        read_project_settings(tmp_path)

    assert key in str(raised.value)


def test_fallback_class_may_be_listed(tmp_path: Path) -> None:
    """Scenario: the fallback class may be listed."""

    write_project(
        tmp_path,
        {"schema": 1, "review": {"finding_classes": ["correctness", "other"]}},
    )

    assert read_project_settings(tmp_path).finding_classes == (
        "correctness",
        "other",
    )


@pytest.mark.parametrize(
    ("data", "read", "key"),
    [
        ({"review": 5}, finding_classes, "review.finding_classes"),
        (
            {"review": []},
            changes_required_threshold,
            "review.changes_required_threshold",
        ),
        ({"contract": "yes"}, require_agreement, "contract.require_agreement"),
    ],
    ids=["review-for-vocabulary", "review-for-threshold", "contract"],
)
def test_section_that_is_not_an_object_is_named(
    tmp_path: Path,
    data: dict[str, object],
    read: Callable[[Path], object],
    key: str,
) -> None:
    """Scenario: a section that is not an object is named."""

    write_project(tmp_path, {"schema": 1, **data})

    with pytest.raises(ProjectSettingsError) as raised:
        read(tmp_path)

    assert key in str(raised.value)
