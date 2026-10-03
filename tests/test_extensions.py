"""Tests for declared process-extension manifests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.extensions import (
    ExtensionManifest,
    ExtensionManifestError,
    ExtensionManifestMissing,
    parse_extension_manifest_text,
    read_extension_manifest,
)


def _write_manifest(
    repo: Path,
    *,
    footprint: str = '["openspec/"]',
    documents: str = '["openspec/specs/"]',
    artifacts: str = '["openspec/changes/archive/"]',
) -> Path:
    path = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1.2.3"\n'
        f"footprint = {footprint}\n"
        f"documents = {documents}\n"
        f"artifacts = {artifacts}\n"
        'install = "npx openspec init"\n'
        'remove = "rm -rf openspec"\n',
        encoding="utf-8",
    )
    return path


def test_read_extension_manifest_returns_every_declared_field(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    manifest = read_extension_manifest(tmp_path, "openspec")

    assert manifest.schema == 1
    assert manifest.name == "openspec"
    assert manifest.version == "1.2.3"
    assert manifest.footprint == ("openspec/",)
    assert manifest.documents == ("openspec/specs/",)
    assert manifest.artifacts == ("openspec/changes/archive/",)
    assert manifest.install == "npx openspec init"
    assert manifest.remove == "rm -rf openspec"


@pytest.mark.parametrize("field", ["footprint", "documents", "artifacts"])
@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        ("/absolute/", "starts with"),
        ("tree/*", "glob metacharacter"),
        ("tree/file?", "glob metacharacter"),
        ("tree/[ab]", "glob metacharacter"),
        ("tree/../elsewhere/", "'..' component"),
    ],
)
def test_manifest_path_fields_use_scope_syntax(
    tmp_path: Path, field: str, entry: str, reason: str
) -> None:
    values = {
        "footprint": '["tree/"]',
        "documents": "[]",
        "artifacts": "[]",
    }
    values[field] = f"[{entry!r}]"
    _write_manifest(tmp_path, **values)

    with pytest.raises(ExtensionManifestError, match=reason) as raised:
        read_extension_manifest(tmp_path, "openspec")

    assert field in str(raised.value)
    assert entry in str(raised.value)


@pytest.mark.parametrize("field", ["documents", "artifacts"])
def test_manifest_documents_and_artifacts_must_lie_under_footprint(
    tmp_path: Path, field: str
) -> None:
    values = {
        "footprint": '["openspec/exact.md", "openspec/tree/"]',
        "documents": "[]",
        "artifacts": "[]",
    }
    values[field] = '["elsewhere/file.md"]'
    _write_manifest(tmp_path, **values)

    with pytest.raises(ExtensionManifestError, match="not under") as raised:
        read_extension_manifest(tmp_path, "openspec")

    assert field in str(raised.value)
    assert "elsewhere/file.md" in str(raised.value)


def test_manifest_accepts_exact_and_directory_footprint_coverage(
    tmp_path: Path,
) -> None:
    _write_manifest(
        tmp_path,
        footprint='["openspec/exact.md", "openspec/tree/"]',
        documents='["openspec/exact.md", "openspec/tree/docs/"]',
        artifacts='["openspec/tree/archive/item.json"]',
    )

    manifest = read_extension_manifest(tmp_path, "openspec")

    assert manifest.documents == (
        "openspec/exact.md",
        "openspec/tree/docs/",
    )


def test_manifest_name_cannot_escape_the_extensions_directory(tmp_path: Path) -> None:
    with pytest.raises(ExtensionManifestError, match="extension name"):
        read_extension_manifest(tmp_path, "../outside")


def test_manifest_is_read_through_a_symlinked_project_root(tmp_path: Path) -> None:
    """A symlink above the project (a temp dir on some hosts) is not the hazard."""

    real = tmp_path / "real"
    real.mkdir()
    _write_manifest(real)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    assert read_extension_manifest(link, "openspec").name == "openspec"


def test_symlinked_manifest_file_is_refused(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    real = tmp_path / ".agentmarshal" / "extensions" / "openspec.toml"
    real.rename(tmp_path / "elsewhere.toml")
    real.symlink_to(tmp_path / "elsewhere.toml")

    with pytest.raises(ExtensionManifestError, match="symlink"):
        read_extension_manifest(tmp_path, "openspec")


def test_manifest_symlink_loop_is_refused_as_a_symlink(tmp_path: Path) -> None:
    """A loop at the manifest path is a link at the manifest path; refused as one."""

    path = tmp_path / ".agentmarshal" / "extensions" / "openspec.toml"
    path.parent.mkdir(parents=True)
    path.symlink_to(path)

    with pytest.raises(ExtensionManifestError, match="symlink"):
        read_extension_manifest(tmp_path, "openspec")


def test_symlink_loop_above_the_manifest_is_a_reader_error(tmp_path: Path) -> None:
    """A loop in an ancestor is not a link at the manifest path; strict resolution
    reports it the same way on every supported Python."""

    (tmp_path / ".agentmarshal").mkdir()
    loop = tmp_path / ".agentmarshal" / "extensions"
    loop.symlink_to(loop)

    with pytest.raises(ExtensionManifestError, match="cannot resolve"):
        read_extension_manifest(tmp_path, "openspec")


def test_missing_manifest_is_its_own_error(tmp_path: Path) -> None:
    with pytest.raises(ExtensionManifestMissing, match="missing"):
        read_extension_manifest(tmp_path, "openspec")


def test_dangling_symlink_at_the_manifest_path_is_refused_as_a_symlink(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".agentmarshal" / "extensions" / "openspec.toml"
    path.parent.mkdir(parents=True)
    path.symlink_to(tmp_path / "nowhere.toml")

    with pytest.raises(ExtensionManifestError, match="symlink"):
        read_extension_manifest(tmp_path, "openspec")


def _manifest_text(
    body: str = "", *, schema: int = 2, artifacts: str | None = "[]"
) -> str:
    return (
        f"schema = {schema}\n"
        'name = "openspec"\n'
        'version = "1.0.0"\n'
        'footprint = ["openspec/"]\n'
        'documents = ["openspec/specs/"]\n'
        + (f"artifacts = {artifacts}\n" if artifacts is not None else "")
        + body
    )


def _parse(
    body: str = "", *, schema: int = 2, artifacts: str | None = "[]"
) -> ExtensionManifest:
    return parse_extension_manifest_text(
        _manifest_text(body, schema=schema, artifacts=artifacts),
        "openspec",
        "the test manifest",
    )


_WRAPS_FIELDS = {
    "product": 'product = "openspec"',
    "version": 'version = "1.13.2"',
    "ecosystem": 'ecosystem = "npm"',
    "lock": 'lock = "lock/package-lock.json"',
    "runtime": 'runtime = "node >= 20"',
    "license": 'license = "MIT"',
}


def _wraps_body(missing: str | None = None, **overrides: str) -> str:
    lines = dict(_WRAPS_FIELDS)
    if missing is not None:
        del lines[missing]
    lines.update(overrides)
    return "[wraps]\n" + "\n".join(lines.values()) + "\n"


_ISOLATION_FIELDS = {
    "network": "network = false",
    "env": 'env = ["HOME", "OPEN_SPEC"]',
    "writes": 'writes = "none"',
    "timeout_seconds": "timeout_seconds = 120",
}


def _isolation_body(missing: str | None = None, **overrides: str) -> str:
    lines = dict(_ISOLATION_FIELDS)
    if missing is not None:
        del lines[missing]
    lines.update(overrides)
    return "[isolation]\n" + "\n".join(lines.values()) + "\n"


def test_schema_3_is_an_unknown_manifest_schema() -> None:
    """Scenario: schema 3 is an unknown manifest schema."""
    with pytest.raises(
        ExtensionManifestError, match="unknown or missing schema version"
    ) as raised:
        _parse(schema=3)
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "field", ["stage", "dependencies", "wraps", "records", "isolation"]
)
def test_schema_2_field_in_schema_1_manifest_requires_schema_2(
    field: str,
) -> None:
    """Scenario: a schema-2 field in a schema-1 manifest requires schema 2."""
    with pytest.raises(
        ExtensionManifestError, match=rf"field '{field}' requires schema 2"
    ) as raised:
        _parse(f"[{field}]\n", schema=1)
    assert "the test manifest" in str(raised.value)


def test_install_remove_and_artifacts_are_optional_in_schema_2() -> None:
    """Scenario: install, remove and artifacts are optional in schema 2."""
    manifest = _parse(artifacts=None)

    assert manifest.install is None
    assert manifest.remove is None
    assert manifest.artifacts == ()


@pytest.mark.parametrize("field", ["install", "remove", "artifacts"])
def test_schema_1_requires_install_remove_and_artifacts(field: str) -> None:
    """Scenario: schema 1 requires install, remove and artifacts."""
    lines = {
        "install": 'install = "npx openspec init"',
        "remove": 'remove = "rm -rf openspec"',
        "artifacts": "artifacts = []",
    }
    del lines[field]

    with pytest.raises(ExtensionManifestError, match=rf"'{field}'") as raised:
        parse_extension_manifest_text(
            _manifest_text("\n".join(lines.values()) + "\n", schema=1, artifacts=None),
            "openspec",
            "the test manifest",
        )
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize("field", ["install", "remove"])
def test_schema_2_free_text_carrying_control_characters_is_refused(
    field: str,
) -> None:
    """Scenario: a schema-2 free-text field carrying control characters is refused."""
    with pytest.raises(ExtensionManifestError, match="control characters") as raised:
        _parse(f'{field} = "do\\u001bevil"\n')
    assert f"'{field}'" in str(raised.value)
    assert "the test manifest" in str(raised.value)


def test_adr_0013s_manifest_example_parses() -> None:
    """ADR-0013's wrapper example declares none of install, remove or artifacts."""
    manifest = parse_extension_manifest_text(
        "schema = 2\n"
        'name = "openspec"\n'
        'version = "1.0.0"\n'
        'footprint = ["openspec/", "..."]\n'
        'documents = ["openspec/specs/"]\n'
        "[[stage]]\n"
        'phase = "pre-gate-stop"\n'
        'command = "bin/validate.py"\n'
        "[dependencies]\n"
        'lock = "lock/uv.lock"\n'
        "[wraps]\n"
        'product = "openspec"\n'
        'version = "1.13.2"\n'
        'ecosystem = "npm"\n'
        'lock = "lock/package-lock.json"\n'
        'runtime = "node >= 20"\n'
        'license = "MIT"\n'
        "[records]\n"
        'kinds = ["openspec/change-archived@1"]\n'
        "[isolation]\n"
        "network = false\n"
        "env = []\n"
        'writes = "none"\n'
        "timeout_seconds = 120\n",
        "openspec",
        "the test manifest",
    )

    assert manifest.install is None
    assert manifest.remove is None
    assert manifest.artifacts == ()
    assert manifest.stages[0].command == "bin/validate.py"
    assert manifest.wraps is not None
    assert manifest.wraps.runtime == "node >= 20"


