## MODIFIED Requirements

### Requirement: The reviewer command's contract is documented where it is configured
The documentation that describes `AGENTMARSHAL_REVIEWER_CMD` SHALL state that
the command runs with its working directory set to a metadata-free snapshot of
the reviewed commit, or — when the review binds to a finding — to a snapshot of
that finding's verified artifacts; that a relative path in the command resolves
inside that snapshot rather than against the operator's checkout; and what the
prompt-file placeholder contains. It SHALL state which subject the verdict must
name for each binding. It SHALL also state that the snapshot bounds where the
command starts and not what the process may read, and that confining the latter
belongs to the adapter.

#### Scenario: an operator learns the contract without reading the launcher
- **WHEN** an operator configures a reviewer command from the documentation
- **THEN** the documentation states the working directory, the resolution of
  relative paths, the prompt-file placeholder, and the adapter's responsibility
  for what the command may read

#### Scenario: the documented contract covers both bindings
- **WHEN** an operator reads that documentation to configure one command for
  both kinds of review
- **THEN** it states what the command is handed for a commit review and for a
  finding review, and which subject each verdict must name
