## 1. The mechanism

- [x] 1.1 `src/agentmarshal/isolation.py` maps the `ST_*` flags
  `os.statvfs(directory).f_flag` reports to the `MS_*` flags a
  user-namespace remount may not clear, carries them on the
  `MS_BIND | MS_REMOUNT | MS_RDONLY` remount, and re-enters the
  candidate with `os.chdir` after it — `_probe_read_only` running
  the same sequence — verify: the forced tests name each mapped
  flag and the re-entry, and a failure of either step is named on
  the read-only guarantee.
- [x] 1.2 Tests force `statvfs`, `mount` and `chdir` outcomes with
  `monkeypatch`, and the end-to-end stage writes the candidate
  through a relative path and an absolute one, skipping with the
  probe's reason where the real probe cannot enforce — verify:
  each delta scenario is demonstrated by a test whose docstring
  names it.

## 2. The delta and the archive

- [x] 2.1 The MODIFIED requirement carries the locked-flag remount
  and the re-entry in its full text with all existing scenarios
  kept — verify: the published `extension-stages` spec folds them.
- [x] 2.2 The change is archived with the archive command —
  verify: it lives under `openspec/changes/archive/`.
