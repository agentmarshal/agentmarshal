"""Stage-process isolation: Linux namespaces and a read-only bind.

ADR-0013 decision 8: isolation is declared in the manifest, and for
``pre-gate`` there is a floor the manifest cannot remove — the candidate
snapshot is read-only. The core enforces what is declared as far as the
platform allows and names in its output what it cannot enforce. The
mechanisms live here: a probe — run once in a throwaway child and cached
for the run — that finds which guarantees this platform and this
environment allow, and the ``preexec_fn``-style setup the stage's own
child applies before exec: ``os.unshare`` of the user and network
namespaces (plus the mount namespace for the read-only floor), ``deny``
to ``/proc/self/setgroups`` and a one-line identity mapping of the
caller's uid and gid to the uid/gid maps, then ``mount(NULL, "/",
NULL, MS_REC | MS_PRIVATE)`` and a bind of the candidate directory onto
itself remounted ``MS_BIND | MS_REMOUNT | MS_RDONLY`` together with the
flags the candidate's own mount holds that a user namespace may not
clear — a remount that would drop one is refused ``EPERM`` — and an
``os.chdir`` back into the directory, since the working directory the
spawn set up before ``preexec_fn`` still names the underlying writable
mount — never a shell and never a tool looked up on ``PATH``. Last,
before exec, the child drops
every capability the new user namespace granted it — the ambient set,
the ``NOROOT``/``NO_SETUID_FIXUP`` securebits and ``no_new_privs``, the
bounding set and the live effective/permitted/inheritable sets —
because those capabilities survive ``execve`` (user_namespaces(7)) and
would let the stage itself remount or unmount what was bound.

A setup step that fails in the stage's child is never silent: before
exec the child writes each requested guarantee's outcome to a dedicated
report pipe the parent created — the write end close-on-exec from
``os.pipe()`` already and never in ``pass_fds``, which would clear the
flag — closed by the spawn's own descriptor sweep before ``execve``, so
the extension's code never holds it — and the run names what the report
calls failed not enforced the same way the probe's refusals are named;
a report that never arrives cannot vouch for a guarantee, so it is
named the same way.
Nothing in the stage's own output is ever read as a core message. A
capability drop that fails names every guarantee the child was asked
to enforce — it must never exec silently with capabilities. The stage
still runs, weakened but honestly reported.
"""

from __future__ import annotations

import ctypes
import os
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

#: The namespace flags (``linux/sched.h``); ``os`` carries them on Linux
#: and the literals keep the probe honest elsewhere.
_CLONE_NEWNS = getattr(os, "CLONE_NEWNS", 0x00020000)
_CLONE_NEWUSER = getattr(os, "CLONE_NEWUSER", 0x10000000)
_CLONE_NEWNET = getattr(os, "CLONE_NEWNET", 0x40000000)

#: The mount flags (``linux/mount.h``).
_MS_RDONLY = 0x0001
_MS_NOSUID = 0x0002
_MS_NODEV = 0x0004
_MS_NOEXEC = 0x0008
_MS_REMOUNT = 0x0020
_MS_NOATIME = 0x0400
_MS_NODIRATIME = 0x0800
_MS_BIND = 0x1000
_MS_REC = 0x4000
_MS_PRIVATE = 0x40000
_MS_RELATIME = 0x200000

#: The ``statvfs`` ``f_flag`` bits (``sys/vfs.h``) for the mount flags a
#: user namespace may not clear. They are not the ``MS_*`` values —
#: ``ST_RELATIME`` is 4096 where ``MS_RELATIME`` is ``1 << 21`` — so the
#: remount's flags come from a mapping, never from copying ``f_flag``.
_ST_NOSUID = getattr(os, "ST_NOSUID", 2)
_ST_NODEV = getattr(os, "ST_NODEV", 4)
_ST_NOEXEC = getattr(os, "ST_NOEXEC", 8)
_ST_NOATIME = getattr(os, "ST_NOATIME", 1024)
_ST_NODIRATIME = getattr(os, "ST_NODIRATIME", 2048)
_ST_RELATIME = getattr(os, "ST_RELATIME", 4096)

