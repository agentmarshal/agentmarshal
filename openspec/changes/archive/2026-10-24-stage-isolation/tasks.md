## 1. The mechanism

- [x] 1.1 `src/agentmarshal/isolation.py` carries the `Probe`
  verdict, the run-once probe in a throwaway `os.fork` child, the
  `stage_setup` `preexec_fn` closure — `os.unshare`, the `deny`
  setgroups and identity uid/gid maps, the private propagation and
  the read-only self-bind through libc `mount`, then the capability
  drop — the close-on-exec report pipe the child's failures ride,
  and `parse_setup_report` reading them —
  verify: `probe()` answers `network`/`readonly` verdicts and the
  closure's steps are exercised by monkeypatched syscalls.
- [x] 1.2 `src/agentmarshal/stages.py` withholds provider secrets at
  `pre-gate`, passes the probe's setup to `Popen` as `preexec_fn`,
  and emits one `not enforced` note per stage in the style of the
  `PATH is fixed by the core` note — verify: the note names each
  unenforced guarantee with its reason and no enforced one.
- [x] 1.3 Tests force every probe branch with `monkeypatch` and one
  end-to-end stage tries `socket.create_connection` and a candidate
  write, skipping with the probe's reason where the real probe finds
  nothing to enforce — verify: each delta scenario is demonstrated
  by a test whose docstring names it.

## 2. The delta and the archive

- [x] 2.1 The MODIFIED requirement carries the provider-secret
  withholding in its full text with all existing scenarios kept, and
  the ADDED requirements carry the namespace floor, the read-only
  candidate and the honest-naming rule — verify: the published
  `extension-stages` spec folds them.
- [x] 2.2 The change is archived with the archive command — verify:
  it lives under `openspec/changes/archive/`.
