"""Tests for stage isolation — the probe, the namespaces and the notes."""

import ctypes
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import agentmarshal.isolation as isolation
from test_stages import (
    _ci,
    _commit_all,
    _extension,
    _git,
    _manifest,
    _project,
    _repo_with_extension,
    _stage_run,
)


def _force_probe(
    monkeypatch: pytest.MonkeyPatch,
    *,
    network: str | None = None,
    readonly: str | None = None,
) -> None:
    """Force the probe's verdict; ``None`` means the guarantee can be enforced."""

    verdicts = isolation.Probe(network=network, readonly=readonly)
    monkeypatch.setattr(isolation, "probe", lambda: verdicts)


def _spy_setup(monkeypatch: pytest.MonkeyPatch, calls: list[dict[str, object]]) -> None:
    """Record each ``stage_setup`` request and answer a harmless preexec.

    The returned callable writes an all-``ok`` report to the run's
    report pipe and marks it close-on-exec — the wiring is what's
    tested, so the branch does not depend on whether this machine
    permits the namespaces. Each call's ``preexec`` key holds the
    closure the run received.
    """

    def spy(
        *, network: bool, readonly: Path | None, report_fd: int
    ) -> Callable[[], None]:
        def fake_setup() -> None:
            os.set_inheritable(report_fd, False)
            os.write(report_fd, b"network=ok\nread-only candidate=ok\n")

        calls.append({"network": network, "readonly": readonly, "preexec": fake_setup})
        return fake_setup

    monkeypatch.setattr(isolation, "stage_setup", spy)


def _setup_report(
    factory: Callable[..., Callable[[], None]],
    *,
    network: bool,
    readonly: Path | None,
) -> dict[str, str]:
    """Run the closure *factory* builds in-process; the report the parent reads.

    The write end goes through the same ``os.pipe`` the run creates;
    the closure's close-on-exec marking is a no-op for an in-process
    call and the drain sees the report to EOF.
    """

    read_fd, write_fd = os.pipe()
    factory(network=network, readonly=readonly, report_fd=write_fd)()
    os.close(write_fd)
    data = b""
    while chunk := os.read(read_fd, 65536):
        data += chunk
    os.close(read_fd)
    return dict(line.split("=", 1) for line in data.decode("utf-8").splitlines())


