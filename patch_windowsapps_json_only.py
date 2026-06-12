#!/usr/bin/env python3
"""Patch only JSON i18n resources in the official Claude Desktop package.

Accepts --app-dir to specify the Claude app directory dynamically.
If not provided, auto-detects WindowsApps and AppData\\Local\\AnthropicClaude installs.

Steps:
1. Backup original files
2. Copy zh-CN JSON resources into the official package
3. Patch the language whitelist in index-*.js to recognize zh-CN
4. Set locale=zh-CN in user config
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESOURCES = ROOT / "resources"
BACKUP_ROOT = Path(os.environ["LOCALAPPDATA"]) / "Claude-zh-CN-official-backup" / "json-only"
CONFIG_PATH = Path(os.environ["APPDATA"]) / "Claude-3p" / "config.json"


DESKTOP_EN_US_FALLBACK_KEYS = {
    "7fdcqxofEs",  # Exit
    "DQTgg21B7g",  # Show App
    "dKX0bpR+a2",  # Quit
    "oQuOiX24pp",  # Quit
}


HARDCODED_UI_FALLBACKS = {
    '"Enable Main Process Debugger"': '"启用主进程调试器"',
    '"Record Performance Trace"': '"记录性能跟踪"',
    '"Write Main Process Heap Snapshot"': '"写入主进程堆快照"',
    '"Record Memory Trace (auto-stop)"': '"记录内存跟踪（自动停止）"',
}


OFFICIAL_LANGUAGE_LOCALES = {
    "en-US",
    "de-DE",
    "fr-FR",
    "ko-KR",
    "ja-JP",
    "es-419",
    "es-ES",
    "it-IT",
    "hi-IN",
    "pt-BR",
    "id-ID",
}

LOCALE_ARRAY_RE = re.compile(
    r'\[\s*"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,4})*"'
    r'(?:\s*,\s*"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,4})*")+\s*\]'
)


def find_claude_package() -> Path | None:
    """Auto-detect Claude app directory from supported Windows install layouts."""
    appx = find_appx_claude_package()
    if appx:
        return appx

    windows_candidates: list[Path] = []
    windowsapps = Path(r"C:\Program Files\WindowsApps")
    if windowsapps.exists():
        windows_candidates.extend(
            path.parent.parent
            for path in windowsapps.glob("Claude_*_x64__*/app/resources/en-US.json")
            if path.is_file()
        )
    if windows_candidates:
        return sorted(set(windows_candidates), key=lambda path: (windowsapps_version_key(path), str(path)), reverse=True)[0]

    local_candidates: list[Path] = []
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        anthropic = Path(localappdata) / "AnthropicClaude"
        if anthropic.exists():
            local_resource_files = [
                anthropic / "resources" / "en-US.json",
                anthropic / "app" / "resources" / "en-US.json",
                *anthropic.glob("app*/resources/en-US.json"),
            ]
            local_candidates.extend(path.parent.parent for path in local_resource_files if path.is_file())

    if not local_candidates:
        return None
    return sorted(set(local_candidates), key=lambda path: (path.stat().st_mtime if path.exists() else 0, str(path)), reverse=True)[0]


def find_appx_claude_package() -> Path | None:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "$p=Get-AppxPackage -Name Claude -ErrorAction SilentlyContinue | Sort-Object Version -Descending | Select-Object -First 1; if ($p) { Join-Path $p.InstallLocation 'app' }",
            ],
            capture_output=True,
            text=True,
            timeout=6,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    for line in result.stdout.splitlines():
        app_dir = Path(line.strip())
        if (app_dir / "resources" / "en-US.json").is_file():
            return app_dir
    return None


def windowsapps_version_key(app_dir: Path) -> tuple[int, ...]:
    parts = app_dir.parent.name.split("_")
    if len(parts) < 2:
        return ()
    version: list[int] = []
    for part in parts[1].split("."):
        try:
            version.append(int(part))
        except ValueError:
            version.append(0)
    return tuple(version)


def find_assets_dir(app_resources: Path) -> Path | None:
    """Locate the active ion-dist/assets version directory."""
    assets_root = app_resources / "ion-dist" / "assets"
    if not assets_root.exists():
        return None

    candidates = sorted(
        {path.parent for path in assets_root.rglob("index-*.js") if path.is_file()},
        key=lambda path: str(path).lower(),
        reverse=True,
    )
    return candidates[0] if candidates else None


def iter_assets_dirs(app_resources: Path) -> list[Path]:
    """Return all discovered ion-dist/assets version directories."""
    assets_root = app_resources / "ion-dist" / "assets"
    if not assets_root.exists():
        return []

    dirs = {
        path.parent
        for path in assets_root.rglob("index-*.js")
        if path.is_file()
    }
    return sorted(dirs, key=lambda path: str(path).lower(), reverse=True)


def backup_file(path: Path, app_resources: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(app_resources)
    dst = BACKUP_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        copy2_best_effort(path, dst, context="backup file")


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
            print(f"Warning: cannot copy {context} from {src} to {dst}: {e}")
            return False
    except OSError as e:
        print(f"Warning: cannot copy {context} from {src} to {dst}: {e}")
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


def should_patch_locale_array(locales: list[str], *, legacy_index_list: bool) -> bool:
    if not locales or locales[0] != "en-US":
        return False
    if "zh-CN" in locales:
        return True
    if legacy_index_list:
        return len(locales) >= 2

    hits = OFFICIAL_LANGUAGE_LOCALES.intersection(locales)
    return len(hits) >= 6 and {"de-DE", "fr-FR", "ja-JP", "ko-KR"}.issubset(hits)


def patch_locale_arrays(text: str, *, legacy_index_list: bool) -> tuple[str, bool, bool]:
    found = False
    changed = False

    def replace_array(match: re.Match[str]) -> str:
        nonlocal found, changed
        array_text = match.group(0)
        try:
            locales = json.loads(array_text)
        except json.JSONDecodeError:
            return array_text
        if not isinstance(locales, list) or not all(isinstance(item, str) for item in locales):
            return array_text
        if not should_patch_locale_array(locales, legacy_index_list=legacy_index_list):
            return array_text

        found = True
        if "zh-CN" in locales:
            return array_text

        changed = True
        insert_at = array_text.rfind("]")
        return array_text[:insert_at] + ',"zh-CN"' + array_text[insert_at:]

    return LOCALE_ARRAY_RE.sub(replace_array, text), changed, found


def patch_whitelist(app_resources: Path) -> str | None:
    """Add zh-CN to every discovered language whitelist. Uses flexible matching."""
    assets_dirs = iter_assets_dirs(app_resources)
    if not assets_dirs:
        print("Warning: no index-*.js found; skipping whitelist patch")
        return None

    candidates: list[Path] = []
    for assets_dir in assets_dirs:
        for path in sorted(assets_dir.glob("*.js")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as e:
                print(f"Warning: cannot read whitelist target at {path}: {e}; skipping")
                continue
            if path.name.startswith("index-") and '"en-US"' in text:
                candidates.append(path)
            elif '"en-US"' in text and '"fr-FR"' in text:
                candidates.append(path)

    if not candidates:
        print("Warning: no candidate JS bundle found; skipping whitelist patch")
        return None

    touched: list[str] = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        legacy_index_list = path.name.startswith("index-")
        patched, changed, found = patch_locale_arrays(text, legacy_index_list=legacy_index_list)
        if not found:
            continue
        if not changed:
            touched.append(path.name)
            continue

        backup_file(path, app_resources)
        if write_text_best_effort(path, patched, context="whitelist patch"):
            touched.append(path.name)

    if touched:
        return ", ".join(touched)

    print("Warning: whitelist pattern not found in any index bundle")
    return None


def patch_hardcoded_ui_fallbacks(app_resources: Path) -> int:
    """Patch visible hardcoded UI labels not covered by JSON resources."""
    assets_dirs = iter_assets_dirs(app_resources)
    if not assets_dirs:
        return 0

    changed_files = 0
    candidates = [path for assets_dir in assets_dirs for path in sorted(assets_dir.glob("*.js"))]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Warning: cannot read hardcoded UI target at {path}: {e}; skipping")
            continue

        patched = text
        for needle, replacement in HARDCODED_UI_FALLBACKS.items():
            patched = patched.replace(needle, replacement)

        if patched == text:
            continue

        backup_file(path, app_resources)
        if write_text_best_effort(path, patched, context="hardcoded UI fallback patch"):
            changed_files += 1

    return changed_files


def set_locale() -> bool:
    """Set locale=zh-CN in user config."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {}
    else:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: cannot parse config: {e}; skipping locale")
            return False

    if data.get("locale") == "zh-CN":
        return True

    data["locale"] = "zh-CN"
    return write_text_best_effort(
        CONFIG_PATH,
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        context="locale config",
    )