#: The ``prctl`` options (``linux/prctl.h``) the capability drop uses.
_PR_CAPBSET_DROP = 24
_PR_SET_SECUREBITS = 28
_PR_SET_NO_NEW_PRIVS = 38
_PR_CAP_AMBIENT = 47
_PR_CAP_AMBIENT_CLEAR_ALL = 4

#: The securebits (``linux/securebits.h``) the drop sets: ``NOROOT``
#: keeps a uid that maps to 0 inside the user namespace — the caller's
#: own, on a uid-0 run — from regaining the full set at ``execve``, and
#: ``NO_SETUID_FIXUP`` keeps a setuid exec from doing the same; the
#: ``LOCKED`` halves make both irreversible.
_SECBITS_NOROOT_AND_FIXUP = 0x01 | 0x02 | 0x04 | 0x08

#: ``capset``'s v3 header accepts the two-word data array covering all
#: 64 capability slots.
_LINUX_CAPABILITY_VERSION_3 = 0x20080522

#: The guarantees a stage's setup can enforce or report: ``network`` — a
#: new user and network namespace — and ``read-only candidate`` — the
#: pre-gate floor. ``writes`` is never a guarantee the setup attempts.
_NETWORK = "network"
_READONLY = "read-only candidate"


@dataclass(frozen=True)
class Probe:
    """What this platform and environment let the core enforce.

    A field holding ``None`` means the guarantee can be enforced; a
    string is the reason it cannot — carried into the run's ``not
    enforced`` note unchanged.
    """

    network: str | None
    readonly: str | None


class _CapabilityDropError(Exception):
    """A capability-drop step failed; the message names the mechanism."""


class _CapHeader(ctypes.Structure):
    """``__user_cap_header_struct`` for the ``capset`` call."""

    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


class _CapData(ctypes.Structure):
    """``__user_cap_data_struct``: the effective, permitted, inheritable sets."""

    _fields_ = [
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32),
    ]


def _error_detail(error: BaseException) -> str:
    """An error's human detail — an ``OSError``'s strerror, else str()."""

    if isinstance(error, OSError):
        return error.strerror or str(error)
    return str(error)


def _write_file(path: str, text: str) -> None:
    """Write *text* to *path*; a small seam for the child's own writes."""

    Path(path).write_text(text, encoding="utf-8")


def _write_identity_maps(uid: int, gid: int) -> None:
    """``deny`` the setgroups and map the caller's uid/gid identically.

    The one-line identity mapping keeps the stage's own uid and gid: the
    capabilities the new user namespace grants are what the mounts need,
    and the stage sees its files exactly as the caller's user would.
    ``setgroups`` must be denied before the gid map is written, and the
    ids are the caller's — captured before ``unshare``: asked inside the
    new namespace, ``getuid`` can only answer the overflow id.
    """

    _write_file("/proc/self/setgroups", "deny")
    _write_file("/proc/self/uid_map", f"{uid} {uid} 1\n")
    _write_file("/proc/self/gid_map", f"{gid} {gid} 1\n")


def _libc() -> ctypes.CDLL:
    """libc with errno capture; a small seam for the child's own calls."""

    return ctypes.CDLL("libc.so.6", use_errno=True)


def _mount(source: str | None, target: str, flags: int) -> None:
    """libc ``mount`` through ctypes; raises ``OSError`` on failure."""

    source_b = None if source is None else os.fsencode(source)
    if (
        _libc().mount(
            ctypes.c_char_p(source_b),
            ctypes.c_char_p(os.fsencode(target)),
            None,
            ctypes.c_ulong(flags),
            None,
        )
        != 0
    ):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _cap_last_cap() -> int:
    """The highest capability index the kernel knows; bounds the drop."""

    return int(
        Path("/proc/sys/kernel/cap_last_cap").read_text(encoding="ascii").strip()
    )