def _spy_popen(monkeypatch: pytest.MonkeyPatch, calls: list[dict[str, object]]) -> None:
    """Record the ``preexec_fn`` and ``pass_fds`` each ``Popen`` is started with."""

    real = subprocess.Popen

    def spy(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        calls.append(
            {
                "argv": args[0],
                "preexec_fn": kwargs.get("preexec_fn"),
                "pass_fds": kwargs.get("pass_fds"),
            }
        )
        return real(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", spy)


def _probe_count(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Count how often the run asks the probe for a verdict."""

    calls: list[int] = []

    def counted() -> isolation.Probe:
        calls.append(1)
        return isolation.Probe("no", "no")

    monkeypatch.setattr(isolation, "probe", counted)
    return calls


_ISOLATION_BLOCK = (
    '[isolation]\nnetwork = false\nenv = []\nwrites = "none"\ntimeout_seconds = 30\n'
)


def _isolation_block(env: str = "[]", network: bool = False) -> str:
    return (
        "[isolation]\n"
        f"network = {'true' if network else 'false'}\n"
        f"env = {env}\n"
        'writes = "none"\n'
        "timeout_seconds = 30\n"
    )


# -- network isolation --------------------------------------------------------


def test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage whose manifest declares no network runs in a new user and network namespace."""  # noqa: E501
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    popens: list[dict[str, object]] = []
    _spy_popen(monkeypatch, popens)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert len(calls) == 1
    assert calls[0]["network"] is True
    snapshot = calls[0]["readonly"]
    assert isinstance(snapshot, Path)
    assert snapshot.name.startswith("snapshot-")
    stage_popens = [
        call
        for call in popens
        if isinstance(call["argv"], list)
        and len(call["argv"]) > 1
        and str(call["argv"][1]).endswith("check.py")
    ]
    assert [call["preexec_fn"] for call in stage_popens] == [calls[0]["preexec"]]
    # The report pipe's write end is what ``pass_fds`` keeps open in the
    # child across the spawn's fd closing.
    assert all(
        isinstance(call["pass_fds"], tuple) and len(call["pass_fds"]) == 1
        for call in stage_popens
    )
    captured = capsys.readouterr()
    assert "not enforced" not in captured.out
    assert "not enforced" not in captured.err


def test_a_stage_declaring_network_true_runs_without_the_network_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage declaring network = true runs without the network namespace."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(isolation=_isolation_block(network=True)),
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert calls[0]["network"] is False
    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert "not enforced: network" not in captured.err


def test_a_network_namespace_the_platform_refuses_is_named_and_the_stage_still_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a network namespace the platform refuses is named and the stage still runs."""  # noqa: E501
    _force_probe(monkeypatch, network="a kernel refusing unprivileged namespaces")
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert calls[0]["network"] is False
    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert (
        "not enforced: network "
        "(a kernel refusing unprivileged namespaces)" in captured.err
    )


# -- the pre-gate floor: a read-only candidate --------------------------------


def test_a_pre_gate_stage_s_candidate_directory_is_bound_read_only_over_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pre-gate stage's candidate directory is bound read-only over itself."""  # noqa: E501
    real_stage_setup = isolation.stage_setup
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    candidate = calls[0]["readonly"]
    assert isinstance(candidate, Path)
    assert candidate.name.startswith("snapshot-")
    capsys.readouterr()

    # The closure the request builds applies the mount chain in the
    # child: the user and mount namespaces, the identity maps, the
    # private propagation, the bind onto itself and the read-only
    # remount — and last, before exec, the capability drop.
    unshared: list[int] = []
    written: list[tuple[str, str]] = []
    mounted: list[tuple[str | None, str, int]] = []
    dropped: list[int] = []
    monkeypatch.setattr(os, "unshare", unshared.append)
    monkeypatch.setattr(
        isolation,
        "_write_file",
        lambda path, text: written.append((path, text)),
    )
    monkeypatch.setattr(
        isolation,
        "_mount",
        lambda source, target, flags: mounted.append((source, target, flags)),
    )
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))
    target = Path("/the/candidate")
    report = _setup_report(real_stage_setup, network=False, readonly=target)

    assert report == {"read-only candidate": "ok"}
    assert unshared == [isolation._CLONE_NEWUSER | isolation._CLONE_NEWNS]
    assert written == [
        ("/proc/self/setgroups", "deny"),
        ("/proc/self/uid_map", f"{os.getuid()} {os.getuid()} 1\n"),
        ("/proc/self/gid_map", f"{os.getgid()} {os.getgid()} 1\n"),
    ]
    assert mounted == [
        (None, "/", isolation._MS_REC | isolation._MS_PRIVATE),
        ("/the/candidate", "/the/candidate", isolation._MS_BIND),
        (
            "/the/candidate",
            "/the/candidate",
            isolation._MS_BIND | isolation._MS_REMOUNT | isolation._MS_RDONLY,
        ),
    ]
    assert dropped == [1]


def test_a_mount_the_platform_refuses_is_named_and_the_stage_still_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a mount the platform refuses is named and the stage still runs."""
    _force_probe(
        monkeypatch,
        readonly="the read-only bind: Operation not permitted",
    )
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert calls[0]["readonly"] is None
    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert (
        "not enforced: read-only candidate "
        "(the read-only bind: Operation not permitted)" in captured.err
    )


def test_a_post_gate_stage_s_candidate_is_not_bound_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a post-gate stage's candidate is not bound read-only."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "print('post ran')\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    assert len(calls) == 1
    assert calls[0]["network"] is True
    assert calls[0]["readonly"] is None
    captured = capsys.readouterr()
    assert "read-only" not in captured.err


def test_a_declared_writes_beyond_the_candidate_is_reported_as_not_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared writes beyond the candidate is reported as not enforced."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path, monkeypatch, manifest=_manifest(isolation=_ISOLATION_BLOCK)
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert (
        "not enforced: writes beyond the candidate "
        "(the core has no filesystem sandbox beyond the candidate)" in captured.err
    )


def test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an isolated stage cannot reach the network or write the candidate."""
    verdicts = isolation.probe()
    if verdicts.network is not None and verdicts.readonly is not None:
        pytest.skip(
            "the probe reports nothing it can enforce: "
            f"network ({verdicts.network}); "
            f"read-only candidate ({verdicts.readonly})"
        )
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "import ctypes, os, socket\n"
                "status = open('/proc/self/status').read()\n"
                "caps = [\n"
                "    line.split(':', 1)[1].strip()\n"
                "    for line in status.splitlines()\n"
                "    if line.startswith(('CapEff', 'CapPrm', 'CapBnd'))\n"
                "]\n"
                "print('CAPS:' + (\n"
                "    'zero'\n"
                "    if len(caps) == 3 and all(c == '0' * 16 for c in caps)\n"
                "    else 'nonzero:' + ','.join(caps)\n"
                "))\n"
                "libc = ctypes.CDLL('libc.so.6', use_errno=True)\n"
                "cwd = os.fsencode(os.getcwd())\n"
                "rw = libc.mount(\n"
                "    None, ctypes.c_char_p(cwd), None,\n"
                "    ctypes.c_ulong(0x20 | 0x1000), None,\n"
                ")\n"
                "print('REMOUNT:' + ('blocked' if rw != 0 else 'ok'))\n"
                "um = libc.umount2(ctypes.c_char_p(cwd), ctypes.c_int(2))\n"
                "print('UMOUNT:' + ('blocked' if um != 0 else 'ok'))\n"
                "try:\n"
                '    socket.create_connection(("1.1.1.1", 53), timeout=2)\n'
                '    print("NET:reachable")\n'
                "except OSError:\n"
                '    print("NET:blocked")\n'
                "try:\n"
                '    open("probe-write.txt", "w").write("x")\n'
                '    print("WRITE:ok")\n'
                "except OSError:\n"
                '    print("WRITE:blocked")\n'
            )
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    # A user namespace was entered for at least one guarantee, so the
    # capability drop ran: the stage holds none at all, and the mount
    # it sees cannot be remounted read-write or unmounted back.
    assert "openspec | CAPS:zero" in captured.out
    assert "openspec | REMOUNT:blocked" in captured.out
    assert "openspec | UMOUNT:blocked" in captured.out
    if verdicts.network is None:
        assert "openspec | NET:blocked" in captured.out
        assert "not enforced: network" not in captured.err
    else:
        assert f"not enforced: network ({verdicts.network})" in captured.err
    if verdicts.readonly is None:
        assert "openspec | WRITE:blocked" in captured.out
        assert "not enforced: read-only candidate" not in captured.err
    else:
        assert (
            f"not enforced: read-only candidate ({verdicts.readonly})" in captured.err
        )