def test_schema_1_manifest_parses_exactly_as_before(tmp_path: Path) -> None:
    """Scenario: a schema-1 manifest parses exactly as before."""
    _write_manifest(tmp_path)

    manifest = read_extension_manifest(tmp_path, "openspec")

    assert manifest.schema == 1
    assert manifest.install == "npx openspec init"
    assert manifest.remove == "rm -rf openspec"
    assert manifest.stages == ()
    assert manifest.dependencies is None
    assert manifest.wraps is None
    assert manifest.record_kinds == ()
    assert manifest.isolation is None


def test_stage_entry_parses_its_phase_and_command() -> None:
    """Scenario: a stage entry parses its phase and command."""
    manifest = _parse(
        "[[stage]]\n"
        'phase = "pre-gate-stop"\n'
        'command = "bin/validate.py"\n'
        "[[stage]]\n"
        'phase = "post-gate"\n'
        'command = "bin/notify.py"\n'
    )

    assert [(stage.phase, stage.command) for stage in manifest.stages] == [
        ("pre-gate-stop", "bin/validate.py"),
        ("post-gate", "bin/notify.py"),
    ]


@pytest.mark.parametrize("phase", ["pre-gate", "pre-merge", ""])
def test_phase_outside_the_three_modes_is_refused(phase: str) -> None:
    """Scenario: a phase outside the three modes is refused."""
    with pytest.raises(ExtensionManifestError, match="'phase'") as raised:
        _parse(f'[[stage]]\nphase = "{phase}"\ncommand = "bin/x.py"\n')
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "command",
    [
        "/abs/run.py",
        "bin/../run.py",
        "bin/",
        "run.py",
        "sbin/run.py",
    ],
)
def test_command_outside_the_extensions_bin_is_refused(command: str) -> None:
    """Scenario: a command outside the extension's bin/ is refused."""
    with pytest.raises(ExtensionManifestError, match="'command'") as raised:
        _parse(f'[[stage]]\nphase = "post-gate"\ncommand = "{command}"\n')
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "command",
    [
        "bin/my file.py",
        "bin/x.py --strict",
        "bin/x;y",
        "bin/x|y",
        "bin/x&y",
        "bin/x>y",
        "bin/x<y",
        "bin/$x",
        "bin/`x`",
        "bin/x(y)",
        "bin/{x}",
        "bin/~x",
        "bin/x'y",
        'bin/x\\"y',  # a quote, escaped in the TOML source
        "bin/x=y",
        "bin/x#y",
        "bin/x!y",
        "bin/\\ty",  # a tab, escaped in the TOML source
    ],
)
def test_command_carrying_whitespace_or_a_shell_metacharacter_is_refused(
    command: str,
) -> None:
    """Scenario: a command carrying whitespace or a shell metacharacter is refused."""
    with pytest.raises(ExtensionManifestError, match="'command'") as raised:
        _parse(f'[[stage]]\nphase = "post-gate"\ncommand = "{command}"\n')
    assert "the test manifest" in str(raised.value)


