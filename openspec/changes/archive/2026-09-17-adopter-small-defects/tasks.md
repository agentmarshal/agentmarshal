## 1. The scan says where and what

- [x] 1.1 A hit names the file and the signature, and never the matched text — verify: capture test on a built-in signature.
- [x] 1.2 A private-marker hit names the file and the marker's position, never its value — verify: capture test asserting the marker string is absent from the rendering.
- [x] 1.3 The gate's added-content warning renders the same records as the standalone command — verify: gate test on the warning line.
- [x] 1.4 A path that is itself a key is described by its signature, never printed — verify: capture test asserting the key is absent from the rendering.
- [x] 1.5 The artefact refusal keeps its category-only shape, and the capability records it — verify: capture test on the refusal message.
- [x] 1.6 The path whose occurrences the self-match rule ignores has one spelling — verify: the standalone command, the gate and the scan default read one constant.

## 2. The scan does not trip on the declaration

- [x] 2.1 A private-marker hit whose only occurrence is the configuration that declares it is not reported — verify: capture test.
- [x] 2.2 The same marker elsewhere in the same content is still reported, naming that file — verify: capture test.

## 3. The reviewer's diagnostics

- [x] 3.1 A zero-exit reviewer command's error output is kept outside the journal and its path is named — verify: launcher test.
- [x] 3.2 A command that writes nothing to its error stream produces no such message — verify: launcher test.
- [x] 3.3 A failure to keep that output does not discard the recorded review — verify: launcher test with preservation refused.

## 4. The outbox

- [x] 4.1 The shipped outbox README says the outbox is not journal evidence and gives, as a runnable command, the pathspec that excludes it from journal staging — verify: read the string and a project test.
