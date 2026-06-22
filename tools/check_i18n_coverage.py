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
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")
TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
CODE_ELEMENT_RE = re.compile(r"<code\b[^>]*>.*?</code>", re.IGNORECASE | re.DOTALL)
URL_RE = re.compile(r"https?://\S+|claude://\S+")
DOMAIN_RE = re.compile(r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?")
EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+")
PATH_RE = re.compile(r"(?:~|\.{1,2})?[/\\][A-Za-z0-9_.+\\/-]+")
SNAKE_IDENTIFIER_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")
HEADER_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b")


ALLOWED_MIXED_WORDS = {
    "access_as_user",
    "account",
    "acme",
    "admin",
    "agent",
    "agents",
    "ai",
    "android",
    "amazon",
    "applocker",
    "anthropics",
    "anthropic",
    "amzn",
    "api",
    "apis",
    "app",
    "apps",
    "applocker",
    "apple",
    "apply",
    "artifact",
    "artifacts",
    "ants",
    "aws",
    "azure",
    "baa",
    "bash",
    "basic",
    "cidr",
    "bedrock",
    "bearer",
    "beta",
    "ble",
    "build",
    "buddy",
    "byoc",
    "canvas",
    "canva",
    "chat",
    "chrome",
    "cimd",
    "claude",
    "claude.ai",
    "claude-desktop-buddy",
    "client",
    "clawddash",
    "cli",
    "cloud",
    "code",
    "coder",
    "cognitive",
    "cmeK".lower(),
    "config",
    "console",
    "conway",
    "cookie",
    "completion",
    "contains",
    "cowork",
    "cpu",
    "cron",
    "crm",
    "crispr",
    "csv",
    "ctrl",
    "cursor",
    "cvc",
    "dau",
    "deck",
    "center",
    "certificate",
    "desktop",
    "design",
    "diff",
    "directory",
    "dispatch",
    "docker",
    "dockerfile",
    "documents",
    "docx",
    "download",
    "drive",
    "dxt",
    "email",
    "entra",
    "enter",
    "enterprise",
    "endpoint",
    "escape",
    "excel",
    "export",
    "fable",
    "favicon",
    "fedramp",
    "finder",
    "foundry",
    "fssl",
    "gdrive",
    "github",
    "git",
    "gitignore",
    "gmail",
    "google",
    "graph",
    "growthbook",
    "ghe",
    "given",
    "global",
    "gnome",
    "grpc",
    "guardrails",
    "guid",
    "haveibeenpwned",
    "hipaa",
    "html",
    "http",
    "https",
    "hotfix",
    "iam",
    "ico",
    "ide",
    "iframe",
    "idp",
    "identity",
    "inspector",
    "install",
    "intel",
    "interviewer",
    "ios",
    "issue",
    "java",
    "jpeg",
    "json",
    "jwt",
    "jamf",
    "jetbrains",
    "keyring",
    "labs",
    "launch",
    "linear",
    "linkedin",
    "linux",
    "line",
    "lite",
    "local",
    "localstorage",
    "logs",
    "mac",
    "macos",
    "magic",
    "manifest",
    "maps",
    "markdown",
    "meet",
    "marketplace",
    "messagebird",
    "mcp",
    "mcpb",
    "mdm",
    "method",
    "mfa",
    "metrics",
    "microsoft",
    "monorepo",
    "nest",
    "nordic",
    "node",
    "no_proxy",
    "nvidia",
    "oauth",
    "npm",
    "office",
    "offline_access",
    "oidc",
    "openid",
    "openai",
    "opentelemetry",
    "opus",
    "orbit",
    "orchestrator",
    "owner",
    "otel",
    "otlp",
    "pdf",
    "parallels",
    "pkce",
    "play",
    "plan",
    "pitch",
    "platform",
    "png",
    "plist",
    "powerpoint",
    "prd",
    "prompt",
    "pptx",
    "protobuf",
    "proxy",
    "plugin",
    "plugins",
    "redistributable",
    "pwned",
    "qbr",
    "react",
    "readonlyhint",
    "rbac",
    "redirect",
    "regex",
    "research",
    "rest",
    "rum",
    "rrggbb",
    "routines",
    "runner",
    "safari",
    "salesforce",
    "saml",
    "scope",
    "scrum",
    "scim",
    "scopes",
    "sdk",
    "security",
    "server",
    "service",
    "sessionstorage",
    "settings",
    "securevmfeaturesenabled",
    "sha",
    "shell",
    "sid",
    "silicon",
    "slack",
    "slug",
    "sonnet",
    "sop",
    "span",
    "spawn",
    "stderr",
    "space",
    "ssh",
    "sso",
    "stdio",
    "streamable",
    "stdout",
    "sts",
    "subject",
    "supabase",
    "tab",
    "team",
    "teams",
    "textlocal",
    "then",
    "tldr",
    "turbovote",
    "token",
    "tokens",
    "tools",
    "uuid",
    "twitter",
    "twilio",
    "uart",
    "ui",
    "unlimited",
    "ultrareview",
    "ultracode",
    "url",
    "urls",
    "usb",
    "utf-8",
    "vertex",
    "virtualhint",
    "analytics",
    "asana",
    "auth",
    "authorization",
    "availablemodels",
    "begin",
    "black",
    "channels",
    "clearance",
    "click",
    "command",
    "curl",
    "datadog",
    "developer",
    "destructivehint",
    "disableautomode",
    "edge",
    "experience",
    "explorer",
    "exporter",
    "false",
    "feature",
    "francisco",
    "frame",
    "functions",
    "gate",
    "gateway",
    "hook",
    "hooks",
    "idempothint",
    "insights",
    "intune",
    "javascript",
    "lint",
    "login",
    "master",
    "mece",
    "mitm",
    "mono",
    "network",
    "nonprofit",
    "only",
    "openworldhint",
    "path",
    "patch",
    "post",
    "profile",
    "profilecreator",
    "prod",
    "python",
    "readme",
    "repo",
    "review",
    "refresh",
    "root",
    "saas",
    "sapling",
    "session",
    "skill",
    "sonoma",
    "ssrf",
    "steward",
    "stop",
    "stripe",
    "true",
    "unicode",
    "visual",
    "vonage",
    "worktree",
    "yaml",
    "your",
    "word",
    "admx",
    "amodei",
    "appsource",
    "authless",
    "bios",
    "california",
    "comsec",
    "computer",
    "context",
    "dario",
    "devops",
    "error",
    "fira",
    "fork",
    "gdpr",
    "headers",
    "homebrew",
    "howard",
    "invokemodel",
    "link",
    "localhost",
    "main",
    "mobile",
    "model",
    "notion",
    "operan",
    "outline",
    "protocol",
    "remix",
    "scrna",
    "secret",
    "segment",
    "services",
    "skills",
    "statsig",
    "street",
    "studio",
    "vercel",
    "wdac",
    "websocket",
    "with",
    "worker",
    "vm",
    "vpc",
    "wau",
    "web",
    "webhook",
    "webhooks",
    "when",
    "webrtc",
    "webp",
    "windows",
    "windsurf",
    "workforce",
    "workspace",
    "xlsx",
    "xcode",
    "zdr",
}


KNOWN_OK_VALUES = {
    "$ / commit",
    "*.corp.example.com",
    ".claude.app",
    "//iam.googleapis.com/locations/global/workforcePools/POOL/providers/PROVIDER",
    "Anthropic API",
    "Anthropic API key",
    "Anthropic Sans",
    "Anthropic Serif",
    "Android Emulator",
    "APIs",
    "AWS — Messages API",
    "AWS SSO account ID",
    "Bearer …",
    "BedrockInference",
    "Beta",
    "cache r",
    "cache w",
    "Claude Code (CLI, Desktop, IDE)",
    "Claude Code Desktop",
    "Claude for Enterprise {tier}",
    "Claude for Outlook",
    "Claude GitHub App",
    "Claude on AWS",
    "Claude Opus 4",
    "Claude Sales",
    "Claude Ship",
    "Claude {featureName}",
    "Claude {plan}",
    "claude-opus-4",
    "claude://cowork/shared-artifact?uuid=…",
    "Client secret helper script",
    "Ctrl+⏎",
    "Dream",
    "e.g. Bearer",
    "e.g. Datadog",
    "e.g. Internal billing API",
    "enduser.id",
    "example.com",
    "Fable",
    "GitHub App",
    "GitHub Enterprise",
    "global",
    "github",
    "GOCSPX-...",
    "grpc or http/protobuf.",
    "HTTP {status}",
    "idempotent",
    "iOS Simulator",
    "Instagram",
    "Linux（x64）",
    "Local MCPB",
    "Mac (Apple Silicon)",
    "Mac（Intel）",
    "MANAGED LOCAL",
    "Markdown",
    "Microsoft 365",
    "McpBuiltinServerM365Opt",
    "my-foundry-resource",
    "my-gcp-project",
    "Mythos",
    "NNN.apps.googleusercontent.com",
    "OAuth client ID",
    "Provisioner idempotency key:",
    "RUM session:",
    "Session Lens",
    "shell",
    "the Anthropic API",
    "the Claude API",
    "Ultracode",
    "us-east-1",
    "us-west-2",
    "us-east5",
    "Vertex OAuth client ID",
    "Vertex OAuth client secret",
    "Windows（arm64）",
    "Windows（x64）",
    "Workforce Identity (STS)",
    "Workforce Identity audience",
    "Workforce Identity IdP (OIDC)",
    "X / Twitter",
    "your-site",
    "'{username}'@example.com",
    "{label}，Beta",
    "{n}/user",
}


KNOWN_OK_PATTERNS = [
    re.compile(r"^(USB|AWS|API|SDK|JSON|UTF-8|CI|CLI|MCP|SSH|URL|ID|Caps Lock)$"),
    re.compile(r"^\{.*\}$"),
    re.compile(r"^[\d{}%./: +\-_,()\[\]<>|]+$"),
    re.compile(r"^(Anthropic|Bedrock|Vertex|Foundry|Azure AI|Google Vertex AI|AWS Bedrock)$"),
    re.compile(r"^(Claude|Claude\.ai|Claude API|Claude Code|Claude Code CLI|Claude Enterprise|Claude for Excel)$"),
    re.compile(r"^(Python|Node\.js|Webhook|GitHub|Gmail|JetBrains|Excel|Artifacts|Bash|JPEG|OAuth|LinkedIn|Reddit|TikTok|YouTube|status\.claude\.com)$"),
    re.compile(r"^(Amazon Bedrock|Claude — zsh|website\.com)$"),
    re.compile(r"^(Windows \(x64\)|Windows \(arm64\)|Linux \(x64\)|Linux（arm64）|macOS)$"),
    re.compile(r"^(Latin-1 \(ISO-8859-1\)|Ctrl⏎)$"),
    re.compile(r"^(Headers|X-Header-Name|OAuth 2\.0 JWT bearer|OpenTelemetry|SCIM)$"),
    re.compile(r"^(/[A-Za-z0-9_.+-]+)+$"),
    re.compile(r"^~(/[A-Za-z0-9_.+-]+)+$"),
    re.compile(r"^\[[^\]]+\]$"),
    re.compile(r"^\{[^{}]+\}\s*(KB|MB|GB|ms|tokens?)$"),
    re.compile(r"^v\{version\}$"),
    re.compile(r"^[+-]?\{[^{}]+\}$"),
    re.compile(r"^[#$]?\{[^{}]+\}$"),
    re.compile(r"^.+\(\{email\}\)$"),
    re.compile(r"^https?://\S+$"),
    re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+$"),  # email addresses only
    re.compile(r"^PR #\{.*\}$"),
    re.compile(r"^CI \{.*\}$"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_known_ok(value: str) -> bool:
    if value in KNOWN_OK_VALUES:
        return True
    return any(p.search(value) for p in KNOWN_OK_PATTERNS)


def strip_format_blocks(value: str) -> str:
    previous = None
    current = value
    while previous != current:
        previous = current
        current = PLACEHOLDER_RE.sub(" ", current)
    return current


def normalize_for_ascii_scan(value: str) -> str:
    value = CODE_ELEMENT_RE.sub(" ", value)
    value = CODE_SPAN_RE.sub(" ", value)
    value = URL_RE.sub(" ", value)
    value = EMAIL_RE.sub(" ", value)
    value = DOMAIN_RE.sub(" ", value)
    value = PATH_RE.sub(" ", value)
    value = SNAKE_IDENTIFIER_RE.sub(" ", value)
    value = HEADER_IDENTIFIER_RE.sub(" ", value)
    value = TAG_RE.sub(" ", value)
    return strip_format_blocks(value)


def has_unapproved_ascii_words(value: str) -> bool:
    normalized = normalize_for_ascii_scan(value)
    if is_known_ok(normalized):
        return False
    for match in ASCII_WORD_RE.finditer(normalized):
        token = match.group(0).strip("._+-").lower()
        if len(token) < 4:
            continue
        if token in ALLOWED_MIXED_WORDS:
            continue
        if re.fullmatch(r"[a-f0-9]{6,}", token):
            continue
        return True
    return False


def classify_value(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    if is_known_ok(value):
        return None
    if has_unapproved_ascii_words(value):
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