def _drop_capabilities() -> None:
    """Drop every capability the child's user namespace granted.

    A new user namespace hands the process its full capability set, and
    ``execve`` does not take it back (user_namespaces(7)) — with it a
    stage could remount or unmount the read-only bind. The sequence,
    all through libc: the ambient set cleared, the ``NOROOT`` and
    ``NO_SETUID_FIXUP`` securebits set and locked, ``no_new_privs`` set,
    every bounding capability dropped up to ``cap_last_cap`` — which
    needs ``CAP_SETPCAP``, so the live ``capset`` clearing the
    effective, permitted and inheritable sets comes last. Every step
    that fails raises ``_CapabilityDropError`` naming the step: a child
    must never exec silently still holding capabilities.
    """

    libc = _libc()
    try:
        last_cap = _cap_last_cap()
    except (OSError, ValueError) as caught:
        raise _CapabilityDropError(
            f"capabilities could not be dropped: cap_last_cap: {_error_detail(caught)}"
        ) from caught

    def prctl(option: int, arg2: int, name: str) -> None:
        if (
            libc.prctl(
                ctypes.c_int(option),
                ctypes.c_ulong(arg2),
                ctypes.c_ulong(0),
                ctypes.c_ulong(0),
                ctypes.c_ulong(0),
            )
            != 0
        ):
            errno = ctypes.get_errno()
            raise _CapabilityDropError(
                f"capabilities could not be dropped: {name}: {os.strerror(errno)}"
            )

    prctl(
        _PR_CAP_AMBIENT,
        _PR_CAP_AMBIENT_CLEAR_ALL,
        "prctl(PR_CAP_AMBIENT_CLEAR_ALL)",
    )
    prctl(_PR_SET_SECUREBITS, _SECBITS_NOROOT_AND_FIXUP, "prctl(PR_SET_SECUREBITS)")
    prctl(_PR_SET_NO_NEW_PRIVS, 1, "prctl(PR_SET_NO_NEW_PRIVS)")
    for cap in range(last_cap + 1):
        prctl(_PR_CAPBSET_DROP, cap, f"prctl(PR_CAPBSET_DROP, {cap})")
    header = _CapHeader(version=_LINUX_CAPABILITY_VERSION_3, pid=0)
    data = (_CapData * 2)()
    if libc.capset(ctypes.pointer(header), data) != 0:
        errno = ctypes.get_errno()
        raise _CapabilityDropError(
            f"capabilities could not be dropped: capset: {os.strerror(errno)}"
        )


def _drop_failure(error: BaseException) -> _CapabilityDropError:
    """A drop error normalised to the ``capabilities could not be dropped`` text."""

    if isinstance(error, _CapabilityDropError):
        return error
    return _CapabilityDropError(
        f"capabilities could not be dropped: {_error_detail(error)}"
    )


#: ``ST_*`` → ``MS_*`` for each mount flag the kernel locks on a mount a
#: user namespace touches: the remount must carry what the candidate's
#: own mount already holds or the kernel answers ``EPERM``.
_LOCKED_FLAG_MAP = (
    (_ST_NOSUID, _MS_NOSUID),
    (_ST_NODEV, _MS_NODEV),
    (_ST_NOEXEC, _MS_NOEXEC),
    (_ST_NOATIME, _MS_NOATIME),
    (_ST_NODIRATIME, _MS_NODIRATIME),
    (_ST_RELATIME, _MS_RELATIME),
)


def _locked_mount_flags(f_flag: int) -> int:
    """The ``MS_*`` flags *f_flag* reports that the remount must keep."""

    flags = 0
    for statvfs_flag, mount_flag in _LOCKED_FLAG_MAP:
        if f_flag & statvfs_flag:
            flags |= mount_flag
    return flags


def _bind_read_only(directory: str) -> None:
    """Make propagation private, bind *directory* read-only, re-enter it.

    The bind mounts the directory onto itself and the remount turns that
    new mount read-only. A remount made inside a user namespace may not
    clear a flag the mount it was cloned from holds — the kernel
    answers ``EPERM``, which is why a candidate under a
    ``nosuid,nodev`` mount such as ``/tmp`` could not be bound before —
    so the remount carries every locked flag ``statvfs`` reports for
    the directory's own mount. Then the child re-enters the directory:
    the working directory the spawn set before ``preexec_fn`` still
    names the underlying writable mount, and only a fresh lookup lands
    on the read-only bind.
    """

    locked = _locked_mount_flags(os.statvfs(directory).f_flag)
    _mount(None, "/", _MS_REC | _MS_PRIVATE)
    _mount(directory, directory, _MS_BIND)
    _mount(directory, directory, _MS_BIND | _MS_REMOUNT | _MS_RDONLY | locked)
    os.chdir(directory)