def test_malformed_stage_declaration_is_refused() -> None:
    """Scenario: a malformed stage declaration is refused."""
    with pytest.raises(ExtensionManifestError, match="'stage'") as raised:
        _parse('stage = "bin/x.py"\n')
    assert "the test manifest" in str(raised.value)
    with pytest.raises(ExtensionManifestError, match="'stage'"):
        _parse('stage = ["bin/x.py"]\n')
    with pytest.raises(ExtensionManifestError, match="'command'"):
        _parse('[[stage]]\nphase = "post-gate"\n')
    with pytest.raises(ExtensionManifestError, match="'phase'"):
        _parse('[[stage]]\ncommand = "bin/x.py"\n')


def test_dependencies_lock_under_lock_parses() -> None:
    """Scenario: a dependencies lock under lock/ parses."""
    manifest = _parse('[dependencies]\nlock = "lock/uv.lock"\n')

    assert manifest.dependencies is not None
    assert manifest.dependencies.lock == "lock/uv.lock"


@pytest.mark.parametrize(
    "lock",
    ["/lock/uv.lock", "lock/../uv.lock", "uv.lock", "deps/uv.lock", "lock/u v.lock"],
)
def test_dependencies_lock_outside_lock_is_refused(lock: str) -> None:
    """Scenario: a dependencies lock outside lock/ is refused."""
    with pytest.raises(ExtensionManifestError, match="'lock'") as raised:
        _parse(f'[dependencies]\nlock = "{lock}"\n')
    assert "the test manifest" in str(raised.value)


