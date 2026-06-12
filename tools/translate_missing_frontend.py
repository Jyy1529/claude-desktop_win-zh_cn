#!/usr/bin/env python3
"""Best-effort zh-CN translation filler for Claude frontend i18n resources.

This maintenance helper reads the official en-US frontend i18n file from an
installed Claude build, translates missing zh-CN keys through Google Translate's
public endpoint, and writes resources/frontend-zh-CN.json with official keys
first and stale local keys kept at the end.

It preserves ICU placeholders, React-style tags, code spans, paths, URLs, and a
small glossary of product/technical terms that should stay in English.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZH = ROOT / "resources" / "frontend-zh-CN.json"

TOKEN_RE = re.compile(r"⟦\d{3}⟧")
OLD_TOKEN_RE = re.compile(r"⟦PH\d{3}⟧")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{3,}")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

GLOSSARY = [
    "Claude Code Desktop",
    "Claude Code CLI",
    "Claude Code",
    "Claude Desktop",
    "Claude Enterprise",
    "Claude Console",
    "Claude Security",
    "Claude for Outlook",
    "Claude for Excel",
    "Claude.ai",
    "Claude",
    "Anthropic Console",
    "Anthropic",
    "GitHub Enterprise Server",
    "GitHub Enterprise",
    "GitHub App",
    "GitHub",
    "GitLab",
    "Google Workspace",
    "Google Drive",
    "Google Play",
    "Google Vertex AI",
    "Google",
    "Microsoft Entra",
    "Microsoft 365",
    "Microsoft",
    "Amazon Bedrock",
    "AWS Bedrock",
    "AWS Marketplace",
    "AWS",
    "Azure AI",
    "Azure",
    "Vertex AI",
    "Vertex",
    "Bedrock",
    "Linear",
    "Jira",
    "Slack",
    "Gmail",
    "NetSuite",
    "Stripe",
    "Brex",
    "Salesforce",
    "HubSpot",
    "Notion",
    "Asana",
    "Figma",
    "Zapier",
    "Atlassian",
    "Instagram",
    "Chrome",
    "Safari",
    "Office",
    "Outlook",
    "Excel",
    "Conway",
    "Launch",
    "Canvas",
    "Cowork",
    "Artifacts",
    "Artifact",
    "Research Labs Premium",
    "Research Labs",
    "API",
    "SDK",
    "CLI",
    "CI",
    "SSH",
    "JSON",
    "URL",
    "URI",
    "ID",
    "UUID",
    "OAuth",
    "JWT",
    "OIDC",
    "SAML",
    "SCIM",
    "SSO",
    "OTLP",
    "OpenTelemetry",
    "CIMD",
    "HIPAA",
    "BAA",
    "ZDR",
    "PHI",
    "MDM",
    "MFA",
    "2FA",
    "BYOK",
    "DAU",
    "WAU",
    "CPA",
    "CRM",
    "CSV",
    "PDF",
    "ZIP",
    "PNG",
    "JPEG",
    "GIF",
    "WebP",
    "HTML",
    "XML",
    "YAML",
    "SQL",
    "GraphQL",
    "REST",
    "HTTP",
    "HTTPS",
    "VPN",
    "PR",
    "PRs",
    "MCPs",
    "MCP",
    "Mac",
    "macOS",
    "Windows",
    "Linux",
    "iOS",
    "Android",
    "Python",
    "Node.js",
    "JavaScript",
    "TypeScript",
    "React",
    "npm",
    "zsh",
    "bash",
    "PowerShell",
    "Shell",
    "VS Code",
    "Cursor",
    "Windsurf",
    "Opus",
    "Sonnet",
    "Haiku",
    "Pro",
    "Max",
    "Team",
    "Enterprise",
    "IdP",
    "CORS",
    "CSP",
    "X-Header-Name",
    "Webhooks",
    "Webhook",
    "GOCSPX",
    "Acme Platform",
]

KEEP_EXACT_VALUES = {
    "Claude",
    "Claude.ai data import",
    "Claude for Outlook",
    "Anthropic API",
    "OAuth 2.0 JWT bearer",
    "X-Header-Name",
    "CLI",
    "API",
    "MCP",
    "JSON",
    "URL",
    "GitHub App",
    "Microsoft 365",
    "Google Play",
    "Instagram",
    "Python",
    "Node.js",
    "5000000",
    "GOCSPX-...",
    "~/Documents/work",
    "/usr/local/bin/corp-cred-helper",
    "openid email https://www.googleapis.com/auth/cloud-platform",
    "api://…/access_as_user offline_access",
}

FORCE_TRANSLATIONS = {
    "Auto": "自动",
    "Early": "早期",
    "Server": "服务器",
    "shells": "shell",
    "At limit": "已达上限",
    "Monthly limit": "每月限额",
    "Weekly limit": "每周限额",
    "Session was interrupted": "会话已中断",
    "Filter by owner": "按所有者筛选",
    "Allowed hosts": "允许的主机",
    "Not synced yet": "尚未同步",
    "Drawing tool": "绘图工具",
    "Sports coach": "体育教练",
    "Photographer": "摄影师",
    "Digital marketer": "数字营销人员",
    "Private equity associate": "私募股权助理",
    "Program and project management": "项目群和项目管理",
    "Draft something for me": "帮我起草内容",
    "Try the basics": "试试基础功能",
    "Answer questions": "回答问题",
    "Summarize a paper": "总结论文",
    "Draft an SOP": "起草 SOP",
    "Artifact view": "Artifact 视图",
    "Project conversation view": "项目对话视图",
    "Usage credit balance": "使用积分余额",
    "Manage usage settings": "管理用量设置",
    "Connected browsers": "已连接的浏览器",
    "Tenant ID": "租户 ID",
    "Coach": "教练",
}

KEEP_WHOLE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^[\d\s{}%./:+\-_,()\[\]<>|~#…]+$"),
    re.compile(r"^\{[A-Za-z0-9_.$/+-]+\}(?:\s*[/·]\s*\{[A-Za-z0-9_.$/+-]+\})*$"),
    re.compile(r"^\{[^{}]+,\s*number(?:,\s*[^{}]+)?\}$"),
    re.compile(r"^https?://\S+$"),
    re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://\S+$"),
    re.compile(r"^[\w.+-]+@[\w.-]+$"),
    re.compile(r"^(?:~|/)[\w./~+\-]+$"),
    re.compile(r"^[A-Za-z]:\\"),
    re.compile(r"^[\w.-]+\.(?:json|zip|pdf|csv|ts|tsx|js|jsx|py|md|yml|yaml|toml|xml|html|css)$", re.I),
    re.compile(r"^[A-Z0-9_./:+\- ]{2,}$"),
]

PROTECT_PATTERNS = [
    re.compile(r"`[^`]*`"),
    re.compile(r"<[^>]+>"),
    re.compile(r"https?://[^\s<>()]+"),
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s<>()]+"),
    re.compile(r"[\w.+-]+@[\w.-]+"),
    re.compile(r"(?<!\w)(?:~|/)[\w./~+\-]*"),
    re.compile(r"\b[\w.-]+\.(?:json|zip|pdf|csv|ts|tsx|js|jsx|py|md|yml|yaml|toml|xml|html|css|com)\b", re.I),
    re.compile(r"--[A-Za-z0-9][A-Za-z0-9-]*"),
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b"),
    re.compile(r"#"),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def should_keep_whole(value: str) -> bool:
    stripped = value.strip()
    if stripped in KEEP_EXACT_VALUES:
        return True
    if stripped in GLOSSARY:
        return True
    return any(pattern.fullmatch(stripped) for pattern in KEEP_WHOLE_PATTERNS)


def find_matching_brace(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def split_top_level_commas(text: str, maxsplit: int = 2) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
            if len(parts) == maxsplit:
                break
    parts.append(text[start:].strip())
    return parts


@dataclass
class ICUOption:
    selector: str
    message: "MessageNode"


@dataclass
class ICUNode:
    variable: str
    kind: str
    prefix: str
    options: list[ICUOption]

    def collect(self, collector: set[str]) -> None:
        for option in self.options:
            option.message.collect(collector)

    def render(self, translations: dict[str, str]) -> str:
        pieces = [f"{{{self.variable}, {self.kind},"]
        if self.prefix:
            pieces.append(f" {self.prefix.strip()}")
        for option in self.options:
            pieces.append(f" {option.selector} {{{option.message.render(translations)}}}")
        pieces.append("}")
        return "".join(pieces)


@dataclass
class MessageNode:
    masked: str
    replacements: list[tuple[str, str | ICUNode]]
    force: str | None = None

    def collect(self, collector: set[str]) -> None:
        if self.force is None and should_translate_masked(self.masked):
            collector.add(self.masked)
        for _, replacement in self.replacements:
            if isinstance(replacement, ICUNode):
                replacement.collect(collector)

    def render(self, translations: dict[str, str]) -> str:
        if self.force is not None:
            return self.force
        rendered = translations.get(self.masked, self.masked)
        for token, replacement in self.replacements:
            value = replacement.render(translations) if isinstance(replacement, ICUNode) else replacement
            rendered = rendered.replace(token, value)
        return cleanup(rendered)


class Masker:
    def __init__(self) -> None:
        self.replacements: list[tuple[str, str | ICUNode]] = []

    def add(self, value: str | ICUNode) -> str:
        token = f"⟦{len(self.replacements):03d}⟧"
        self.replacements.append((token, value))
        return token


def parse_icu(expr: str) -> ICUNode | None:
    if not (expr.startswith("{") and expr.endswith("}")):
        return None
    parts = split_top_level_commas(expr[1:-1], maxsplit=2)
    if len(parts) != 3:
        return None
    variable, kind, rest = parts
    if kind not in {"plural", "select", "selectordinal"}:
        return None

    index = 0
    prefix = ""
    options: list[ICUOption] = []
    while index < len(rest):
        while index < len(rest) and rest[index].isspace():
            index += 1
        if index >= len(rest):
            break
        if rest.startswith("offset:", index):
            start = index
            while index < len(rest) and not rest[index].isspace():
                index += 1
            prefix = rest[start:index]
            continue
        selector_start = index
        while index < len(rest) and not rest[index].isspace() and rest[index] != "{":
            index += 1
        selector = rest[selector_start:index].strip()
        while index < len(rest) and rest[index].isspace():
            index += 1
        if not selector or index >= len(rest) or rest[index] != "{":
            return None
        end = find_matching_brace(rest, index)
        if end < 0:
            return None
        message = rest[index + 1:end]
        options.append(ICUOption(selector=selector, message=build_node(message)))
        index = end + 1

    if not options:
        return None
    return ICUNode(variable=variable, kind=kind, prefix=prefix, options=options)


def protect_glossary(text: str, masker: Masker) -> str:
    for term in sorted(GLOSSARY, key=len, reverse=True):
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])")
        text = pattern.sub(lambda match: masker.add(match.group(0)), text)
    return text


def protect_patterns(text: str, masker: Masker) -> str:
    for pattern in PROTECT_PATTERNS:
        text = pattern.sub(lambda match: masker.add(match.group(0)), text)
    return text


def build_node(value: str) -> MessageNode:
    if value in FORCE_TRANSLATIONS:
        return MessageNode(masked=value, replacements=[], force=FORCE_TRANSLATIONS[value])
    if should_keep_whole(value):
        return MessageNode(masked=value, replacements=[], force=value)

    masker = Masker()
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "{":
            end = find_matching_brace(value, index)
            if end >= 0:
                expr = value[index:end + 1]
                icu = parse_icu(expr)
                output.append(masker.add(icu if icu else expr))
                index = end + 1
                continue
        output.append(value[index])
        index += 1

    masked = "".join(output)
    masked = protect_patterns(masked, masker)
    masked = protect_glossary(masked, masker)
    return MessageNode(masked=masked, replacements=masker.replacements)


def should_translate_masked(masked: str) -> bool:
    without_tokens = TOKEN_RE.sub("", masked)
    if not ASCII_WORD_RE.search(without_tokens):
        return False
    if should_keep_whole(without_tokens.strip()):
        return False
    return True


def cleanup(text: str) -> str:
    text = text.replace("您", "你")
    text = re.sub(r"\s+([，。！？；：、）】》])", r"\1", text)
    text = re.sub(r"([（【《])\s+", r"\1", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([.,!?;:])", r"\1\2", text)
    text = text.replace("％", "%")
    return text.strip()


def google_translate_batch(texts: list[str], *, sleep: float = 0.2) -> dict[str, str]:
    session = requests.Session()
    results: dict[str, str] = {}
    unique = list(dict.fromkeys(texts))
    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    delimiter = "\n<<<I18N_DELIM_8F4C2D>>>\n"
    max_chars = 3500

    for text in unique:
        projected = current_len + len(text) + len(delimiter)
        if current and projected > max_chars:
            batches.append(current)
            current = []
            current_len = 0
        current.append(text)
        current_len += len(text) + len(delimiter)
    if current:
        batches.append(current)

    def translate_joined(batch: list[str]) -> list[str]:
        joined = delimiter.join(batch)
        params = {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": joined}
        for attempt in range(5):
            try:
                response = session.get(
                    "https://translate.googleapis.com/translate_a/single",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                translated = "".join(part[0] for part in data[0] if part and part[0])
                parts = translated.split(delimiter)
                if len(parts) == len(batch):
                    return [cleanup(part) for part in parts]
                if len(batch) == 1:
                    return [cleanup(translated)]
            except Exception as exc:  # noqa: BLE001 - retry public endpoint failures.
                if attempt == 4:
                    raise RuntimeError(f"Google Translate request failed: {exc}") from exc
            time.sleep((attempt + 1) * 1.5)
        if len(batch) > 1:
            translated_parts: list[str] = []
            for item in batch:
                translated_parts.extend(translate_joined([item]))
                time.sleep(sleep)
            return translated_parts
        raise RuntimeError("Google Translate delimiter split failed")

    total = len(batches)
    for batch_index, batch in enumerate(batches, start=1):
        translated_batch = translate_joined(batch)
        for source, translated in zip(batch, translated_batch, strict=True):
            results[source] = translated
        print(f"translated batch {batch_index}/{total} ({len(batch)} strings)")
        time.sleep(sleep)

    return results


def values_needing_translation(en_data: dict, zh_data: dict, *, only_missing: bool) -> dict[str, str]:
    needs: dict[str, str] = {}
    for key, english in en_data.items():
        if not isinstance(english, str):
            continue
        if key not in zh_data:
            if english in FORCE_TRANSLATIONS or not should_keep_whole(english):
                needs[key] = english
            continue
        current = zh_data[key]
        if (
            not only_missing
            and isinstance(current, str)
            and (current == english or OLD_TOKEN_RE.search(current))
            and (english in FORCE_TRANSLATIONS or not should_keep_whole(english))
        ):
            needs[key] = english
    return needs


def render_translations(values: Iterable[str]) -> dict[str, str]:
    nodes = {value: build_node(value) for value in values}
    masked_to_translate: set[str] = set()
    for node in nodes.values():
        node.collect(masked_to_translate)
    print(f"unique source values: {len(nodes)}")
    print(f"unique masked strings sent to translator: {len(masked_to_translate)}")
    translations = google_translate_batch(sorted(masked_to_translate)) if masked_to_translate else {}
    return {source: node.render(translations) for source, node in nodes.items()}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Fill missing frontend zh-CN translations from an installed en-US file")
    parser.add_argument("--en", type=Path, required=True, help="Official frontend en-US.json")
    parser.add_argument("--zh", type=Path, default=DEFAULT_ZH, help="Local resources/frontend-zh-CN.json")
    parser.add_argument("--only-missing", action="store_true", help="Only translate keys absent from zh-CN")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without writing")
    args = parser.parse_args()

    en_data = load_json(args.en)
    zh_data = load_json(args.zh)
    needs = values_needing_translation(en_data, zh_data, only_missing=args.only_missing)

    kept_missing = [key for key in en_data if key not in zh_data and key not in needs]
    print(f"official keys: {len(en_data)}")
    print(f"local keys before: {len(zh_data)}")
    print(f"missing technical/protected kept as-is: {len(kept_missing)}")
    print(f"keys needing translation: {len(needs)}")
    if args.dry_run:
        for key, value in list(needs.items())[:40]:
            print(f"{key}: {value[:160]}")
        return 0

    translated_by_value = render_translations(dict.fromkeys(needs.values()).keys())

    merged: dict[str, str] = {}
    for key, english in en_data.items():
        if key in needs:
            merged[key] = translated_by_value[english]
        elif key in zh_data:
            merged[key] = zh_data[key]
        else:
            merged[key] = english

    for key, value in zh_data.items():
        if key not in merged:
            merged[key] = value

    args.zh.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.zh}: {len(merged)} keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
