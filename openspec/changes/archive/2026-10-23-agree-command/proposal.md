## Why

ADR-0018 decision 2 decided agreement with the contract can be recorded
— a declared actor states agreement with the contract at a stated hash,
any declared actor may record it, there are no roles — and CR-177 gave
the journal the `agreement` record that carries it. What does not exist
yet is the way a recorder writes one: agreement today is a record with
no command, so the evidence the record type exists for cannot be
produced except by hand.

## What Changes

- `agentmarshal agree --task <id>` writes one `agreement` record whose
  `contract` is the `contract_sha256` of the task's `contract.md` as it
  stands, prints the agreed hash and the recorder, and is registered
  from its own module the way `steps` is.
- `--contract <hash>` binds the agreement to the text the actor read:
  the command writes only when the value equals the contract's current
  hash; anything else — a different hash or a value that is not exactly
  64 lowercase hex — is refused, writing nothing.
- A task whose latest pin — the `contract` of its latest `opened` or
  `amendment` record carrying one — differs from the current hash is
  refused, naming both short hashes and that the edit should be recorded
  with `amend`; a task whose records carry no hash agrees at the current
  text.
- An unknown, completed or abandoned task is refused naming the reason,
  writing nothing; a recorder that cannot be resolved is refused before
  anything is created, while a recorder who is not a declared actor is
  accepted and the output says so.
- The requirement text that said nothing reads agreements yet is
  updated: `agree` writes the record now; the gate's
  `require_agreement` check and `status` showing agreement remain later
  tasks.

## Capabilities

- modified: `contract-governance`

## Impact

One new command and one new module; no other command's behaviour or
output changes. Agreement stays advisory — no gate reads it, no role
restricts who may record it, and nothing is added beyond the guarantees
the threat model publishes.
