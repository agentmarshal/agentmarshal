## 1. The scan says where and what

- [x] 1.1 A hit names the file and the signature, and never the matched text — verify: capture test on a built-in signature.
- [x] 1.2 A private-marker hit names the file and the marker's position, never its value — verify: capture test asserting the marker string is absent from the rendering.
- [x] 1.3 The gate's added-content warning renders the same records as the standalone command — verify: gate test on the warning line.

## 2. The scan does not trip on the declaration

- [x] 2.1 A private-marker hit whose only occurrence is the configuration that declares it is not reported — verify: capture test.
- [x] 2.2 The same marker elsewhere in the same content is still reported, naming that file — verify: capture test.

## 3. The reviewer's diagnostics

- [x] 3.1 A zero-exit reviewer command's error output is kept outside the journal and its path is named — verify: launcher test.
- [x] 3.2 A command that writes nothing to its error stream produces no such message — verify: launcher test.

## 4. The outbox

- [x] 4.1 The shipped outbox README says the outbox is not journal evidence and gives the pathspec that excludes it from journal staging — verify: read the string and a project test.
