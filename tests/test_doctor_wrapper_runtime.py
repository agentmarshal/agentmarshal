"""``doctor`` checks the runtime a wrapper declares — ADR-0013 D13.

For each shared extension whose manifest declares ``[wraps]``,
``doctor`` gains an ``extension runtime <name>`` check: the declared
``<name>`` is found on ``PATH`` — the one ``PATH`` exception of
decision 13 as amended — run with ``--version`` as an argv call,
never through a shell, under a short limit, and the answer is
compared numerically against the declared minimum. A runtime not
found, failed, silent, unreadable or too old fails the check by
doctor's ordinary rules; an extension without ``[wraps]`` gets no
runtime line at all.

Every scenario the delta spec names is exercised by one test whose
docstring names it. No test depends on what the machine has
installed: each puts a fake runtime on a temporary ``PATH``.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

import agentmarshal.doctor as doctor
from agentmarshal.cli import main
from test_doctor_extensions import (
    _dir_extension,
    _every_precondition_met,
    _file_extension,
    _project,
)


@pytest.fixture(autouse=True)
def clear_precondition_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep doctor checks independent of the test runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)


def _wrapper_extension(
    repo: Path,
    name: str = "openspec",
    runtime: str = "node >= 20",
    extra: dict[str, str] | None = None,
) -> Path:
    """A directory-form shared extension whose manifest wraps a product.

    The ``[wraps]`` section follows ADR-0013's amended manifest
    example: product, verified version, ecosystem, the product's own
    lock under ``lock/``, the declared runtime and the license.
    """

    directory = repo / ".agentmarshal" / "extensions" / name
    files = {
        "manifest.toml": (
            "schema = 2\n"
            f'name = "{name}"\n'
            'version = "1.0.0"\n'
            f'footprint = ["{name}/"]\n'
            "documents = []\n"
            "\n"
            "[[stage]]\n"
            'phase = "pre-gate-stop"\n'
            'command = "bin/run.py"\n'
            "\n"
            "[wraps]\n"
            f'product = "{name}"\n'
            'version = "1.13.2"\n'
            'ecosystem = "npm"\n'
            'lock = "lock/package-lock.json"\n'
            f'runtime = "{runtime}"\n'
            'license = "MIT"\n'
        ),
        "bin/run.py": "print('runs the check')\n",
        "lock/package-lock.json": '{"lockfileVersion": 3}\n',
    }
    files.update(extra or {})
    for relpath, content in files.items():
        path = directory / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def _fake_runtime(
    directory: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str = "node",
    body: str = "printf 'v20.11.0\\n'",
) -> Path:
    """An executable *name* printing its ``--version`` answer.

    The script lives in *directory*, which is prepended to ``PATH`` so
    the check resolves it — and so nothing depends on what the machine
    itself has installed.
    """

    directory.mkdir(parents=True, exist_ok=True)
    script = directory / name
    script.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{directory}{os.pathsep}{os.environ.get('PATH', '')}")
    return script


# -- the check -------------------------------------------------------------------


def test_a_wrappers_runtime_that_meets_the_declared_minimum_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a wrapper's runtime that meets the declared minimum passes."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _wrapper_extension(repo)
    script = _fake_runtime(tmp_path / "fake-bin", monkeypatch)

    assert main(["doctor"]) == 0

    out = capsys.readouterr().out
    assert (
        f"OK: extension runtime openspec — {script} reports 20.11.0, "
        "meeting node >= 20" in out
    )
    assert "Summary: all 12 checks passed" in out


def test_versions_compare_by_leading_numeric_components_a_leading_v_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: versions compare by leading numeric components, a leading v ignored."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _wrapper_extension(repo, runtime="node >= 20")
    # 9.11.0 is below 20 numerically; a lexicographic comparison would
    # read "9.11.0" as the greater string and pass it.
    _fake_runtime(tmp_path / "fake-bin", monkeypatch, body="printf 'v9.11.0\\n'")

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        "FAIL: extension runtime openspec — " in out
        and "reports 9.11.0, below the declared minimum node >= 20" in out
    )


def test_a_runtime_not_found_on_path_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a runtime not found on PATH fails the check."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo)
    # A PATH the machine's contents cannot leak into: only git is
    # linked in — project discovery needs it — and no `node` is there.
    nowhere = tmp_path / "nowhere-bin"
    nowhere.mkdir()
    (nowhere / "git").symlink_to(shutil.which("git") or "/usr/bin/git")
    monkeypatch.setenv("PATH", str(nowhere))

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        "FAIL: extension runtime openspec — node was not found on PATH; "
        "openspec requires node >= 20" in out
    )


def test_a_runtime_whose_version_invocation_fails_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a runtime whose --version fails fails the check."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo)
    script = _fake_runtime(tmp_path / "fake-bin", monkeypatch, body="exit 3")

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} --version failed "
        "(exit status 3)" in out
    )


def test_a_runtime_that_does_not_answer_in_time_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a runtime that does not answer in time fails the check."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo)
    monkeypatch.setattr(doctor, "_RUNTIME_VERSION_TIMEOUT_SECONDS", 0.5)
    script = _fake_runtime(tmp_path / "fake-bin", monkeypatch, body="sleep 5")

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} did not answer "
        "--version within 0.5 seconds" in out
    )


def test_a_runtime_reporting_no_readable_version_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a runtime reporting no readable version fails the check."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo)
    script = _fake_runtime(
        tmp_path / "fake-bin", monkeypatch, body="echo 'no version here'"
    )

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} reports no readable "
        "version" in out
    )

    # An answer that cannot even be decoded is just as unreadable —
    # reported, never guessed.
    script.write_text("#!/bin/sh\nprintf '\\377\\376\\n'\n", encoding="utf-8")
    assert main(["doctor"]) == 1
    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} reports no readable "
        "version" in out
    )

    # And a digit run past the interpreter's integer-conversion limit
    # is just as unreadable — reported, never an exception out of the
    # check.
    digits = "9" * 5000
    script.write_text(f"#!/bin/sh\nprintf 'v{digits}\\n'\n", encoding="utf-8")
    assert main(["doctor"]) == 1
    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} reports no readable "
        "version" in out
    )


def test_a_runtime_below_the_declared_minimum_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a runtime below the declared minimum fails the check."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo, runtime="node >= 20")
    script = _fake_runtime(
        tmp_path / "fake-bin", monkeypatch, body="printf 'v18.19.0\\n'"
    )

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — {script} reports 18.19.0, "
        "below the declared minimum node >= 20" in out
    )


def test_each_value_a_runtime_result_names_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each value a runtime result names is escaped on display."""
    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo)
    # A PATH element can carry a control character; the resolved path
    # then carries it onto the check's line — escaped, as every
    # displayed value is.
    forged = tmp_path / "fake\nbin"
    script = _fake_runtime(forged, monkeypatch)

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert "OK: extension runtime openspec" in captured.out
    assert "fake\\nbin" in captured.out
    assert str(script) not in captured.out
    assert "fake\nbin" not in captured.out


