#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"

FILES = [
    RESOURCES / "desktop-zh-CN.json",
    RESOURCES / "frontend-zh-CN.json",
    RESOURCES / "statsig-zh-CN.json",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")
        data = load_json(path)
        if not isinstance(data, dict):
            raise SystemExit(f"Expected JSON object at: {path}")
        print(f"OK {path.name}: {len(data)} keys")

    print("All resource files validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
