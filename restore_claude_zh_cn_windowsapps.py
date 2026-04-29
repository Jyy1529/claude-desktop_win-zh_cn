#!/usr/bin/env python3
"""Restore WindowsApps files from backup and remove locale setting.

Accepts --app-dir to specify the Claude app directory dynamically.
If not provided, auto-detects from C:\\Program Files\\WindowsApps.

Restores backed-up files (relative to app\\resources) and removes
locale=zh-CN from user config.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
from pathlib import Path


BACKUP_BASE = Path(os.environ["LOCALAPPDATA"]) / "Claude-zh-CN-official-backup"
BACKUP_JSON_ONLY = BACKUP_BASE / "json-only"
CONFIG_PATH = Path(os.environ["APPDATA"]) / "Claude-3p" / "config.json"
FONT_KEY = "claudeZhCnFont"


def find_claude_package() -> Path | None:
    """Auto-detect Claude package under WindowsApps."""
    base = Path(r"C:\Program Files\WindowsApps")
    if not base.exists():
        return None
    candidates = sorted(base.glob("Claude_*_x64__*/app/resources/en-US.json"), reverse=True)
    if candidates:
        return candidates[0].parent.parent  # .../app
    return None


def restore_from(backup_root: Path, app_resources: Path) -> int:
    """Restore files from backup to app/resources."""
    restored = 0
    for src in backup_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(backup_root)
        dst = app_resources / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if copy2_best_effort(src, dst, context="restore backup"):
            restored += 1
    return restored


def copy2_best_effort(src: Path, dst: Path, *, context: str) -> bool:
    """Copy a file and retry once after clearing the destination readonly bit."""
    try:
        shutil.copy2(src, dst)
        return True
    except PermissionError:
        if dst.exists():
            try:
                dst.chmod(dst.stat().st_mode | stat.S_IWRITE)
            except OSError:
                pass
        try:
            shutil.copy2(src, dst)
            return True
        except OSError as e:
            print(f"Warning: cannot copy {context} from {src} to {dst}: {e}; skipping")
            return False
    except OSError as e:
        print(f"Warning: cannot copy {context} from {src} to {dst}: {e}; skipping")
        return False


def write_text_best_effort(path: Path, text: str, *, context: str) -> bool:
    """Write text and degrade gracefully on Windows permission issues."""
    try:
        path.write_text(text, encoding="utf-8")
        return True
    except PermissionError:
        try:
            path.chmod(path.stat().st_mode | stat.S_IWRITE)
        except OSError:
            pass
        try:
            path.write_text(text, encoding="utf-8")
            return True
        except OSError as e:
            print(f"Warning: cannot write {context} at {path}: {e}; skipping")
            return False
    except OSError as e:
        print(f"Warning: cannot write {context} at {path}: {e}; skipping")
        return False


def remove_locale() -> bool:
    """Remove locale=zh-CN and zh-CN font mirror from user config."""
    if not CONFIG_PATH.exists():
        return False

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    changed = False
    if "locale" in data:
        del data["locale"]
        changed = True
    if FONT_KEY in data:
        del data[FONT_KEY]
        changed = True

    if not changed:
        return False

    return write_text_best_effort(
        CONFIG_PATH,
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        context="restore locale config",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore Claude Desktop from backup")
    parser.add_argument("--app-dir", type=str, default=None,
                        help="Path to Claude app directory (auto-detected if omitted)")
    args = parser.parse_args()

    if args.app_dir:
        app_dir = Path(args.app_dir)
    else:
        app_dir = find_claude_package()

    if not app_dir or not app_dir.exists():
        raise SystemExit("Claude app directory not found. Use --app-dir to specify manually.")

    app_resources = app_dir / "resources"

    # Also check for full-patch backups (legacy)
    backup_full = None
    for d in sorted(BACKUP_BASE.glob("Claude_*"), reverse=True):
        if d.is_dir() and any(d.rglob("*")):
            backup_full = d
            break

    # Check for chunk backups
    backup_chunks = BACKUP_BASE / "chunks"

    candidates = []
    if BACKUP_JSON_ONLY.exists() and any(BACKUP_JSON_ONLY.rglob("*")):
        candidates.append(("json-only", BACKUP_JSON_ONLY, app_resources))
    if backup_chunks.exists() and any(backup_chunks.rglob("*")):
        assets_dir = app_resources / "ion-dist" / "assets" / "v1"
        candidates.append(("chunks", backup_chunks, assets_dir))
    if backup_full:
        candidates.append(("full-patch", backup_full, app_resources))

    if not candidates:
        raise SystemExit(f"No backup found under {BACKUP_BASE}")

    total_restored = 0
    for label, root, target in candidates:
        count = restore_from(root, target)
        total_restored += count
        print(f"  Restored from {label}: {root} ({count} files)")

    # Remove locale
    locale_removed = remove_locale()

    print()
    print("Done")
    print(f"Total restored files: {total_restored}")
    print(f"Locale removed: {locale_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
