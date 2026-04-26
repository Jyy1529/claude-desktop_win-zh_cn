#!/usr/bin/env python3
"""Check i18n coverage: detect likely-untranslated entries in zh-CN resources.

Self-check mode: scans Chinese values for ASCII words that suggest untranslated content.
Excludes known brand names, format strings, URLs, and technical terms.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"

TARGETS = [
    {"name": "desktop",  "zh": RESOURCES / "desktop-zh-CN.json"},
    {"name": "frontend", "zh": RESOURCES / "frontend-zh-CN.json"},
    {"name": "statsig",  "zh": RESOURCES / "statsig-zh-CN.json"},
]


ASCII_WORD_RE = re.compile(r"[A-Za-z]{4,}")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


KNOWN_OK_PATTERNS = [
    re.compile(r"^(USB|AWS|API|SDK|JSON|UTF-8|CI|CLI|MCP|SSH|URL|ID|Caps Lock)$"),
    re.compile(r"^\{.*\}$"),
    re.compile(r"^[\d{}%./: +\-_,()\[\]<>|]+$"),
    re.compile(r"^(Anthropic|Bedrock|Vertex|Foundry|Azure AI|Google Vertex AI|AWS Bedrock)$"),
    re.compile(r"^(Claude|Claude\.ai|Claude API|Claude Code|Claude Code CLI|Claude Enterprise|Claude for Excel)$"),
    re.compile(r"^(Python|Node\.js|Webhook|GitHub|Gmail|JetBrains|Excel|Artifacts|status\.claude\.com)$"),
    re.compile(r"^(Amazon Bedrock|Claude — zsh|website\.com)$"),
    re.compile(r"^(Windows \(x64\)|Windows \(arm64\)|Linux \(x64\)|Linux（arm64）|macOS)$"),
    re.compile(r"^(Latin-1 \(ISO-8859-1\)|Ctrl⏎)$"),
    re.compile(r"^https?://\S+$"),
    re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+$"),  # email addresses only
    re.compile(r"^PR #\{.*\}$"),
    re.compile(r"^CI \{.*\}$"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_known_ok(value: str) -> bool:
    return any(p.search(value) for p in KNOWN_OK_PATTERNS)


def classify_value(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    if CJK_RE.search(value):
        return None
    if is_known_ok(value):
        return None
    if ASCII_WORD_RE.search(value):
        return "likely_untranslated"
    return None


def main() -> int:
    report_lines: list[str] = []
    total_issues = 0

    for target in TARGETS:
        zh_path = target["zh"]
        if not zh_path.exists():
            report_lines.append(f"## {target['name']}")
            report_lines.append("MISSING: file not found")
            report_lines.append("")
            continue

        data = load_json(zh_path)
        issues = []
        for key, value in data.items():
            kind = classify_value(value)
            if kind:
                issues.append((key, value))

        report_lines.append(f"## {target['name']}")
        report_lines.append(f"suspect_count: {len(issues)}")
        for key, value in issues:
            report_lines.append(f"- {key}: {value}")
        report_lines.append("")
        total_issues += len(issues)

    report = "\n".join(report_lines)
    out = ROOT / "I18N-COVERAGE-REPORT.md"
    out.write_text(report, encoding="utf-8")

    print(f"Wrote: {out}")
    print(f"Total suspect entries: {total_issues}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
