#!/usr/bin/env python3
"""Patch only JSON i18n resources in the official WindowsApps package.

Accepts --app-dir to specify the Claude app directory dynamically.
If not provided, auto-detects from C:\\Program Files\\WindowsApps.

Steps:
1. Backup original files
2. Copy zh-CN JSON resources into the official package
3. Patch the locale bootstrap/whitelist in bundled JS to recognize zh-CN
4. Set locale=zh-CN in user config
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path

from claude_app_discovery import (
    app_backup_key,
    find_claude_package,
    resources_dir_for_app,
    resolve_app_dir,
)
from resource_sync import sync_resources

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


def backup_root_for_app(app_resources: Path) -> Path:
    return BACKUP_ROOT / app_backup_key(app_resources)


def backup_file(path: Path, app_resources: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(app_resources)
    dst = backup_root_for_app(app_resources) / rel
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


def copy_json_payload_best_effort(payload: dict, dst: Path, *, context: str) -> bool:
    """Copy JSON through a temp file so permission retry behavior stays uniform."""
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            tmp_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return copy2_best_effort(tmp_path, dst, context=context)
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def resource_destinations(app_resources: Path) -> dict[str, Path]:
    return {
        "desktop": app_resources / "zh-CN.json",
        "frontend": app_resources / "ion-dist" / "i18n" / "zh-CN.json",
        "statsig": app_resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json",
        "dynamic": app_resources / "ion-dist" / "i18n" / "dynamic" / "zh-CN.json",
    }


LOCALE_ARRAY_RE = re.compile(r'\["en-US"(?:,"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,4})*")+\]')
SPA_LOCALE_BOOTSTRAP_RE = re.compile(
    r'const (?P<storage>[A-Za-z_$][\w$]*)="spa:locale",'
    r'(?P<locale>[A-Za-z_$][\w$]*)=NS\(\[\(\(\)=>\{try\{return localStorage\.getItem\((?P=storage)\)\}'
    r'catch\{return null\}\}\)\(\),\.\.\.navigator\.languages\]\);'
)
SPA_BOOTSTRAP_LOCALE_RE = re.compile(
    r'const (?P<locale>[A-Za-z_$][\w$]*)=NS\(\[(?P<source>[A-Za-z_$][\w$]*)\.locale\]\);'
    r'try\{localStorage\.setItem\((?P<storage>[A-Za-z_$][\w$]*),(?P=locale)\)\}catch\{\}'
)


def add_zh_cn_to_locale_arrays(text: str) -> tuple[str, int]:
    """Add zh-CN to minified locale allow-list arrays such as Kw=[...]."""
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        array = match.group(0)
        items = re.findall(r'"([^"]+)"', array)
        non_zh_items = [item for item in items if item != "zh-CN"]
        has_non_english_locale = any(
            not (item == "en" or item.startswith("en-"))
            for item in (value.lower() for value in non_zh_items)
        )
        if not has_non_english_locale:
            cleaned = array.replace(',"zh-CN"', '').replace('"zh-CN",', '')
            if cleaned != array:
                changed += 1
            return cleaned
        if '"zh-CN"' in array:
            return array
        changed += 1
        return array[:-1] + ',"zh-CN"]'

    return LOCALE_ARRAY_RE.sub(replace, text), changed


def patch_spa_locale_bootstrap(text: str) -> tuple[str, int]:
    """Prefer zh-CN in the SPA locale bootstrap used by recent Claude bundles."""
    changed = 0

    def replace_bootstrap(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        storage = match.group("storage")
        locale = match.group("locale")
        return (
            f'const {storage}="spa:locale",{locale}=NS(["zh-CN",(()=>{{try{{return '
            f'localStorage.getItem({storage})}}catch{{return null}}}})(),...navigator.languages]);'
            f'try{{localStorage.setItem({storage},{locale})}}catch{{}}'
        )

    text = SPA_LOCALE_BOOTSTRAP_RE.sub(replace_bootstrap, text)

    def replace_bootstrap_locale(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        locale = match.group("locale")
        source = match.group("source")
        storage = match.group("storage")
        return (
            f'const {locale}=NS(["zh-CN",{source}.locale]);'
            f'try{{localStorage.setItem({storage},{locale})}}catch{{}}'
        )

    text = SPA_BOOTSTRAP_LOCALE_RE.sub(replace_bootstrap_locale, text)
    return text, changed


def patch_whitelist(app_resources: Path) -> str | None:
    """Add zh-CN support to discovered locale lists and SPA locale bootstrap code."""
    assets_dirs = iter_assets_dirs(app_resources)
    if not assets_dirs:
        print("Warning: no asset bundles found; skipping locale support patch")
        return None

    candidates = [path for assets_dir in assets_dirs for path in sorted(assets_dir.glob("*.js"))]
    if not candidates:
        print("Warning: no asset bundles found; skipping locale support patch")
        return None

    touched: list[str] = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")

        patched, _ = add_zh_cn_to_locale_arrays(text)
        patched, _ = patch_spa_locale_bootstrap(patched)

        if patched == text:
            has_supported_locale = bool(LOCALE_ARRAY_RE.search(text) and '"zh-CN"' in text)
            has_spa_locale = '"spa:locale"' in text and 'NS(["zh-CN"' in text
            if has_supported_locale or has_spa_locale:
                touched.append(path.name)
            continue

        # Backup only when this run changes the bundle.
        backup_file(path, app_resources)
        if write_text_best_effort(path, patched, context="locale support patch"):
            touched.append(path.name)

    if touched:
        return ", ".join(touched)

    print("Warning: locale support pattern not found in any asset bundle")
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
    parser.add_argument("--sync-local-resources", action="store_true",
                        help="Also write newly discovered official keys back to resources/*.json")
    args = parser.parse_args()

    if args.app_dir:
        app_dir = resolve_app_dir(args.app_dir)
    else:
        app_dir = find_claude_package()

    if not app_dir or not app_dir.exists():
        raise SystemExit("Claude app directory not found. Use --app-dir to specify manually.")

    app_resources = resources_dir_for_app(app_dir)
    if not app_resources.exists():
        raise SystemExit(f"App resources not found: {app_resources}")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # Step 1: Merge local zh-CN with the target app's official en-US keys, then copy.
    sync_results = sync_resources(
        app_resources,
        write=args.sync_local_resources,
        keep_stale=True,
    )
    destinations = resource_destinations(app_resources)
    copied = 0
    missing_total = 0
    stale_total = 0
    for result in sync_results:
        dst = destinations[result.name]
        backup_file(dst, app_resources)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not copy_json_payload_best_effort(result.merged, dst, context="json resource"):
            raise SystemExit(f"Failed to copy json resource: {result.zh_path} -> {dst}")
        copied += 1
        missing_total += len(result.missing)
        stale_total += len(result.stale)

    # Step 2: Patch locale support
    wl_file = patch_whitelist(app_resources)

    # Step 3: Patch desktop fallback labels used before zh-CN is loaded
    fallback_labels = patch_desktop_en_us_fallback(app_resources)

    # Step 4: Patch hardcoded visible labels not represented in JSON i18n.
    hardcoded_labels = patch_hardcoded_ui_fallbacks(app_resources)

    # Step 5: Set locale
    locale_set = set_locale()

    print("Done")
    print(f"App dir: {app_dir}")
    print(f"App resources: {app_resources}")
    print(f"Backup key: {app_backup_key(app_resources)}")
    print(f"Copied json resources: {copied}")
    print(f"Synced missing official keys: {missing_total}")
    print(f"Stale local zh-CN keys kept: {stale_total}")
    print(f"Local resources updated: {args.sync_local_resources}")
    print(f"Locale support patched: {wl_file or 'skipped'}")
    print(f"Desktop en-US fallback labels patched: {fallback_labels}")
    print(f"Hardcoded UI fallback files patched: {hardcoded_labels}")
    print(f"Locale set: {locale_set}")
    print(f"Backup root: {backup_root_for_app(app_resources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
