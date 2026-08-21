#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正 frontend-zh-CN.json 里的短词误译。

这些词在英文里一词多义，机器翻译缺少界面上下文就会选错义项：
Auto 被当成汽车、Manual 被当成手册、Light/Dark 被当成光和黑暗。

用法:
    python fix-zh-translations.py            # 应用修正
    python fix-zh-translations.py --dry-run  # 只看会改什么
    python fix-zh-translations.py --check    # 校验是否已全部修正（CI 用），有残留则退出码 1
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ZH_PATH = Path(__file__).resolve().parent.parent / "resources" / "frontend-zh-CN.json"

# (键, 期望的英文原文, 错误译法, 正确译法)
# 带英文原文是为了防止 Claude 更新后键被复用到别的文案上——
# 键是内容哈希，理论上原文变了键就变，但显式校验更安全。
FIXES: list[tuple[str, str, str, str]] = [
    ("NXI/XLSYwc", "Auto",        "汽车",   "自动"),
    ("xn3dIBnIVy", "Auto",        "汽车",   "自动"),
    ("M59JhXXku8", "Manual",      "手册",   "手动"),
    ("bEP1fZ8uSe", "Manual",      "手册",   "手动"),
    ("Bzy/54I5zQ", "Manual only", "仅手册", "仅手动"),
    ("vErdXkZBiq", "Manual only", "仅手册", "仅手动"),
    ("3cc4CtJM5h", "Light",       "光",     "浅色"),
    ("tOdNiYuuag", "Dark",        "黑暗",   "深色"),
]

# 新版 en-US.json 里已不存在的旧键，其译文是明显误译，直接删除
STALE_KEYS = ["JU8+dFfEFi", "gqoZMYUd/j"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只显示将要修改的内容")
    ap.add_argument("--check", action="store_true", help="校验模式：有未修正项则退出码 1")
    args = ap.parse_args()

    if not ZH_PATH.exists():
        print(f"[X] 找不到翻译文件: {ZH_PATH}")
        return 1

    zh = json.loads(ZH_PATH.read_text(encoding="utf-8"))

    applied, skipped, missing = [], [], []

    for key, en_expect, wrong, right in FIXES:
        if key not in zh:
            missing.append((key, en_expect, "键不存在"))
            continue
        current = zh[key]
        if current == right:
            skipped.append((key, right))
            continue
        if current != wrong:
            # 译文既不是已知错误也不是期望值，可能上游改过——不覆盖，只报告
            missing.append((key, en_expect, f"译文意外: {current!r}"))
            continue
        if not args.dry_run and not args.check:
            zh[key] = right
        applied.append((key, en_expect, wrong, right))

    removed = []
    for key in STALE_KEYS:
        if key in zh:
            removed.append((key, zh[key]))
            if not args.dry_run and not args.check:
                del zh[key]

    # ---- 报告 ----
    if applied:
        print(f"需修正 {len(applied)} 处:")
        for key, en, wrong, right in applied:
            print(f"  {en!r:<14} {wrong!r} -> {right!r}   ({key})")
    if removed:
        print(f"\n删除 {len(removed)} 个旧键（新版 en 已无对应文案）:")
        for key, val in removed:
            print(f"  {key} = {val!r}")
    if skipped:
        print(f"\n已是正确译法，跳过 {len(skipped)} 处")
    if missing:
        print(f"\n[!] {len(missing)} 处需人工确认:")
        for key, en, why in missing:
            print(f"  {key} (en={en!r}): {why}")

    if args.check:
        if applied or removed:
            print("\n[X] 存在未修正项")
            return 1
        print("\n[OK] 全部已修正")
        return 0

    if args.dry_run:
        print("\n(--dry-run，未写入)")
        return 0

    if not applied and not removed:
        print("无需修改")
        return 0

    backup = ZH_PATH.with_suffix(".json.bak")
    if not backup.exists():
        shutil.copy2(ZH_PATH, backup)
        print(f"\n已备份原文件: {backup.name}")

    # 原子写入：先写临时文件再替换，避免写一半损坏翻译文件
    tmp = ZH_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(zh, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    # 写完立刻验证能否解析回来
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(ZH_PATH)

    print(f"[OK] 已写入 {ZH_PATH.name}（{len(zh)} 个键）")
    print("     重装汉化后生效: powershell -NoProfile -ExecutionPolicy Bypass -File claude-zh-update.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