def test_wraps_section_parses_every_field() -> None:
    """Scenario: a wraps section parses every field."""
    manifest = _parse(_wraps_body())

    wraps = manifest.wraps
    assert wraps is not None
    assert wraps.product == "openspec"
    assert wraps.version == "1.13.2"
    assert wraps.ecosystem == "npm"
    assert wraps.lock == "lock/package-lock.json"
    assert wraps.runtime == "node >= 20"
    assert wraps.license == "MIT"


@pytest.mark.parametrize("missing", list(_WRAPS_FIELDS))
def test_missing_wraps_field_is_refused(missing: str) -> None:
    """Scenario: a missing wraps field is refused."""
    with pytest.raises(ExtensionManifestError, match=rf"'{missing}'") as raised:
        _parse(_wraps_body(missing=missing))
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    ("field", "line"),
    [
        ("product", 'product = "open\\u202espec"'),
        ("version", 'version = "1.13\\u000b2"'),
        ("ecosystem", 'ecosystem = "n\\u001bpm"'),
        ("license", 'license = "MIT\\u2028"'),
        ("runtime", 'runtime = "no\\u200ede >= 20"'),
        ("runtime", 'runtime = "node >= 2\\u202e0"'),
    ],
)
def test_wraps_field_carrying_control_characters_is_refused(
    field: str, line: str
) -> None:
    """Scenario: a wraps field carrying control characters is refused."""
    with pytest.raises(ExtensionManifestError, match="control characters") as raised:
        _parse(_wraps_body(**{field: line}))
    assert f"'{field}'" in str(raised.value)
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "runtime",
    ["node>=20", "node 20", ">= 20", "node >=", "node = 20", "node >= 20 x"],
)
def test_runtime_not_of_the_declared_form_is_refused(runtime: str) -> None:
    """Scenario: a runtime not of the declared form is refused."""
    with pytest.raises(ExtensionManifestError, match="'runtime'") as raised:
        _parse(_wraps_body(runtime=f'runtime = "{runtime}"'))
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "lock",
    ["/lock/package-lock.json", "lock/../x", "package-lock.json", "deps/x", "lock/x y"],
)
def test_product_lock_outside_lock_is_refused(lock: str) -> None:
    """Scenario: a product lock outside lock/ is refused."""
    with pytest.raises(ExtensionManifestError, match="'lock'") as raised:
        _parse(_wraps_body(lock=f'lock = "{lock}"'))
    assert "the test manifest" in str(raised.value)