def stage_setup(
    *, network: bool, readonly: Path | None, report_fd: int
) -> Callable[[], None]:
    """The ``preexec_fn``-style setup for a stage's child.

    *network* asks for a new user and network namespace (the manifest did
    not declare ``network = true``); *readonly* asks for the read-only
    candidate floor (a ``pre-gate`` stage): in the same child a new mount
    namespace binds the candidate directory read-only over itself — the
    remount keeping the locked flags the candidate's mount reports — and
    re-enters it, so the working directory the spawn inherited names the
    read-only bind. Each requested guarantee is attempted so a failure
    is named on the right
    guarantee: the combined ``os.unshare`` is tried first — the call the
    design prescribes — and only on a refusal is each namespace retried
    on its own so each guarantee carries its own reason. Last, before
    exec, every capability the new user namespace granted is dropped —
    they survive ``execve`` and would let the stage undo the
    enforcement — so a drop failure is reported on every guarantee
    still standing.

    *report_fd* is the write end of a dedicated pipe the parent created:
    ``os.pipe()`` returns it close-on-exec already (PEP 446) and it is
    never in ``pass_fds`` — ``pass_fds`` would clear the flag — so the
    spawn's own descriptor sweep closes it before ``execve`` and the
    extension's code never holds it. Still before exec the child writes
    one ``<guarantee>=<ok|reason>`` line per requested guarantee in a
    single write, the report the parent reads to EOF. Whatever fails is
    named in the report and the stage runs weakened; the setup itself
    never raises out of the child.
    """

    requested = [
        label
        for label, asked in ((_NETWORK, network), (_READONLY, readonly is not None))
        if asked
    ]
    target = None if readonly is None else str(readonly)
    uid, gid = os.getuid(), os.getgid()

    def setup() -> None:
        # The write end needs no marking here: ``os.pipe()`` returned it
        # close-on-exec already (PEP 446) and it is not in ``pass_fds``
        # — ``pass_fds`` would clear the flag — so the spawn's own fd
        # sweep closes it before ``execve``. And the whole setup is one
        # guarded block from its first line: whatever step fails names
        # each asked-for guarantee in the report and the function
        # returns, so the stage still execs and runs unconfined for
        # what failed — an exception escaping a ``preexec_fn`` is the
        # parent's ``SubprocessError``, a ``not run`` where a run and a
        # name were owed. The capability drop keeps its own rule inside
        # ``_setup``: a failure there names every guarantee.
        try:
            problems: list[tuple[str, BaseException]] = []
            failed: set[str] = set()
            try:
                _setup(problems, failed)
            except Exception as error:
                for label in requested:
                    if label not in failed:
                        problems.append((label, error))
                        failed.add(label)
            reasons = {
                label: _error_detail(problem).replace("\n", " ")
                for label, problem in problems
            }
            payload = b"".join(
                f"{label}={reasons.get(label, 'ok')}\n".encode(
                    "utf-8", errors="replace"
                )
                for label in requested
            )
            os.write(report_fd, payload)
        except BaseException:
            # Whatever failed — the setup, the report's build or its
            # write — what the pipe does not carry cannot vouch for a
            # guarantee: the parent names each not enforced. The
            # function always returns, so the stage still execs.
            pass

    def _setup(problems: list[tuple[str, BaseException]], failed: set[str]) -> None:
        flags = _CLONE_NEWUSER
        if network:
            flags |= _CLONE_NEWNET
        if target is not None:
            flags |= _CLONE_NEWNS
        user_namespace = False
        try:
            os.unshare(flags)
            user_namespace = True
        except OSError as combined_error:
            if len(requested) == 1:
                problems.append((requested[0], combined_error))
                failed.add(requested[0])
            else:
                # The combined call refused: take the guarantees apart
                # so each names its own reason — a network namespace the
                # kernel allows must not go unmade because the mount
                # namespace was refused, and the note must say which.
                retried = _try_unshare(_CLONE_NEWUSER | _CLONE_NEWNET)
                if retried is None:
                    user_namespace = True
                else:
                    problems.append((_NETWORK, retried))
                    failed.add(_NETWORK)
                retried = _try_unshare(
                    _CLONE_NEWNS if user_namespace else _CLONE_NEWUSER | _CLONE_NEWNS
                )
                if retried is None:
                    user_namespace = True
                else:
                    problems.append((_READONLY, retried))
                    failed.add(_READONLY)
        if user_namespace:
            try:
                _write_identity_maps(uid, gid)
            except OSError as error:
                # The maps underpin whatever the namespaces were raised
                # for: name every requested guarantee still standing.
                for label in requested:
                    if label not in failed:
                        problems.append((label, error))
                        failed.add(label)
            else:
                if target is not None and _READONLY not in failed:
                    try:
                        _bind_read_only(target)
                    except OSError as error:
                        problems.append((_READONLY, error))
                        failed.add(_READONLY)
                # The user namespace's capabilities survive execve and
                # would let the stage undo what was enforced — drop them
                # last, after the mounts that needed them. A failure
                # must never exec silently with capabilities: every
                # guarantee still standing is named not enforced.
                try:
                    _drop_capabilities()
                except Exception as error:
                    dropped = _drop_failure(error)
                    for label in requested:
                        if label not in failed:
                            problems.append((label, dropped))
                            failed.add(label)

    return setup