def patch_desktop_en_us_fallback(app_resources: Path) -> int:
    """Patch desktop tray labels that may still be read from en-US resources."""
    en_us_path = app_resources / "en-US.json"
    zh_cn_path = RESOURCES / "desktop-zh-CN.json"
    if not en_us_path.exists() or not zh_cn_path.exists():
        return 0

    try:
        en_us = json.loads(en_us_path.read_text(encoding="utf-8-sig"))
        zh_cn = json.loads(zh_cn_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: cannot patch desktop en-US fallback: {e}; skipping")
        return 0

    changed = 0
    for key in DESKTOP_EN_US_FALLBACK_KEYS:
        if key in en_us and key in zh_cn and en_us[key] != zh_cn[key]:
            en_us[key] = zh_cn[key]
            changed += 1

    if not changed:
        return 0

    backup_file(en_us_path, app_resources)
    if not write_text_best_effort(
        en_us_path,
        json.dumps(en_us, ensure_ascii=False, indent=2) + "\n",
        context="desktop en-US fallback patch",
    ):
        return 0
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Claude Desktop with zh-CN resources")
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
    if not app_resources.exists():
        raise SystemExit(f"App resources not found: {app_resources}")

    files = [
        (RESOURCES / "desktop-zh-CN.json", app_resources / "zh-CN.json"),
        (RESOURCES / "frontend-zh-CN.json", app_resources / "ion-dist" / "i18n" / "zh-CN.json"),
        (RESOURCES / "statsig-zh-CN.json", app_resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json"),
    ]

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # Step 1: Copy JSON resources
    copied = 0
    for src, dst in files:
        if not src.exists():
            raise SystemExit(f"Missing source resource: {src}")
        backup_file(dst, app_resources)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not copy2_best_effort(src, dst, context="json resource"):
            raise SystemExit(f"Failed to copy json resource: {src} -> {dst}")
        copied += 1

    # Step 2: Patch whitelist
    wl_file = patch_whitelist(app_resources)

    # Step 3: Patch desktop fallback labels used before zh-CN is loaded
    fallback_labels = patch_desktop_en_us_fallback(app_resources)

    # Step 4: Patch hardcoded visible labels not represented in JSON i18n.
    hardcoded_labels = patch_hardcoded_ui_fallbacks(app_resources)

    # Step 5: Set locale
    locale_set = set_locale()

    print("Done")
    print(f"App dir: {app_dir}")
    print(f"Copied json resources: {copied}")
    print(f"Whitelist patched: {wl_file or 'skipped'}")
    print(f"Desktop en-US fallback labels patched: {fallback_labels}")
    print(f"Hardcoded UI fallback files patched: {hardcoded_labels}")
    print(f"Locale set: {locale_set}")
    print(f"Backup root: {BACKUP_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
