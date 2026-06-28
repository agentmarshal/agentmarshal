#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

# Redaction секретов (ревью CR-001 F-008): сессии содержат tool input/output,
# куда могут попасть токены/креды/ключи. По умолчанию чистим перед записью.
_REDACT = [
    (re.compile(r"-----BEGIN[^-]+PRIVATE KEY-----.*?-----END[^-]+PRIVATE KEY-----", re.S),
     "[REDACTED-PRIVATE-KEY]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[REDACTED-JWT]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED-AWS-KEY]"),
    (re.compile(r"(?i)(authorization\s*:\s*)(bearer\s+)?[A-Za-z0-9._\-]{12,}"),
     r"\1\2[REDACTED]"),
    (re.compile(r"""(?i)\b(api[_-]?key|secret|token|password|passwd|pwd|access[_-]?key|client[_-]?secret|gitflic_api_token)\b(\s*[:=]\s*)(['"]?)[^\s'"]{6,}(\3)"""),
     r"\1\2\3[REDACTED]\4"),
]


def redact_text(s: str) -> str:
    for pat, repl in _REDACT:
        s = pat.sub(repl, s)
    return s


def parse_args():
    p = argparse.ArgumentParser(
        description="Convert Claude session JSONL to Markdown"
    )
    p.add_argument("input", help="Path to Claude session JSONL file")
    p.add_argument("-o", "--output", help="Path to output Markdown file")
    p.add_argument(
        "-c", "--clean",
        action="store_true",
        help="Remove empty and duplicate blocks from output",
    )
    p.add_argument(
        "--no-redact",
        action="store_true",
        help="Не вычищать секреты (по умолчанию redaction включён)",
    )
    return p.parse_args()


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip ANSI escape codes
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_xml_injection(text: str) -> bool:
    return bool(re.match(r"^\s*<(command-|local-command-|system-reminder)", text))


def format_tool_use(name: str, input_data: dict, description: str) -> str:
    lines = [f"**`{name}`**"]
    if description:
        lines.append(f"_{description}_")
    if input_data:
        input_str = json.dumps(input_data, ensure_ascii=False, indent=2)
        lines.append(f"\n```json\n{input_str}\n```")
    return "\n\n".join(lines)


def format_tool_result(name: str, content, is_error: bool) -> str:
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
            else:
                parts.append(json.dumps(c, ensure_ascii=False))
        text = "\n".join(parts)
    elif content is None:
        text = ""
    else:
        text = str(content)

    text = normalize(text)
    label = f"**Result: `{name}`**" if name else "**Result**"
    if is_error:
        label += " _(error)_"
    return f"{label}\n\n```\n{text}\n```"


def process_user_entry(obj: dict, tool_names: dict) -> list[tuple]:
    if obj.get("isMeta"):
        return []

    ts = obj.get("timestamp", "")
    content = obj.get("message", {}).get("content")

    if isinstance(content, str):
        text = normalize(content)
        if not text or is_xml_injection(text):
            return []
        return [("User", text, ts)]

    if isinstance(content, list):
        text_parts = []
        tool_results = []
        for c in content:
            if not isinstance(c, dict):
                continue
            ctype = c.get("type")
            if ctype == "tool_result":
                tool_id = c.get("tool_use_id", "")
                name = tool_names.get(tool_id, "")
                tool_results.append(
                    format_tool_result(name, c.get("content"), c.get("is_error", False))
                )
            elif ctype == "text":
                text_parts.append(c.get("text", ""))

        blocks = []
        if text_parts:
            text = normalize("\n\n".join(text_parts))
            if text and not is_xml_injection(text):
                blocks.append(("User", text, ts))
        if tool_results:
            blocks.append(("Tool_result", "\n\n".join(tool_results), ts))
        return blocks

    return []


def process_assistant_entry(obj: dict, tool_names: dict) -> list[tuple]:
    ts = obj.get("timestamp", "")
    content = obj.get("message", {}).get("content", [])
    if not isinstance(content, list):
        return []

    text_parts = []
    tool_calls = []
    for c in content:
        if not isinstance(c, dict):
            continue
        ctype = c.get("type")
        if ctype == "text":
            text = c.get("text", "").strip()
            if text:
                text_parts.append(text)
        elif ctype == "tool_use":
            tool_id = c.get("id", "")
            name = c.get("name", "")
            if tool_id:
                tool_names[tool_id] = name
            inp = c.get("input", {})
            desc = inp.get("description", "") if isinstance(inp, dict) else ""
            tool_calls.append(format_tool_use(name, inp, desc))
        # skip "thinking"

    parts = []
    if text_parts:
        parts.append(normalize("\n\n".join(text_parts)))
    parts.extend(tool_calls)

    body = "\n\n".join(p for p in parts if p)
    if not body:
        return []
    return [("Assistant", body, ts)]


def entry_to_blocks(obj: dict, tool_names: dict) -> list[tuple]:
    t = obj.get("type")
    if t == "user":
        return process_user_entry(obj, tool_names)
    if t == "assistant":
        return process_assistant_entry(obj, tool_names)
    return []


def block_to_md(header: str, body: str, ts: str) -> str:
    parts = [f"## {header}"]
    if ts:
        parts += ["", f"Time: {ts}"]
    parts += ["", body]
    return "\n".join(parts)


def get_body(md_block: str) -> str:
    lines = md_block.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Time: "):
            return "\n".join(lines[i + 1:]).strip()
    return "\n".join(lines[1:]).strip()


def clean_blocks(blocks: list) -> list:
    seen: set = set()
    result = []
    for block in blocks:
        body = get_body(block)
        if not body:
            continue
        if body in seen:
            continue
        seen.add(body)
        result.append(block)
    return result


def main():
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output) if args.output else in_path.with_suffix(".md")

    items = []
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    ai_title = ""
    session_id = ""
    for obj in items:
        if obj.get("type") == "ai-title" and obj.get("aiTitle"):
            ai_title = obj["aiTitle"]
        if not session_id and obj.get("sessionId"):
            session_id = obj["sessionId"]

    tool_names: dict = {}
    md_blocks = []
    for obj in items:
        for header, body, ts in entry_to_blocks(obj, tool_names):
            md_blocks.append(block_to_md(header, body, ts))

    if args.clean:
        md_blocks = clean_blocks(md_blocks)

    heading = ai_title if ai_title else in_path.stem
    meta_line = f"_File: {in_path.name}_"
    if session_id and session_id not in in_path.name:
        meta_line += f" | _Session: {session_id}_"

    md = [f"# {heading}", "", meta_line, ""]
    for block in md_blocks:
        md.append(block)
        md.append("")
        md.append("---")
        md.append("")

    text = "\n".join(md).rstrip() + "\n"
    if not args.no_redact:
        text = redact_text(text)
    out_path.write_text(text, encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
