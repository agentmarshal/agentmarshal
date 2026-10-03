## MODIFIED Requirements

### Requirement: The log directory is bounded as a whole

Every process run is a writer of its own, so per-writer retention bounds
nothing: a writer that opens SHALL bound the `log/` directory as a whole —
its writer files and the `files/` payload area alike. While the regular
files it holds total more than the directory cap — a module constant of
50 MiB — the oldest files SHALL be deleted first, by modification time. A
rotated writer file — `<name>.jsonl.<n>` — SHALL be a deletion candidate at
any age, since no writer ever appends to one again, and a published payload
file under `files/` SHALL be a candidate at any age, since its publish
rename is the last write it ever sees. A current `<name>.jsonl` writer
file and a `.part` staging file SHALL be candidates only once their last
write is older than the abandonment age — a module constant — since a
younger one may still belong to a running writer: a current writer file a
writer may still hold is never deleted. The sweep SHALL never follow a
symlink: a `files/` entry that is not a real directory is skipped whole,
and so is any entry that is not a regular file — under `files/` or beside
it — so only regular files inside the real area are ever unlinked. A file
that is no candidate, and a deletion that fails, SHALL be skipped: the
bound is best-effort and SHALL NOT fail the open that runs it.

#### Scenario: a directory over the bound sheds its oldest files first
- **WHEN** a writer opens against a directory holding more than the cap
- **THEN** files are deleted until the total fits, oldest by modification
  time first, and the open still succeeds

#### Scenario: a young current file is never deleted
- **WHEN** a writer opens against a directory over the cap whose current
  files were all written within the abandonment age
- **THEN** every current file stays — the bound gives way before a file a
  writer may still hold

#### Scenario: a rotated file is a candidate whatever its age
- **WHEN** a writer opens against a directory over the cap holding a
  freshly rotated file
- **THEN** the rotated file may be deleted even though it is young

#### Scenario: a published payload is a candidate whatever its age
- **WHEN** a writer opens against a directory over the cap holding a
  freshly published payload file
- **THEN** the payload file may be deleted even though it is young

#### Scenario: a young staging file is never deleted
- **WHEN** a writer opens against a directory over the cap holding a
  `.part` staging file written within the abandonment age
- **THEN** the staging file stays — the bound gives way before a file a
  writer may still be writing

#### Scenario: an abandoned staging file is a candidate
- **WHEN** a writer opens against a directory over the cap holding a
  `.part` staging file whose last write is older than the abandonment age
- **THEN** the staging file may be deleted, like an abandoned current file

#### Scenario: a symlinked files area is skipped whole
- **WHEN** a writer opens against a log directory whose `files/` entry is
  a symlink to a directory of files
- **THEN** the sweep never enters it and every file the link names stays

#### Scenario: a symlinked entry is never unlinked
- **WHEN** a writer opens against a directory over the cap holding a
  symlink — under `files/` or beside it — that names a regular file
- **THEN** the link stays and so does the file it names
