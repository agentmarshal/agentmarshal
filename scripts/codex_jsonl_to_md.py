#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

# Redaction секретов (ревью CR-001 F-008): по умолчанию чистим перед записью.
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
        description="Convert Codex JSONL history to Markdown"
    )
    p.add_argument("input", help="Path to Codex JSONL file")
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


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fence_for_code(code: str) -> str:
    fences = re.findall(r"`+", code)
    if not fences:
        return "```"
    max_run = max(len(x) for x in fences)
    return "`" * (max_run + 1)


def format_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return normalize_text(content)
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                t = item.get("type")
                if t in {"text", "output_text", "input_text"}:
                    parts.append(item.get("text", ""))
                elif t in {"code", "code_block"}:
                    code = item.get("text") or item.get("code") or ""
                    lang = item.get("language", "")
                    fence = fence_for_code(code)
                    parts.append(f"{fence}{lang}\n{code}\n{fence}")
                else:
                    txt = item.get("text")
                    if txt:
                        parts.append(txt)
        return normalize_text("\n\n".join(p for p in parts if p.strip()))
    if isinstance(content, dict):
        if "text" in content:
            return normalize_text(content["text"])
        if "code" in content:
            code = content.get("code", "")
            lang = content.get("language", "")
            fence = fence_for_code(code)
            return f"{fence}{lang}\n{code}\n{fence}"
    return normalize_text(str(content))


def detect_role(obj: dict) -> str:
    for key in ("role", "author", "speaker", "type"):
        v = obj.get(key)
        if isinstance(v, str) and v:
            return v
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("role", "author", "speaker", "type"):
            v = payload.get(key)
            if isinstance(v, str) and v:
                return v
    return "unknown"


def detect_text(obj: dict) -> str:
    for key in ("content", "text", "message", "body", "prompt", "response"):
        v = obj.get(key)
        if isinstance(v, (str, list, dict)):
            return format_content(v)
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("content", "text", "message", "body", "prompt", "response"):
            v = payload.get(key)
            if isinstance(v, (str, list, dict)):
                return format_content(v)
    return ""


def detect_timestamp(obj: dict) -> str:
    for key in ("timestamp", "time", "created_at", "created", "ts"):
        v = obj.get(key)
        if v:
            return str(v)
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("timestamp", "time", "created_at", "created", "ts"):
            v = payload.get(key)
            if v:
                return str(v)
    return ""


def detect_id(obj: dict) -> str:
    for key in ("id", "message_id", "uuid", "request_id"):
        v = obj.get(key)
        if v:
            return str(v)
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("id", "message_id", "uuid", "request_id"):
            v = payload.get(key)
            if v:
                return str(v)
    return ""


def load_jsonl(path: Path):
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                items.append({
                    "_parse_error": True,
                    "_line_no": line_no,
                    "_raw": line,
                })
    return items


def message_to_md(obj: dict) -> str:
    role = detect_role(obj)
    text = detect_text(obj)
    ts = detect_timestamp(obj)
    msg_id = detect_id(obj)

    header = f"## {role.capitalize()}"
    meta = []
    if ts:
        meta.append(f"Time: {ts}")
    if msg_id:
        meta.append(f"ID: {msg_id}")

    parts = [header]
    if meta:
        parts.append("")
        parts.append(" | ".join(meta))
    if text:
        parts.append("")
        parts.append(text)
    else:
        parts.append("")
        parts.append("_(empty message)_")
    return "\n".join(parts).strip()


def get_body(block: str) -> str:
    lines = block.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Time: "):
            return "\n".join(lines[i + 1:]).strip()
    return "\n".join(lines[1:]).strip()


def clean_blocks(blocks: list) -> list:
    seen: set = set()
    result = []
    for block in blocks:
        body = get_body(block)
        if body in ("_(empty message)_", ""):
            continue
        if body in seen:
            continue
        seen.add(body)
        result.append(block)
    return result


def sort_key(obj, idx):
    for key in ("seq", "index", "position", "order"):
        v = obj.get(key)
        if isinstance(v, int):
            return (0, v, idx)
    ts = detect_timestamp(obj)
    return (1, ts, idx)


def main():
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output) if args.output else in_path.with_suffix(".md")

    items = load_jsonl(in_path)
    items = [x for x in items if not x.get("_parse_error")]
    indexed_items = list(enumerate(items))
    indexed_items = sorted(indexed_items, key=lambda t: sort_key(t[1], t[0]))
    items = [obj for obj in indexed_items]

    blocks = [message_to_md(obj) for _, obj in items]
    if args.clean:
        blocks = clean_blocks(blocks)

    md = [f"# {in_path.name}", ""]
    for block in blocks:
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