def _try_unshare(flags: int) -> OSError | None:
    """One ``os.unshare`` attempt; the error, or ``None`` on success."""

    try:
        os.unshare(flags)
    except OSError as error:
        return error
    return None


def parse_setup_report(
    data: bytes, *, network: bool, readonly: bool
) -> list[tuple[str, str]]:
    """The guarantees the stage child's report names as failed or cannot vouch for.

    *data* is what the dedicated report pipe carried to EOF: one
    ``<guarantee>=<ok|reason>`` line per guarantee the child was asked
    to enforce — the pipe is a channel the extension's own output
    cannot reach, closed the instant ``execve`` succeeds. A guarantee
    the report does not name — a child that died before writing, a
    write that failed — may have stopped halfway through its setup, so
    it is reported not enforced, never assumed enforced. *network* and
    *readonly* name the guarantees the stage's child was asked for, in
    the same terms ``stage_setup`` takes.
    """

    reported: dict[str, str] = {}
    for line in data.decode("utf-8", errors="replace").splitlines():
        label, separator, value = line.partition("=")
        if separator:
            reported.setdefault(label, value)
    failures: list[tuple[str, str]] = []
    for label, asked in ((_NETWORK, network), (_READONLY, readonly)):
        if not asked:
            continue
        outcome = reported.get(label)
        if outcome is None:
            failures.append(
                (label, "the child's setup report did not arrive before exec")
            )
        elif outcome != "ok":
            failures.append((label, outcome))
    return failures


def probe() -> Probe:
    """Which guarantees this platform and environment allow; run once.

    Non-Linux platforms and Pythons without ``os.unshare`` or ``os.fork``
    answer without a child; on Linux a throwaway ``os.fork`` child runs
    ``_probe_child`` — the real sequence, against a temporary directory —
    and reports each guarantee's verdict over a pipe. The child must not
    exec: a uid/gid map written after ``execve`` is refused, which is
    the same reason the stage's setup is a ``preexec_fn`` and not a
    wrapper process. A probe that cannot fork, that dies or that does
    not report is itself the reason both guarantees are named not
    enforceable: never a silent pass.
    """

    if sys.platform != "linux":
        reason = f"not Linux ({sys.platform})"
        return Probe(reason, reason)
    mechanisms = getattr(os, "unshare", None), getattr(os, "fork", None)
    if None in mechanisms:
        reason = "os.unshare or os.fork is unavailable"
        return Probe(reason, reason)
    reasons: dict[str, str] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="agentmarshal-probe-") as directory:
            read_fd, write_fd = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(read_fd)
                try:
                    verdicts = _probe_child(directory)
                    payload = "".join(
                        f"{key}={verdict or 'ok'}\n"
                        for key, verdict in verdicts.items()
                    ).encode()
                except BaseException as error:  # report, then leave
                    payload = f"probe={error}\n".encode()
                try:
                    os.write(write_fd, payload)
                finally:
                    os._exit(0)
            os.close(write_fd)
            try:
                data = b""
                while chunk := os.read(read_fd, 4096):
                    data += chunk
            finally:
                os.close(read_fd)
                os.waitpid(pid, 0)
    except OSError as error:
        reason = f"the namespace probe could not run: {error}"
        return Probe(reason, reason)
    for line in data.decode("utf-8", errors="replace").splitlines():
        key, _, value = line.partition("=")
        if key in ("network", "readonly", "probe") and value:
            reasons[key] = value
    failed = reasons.get(
        "probe",
        "the namespace probe did not report",
    )
    return Probe(
        None if reasons.get("network") == "ok" else reasons.get("network", failed),
        None if reasons.get("readonly") == "ok" else reasons.get("readonly", failed),
    )