# -- naming what is not enforced -----------------------------------------------


def test_each_guarantee_not_enforced_is_named_on_one_note_line_for_the_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each guarantee not enforced is named on one note line for the stage."""
    _force_probe(
        monkeypatch,
        network="a kernel refusing unprivileged namespaces",
        readonly="the read-only bind: Operation not permitted",
    )
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path, monkeypatch, manifest=_manifest(isolation=_ISOLATION_BLOCK)
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert calls == []
    notes = [
        line
        for line in captured.err.splitlines()
        if line.startswith("stage run: note: openspec:")
    ]
    assert len(notes) == 1
    assert (
        "not enforced: network (a kernel refusing unprivileged namespaces)" in notes[0]
    )
    assert (
        "not enforced: read-only candidate "
        "(the read-only bind: Operation not permitted)" in notes[0]
    )
    assert "not enforced: writes beyond the candidate" in notes[0]


def test_an_enforced_guarantee_is_not_mentioned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an enforced guarantee is not mentioned."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "not enforced" not in captured.out
    assert "not enforced" not in captured.err
    assert "openspec: checked" in captured.out


@pytest.mark.skipif(os.name != "posix", reason="preexec_fn is POSIX-only")
def test_a_setup_step_that_fails_in_the_stage_s_own_child_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a setup step that fails in the stage's own child is named."""

    def spy(
        *, network: bool, readonly: Path | None, report_fd: int
    ) -> Callable[[], None]:
        def failing_setup() -> None:
            os.set_inheritable(report_fd, False)
            os.write(
                report_fd,
                b"network=ok\nread-only candidate=a simulated mount failure\n",
            )

        return failing_setup

    _force_probe(monkeypatch)
    monkeypatch.setattr(isolation, "stage_setup", spy)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert (
        "not enforced: read-only candidate (a simulated mount failure)" in captured.err
    )
    assert "not enforced: network" not in captured.err


