#!/usr/bin/env python3
"""Shared Claude Desktop installation discovery helpers."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path


def _existing(path: Path | None) -> Path | None:
    return path if path and path.exists() else None


def is_resources_dir(path: Path) -> bool:
    """Return True when a directory looks like Claude's resources directory."""
    return (
        path.is_dir()
        and (
            (path / "en-US.json").exists()
            or (path / "ion-dist" / "i18n" / "en-US.json").exists()
            or (path / "ion-dist" / "assets").exists()
        )
    )


def resources_dir_for_app(app_dir: Path) -> Path:
    """Return the resources directory for an app or resources path."""
    if is_resources_dir(app_dir):
        return app_dir
    return app_dir / "resources"


def resolve_app_dir(input_path: str | Path | None) -> Path | None:
    """Normalize a user-provided Claude app/resources/install directory."""
    if not input_path:
        return None

    try:
        path = Path(input_path).expanduser()
    except (OSError, TypeError, ValueError):
        return None

    candidates = [
        path,
        path / "app",
        path.parent if path.name.lower() == "resources" else None,
    ]

    for candidate in candidates:
        candidate = _existing(candidate)
        if not candidate:
            continue
        if is_resources_dir(candidate):
            return candidate.parent
        if is_resources_dir(candidate / "resources"):
            return candidate

    return None


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def candidate_app_dirs() -> list[Path]:
    """Return likely Claude app directories without recursively scanning disks."""
    candidates: list[Path] = []

    windows_apps = Path(r"C:\Program Files\WindowsApps")
    if windows_apps.exists():
        for pattern in ("Claude_*__*/app/resources/en-US.json", "*Claude*/app/resources/en-US.json"):
            candidates.extend(path.parent.parent for path in windows_apps.glob(pattern))

    local_appdata = _env_path("LOCALAPPDATA")
    appdata = _env_path("APPDATA")
    program_files = _env_path("ProgramFiles")
    program_files_x86 = _env_path("ProgramFiles(x86)")

    explicit = [
        local_appdata / "Programs" / "Claude" if local_appdata else None,
        local_appdata / "Programs" / "Claude Desktop" if local_appdata else None,
        local_appdata / "Claude" / "app" if local_appdata else None,
        local_appdata / "AnthropicClaude" / "app" if local_appdata else None,
        local_appdata / "Anthropic" / "Claude" if local_appdata else None,
        appdata / "Claude" / "app" if appdata else None,
        program_files / "Claude" if program_files else None,
        program_files / "Claude Desktop" if program_files else None,
        program_files_x86 / "Claude" if program_files_x86 else None,
    ]

    for path in explicit:
        if path:
            candidates.append(path)

    resolved: dict[str, Path] = {}
    for path in candidates:
        app_dir = resolve_app_dir(path)
        if app_dir:
            resolved[str(app_dir).lower()] = app_dir

    return sorted(
        resolved.values(),
        key=lambda path: (
            describe_app_version(path) or "",
            resources_dir_for_app(path).stat().st_mtime if resources_dir_for_app(path).exists() else 0,
            str(path).lower(),
        ),
        reverse=True,
    )


def find_claude_package() -> Path | None:
    """Auto-detect a Claude Desktop app directory."""
    candidates = candidate_app_dirs()
    return candidates[0] if candidates else None


def describe_app_version(app_or_resources: Path) -> str | None:
    """Extract a best-effort Claude version from the path."""
    text = str(app_or_resources)
    match = re.search(r"Claude[_\s-]+([0-9]+(?:\.[0-9]+){1,4})", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"\bapp-([0-9]+(?:\.[0-9]+){1,4})\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def app_backup_key(app_or_resources: Path) -> str:
    """Return a stable per-install backup key using version and path hash."""
    try:
        resolved = app_or_resources.resolve()
    except OSError:
        resolved = app_or_resources

    version = describe_app_version(resolved) or "unknown"
    version = re.sub(r"[^0-9A-Za-z._-]+", "-", version).strip("-") or "unknown"
    digest = hashlib.sha1(str(resolved).lower().encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"{version}-{digest}"
