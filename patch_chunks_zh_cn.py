#!/usr/bin/env python3
"""Patch JS chunks with Chinese UI labels.

This script applies safe string replacements to hardcoded UI labels
in Claude Desktop's JS bundle files. It backs up original files before
modifying and only replaces exact string patterns.

Run after patch_windowsapps_json_only.py.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


BACKUP_ROOT = Path(os.environ["LOCALAPPDATA"]) / "Claude-zh-CN-official-backup" / "chunks"


def find_claude_package() -> Path | None:
    base = Path(r"C:\Program Files\WindowsApps")
    if not base.exists():
        return None
    candidates = sorted(base.glob("Claude_*_x64__*/app/resources/en-US.json"), reverse=True)
    if candidates:
        return candidates[0].parent.parent
    return None


def backup_file(path: Path, assets_dir: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(assets_dir)
    dst = BACKUP_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(path, dst)


PATCHES: dict[str, list[tuple[str, str]]] = {}

# === 3P settings page (c71860c77-DNv5VYLZ.js) ===
PATCHES["c71860c77-DNv5VYLZ.js"] = [
    ('"Egress Requirements"', '"\u51fa\u53e3\u8981\u6c42"'),
    ('"Gateway base URL"', '"\u81ea\u5b9a\u4e49 Base URL"'),
    ('"Gateway API key"', '"\u81ea\u5b9a\u4e49 API Key"'),
    ('"Gateway auth scheme"', '"\u81ea\u5b9a\u4e49\u8ba4\u8bc1\u65b9\u5f0f"'),
    ('"Gateway extra headers"', '"\u81ea\u5b9a\u4e49\u989d\u5916\u8bf7\u6c42\u5934"'),
    ('"Allow desktop extensions"', '"\u5141\u8bb8\u684c\u9762\u6269\u5c55"'),
    ('"Show extension directory"', '"\u663e\u793a\u6269\u5c55\u76ee\u5f55"'),
    ('"Require signed extensions"', '"\u8981\u6c42\u6269\u5c55\u7b7e\u540d"'),
    ('"Allow user-added MCP servers"', '"\u5141\u8bb8\u7528\u6237\u6dfb\u52a0 MCP \u670d\u52a1\u5668"'),
    ('"Allow Claude Code tab"', '"\u5141\u8bb8 Claude Code \u6807\u7b7e\u9875"'),
    ('"Secure VM features"', '"\u5b89\u5168\u865a\u62df\u673a\u529f\u80fd"'),
    ('"Require full VM sandbox"', '"\u8981\u6c42\u5b8c\u6574\u865a\u62df\u673a\u6c99\u76d2"'),
    ('"Allowed egress hosts"', '"\u5141\u8bb8\u7684\u51fa\u53e3\u4e3b\u673a"'),
    ('"OpenTelemetry collector endpoint"', '"OpenTelemetry \u91c7\u96c6\u5668\u7aef\u70b9"'),
    ('"OpenTelemetry exporter protocol"', '"OpenTelemetry \u5bfc\u51fa\u534f\u8bae"'),
    ('"OpenTelemetry exporter headers"', '"OpenTelemetry \u5bfc\u51fa\u8bf7\u6c42\u5934"'),
    ('"Auto-update enforcement window"', '"\u81ea\u52a8\u66f4\u65b0\u5f3a\u5236\u7a97\u53e3"'),
    ('"Block auto-updates"', '"\u7981\u6b62\u81ea\u52a8\u66f4\u65b0"'),
    ('"Skip login-mode chooser"', '"\u8df3\u8fc7\u767b\u5f55\u6a21\u5f0f\u9009\u62e9"'),
    ('"Required organization"', '"\u5fc5\u9700\u7684\u7ec4\u7ec7"'),
    ('"Inference provider"', '"\u63a8\u7406\u4f9b\u5e94\u5546"'),
    ('"Connection"', '"\u8fde\u63a5\u65b9\u5f0f"'),
    ('"Sandbox & workspace"', '"\u6c99\u76d2\u4e0e\u5de5\u4f5c\u533a"'),
    ('"Connectors & extensions"', '"\u8fde\u63a5\u5668\u4e0e\u6269\u5c55"'),
    ('"Telemetry & updates"', '"\u9065\u6d4b\u4e0e\u66f4\u65b0"'),
    ('"Usage limits"', '"\u4f7f\u7528\u9650\u5236"'),
    ('"Plugins & skills"', '"\u63d2\u4ef6\u4e0e\u6280\u80fd"'),
    ('gateway:"\u81ea\u5b9a\u4e49"', 'gateway:"\u81ea\u5b9a\u4e49"'),
    ('gateway:"Gateway"', 'gateway:"\u81ea\u5b9a\u4e49"'),
]

# === Sidebar navigation (cbc59a8af-DbOQVv5S.js) ===
PATCHES["cbc59a8af-DbOQVv5S.js"] = [
    ('label:"\u804a\u5929"', 'label:"\u804a\u5929"'),
    ('label:"Chat"', 'label:"\u804a\u5929"'),
    ('label:"Cowork"', 'label:"\u534f\u4f5c"'),
    ('label:"Code"', 'label:"\u4ee3\u7801"'),
    ('label:"Operon"', 'label:"\u5b9e\u9a8c\u5ba4"'),
    ('label:"\u9879\u76ee"', 'label:"\u9879\u76ee"'),
    ('label:"Projects"', 'label:"\u9879\u76ee"'),
    ('label:"\u5df2\u5b89\u6392"', 'label:"\u5df2\u5b89\u6392"'),
    ('label:"Scheduled"', 'label:"\u5df2\u5b89\u6392"'),
    ('label:"Live artifacts"', 'label:"\u5b9e\u65f6 Artifacts"'),
    ('label:"\u4efb\u52a1"', 'label:"\u4efb\u52a1"'),
    ('label:"Tasks"', 'label:"\u4efb\u52a1"'),
    ('label:"Pull Requests"', 'label:"\u62c9\u53d6\u8bf7\u6c42"'),
    ('label:"\u56de\u653e"', 'label:"\u56de\u653e"'),
    ('label:"Replay"', 'label:"\u56de\u653e"'),
    ('label:"\u8c03\u5ea6"', 'label:"\u8c03\u5ea6"'),
    ('label:"Dispatch"', 'label:"\u8c03\u5ea6"'),
    ('label:"\u60f3\u6cd5"', 'label:"\u60f3\u6cd5"'),
    ('label:"Ideas"', 'label:"\u60f3\u6cd5"'),
    ('label:"\u5e94\u7528"', 'label:"\u5e94\u7528"'),
    ('label:"Apps"', 'label:"\u5e94\u7528"'),
    ('label:"\u5b89\u5168"', 'label:"\u5b89\u5168"'),
    ('label:"Security"', 'label:"\u5b89\u5168"'),
    ('label:"\u81ea\u5b9a\u4e49"', 'label:"\u81ea\u5b9a\u4e49"'),
    ('label:"Customize"', 'label:"\u81ea\u5b9a\u4e49"'),
    ('label:"\u72b6\u6001"', 'label:"\u72b6\u6001"'),
    ('label:"Status"', 'label:"\u72b6\u6001"'),
    ('label:"\u73af\u5883"', 'label:"\u73af\u5883"'),
    ('label:"Environment"', 'label:"\u73af\u5883"'),
    ('chat:"\u65b0\u5efa\u804a\u5929"', 'chat:"\u65b0\u5efa\u804a\u5929"'),
    ('chat:"New chat"', 'chat:"\u65b0\u5efa\u804a\u5929"'),
    ('cowork:"\u65b0\u5efa\u4efb\u52a1"', 'cowork:"\u65b0\u5efa\u4efb\u52a1"'),
    ('cowork:"New task"', 'cowork:"\u65b0\u5efa\u4efb\u52a1"'),
    ('code:"\u65b0\u5efa\u4f1a\u8bdd"', 'code:"\u65b0\u5efa\u4f1a\u8bdd"'),
    ('code:"New session"', 'code:"\u65b0\u5efa\u4f1a\u8bdd"'),
    ('operon:"\u65b0\u5efa\u4f1a\u8bdd"', 'operon:"\u65b0\u5efa\u4f1a\u8bdd"'),
    ('operon:"New session"', 'operon:"\u65b0\u5efa\u4f1a\u8bdd"'),
    ('oo="\u672c\u5730"', 'oo="\u672c\u5730"'),
    ('oo="Local"', 'oo="\u672c\u5730"'),
    ('io="\u4e91\u7aef"', 'io="\u4e91\u7aef"'),
    ('io="Cloud"', 'io="\u4e91\u7aef"'),
    ('ro="\u8fdc\u7a0b\u63a7\u5236"', 'ro="\u8fdc\u7a0b\u63a7\u5236"'),
    ('ro="Remote Control"', 'ro="\u8fdc\u7a0b\u63a7\u5236"'),
    ('co="\u5168\u90e8"', 'co="\u5168\u90e8"'),
    ('co="All"', 'co="\u5168\u90e8"'),
    ('const Ea="\u5df2\u5b89\u6392"', 'const Ea="\u5df2\u5b89\u6392"'),
    ('const Ea="Scheduled"', 'const Ea="\u5df2\u5b89\u6392"'),
    ('["active","\u6d3b\u8dc3"]', '["active","\u6d3b\u8dc3"]'),
    ('["active","Active"]', '["active","\u6d3b\u8dc3"]'),
    ('["archived","\u5df2\u5f52\u6863"]', '["archived","\u5df2\u5f52\u6863"]'),
    ('["archived","Archived"]', '["archived","\u5df2\u5f52\u6863"]'),
    ('["all","\u5168\u90e8"]', '["all","\u5168\u90e8"]'),
    ('["all","All"]', '["all","\u5168\u90e8"]'),
    ('["0","\u5168\u90e8"]', '["0","\u5168\u90e8"]'),
    ('["0","All"]', '["0","\u5168\u90e8"]'),
    ('["1","\u0031\u5929"]', '["1","1\u5929"]'),
    ('["1","1d"]', '["1","1\u5929"]'),
    ('["3","\u0033\u5929"]', '["3","3\u5929"]'),
    ('["3","3d"]', '["3","3\u5929"]'),
    ('["7","\u0037\u5929"]', '["7","7\u5929"]'),
    ('["7","7d"]', '["7","7\u5929"]'),
    ('["14","14\u5929"]', '["14","14\u5929"]'),
    ('["14","14d"]', '["14","14\u5929"]'),
    ('["30","\u0033\u0030\u5929"]', '["30","30\u5929"]'),
    ('["30","30d"]', '["30","30\u5929"]'),
    ('"\u65e5\u671f"', '"\u65e5\u671f"'),
    ('"Date"', '"\u65e5\u671f"'),
    ('"\u65e0"', '"\u65e0"'),
    ('"None"', '"\u65e0"'),
    ('["project","\u9879\u76ee"]', '["project","\u9879\u76ee"]'),
    ('["project","Project"]', '["project","\u9879\u76ee"]'),
    ('["state","\u72b6\u6001"]', '["state","\u72b6\u6001"]'),
    ('["state","State"]', '["state","\u72b6\u6001"]'),
    ('?"\u5168\u90e8":', '?"\u5168\u90e8":'),
    ('?"All":', '?"\u5168\u90e8":'),
    ('children:"\u5df2\u56fa\u5b9a"', 'children:"\u5df2\u56fa\u5b9a"'),
    ('children:"Pinned"', 'children:"\u5df2\u56fa\u5b9a"'),
    ('children:"\u62d6\u62fd\u56fa\u5b9a"', 'children:"\u62d6\u62fd\u56fa\u5b9a"'),
    ('children:"Drag to pin"', 'children:"\u62d6\u62fd\u56fa\u5b9a"'),
    ('"Drop here"', '"\u653e\u5728\u8fd9\u91cc"'),
    ('"Let go"', '"\u677e\u5f00"'),
    ('children:["\u67e5\u770b\u5168\u90e8"', 'children:["\u67e5\u770b\u5168\u90e8"'),
    ('children:["View all"', 'children:["\u67e5\u770b\u5168\u90e8"'),
    ('title:"\u5220\u9664\u8f83\u65e7\u7684\u4f1a\u8bdd\uff1f"', 'title:"\u5220\u9664\u8f83\u65e7\u7684\u4f1a\u8bdd\uff1f"'),
    ('title:"Delete older sessions?"', 'title:"\u5220\u9664\u8f83\u65e7\u7684\u4f1a\u8bdd\uff1f"'),
    ('children:"\u6e05\u9664\u7b5b\u9009"', 'children:"\u6e05\u9664\u7b5b\u9009"'),
    ('children:"Clear filters"', 'children:"\u6e05\u9664\u7b5b\u9009"'),
    ('children:"\u6240\u6709\u9879\u76ee"', 'children:"\u6240\u6709\u9879\u76ee"'),
    ('children:"All projects"', 'children:"\u6240\u6709\u9879\u76ee"'),
    ('children:"\u5f00\u53d1\u9762\u677f"', 'children:"\u5f00\u53d1\u9762\u677f"'),
    ('children:"Dev panels"', 'children:"\u5f00\u53d1\u9762\u677f"'),
    ('children:"\u4e3b\u9898"', 'children:"\u4e3b\u9898"'),
    ('children:"Theme"', 'children:"\u4e3b\u9898"'),
    ('children:"\u5b57\u4f53"', 'children:"\u5b57\u4f53"'),
    ('children:"Font"', 'children:"\u5b57\u4f53"'),
    ('children:"\u9879\u76ee"', 'children:"\u9879\u76ee"'),
    ('children:"Project"', 'children:"\u9879\u76ee"'),
    ('const Co="\u6700\u8fd1"', 'const Co="\u6700\u8fd1"'),
    ('const Co="Recents"', 'const Co="\u6700\u8fd1"'),
    ('label:"\u6700\u8fd1\u6d3b\u52a8"', 'label:"\u6700\u8fd1\u6d3b\u52a8"'),
    ('label:"Last activity"', 'label:"\u6700\u8fd1\u6d3b\u52a8"'),
    ('label:"\u5206\u7ec4\u65b9\u5f0f"', 'label:"\u5206\u7ec4\u65b9\u5f0f"'),
    ('label:"Group by"', 'label:"\u5206\u7ec4\u65b9\u5f0f"'),
    ('"Stale after"', '"\u8fc7\u671f\u65f6\u95f4"'),
    ('"Older"', '"\u66f4\u65e9"'),
    ('"Ungrouped"', '"\u672a\u5206\u7ec4"'),
]

# === Index bundle (index-BlXy9TJN.js) - use glob pattern ===
PATCHES["index-*.js"] = [
    ('title:"\u8ba1\u5212\u4efb\u52a1"', 'title:"\u8ba1\u5212\u4efb\u52a1"'),
    ('title:"Scheduled tasks",subheader', 'title:"\u8ba1\u5212\u4efb\u52a1",subheader'),
    ('message:"\u8ba1\u5212\u4efb\u52a1\u4ec5\u5728\u8ba1\u7b97\u673a\u4fdd\u6301\u5524\u9192\u65f6\u8fd0\u884c\u3002"', 'message:"\u8ba1\u5212\u4efb\u52a1\u4ec5\u5728\u8ba1\u7b97\u673a\u4fdd\u6301\u5524\u9192\u65f6\u8fd0\u884c\u3002"'),
    ('message:"Scheduled tasks only run while your computer is awake."', 'message:"\u8ba1\u5212\u4efb\u52a1\u4ec5\u5728\u8ba1\u7b97\u673a\u4fdd\u6301\u5524\u9192\u65f6\u8fd0\u884c\u3002"'),
    ('Ifn={all:"\u5168\u90e8",active:"\u6d3b\u8dc3",archived:"\u5df2\u5f52\u6863"}', 'Ifn={all:"\u5168\u90e8",active:"\u6d3b\u8dc3",archived:"\u5df2\u5f52\u6863"}'),
    ('Ifn={all:"All",active:"Active",archived:"Archived"}', 'Ifn={all:"\u5168\u90e8",active:"\u6d3b\u8dc3",archived:"\u5df2\u5f52\u6863"}'),
    ('"No tasks yet."', '"\u8fd8\u6ca1\u6709\u4efb\u52a1\u3002"'),
    ('"No active tasks."', '"\u6ca1\u6709\u6d3b\u8dc3\u4efb\u52a1\u3002"'),
    ('"No archived tasks."', '"\u6ca1\u6709\u5df2\u5f52\u6863\u4efb\u52a1\u3002"'),
    ('children:"\u6d3b\u8dc3"}),renderRow', 'children:"\u6d3b\u8dc3"}),renderRow'),
    ('children:"Active"}),renderRow', 'children:"\u6d3b\u8dc3"}),renderRow'),
    ('children:"\u65b0\u5efa\u4efb\u52a1"', 'children:"\u65b0\u5efa\u4efb\u52a1"'),
    ('children:"New task"', 'children:"\u65b0\u5efa\u4efb\u52a1"'),
    ('?"\u65b0\u5efa\u4efb\u52a1":"\u65b0\u5efa\u804a\u5929"', '?"\u65b0\u5efa\u4efb\u52a1":"\u65b0\u5efa\u804a\u5929"'),
    ('?"New task":"New chat"', '?"\u65b0\u5efa\u4efb\u52a1":"\u65b0\u5efa\u804a\u5929"'),
    ('baseDescription:"\u65b0\u5efa\u4efb\u52a1"', 'baseDescription:"\u65b0\u5efa\u4efb\u52a1"'),
    ('baseDescription:"New task"', 'baseDescription:"\u65b0\u5efa\u4efb\u52a1"'),
    ('title:"\u4efb\u52a1"', 'title:"\u4efb\u52a1"'),
    ('nextRun:"\u4e0b\u6b21\u8fd0\u884c",name:"\u540d\u79f0"', 'nextRun:"\u4e0b\u6b21\u8fd0\u884c",name:"\u540d\u79f0"'),
    ('nextRun:"Next run",name:"Name"', 'nextRun:"\u4e0b\u6b21\u8fd0\u884c",name:"\u540d\u79f0"'),
    ('children:"3P"', 'children:"\u7b2c\u4e09\u65b9"'),
    ('label:"\u6587\u6863"', 'label:"\u6587\u6863"'),
    ('label:"Documents"', 'label:"\u6587\u6863"'),
    ('label:"\u6587\u4ef6"', 'label:"\u6587\u4ef6"'),
    ('label:"Files"', 'label:"\u6587\u4ef6"'),
    ('label:"\u540c\u6b65\u6e90"', 'label:"\u540c\u6b65\u6e90"'),
    ('label:"Sync Sources"', 'label:"\u540c\u6b65\u6e90"'),
    ('title:"\u4ece GitHub \u6dfb\u52a0\u5185\u5bb9"', 'title:"\u4ece GitHub \u6dfb\u52a0\u5185\u5bb9"'),
    ('title:"Add content from GitHub"', 'title:"\u4ece GitHub \u6dfb\u52a0\u5185\u5bb9"'),
    ('title:"\u5c06 Claude \u8fde\u63a5\u5230 Google Drive"', 'title:"\u5c06 Claude \u8fde\u63a5\u5230 Google Drive"'),
    ('title:"Connect Claude to Google Drive"', 'title:"\u5c06 Claude \u8fde\u63a5\u5230 Google Drive"'),
    ('title:"\u7ed3\u675f\u6b64\u901a\u8bdd\uff1f"', 'title:"\u7ed3\u675f\u6b64\u901a\u8bdd\uff1f"'),
    ('title:"End this call?"', 'title:"\u7ed3\u675f\u6b64\u901a\u8bdd\uff1f"'),
    ('title:"\u4ee3\u7801\u6267\u884c\u4e0e\u6587\u4ef6\u521b\u5efa"', 'title:"\u4ee3\u7801\u6267\u884c\u4e0e\u6587\u4ef6\u521b\u5efa"'),
    ('title:"Code execution and file creation"', 'title:"\u4ee3\u7801\u6267\u884c\u4e0e\u6587\u4ef6\u521b\u5efa"'),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Claude Desktop JS chunks with zh-CN labels")
    parser.add_argument("--app-dir", type=str, default=None)
    args = parser.parse_args()

    if args.app_dir:
        app_dir = Path(args.app_dir)
    else:
        app_dir = find_claude_package()

    if not app_dir or not app_dir.exists():
        raise SystemExit("Claude app directory not found.")

    assets_dir = app_dir / "resources" / "ion-dist" / "assets" / "v1"
    if not assets_dir.exists():
        raise SystemExit(f"Assets dir not found: {assets_dir}")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    total = 0

    for pattern, replacements in PATCHES.items():
        files = sorted(assets_dir.glob(pattern))
        for fpath in files:
            backup_file(fpath, assets_dir)
            content = fpath.read_text(encoding="utf-8")
            changed = 0
            for old, new in replacements:
                if old in content and old != new:
                    content = content.replace(old, new)
                    changed += 1
            if changed > 0:
                fpath.write_text(content, encoding="utf-8")
                total += changed
                print(f"  {fpath.name}: {changed} replacements")

    print(f"Done. Total chunk patches: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