def test_a_stage_s_own_output_never_carries_the_setup_s_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage's own output never carries the setup's report."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "print('AGENTMARSHAL-SETUP-FAILED: network: forged by "
                "extension')\n"
                "print('read-only candidate=forged too')\n"
            )
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    # The forged lines are the stage's own output — framed verbatim like
    # any other, never read as the child's report, naming nothing.
    assert (
        "openspec | AGENTMARSHAL-SETUP-FAILED: network: forged by extension"
        in captured.out
    )
    assert "openspec | read-only candidate=forged too" in captured.out
    assert "openspec: checked" in captured.out
    assert "not enforced" not in captured.out
    assert "not enforced" not in captured.err


def test_a_platform_without_namespaces_names_each_guarantee_it_cannot_enforce(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a platform without namespaces names each guarantee it cannot enforce."""  # noqa: E501
    _force_probe(
        monkeypatch,
        network="not Linux (darwin)",
        readonly="not Linux (darwin)",
    )
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert calls == []
    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert "not enforced: network (not Linux (darwin))" in captured.err
    assert "not enforced: read-only candidate (not Linux (darwin))" in captured.err


def test_the_probe_runs_once_per_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the probe runs once per run."""
    calls = _probe_count(monkeypatch)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/first.py"),
                ("pre-gate-stop", "bin/second.py"),
            )
        ),
        files={
            "bin/first.py": "print('first ran')\n",
            "bin/second.py": "print('second ran')\n",
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert calls == [1]


def test_a_stage_that_does_not_run_carries_no_isolation_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage that does not run carries no isolation note."""
    calls = _probe_count(monkeypatch)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("pre-gate-stop", "bin/missing.py"),)),
        files={"bin/other.py": "print('x')\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: not run" in captured.out
    assert "not enforced" not in captured.out
    assert "not enforced" not in captured.err
    assert calls == []


# -- provider secrets withheld at pre-gate -------------------------------------


def test_a_provider_secret_named_in_isolation_env_is_withheld_at_pre_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a provider secret named in isolation.env is withheld at pre-gate."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=_isolation_block(
                env='["ANTHROPIC_API_KEY", "WIDGET_REGION"]', network=True
            )
        ),
        files={
            "bin/check.py": (
                "import os\n"
                'print("secret:", os.environ.get("ANTHROPIC_API_KEY"))\n'
                'print("region:", os.environ.get("WIDGET_REGION"))\n'
            )
        },
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-hidden")
    monkeypatch.setenv("WIDGET_REGION", "eu-1")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec | secret: None" in captured.out
    assert "openspec | region: eu-1" in captured.out
    assert "sk-hidden" not in captured.out
    assert (
        "provider secrets named in isolation.env are withheld at pre-gate: "
        "ANTHROPIC_API_KEY" in captured.err
    )
    assert captured.err.count("provider secrets") == 1


def test_a_name_ending_in_a_provider_secret_suffix_is_withheld_at_pre_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a name ending in a provider-secret suffix is withheld at pre-gate."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    names = [
        "ACME_API_KEY",
        "ACME_TOKEN",
        "ACME_SECRET",
        "ACME_PASSWORD",
    ]
    declared = ", ".join(f'"{name}"' for name in names)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=_isolation_block(env=f"[{declared}]", network=True)
        ),
        files={
            "bin/check.py": (
                "import os\n"
                + "".join(
                    f'print("{name}:", os.environ.get("{name}"))\n' for name in names
                )
            )
        },
    )
    for name in names:
        monkeypatch.setenv(name, "hidden")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    for name in names:
        assert f"openspec | {name}: None" in captured.out
    assert "hidden" not in captured.out
    for name in names:
        assert name in captured.err
    assert captured.err.count("provider secrets") == 1


def test_a_declared_provider_secret_reaches_a_post_gate_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared provider secret reaches a post-gate stage."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(("post-gate", "bin/post.py"),),
            isolation=_isolation_block(env='["ANTHROPIC_API_KEY"]', network=True),
        ),
        files={
            "bin/post.py": (
                'import os\nprint("secret:", os.environ.get("ANTHROPIC_API_KEY"))\n'
            )
        },
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-passed")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec | secret: sk-passed" in captured.out
    assert "provider secrets" not in captured.err


def test_the_withheld_provider_secret_names_are_noted_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the withheld provider-secret names are noted once."""
    _force_probe(monkeypatch)
    calls: list[dict[str, object]] = []
    _spy_setup(monkeypatch, calls)
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        name="zeta",
        manifest=_manifest(
            name="zeta",
            stages=(("pre-gate-stop", "bin/z.py"),),
            isolation=_isolation_block(env='["GH_TOKEN"]', network=True),
        ),
        files={"bin/z.py": "print('zeta ran')\n"},
    )
    _extension(
        repo,
        name="alpha",
        manifest=_manifest(
            name="alpha",
            stages=(("pre-gate-stop", "bin/a.py"),),
            isolation=_isolation_block(env='["GITLAB_TOKEN"]', network=True),
        ),
        files={"bin/a.py": "print('alpha ran')\n"},
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    monkeypatch.setenv("GH_TOKEN", "a")
    monkeypatch.setenv("GITLAB_TOKEN", "b")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    notes = [line for line in captured.err.splitlines() if "provider secrets" in line]
    assert len(notes) == 1
    assert "GH_TOKEN" in notes[0]
    assert "GITLAB_TOKEN" in notes[0]


# -- the probe and the child's own machinery -----------------------------------


def test_probe_names_a_platform_that_is_not_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The probe answers without a child where the mechanism cannot exist."""

    monkeypatch.setattr(sys, "platform", "darwin")
    verdicts = isolation.probe()
    assert verdicts.network == "not Linux (darwin)"
    assert verdicts.readonly == "not Linux (darwin)"


def test_probe_names_a_missing_mechanism(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Python without ``os.unshare`` is its own verdict."""

    monkeypatch.delattr(os, "unshare")
    verdicts = isolation.probe()
    assert verdicts.network == "os.unshare or os.fork is unavailable"


def test_the_child_setup_names_each_refused_namespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A combined refusal is decomposed so each guarantee names its own."""

    def refuse(flags: int) -> None:
        raise OSError(1, "Operation not permitted")

    dropped: list[int] = []
    monkeypatch.setattr(os, "unshare", refuse)
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))
    report = _setup_report(isolation.stage_setup, network=True, readonly=Path("/cand"))
    assert report == {
        "network": "Operation not permitted",
        "read-only candidate": "Operation not permitted",
    }
    # No user namespace was entered, so there are no capabilities to drop.
    assert dropped == []


def test_the_child_setup_keeps_a_namespace_the_retry_allows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mount-namespace refusal does not take down the network namespace."""

    def refuse_newns(flags: int) -> None:
        if flags & isolation._CLONE_NEWNS:
            raise OSError(1, "Operation not permitted")

    dropped: list[int] = []
    monkeypatch.setattr(os, "unshare", refuse_newns)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))
    report = _setup_report(isolation.stage_setup, network=True, readonly=Path("/cand"))
    assert report == {
        "network": "ok",
        "read-only candidate": "Operation not permitted",
    }
    # The network namespace stands, so the drop it needs still ran.
    assert dropped == [1]


