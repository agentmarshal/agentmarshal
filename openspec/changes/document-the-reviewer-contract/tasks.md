## 1. The documented contract

- [ ] 1.1 The configuration section states the snapshot as working directory, relative-path resolution inside it, and the prompt-file placeholder — verify: read `docs/quickstart.md`.
- [ ] 1.2 The same section states that the snapshot bounds where the command starts and not what it may read, and that confining reads is the adapter's job — verify: read.

## 2. The named token

- [ ] 2.1 An unsupported placeholder is named in the refusal — verify: launcher test asserting the token appears in the message.

## 3. The dry run

- [ ] 3.1 `review --dry-run` launches the configured command on a synthetic prompt and reports a parseable verdict as success — verify: test with a stub reviewer.
- [ ] 3.2 Output with no parseable verdict is reported as a failure naming what could not be parsed — verify: test with a stub that prints prose only.
- [ ] 3.3 A dry run requires neither task nor commit and writes nothing into the journal — verify: test asserting the journal directory is unchanged.
- [ ] 3.4 The flag's help says it records nothing — verify: CLI help test.