def test_the_check_runs_nothing_else_an_extension_declares_and_installs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the check runs nothing else an extension declares and installs nothing."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    sentinel = repo / "sentinel"
    _wrapper_extension(
        repo,
        extra={
            "bin/run.py": (
                f"import pathlib\npathlib.Path({str(sentinel)!r}).write_text('ran')\n"
            )
        },
    )
    (repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "run.py").chmod(0o755)
    _fake_runtime(tmp_path / "fake-bin", monkeypatch)
    capsys.readouterr()

    assert main(["doctor"]) == 0

    out = capsys.readouterr().out
    assert "OK: extension runtime openspec" in out
    assert not sentinel.exists()
    assert not (repo / ".git" / "agentmarshal").exists()


# -- which extensions gain the check -----------------------------------------------


def test_each_wrapper_gets_its_own_runtime_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each wrapper gets its own runtime check."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _wrapper_extension(repo, name="openspec", runtime="node >= 20")
    _wrapper_extension(repo, name="denoed", runtime="deno >= 2")
    fake_bin = tmp_path / "fake-bin"
    _fake_runtime(fake_bin, monkeypatch, name="node")
    _fake_runtime(fake_bin, monkeypatch, name="deno", body="printf '2.1.4\\n'")

    assert main(["doctor"]) == 0

    out = capsys.readouterr().out
    assert (
        "OK: extension runtime denoed — " in out
        and "reports 2.1.4, meeting deno >= 2" in out
    )
    assert (
        "OK: extension runtime openspec — " in out
        and "reports 20.11.0, meeting node >= 20" in out
    )
    assert "Summary: all 14 checks passed" in out