def test_the_child_setup_names_a_failed_mount(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mount failure after the unshares names only the read-only floor."""

    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: None)

    def refuse(source: str | None, target: str, flags: int) -> None:
        if flags & isolation._MS_REMOUNT:
            raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(isolation, "_mount", refuse)
    report = _setup_report(isolation.stage_setup, network=True, readonly=Path("/cand"))
    assert report == {
        "network": "ok",
        "read-only candidate": "Operation not permitted",
    }


def test_parse_setup_report_names_failures_and_a_missing_report() -> None:
    """An ``ok`` line enforces, a reason names the failure, silence cannot vouch."""

    assert isolation.parse_setup_report(
        b"network=ok\nread-only candidate=the bind failed\n",
        network=True,
        readonly=True,
    ) == [("read-only candidate", "the bind failed")]
    # Nothing arrived — a child that died before writing or a lost write
    # cannot vouch for a guarantee: each is named not enforced.
    assert isolation.parse_setup_report(b"", network=True, readonly=True) == [
        ("network", "the child's setup report did not arrive before exec"),
        (
            "read-only candidate",
            "the child's setup report did not arrive before exec",
        ),
    ]
    assert (
        isolation.parse_setup_report(b"network=ok\n", network=True, readonly=False)
        == []
    )


# -- the capability drop -------------------------------------------------------


class _FakeLibc:
    """Records the ``prctl``/``capset`` calls the drop makes.

    ``fail_prctl`` names an option value for which the call answers -1 —
    the drop's own seam, exercised without the process's real capability
    set ever changing.
    """

    def __init__(self, fail_prctl: int | None = None) -> None:
        self.calls: list[tuple[str, object]] = []
        self.fail_prctl = fail_prctl

    def prctl(self, *args: Any) -> int:
        values = tuple(getattr(arg, "value", arg) for arg in args)
        self.calls.append(("prctl", values))
        return -1 if values and values[0] == self.fail_prctl else 0

    def capset(self, header: Any, data: Any) -> int:
        self.calls.append(
            (
                "capset",
                (
                    header.contents.version,
                    header.contents.pid,
                    [
                        (word.effective, word.permitted, word.inheritable)
                        for word in data
                    ],
                ),
            )
        )
        return 0


def test_drop_capabilities_clears_every_capability_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The drop clears ambient, bounding and live sets, securebits, no_new_privs."""

    fake = _FakeLibc()
    monkeypatch.setattr(isolation, "_libc", lambda: fake)
    monkeypatch.setattr(isolation, "_cap_last_cap", lambda: 2)

    isolation._drop_capabilities()

    assert fake.calls == [
        ("prctl", (47, 4, 0, 0, 0)),  # PR_CAP_AMBIENT, CLEAR_ALL
        ("prctl", (28, 0x0F, 0, 0, 0)),  # PR_SET_SECUREBITS, the four bits
        ("prctl", (38, 1, 0, 0, 0)),  # PR_SET_NO_NEW_PRIVS
        ("prctl", (24, 0, 0, 0, 0)),  # PR_CAPBSET_DROP for 0..cap_last_cap
        ("prctl", (24, 1, 0, 0, 0)),
        ("prctl", (24, 2, 0, 0, 0)),
        (
            "capset",
            (isolation._LINUX_CAPABILITY_VERSION_3, 0, [(0, 0, 0), (0, 0, 0)]),
        ),
    ]


def test_drop_capabilities_names_the_step_that_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A refused step is the drop failure's reason, not a silent pass."""

    fake = _FakeLibc(fail_prctl=28)  # PR_SET_SECUREBITS
    monkeypatch.setattr(isolation, "_libc", lambda: fake)
    monkeypatch.setattr(isolation, "_cap_last_cap", lambda: 2)
    monkeypatch.setattr(ctypes, "get_errno", lambda: 1)

    with pytest.raises(isolation._CapabilityDropError) as caught:
        isolation._drop_capabilities()
    assert str(caught.value) == (
        "capabilities could not be dropped: "
        "prctl(PR_SET_SECUREBITS): Operation not permitted"
    )


def test_a_network_only_stage_setup_drops_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The drop follows the user namespace however it was asked for."""

    dropped: list[int] = []
    mounted: list[tuple[str | None, str, int]] = []
    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(
        isolation,
        "_mount",
        lambda source, target, flags: mounted.append((source, target, flags)),
    )
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))

    report = _setup_report(isolation.stage_setup, network=True, readonly=None)

    assert report == {"network": "ok"}
    assert dropped == [1]
    assert mounted == []


def test_a_capability_drop_failure_names_every_guarantee_the_child_was_asked_to_enforce(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: a capability drop that fails names every guarantee the child was asked to enforce."""  # noqa: E501

    def refuse() -> None:
        raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_mount", lambda s, t, f: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", refuse)
    report = _setup_report(isolation.stage_setup, network=True, readonly=Path("/cand"))
    detail = "capabilities could not be dropped: Operation not permitted"
    assert report == {"network": detail, "read-only candidate": detail}


