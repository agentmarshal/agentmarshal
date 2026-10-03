## ADDED Requirements

### Requirement: Local state needs git 2.31 or newer, and `doctor` says so

The helper asking `git rev-parse` asks it with
`--path-format=absolute` — a flag git learned at 2.31 — so resolving
local state requires git 2.31 or newer. `doctor`'s git check SHALL
name that minimum and what it is needed for, and SHALL fail with the
remedy — upgrade git — in the message when the installed git is older
or its version cannot be read. The version SHALL be parsed from `git
--version` output as its first dotted number, so a platform suffix —
`.windows.1`, `(Apple Git-…)`, a vendor's own — plays no part.

#### Scenario: an older git fails the check naming the minimum and the remedy
- **WHEN** `git --version` reports a version older than 2.31
- **THEN** `doctor`'s git check fails, naming 2.31 as the minimum
  local state needs and upgrade git as the remedy

#### Scenario: a new-enough git passes the check
- **WHEN** `git --version` reports version 2.31 or newer
- **THEN** `doctor`'s git check reports the executable available

#### Scenario: the version parses without its platform suffix
- **WHEN** `git --version` reports a version carrying a platform
  suffix, such as `2.39.2.windows.1`
- **THEN** the check reads the version and judges it against the
  minimum, the suffix playing no part

#### Scenario: a version that cannot be read fails the check
- **WHEN** `git --version` succeeds but names no dotted version
- **THEN** `doctor`'s git check fails, naming the minimum local state
  needs and the remedy
