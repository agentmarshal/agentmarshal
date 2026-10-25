# Tasks

## 1. The linked-path refusal

- [x] 1.1 `_locate` checks `.agentmarshal` and `upstream` with
  `is_symlink()` (lstat) before any outbox I/O — the same refusal
  `extension_trust` applies to the managed extensions directory —
  printing the component through `_printable` with the command's
  markers, and `init`'s `_scaffold_outbox` refuses the same components
  before creating or writing — verify:
  `test_a_linked_outbox_refuses_a_command_before_it_writes`,
  `test_a_linked_agentmarshal_component_refuses_the_command`,
  `test_init_never_scaffolds_through_a_linked_outbox`,
  `test_a_sidecars_linked_outbox_never_writes_the_host`,
  `test_a_linked_components_path_is_masked_in_the_refusal`.

## 2. Only checked bytes are committed

- [x] 2.1 `_pinned_blob` compares `hash-object --stdin --path` with
  `--no-filters` of the same bytes; the comparison runs in `check` —
  the refusal point a batch wrapper consults — not only in `send`, a
  mismatch names the remedy its attributes imply (`_transform_cause`),
  and the manifest's update is pinned by the same rule — verify:
  `test_check_refuses_a_draft_a_clean_filter_would_transform`,
  `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off`,
  `test_an_autocrlf_refusal_names_the_same_remedy`,
  `test_send_refuses_a_draft_a_clean_filter_would_transform`,
  `test_send_refuses_when_a_filter_would_transform_the_sent_manifest`,
  `test_check_refuses_when_git_cannot_verify_a_files_staged_bytes`,
  `test_the_cannot_verify_reason_is_masked_and_display_escaped`,
  `test_a_transformation_with_no_known_cause_names_none`.

## 3. `status` escapes names

- [x] 3.1 `_run_status` prints every name through `_printable` — the
  masked, display-escaped renderer `check` and `send` use — verify:
  `test_a_control_character_in_a_file_name_is_escaped_in_the_report`.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv run agentmarshal validate; uv run pytest -q; uv run ruff check;
  uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