@pytest.mark.skipif(os.name != "posix", reason="preexec_fn is POSIX-only")
def test_a_failed_capability_drop_is_named_and_the_stage_still_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A drop forced to fail in the stage's child names both guarantees."""

    def refuse() -> None:
        raise OSError(1, "Operation not permitted")

    _force_probe(monkeypatch)
    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_mount", lambda s, t, f: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", refuse)
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    detail = "capabilities could not be dropped: Operation not permitted"
    assert f"not enforced: network ({detail})" in captured.err
    assert f"not enforced: read-only candidate ({detail})" in captured.err


def test_the_probe_child_runs_the_capability_drop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The probe's enforceable verdict covers the drop: it runs it."""

    dropped: list[int] = []
    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_probe_read_only", lambda directory: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))

    verdicts = isolation._probe_child("/unused")

    assert verdicts == {"network": None, "readonly": None}
    assert dropped == [1]


def test_the_probe_names_a_capability_drop_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A drop failure in the probe's child marks the guarantees unenforceable."""

    def refuse() -> None:
        raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", lambda path, text: None)
    monkeypatch.setattr(isolation, "_probe_read_only", lambda directory: None)
    monkeypatch.setattr(isolation, "_drop_capabilities", refuse)

    verdicts = isolation._probe_child("/unused")

    detail = "capabilities could not be dropped: Operation not permitted"
    assert verdicts == {"network": detail, "readonly": detail}


def test_the_probe_child_skips_the_drop_without_the_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No uid/gid maps, no granted capabilities: the drop is not attempted."""

    dropped: list[int] = []

    def refuse(path: str, text: str) -> None:
        raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(os, "unshare", lambda flags: None)
    monkeypatch.setattr(isolation, "_write_file", refuse)
    monkeypatch.setattr(isolation, "_drop_capabilities", lambda: dropped.append(1))

    verdicts = isolation._probe_child("/unused")

    assert dropped == []
    assert verdicts["network"] is not None
    assert verdicts["network"].startswith("the uid/gid maps:")
    assert verdicts["readonly"] is not None
