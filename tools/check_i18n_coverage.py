#!/usr/bin/env python3
"""Check i18n coverage: detect likely-untranslated entries in zh-CN resources.

Self-check mode: scans Chinese values for ASCII words that suggest untranslated content.
Excludes known brand names, format strings, URLs, and technical terms.
"""
from __future__ import annotations

import json
import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"

TARGETS = [
    {"name": "desktop",  "zh": RESOURCES / "desktop-zh-CN.json"},
    {"name": "frontend", "zh": RESOURCES / "frontend-zh-CN.json"},
    {"name": "dynamic",  "zh": RESOURCES / "dynamic-zh-CN.json"},
    {"name": "statsig",  "zh": RESOURCES / "statsig-zh-CN.json"},
]


ASCII_WORD_RE = re.compile(r"[A-Za-z]{4,}")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


KNOWN_OK_PATTERNS = [
    re.compile(r"^(USB|AWS|API|SDK|JSON|UTF-8|CI|CLI|MCP|SSH|URL|ID|Caps Lock)$"),
    re.compile(r"^\{.*\}$"),
    re.compile(r"^[\d{}%./: +\-−_,=，。()\[\]<>|]+$"),
    re.compile(r"^(?:\{[^{}]+\}|<[^>]+>|</[^>]+>|[\s/:,().+%$#·=—\-_'\"[\]（）]|[A-Za-z]{1,3})+$"),
    re.compile(r"^(?:\{[^{}]+\}|[\d\s=，。＋+\-−×/%:·])+$"),
    re.compile(r"^(Anthropic|Bedrock|Vertex|Foundry|Azure AI|Google Vertex AI|AWS Bedrock)$"),
    re.compile(r"^(Claude|Claude\.ai|Claude\.ai data import|Claude API|Claude Code|Claude Code Desktop|Claude Code CLI|Claude Enterprise|Claude GitHub App|Claude for Excel|Claude for Outlook)$"),
    re.compile(r"^(Python|Node\.js|Webhook|GitHub|GitHub App|GitHub Enterprise|Gmail|JetBrains|Excel|Artifacts|Instagram|YouTube|YouTuber|status\.claude\.com)$"),
    re.compile(r"^(Amazon Bedrock|Anthropic API|Anthropic Sans|Claude — zsh|Claude Opus 4|website\.com|Microsoft 365|X-Header-Name|OAuth|OAuth 2\.0 JWT bearer|OpenTelemetry|SCIM)$"),
    re.compile(r"^(Windows（x64）|Windows（arm64）|Windows \(x64\)|Windows \(arm64\)|Linux \(x64\)|Linux（x64）|Linux（arm64）|macOS)$"),
    re.compile(r"^(Latin-1 \(ISO-8859-1\)|Ctrl⏎|Ctrl\+⏎)$"),
    re.compile(r"^https?://\S+$"),
    re.compile(r"^[a-z][a-z0-9+.-]*://\S+$"),
    re.compile(r"^api://\S+\s+offline_access$"),
    re.compile(r"^(?:~|/|\.|\*\.|//)[^\s]+$"),
    re.compile(r"^[\w.-]+\.(?:com|app|json|zip|pdf|csv|md|txt|yaml|yml)$"),
    re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+$"),  # email addresses only
    re.compile(r"^'.+'@[A-Za-z0-9.-]+$"),
    re.compile(r"^[A-Z0-9_./:+\- ]{2,}$"),
    re.compile(r"^(?:p50|p95|p99|4xx|5xx|FPS: \?\?\?|GOCSPX-\.\.\.|MANAGED LOCAL|NNN\.apps\.googleusercontent\.com)$"),
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


def build_report() -> tuple[str, int]:
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
    return report, total_issues


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Check likely untranslated zh-CN resource entries")
    parser.add_argument("--check", action="store_true", help="Print the report without writing I18N-COVERAGE-REPORT.md")
    parser.add_argument("--fail-on-issues", action="store_true", help="Exit with code 1 when suspicious entries are found")
    args = parser.parse_args()

    report, total_issues = build_report()
    out = ROOT / "I18N-COVERAGE-REPORT.md"
    if args.check:
        print(report)
    else:
        out.write_text(report, encoding="utf-8")
        print(f"Wrote: {out}")

    print(f"Total suspect entries: {total_issues}")
    if args.fail_on_issues and total_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
