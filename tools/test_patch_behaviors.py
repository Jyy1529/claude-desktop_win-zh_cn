#!/usr/bin/env python3
"""Regression tests for patch scripts that do not need admin access."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_font_runtime_replaces_legacy_injection() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text(
            "console.log('app');\n"
            ";(()=>{\n"
            "  if (globalThis.__CLAUDE_ZH_CN_FONT_PATCH__) return;\n"
            "  globalThis.__CLAUDE_ZH_CN_FONT_PATCH__ = true;\n"
            "  const PANEL_ID = \"claude-zh-cn-font-panel\";\n"
            "})();\n"
            "console.log('after legacy');\n",
            encoding="utf-8",
        )

        changed = patch_chunks.patch_font_runtime(assets)
        content = index.read_text(encoding="utf-8")

    assert changed == 1
    assert "__CLAUDE_ZH_CN_FONT_PATCH_BEGIN__" in content
    assert "__CLAUDE_ZH_CN_FONT_PATCH_END__" in content
    assert "claude-zh-cn-font-floating-panel" in content
    assert "data-font-layout" in content
    assert "中文字体预览" in content
    assert "function shouldFixTextNode" in content
    assert "if (!scope) return false" in content
    assert "document.body.innerText ||" not in content
    assert "body *" not in content
    assert "[class], [class] *" not in content
    assert ":not([aria-hidden=\"true\"])" in content
    assert ":not([class*=\"icon\" i])" in content
    assert "console.log('after legacy');" in content


def test_font_runtime_updates_marked_injection() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text(
            "console.log('app');\n"
            "// __CLAUDE_ZH_CN_FONT_PATCH_BEGIN__\n"
            ";(()=>{globalThis.__CLAUDE_ZH_CN_FONT_PATCH__ = true; const old = true;})();\n"
            "// __CLAUDE_ZH_CN_FONT_PATCH_END__\n"
            "console.log('after');\n",
            encoding="utf-8",
        )

        changed = patch_chunks.patch_font_runtime(assets)
        content = index.read_text(encoding="utf-8")

    assert changed == 1
    assert "const old = true" not in content
    assert content.count("__CLAUDE_ZH_CN_FONT_PATCH_BEGIN__") == 1
    assert "console.log('after');" in content


def test_frontend_resource_key_translations() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))

    assert data["Mn8BAEIrHk"] == "当前连续使用天数"
    assert data["SHC19EXDV4"] == "分支"
    assert data["puLNUJezx6"] == "固定"
    assert data["aNzS6KFyd2"] == "无衬线聊天字体"
    assert data["oZJlI1WvFj"] == "无衬线"


def test_restore_removes_font_mirror_and_locale() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        appdata = Path(tmp) / "appdata"
        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.json"
        config_path.write_text(
            json.dumps({"locale": "zh-CN", "claudeZhCnFont": {"mode": "preset"}, "keep": True}),
            encoding="utf-8",
        )

        old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = str(appdata)
        try:
            restore = load_module("restore_claude_zh_cn_windowsapps", ROOT / "restore_claude_zh_cn_windowsapps.py")
            changed = restore.remove_locale()
            data = json.loads(config_path.read_text(encoding="utf-8"))
        finally:
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

    assert changed is True
    assert data == {"keep": True}


def test_json_patch_copies_resources_and_patches_locale_whitelist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        (resources / "ion-dist" / "i18n" / "statsig").mkdir(parents=True)
        assets.mkdir(parents=True)
        (resources / "zh-CN.json").write_text('{"old":true}', encoding="utf-8")
        (resources / "ion-dist" / "i18n" / "zh-CN.json").write_text('{"old":true}', encoding="utf-8")
        (resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json").write_text('{"old":true}', encoding="utf-8")
        index = assets / "index-test.js"
        index.write_text('const locales=["en-US","fr-FR"];', encoding="utf-8")
        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text('{"keep":true}', encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_json = load_module("patch_windowsapps_json_only", ROOT / "patch_windowsapps_json_only.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_windowsapps_json_only.py", "--app-dir", str(app_dir)]
            try:
                result = patch_json.main()
            finally:
                os.sys.argv = old_argv
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

        assert result == 0
        assert '"zh-CN"' in index.read_text(encoding="utf-8")
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8"))["locale"] == "zh-CN"
        assert json.loads((resources / "zh-CN.json").read_text(encoding="utf-8-sig"))
        assert (localappdata / "Claude-zh-CN-official-backup" / "json-only" / "zh-CN.json").exists()


def test_restore_restores_json_and_chunk_backups() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        (resources / "zh-CN.json").write_text('{"patched":true}', encoding="utf-8")
        (assets / "index-test.js").write_text("patched", encoding="utf-8")

        backup_base = localappdata / "Claude-zh-CN-official-backup"
        backup_json = backup_base / "json-only"
        backup_chunks = backup_base / "chunks"
        backup_json.mkdir(parents=True)
        backup_chunks.mkdir(parents=True)
        (backup_json / "zh-CN.json").write_text('{"original":true}', encoding="utf-8")
        (backup_chunks / "index-test.js").write_text("original", encoding="utf-8")
        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text(
            json.dumps({"locale": "zh-CN", "claudeZhCnFont": {"mode": "preset"}, "keep": True}),
            encoding="utf-8",
        )

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            restore = load_module("restore_for_restore_test", ROOT / "restore_claude_zh_cn_windowsapps.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["restore_claude_zh_cn_windowsapps.py", "--app-dir", str(app_dir)]
            try:
                result = restore.main()
            finally:
                os.sys.argv = old_argv
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

        assert result == 0
        assert json.loads((resources / "zh-CN.json").read_text(encoding="utf-8")) == {"original": True}
        assert (assets / "index-test.js").read_text(encoding="utf-8") == "original"
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8")) == {"keep": True}


def main() -> int:
    tests = [
        test_font_runtime_replaces_legacy_injection,
        test_font_runtime_updates_marked_injection,
        test_frontend_resource_key_translations,
        test_restore_removes_font_mirror_and_locale,
        test_json_patch_copies_resources_and_patches_locale_whitelist,
        test_restore_restores_json_and_chunk_backups,
    ]
    for test in tests:
        test()
        print(f"OK {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
