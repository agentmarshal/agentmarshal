## 1. The documented contract

- [x] 1.1 The configuration section states the snapshot as working directory, relative-path resolution inside it, and the prompt-file placeholder — verify: read `docs/quickstart.md`.
- [x] 1.2 The same section states that the snapshot bounds where the command starts and not what it may read, and that confining reads is the adapter's job — verify: read.

## 2. The named token

- [x] 2.1 An unsupported placeholder is named in the refusal — verify: launcher test asserting the token appears in the message.

## 3. The dry run

- [x] 3.1 `review --dry-run` launches the configured command on a synthetic prompt and reports a parseable verdict as success — verify: test with a stub reviewer.
- [x] 3.2 Output with no parseable verdict is reported as a failure naming what could not be parsed — verify: test with a stub that prints prose only.
- [x] 3.3 A dry run requires neither task nor commit and writes nothing into the journal — verify: test asserting the journal directory is unchanged.
- [x] 3.4 The flag's help says it records nothing — verify: CLI help test.
