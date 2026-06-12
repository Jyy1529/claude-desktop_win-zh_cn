#!/usr/bin/env python3
"""Synchronize zh-CN resources with an installed Claude Desktop build.

The installer uses this module to merge newly-added official en-US keys into
the copied zh-CN resources, so newer Claude builds do not fall back simply
because the local translation file is missing a key.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from claude_app_discovery import find_claude_package, resources_dir_for_app, resolve_app_dir


ROOT = Path(__file__).resolve().parent
RESOURCES = ROOT / "resources"


@dataclass(frozen=True)
class ResourceTarget:
    name: str
    en_rel: Path
    zh_path: Path | None
    fallback_zh_paths: tuple[Path, ...] = field(default_factory=tuple)
    copy_when_en_missing: bool = True


@dataclass
class SyncResult:
    name: str
    merged: dict
    missing: list[str]
    stale: list[str]
    en_path: Path | None
    zh_path: Path | None


TARGETS = [
    ResourceTarget("desktop", Path("en-US.json"), RESOURCES / "desktop-zh-CN.json"),
    ResourceTarget("frontend", Path("ion-dist") / "i18n" / "en-US.json", RESOURCES / "frontend-zh-CN.json"),
    ResourceTarget("statsig", Path("ion-dist") / "i18n" / "statsig" / "en-US.json", RESOURCES / "statsig-zh-CN.json"),
    ResourceTarget(
        "dynamic",
        Path("ion-dist") / "i18n" / "dynamic" / "en-US.json",
        RESOURCES / "dynamic-zh-CN.json",
        fallback_zh_paths=(RESOURCES / "statsig-zh-CN.json",),
        copy_when_en_missing=False,
    ),
]


def load_json_object(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def load_target_zh_cn(target: ResourceTarget) -> dict:
    """Load local zh-CN data for a target, optionally layering fallback files."""
    data: dict = {}
    paths: list[Path] = []
    if target.zh_path:
        paths.append(target.zh_path)
    paths.extend(target.fallback_zh_paths)

    for path in paths:
        if path.exists():
            data.update(load_json_object(path))
    if data or not target.zh_path:
        return data
    return load_json_object(target.zh_path)


def merge_resource(english: dict, zh_cn: dict, *, keep_stale: bool = True) -> tuple[dict, list[str], list[str]]:
    """Return zh-CN data ordered by official keys, filling new keys with English."""
    missing = [key for key in english.keys() if key not in zh_cn]
    stale = [key for key in zh_cn.keys() if key not in english]

    merged = {key: zh_cn.get(key, value) for key, value in english.items()}
    if keep_stale:
        for key in stale:
            merged[key] = zh_cn[key]
    return merged, missing, stale


def sync_resources(app_resources: Path, *, write: bool = False, keep_stale: bool = True) -> list[SyncResult]:
    """Compare local zh-CN resources with an installed app and optionally write them."""
    results: list[SyncResult] = []
    for target in TARGETS:
        zh_cn = load_target_zh_cn(target)
        en_path = app_resources / target.en_rel
        if not en_path.exists():
            if not target.copy_when_en_missing:
                continue
            results.append(SyncResult(target.name, zh_cn, [], [], None, target.zh_path))
            continue

        english = load_json_object(en_path)
        merged, missing, stale = merge_resource(english, zh_cn, keep_stale=keep_stale)
        if write and target.zh_path and (missing or stale or merged != zh_cn):
            target.zh_path.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        results.append(SyncResult(target.name, merged, missing, stale, en_path, target.zh_path))
    return results


def print_report(results: list[SyncResult]) -> None:
    for result in results:
        source = result.en_path if result.en_path else "missing official en-US resource"
        zh_source = result.zh_path if result.zh_path else "generated from fallback zh-CN resources"
        print(f"{result.name}: source={source}")
        print(f"  zh-CN: {zh_source}")
        print(f"  keys: {len(result.merged)}")
        print(f"  missing in zh-CN: {len(result.missing)}")
        print(f"  stale in zh-CN: {len(result.stale)}")
        if result.missing:
            preview = ", ".join(result.missing[:10])
            suffix = " ..." if len(result.missing) > 10 else ""
            print(f"  new keys filled with English: {preview}{suffix}")
        if result.stale:
            preview = ", ".join(result.stale[:10])
            suffix = " ..." if len(result.stale) > 10 else ""
            print(f"  stale keys kept: {preview}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local zh-CN resources with an installed Claude app")
    parser.add_argument("--app-dir", type=str, default=None, help="Claude app/resources/install directory")
    parser.add_argument("--write", action="store_true", help="Write merged resources back to resources/*.json")
    parser.add_argument("--drop-stale", action="store_true", help="Do not keep zh-CN keys missing from official en-US")
    args = parser.parse_args()

    if args.app_dir:
        app_dir = resolve_app_dir(args.app_dir)
    else:
        app_dir = find_claude_package()

    if not app_dir:
        raise SystemExit("Claude app directory not found. Use --app-dir to specify manually.")

    app_resources = resources_dir_for_app(app_dir)
    if not app_resources.exists():
        raise SystemExit(f"App resources not found: {app_resources}")

    results = sync_resources(app_resources, write=args.write, keep_stale=not args.drop_stale)
    print_report(results)
    if not args.write:
        print("Dry run only. Add --write to update local resources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