def _probe_child(directory: str) -> dict[str, str | None]:
    """The probe's child side: apply the real sequence, return the verdicts.

    Returns ``{"network": ...}`` and ``{"readonly": ...}`` — ``None`` for
    a guarantee the sequence enforces, else the reason naming the step
    that refused, so the run's note can say why. The sequence is the
    stage child's own: the unshares, the identity maps, then the
    private-propagation and read-only bind against *directory* — inside
    the child's own namespaces, which die with it.
    """

    network_reason: str | None = None
    readonly_reason: str | None = None
    user_namespace = False
    mount_ready = False
    mapped = False
    uid, gid = os.getuid(), os.getgid()
    try:
        try:
            os.unshare(_CLONE_NEWUSER | _CLONE_NEWNET)
            user_namespace = True
        except OSError as error:
            network_reason = (
                f"unshare(CLONE_NEWUSER | CLONE_NEWNET): {error.strerror or error}"
            )
        if user_namespace:
            mount_error = _try_unshare(_CLONE_NEWNS)
            mount_ready = mount_error is None
            if mount_error is not None:
                readonly_reason = (
                    f"unshare(CLONE_NEWNS): {mount_error.strerror or mount_error}"
                )
        else:
            mount_error = _try_unshare(_CLONE_NEWUSER | _CLONE_NEWNS)
            user_namespace = mount_ready = mount_error is None
            if mount_error is not None:
                readonly_reason = (
                    "unshare(CLONE_NEWUSER | CLONE_NEWNS): "
                    f"{mount_error.strerror or mount_error}"
                )
        if user_namespace:
            try:
                _write_identity_maps(uid, gid)
            except OSError as error:
                detail = f"the uid/gid maps: {error.strerror or error}"
                network_reason = network_reason or detail
                readonly_reason = readonly_reason or detail
                mount_ready = False
            else:
                mapped = True
        if mount_ready:
            readonly_reason = _probe_read_only(directory)
        if mapped:
            # The stage child drops the capabilities last; the probe's
            # verdict must cover that step too, so the same drop runs
            # here — after the mounts that needed the capabilities.
            drop_reason = _probe_capability_drop()
            network_reason = network_reason or drop_reason
            readonly_reason = readonly_reason or drop_reason
    except Exception as error:
        detail = f"the namespace probe failed: {error}"
        network_reason = network_reason or detail
        readonly_reason = readonly_reason or detail
    return {"network": network_reason, "readonly": readonly_reason}


def _probe_capability_drop() -> str | None:
    """The stage child's capability drop; the reason, or ``None``."""

    try:
        _drop_capabilities()
    except Exception as error:
        return str(_drop_failure(error))
    return None


def _probe_read_only(directory: str) -> str | None:
    """The read-only bind against *directory*; the reason, or ``None``."""

    try:
        _bind_read_only(directory)
    except OSError as error:
        return f"the read-only bind: {error.strerror or error}"
    try:
        Path(directory, ".agentmarshal-read-only-probe").write_text(
            "x", encoding="utf-8"
        )
    except OSError:
        return None
    return "the remount reported success but the directory stayed writable"