def test_an_extension_without_wraps_gets_no_runtime_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension without wraps gets no runtime line."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _dir_extension(repo)

    assert main(["doctor"]) == 0

    out = capsys.readouterr().out
    assert "OK: extension manifest openspec" in out
    assert "extension runtime" not in out
    assert "Summary: all 11 checks passed" in out


def test_an_unreadable_manifest_adds_no_runtime_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unreadable manifest adds no runtime check."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _file_extension(repo, manifest="this is not = toml [unclosed\n")

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert "FAIL: extension manifest declared — " in out
    assert "extension runtime" not in out
    assert "1 check(s) failed" in out


def test_a_project_without_wrappers_prints_doctors_output_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project without wrappers prints doctor's output unchanged."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)

    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert captured.out.count("OK:") == 10
    assert "Summary: all 10 checks passed" in captured.out

    _dir_extension(repo)
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "extension runtime" not in out
    assert "Summary: all 11 checks passed" in out


@pytest.mark.parametrize("runtime_name", ["C:tool", "bin/node", "..", "./tool"])
def test_an_invalid_runtime_name_is_reported_with_no_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_name: str,
) -> None:
    """An invalid `<name>` is reported as invalid and never reaches `which`.

    Not a spec scenario — the check's own seam, and the class review
    finding B1 named: ``shutil.which`` skips the ``PATH`` search for an
    argument it reads as a path — ``bin/node`` or ``./tool``, and on
    Windows a drive-relative ``C:tool`` — and probes it directly. The
    exception is a bare program name, so the name's form is checked
    before any lookup: an executable waits at each spot a lookup could
    reach — ``C:tool`` itself sits on the temporary ``PATH`` (a legal
    POSIX file name), ``bin/node`` and ``tool`` under the working
    directory for the probe POSIX ``which`` would run — and each name
    still fails as invalid rather than finding one.
    """

    repo = _project(tmp_path, monkeypatch)
    _wrapper_extension(repo, runtime=f"{runtime_name} >= 1")
    _fake_runtime(tmp_path / "fake-bin", monkeypatch, name="C:tool")
    for probe in (repo / "bin" / "node", repo / "tool"):
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("#!/bin/sh\nprintf 'v99.0.0\\n'\n", encoding="utf-8")
        probe.chmod(0o755)

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert (
        f"FAIL: extension runtime openspec — the declared runtime name "
        f"{runtime_name} is invalid; openspec requires {runtime_name} >= 1" in out
    )


def test_a_runtime_name_of_bare_program_name_form_resolves_on_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `<name>` of bare program-name characters resolves on PATH.

    The declared form keeps dots, digits, underscores and dashes — a
    runtime named ``py3.11-fmt_1`` is a bare program name, not a path,
    so it is resolved through the temporary ``PATH`` like ``node``.
    """

    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    name = "py3.11-fmt_1"
    _wrapper_extension(repo, runtime=f"{name} >= 2")
    script = _fake_runtime(tmp_path / "fake-bin", monkeypatch, name=name)

    assert main(["doctor"]) == 0

    out = capsys.readouterr().out
    assert (
        f"OK: extension runtime openspec — {script} reports 20.11.0, "
        f"meeting {name} >= 2" in out
    )