def test_declared_record_kinds_parse() -> None:
    """Scenario: declared record kinds parse."""
    manifest = _parse('[records]\nkinds = ["openspec/change-archived@1"]\n')

    assert manifest.record_kinds == ("openspec/change-archived@1",)


def test_kind_naming_another_extension_is_refused() -> None:
    """Scenario: a kind naming another extension is refused."""
    with pytest.raises(ExtensionManifestError, match="'kinds'") as raised:
        _parse('[records]\nkinds = ["other/change-archived@1"]\n')
    assert "other/change-archived@1" in str(raised.value)
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "kind",
    [
        "openspec-change@1",
        "openspec/change",
        "openspec/@1",
        "openspec/change@",
        "/change@1",
        "openspec/change@1@2",
    ],
)
def test_malformed_kind_is_refused(kind: str) -> None:
    """Scenario: a malformed kind is refused."""
    with pytest.raises(ExtensionManifestError, match="'kinds'") as raised:
        _parse(f'[records]\nkinds = ["{kind}"]\n')
    assert "the test manifest" in str(raised.value)


@pytest.mark.parametrize(
    "kind",
    [
        "openspec/change-arch\\u202eived@1",
        "openspec/change-archived@\\u001b1",
    ],
)
def test_kind_carrying_a_control_character_is_refused(kind: str) -> None:
    """Scenario: a kind carrying a control character is refused."""
    with pytest.raises(ExtensionManifestError, match="control characters") as raised:
        _parse(f'[records]\nkinds = ["{kind}"]\n')
    assert "'kinds'" in str(raised.value)
    assert "the test manifest" in str(raised.value)


def test_isolation_section_parses() -> None:
    """Scenario: an isolation section parses."""
    manifest = _parse(
        _isolation_body(network="network = false", writes='writes = "process-log"')
    )

    isolation = manifest.isolation
    assert isolation is not None
    assert isolation.network is False
    assert isolation.env == ("HOME", "OPEN_SPEC")
    assert isolation.writes == "process-log"
    assert isolation.timeout_seconds == 120


@pytest.mark.parametrize(
    ("field", "line"),
    [
        ("network", 'network = "false"'),
        ("network", "network = 1"),
        ("env", 'env = ["1BAD"]'),
        ("env", 'env = ["HAS-DASH"]'),
        ("env", "env = [1]"),
        ("writes", 'writes = "anywhere"'),
        ("timeout_seconds", "timeout_seconds = 0"),
        ("timeout_seconds", "timeout_seconds = -5"),
        ("timeout_seconds", 'timeout_seconds = "120"'),
        ("timeout_seconds", "timeout_seconds = true"),
        ("network", None),
        ("env", None),
        ("writes", None),
        ("timeout_seconds", None),
    ],
)
def test_malformed_isolation_field_is_refused_naming_it(
    field: str, line: str | None
) -> None:
    """Scenario: a malformed isolation field is refused naming it."""
    body = (
        _isolation_body(missing=field)
        if line is None
        else _isolation_body(**{field: line})
    )
    with pytest.raises(ExtensionManifestError, match=rf"'{field}'") as raised:
        _parse(body)
    assert "the test manifest" in str(raised.value)


def test_parsed_manifest_carries_every_declared_section() -> None:
    """Scenario: the parsed manifest carries every declared section."""
    manifest = _parse(
        "[[stage]]\n"
        'phase = "pre-gate-stop"\n'
        'command = "bin/validate.py"\n'
        "[[stage]]\n"
        'phase = "pre-gate-warn"\n'
        'command = "bin/lint.py"\n'
        "[dependencies]\n"
        'lock = "lock/uv.lock"\n'
        + _wraps_body()
        + '[records]\nkinds = ["openspec/change-archived@1"]\n'
        + _isolation_body()
    )

    assert manifest.schema == 2
    assert [stage.phase for stage in manifest.stages] == [
        "pre-gate-stop",
        "pre-gate-warn",
    ]
    assert manifest.dependencies is not None
    assert manifest.wraps is not None
    assert manifest.record_kinds == ("openspec/change-archived@1",)
    assert manifest.isolation is not None


def test_absent_sections_expose_as_absent() -> None:
    """Scenario: absent sections expose as absent."""
    manifest = _parse()

    assert manifest.schema == 2
    assert manifest.stages == ()
    assert manifest.dependencies is None
    assert manifest.wraps is None
    assert manifest.record_kinds == ()
    assert manifest.isolation is None
