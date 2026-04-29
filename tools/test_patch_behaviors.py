#!/usr/bin/env python3
"""Regression tests for patch scripts that do not need admin access."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from unittest import mock
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
    assert data["6gT5ZWvI0K"] == "模型：{model}"
    assert data["eLHIIAgqml"] == "提供模型 ID，例如 /model claude-sonnet-4-5"
    assert "Haiku" in data["YUXhG8b7by"] or "Sonnet" in data["YUXhG8b7by"]
    assert "Opus" in data["R+afEr3zIZ"]
    assert "Opus" in data["//ixi/rP/O"]


def test_brand_and_model_names_stay_in_english() -> None:
    frontend = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    desktop = json.loads((ROOT / "resources" / "desktop-zh-CN.json").read_text(encoding="utf-8-sig"))

    assert "Claude Code" in frontend["+4sNMiL2sh"]
    assert "GitHub" in frontend["+b6F7XjKgE"]
    assert "Slack" in frontend["0AmHBAraPC"]
    assert "Google Workspace" in frontend["0AmHBAraPC"]
    assert "Chrome" in frontend["1XvgYxOFV4"]
    assert "Claude" in frontend["+4Rjm0+q1q"]
    assert "Claude.ai" in frontend["3CIha9zDJ/"]
    assert "MCP" in frontend["0DZwzm8wVp"]
    assert "Claude" in frontend["1XvgYxOFV4"]
    assert "Claude Code" in desktop["+qat3UyOdy"]
    assert "Claude" in desktop["CizRPROPWo"]
    assert "Chrome" in desktop["5ASYey6oV6"]
    assert "MCP" in desktop["uKCcuVd1Yt"]
    assert "Claude.ai" in desktop["0vttuC3ieI"]


def test_desktop_menu_translations() -> None:
    data = json.loads((ROOT / "resources" / "desktop-zh-CN.json").read_text(encoding="utf-8-sig"))

    assert data["EfdnINFnIz"] == "文件"
    assert data["/PgA81GVOD"] == "编辑"
    assert data["LCWUQ/4Fu6"] == "查看"
    assert data["0tZLEYF8mJ"] == "开发者"
    assert data["pWXxZASpOB"] == "帮助"
    assert data["PW5U8NgTto"] == "打开 MCP 日志文件…"
    assert data["uKCcuVd1Yt"] == "重新加载 MCP 配置"
    assert data["9GRz7bC+rr"] == "管理第三方供应商…"
    assert data["JOf7G+dCf1"] == "打开应用配置文件…"
    assert data["K5GtyaPaw/"] == "打开开发者配置文件…"
    assert data["RTg057HE1D"] == "显示开发者工具"
    assert data["STqYpFr7p4"] == "显示所有开发者工具"


def test_powershell_has_manual_app_dir_fallback() -> None:
    content = (ROOT / "claude-zh-cn.ps1").read_text(encoding="utf-8-sig")
    assert "function Resolve-ClaudeAppPath" in content
    assert "function Resolve-ClaudePackage" in content
    assert "function Set-ClaudePackageManual" in content
    assert "请输入 Claude app 目录" in content
    assert "manual:" in content
    assert "[3] 手动指定 Claude app 目录" in content


def test_noninteractive_scripts_support_app_dir() -> None:
    install = (ROOT / "install-windowsapps-json-only.ps1").read_text(encoding="utf-8-sig")
    restore = (ROOT / "restore-windowsapps-zh-cn.ps1").read_text(encoding="utf-8-sig")
    assert "param(" in install and "[string]$AppDir" in install
    assert "--app-dir \"$AppDir\"" in install
    assert "param(" in restore and "[string]$AppDir" in restore
    assert "--app-dir \"$AppDir\"" in restore


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


def test_restore_remove_locale_permission_error_is_retried() -> None:
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
            restore = load_module("restore_claude_zh_cn_windowsapps_retry", ROOT / "restore_claude_zh_cn_windowsapps.py")
            original_write_text = Path.write_text
            write_calls = {"count": 0}

            def flaky_write_text(self, text, encoding=None):
                if self == config_path and write_calls["count"] == 0:
                    write_calls["count"] += 1
                    raise PermissionError("denied")
                return original_write_text(self, text, encoding=encoding)

            with mock.patch.object(Path, "write_text", flaky_write_text):
                changed = restore.remove_locale()
                data = json.loads(config_path.read_text(encoding="utf-8"))
        finally:
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

    assert write_calls["count"] == 1
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


def test_json_patch_whitelist_write_permission_error_is_retried() -> None:
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
            patch_json = load_module("patch_windowsapps_json_only_retry", ROOT / "patch_windowsapps_json_only.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_windowsapps_json_only.py", "--app-dir", str(app_dir)]
            write_calls = {"count": 0}
            original_write_text = Path.write_text

            def flaky_write_text(self, text, encoding=None):
                if self == index and write_calls["count"] == 0:
                    write_calls["count"] += 1
                    raise PermissionError("denied")
                return original_write_text(self, text, encoding=encoding)

            try:
                with mock.patch.object(Path, "write_text", flaky_write_text):
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
        assert write_calls["count"] == 1
        assert '"zh-CN"' in index.read_text(encoding="utf-8")
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8"))["locale"] == "zh-CN"


def test_json_patch_resource_copy_permission_error_is_retried() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        (resources / "ion-dist" / "i18n" / "statsig").mkdir(parents=True)
        assets.mkdir(parents=True)
        desktop_dst = resources / "zh-CN.json"
        desktop_dst.write_text('{"old":true}', encoding="utf-8")
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
            patch_json = load_module("patch_windowsapps_json_only_copy_retry", ROOT / "patch_windowsapps_json_only.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_windowsapps_json_only.py", "--app-dir", str(app_dir)]
            original_copy2 = patch_json.shutil.copy2
            copy_calls = {"count": 0}

            def flaky_copy2(src, dst, *args, **kwargs):
                if Path(dst) == desktop_dst and copy_calls["count"] == 0:
                    copy_calls["count"] += 1
                    raise PermissionError("denied")
                return original_copy2(src, dst, *args, **kwargs)

            try:
                with mock.patch.object(patch_json.shutil, "copy2", flaky_copy2):
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
        assert copy_calls["count"] == 1
        assert json.loads(desktop_dst.read_text(encoding="utf-8-sig"))


def test_json_patch_backup_copy_permission_error_is_retried() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        (resources / "ion-dist" / "i18n" / "statsig").mkdir(parents=True)
        assets.mkdir(parents=True)
        desktop_dst = resources / "zh-CN.json"
        desktop_dst.write_text('{"old":true}', encoding="utf-8")
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
            patch_json = load_module("patch_windowsapps_json_only_backup_retry", ROOT / "patch_windowsapps_json_only.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_windowsapps_json_only.py", "--app-dir", str(app_dir)]
            original_copy2 = patch_json.shutil.copy2
            backup_dst = localappdata / "Claude-zh-CN-official-backup" / "json-only" / "zh-CN.json"
            copy_calls = {"count": 0}

            def flaky_copy2(src, dst, *args, **kwargs):
                if Path(dst) == backup_dst and copy_calls["count"] == 0:
                    copy_calls["count"] += 1
                    raise PermissionError("denied")
                return original_copy2(src, dst, *args, **kwargs)

            try:
                with mock.patch.object(patch_json.shutil, "copy2", flaky_copy2):
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
        assert copy_calls["count"] == 1
        assert backup_dst.exists()


def test_chunk_patch_permission_error_is_retried() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        assets = app_dir / "resources" / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        index = assets / "index-test.js"
        index.write_text("console.log('app');\n", encoding="utf-8")
        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text("{}", encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_chunks = load_module("patch_chunks_zh_cn_retry", ROOT / "patch_chunks_zh_cn.py")
            original_write_text = Path.write_text
            write_calls = {"index": 0, "config": 0}

            def flaky_write_text(self, text, encoding=None):
                if self == index and write_calls["index"] == 0:
                    write_calls["index"] += 1
                    raise PermissionError("denied")
                if self == config_dir / "config.json" and write_calls["config"] == 0:
                    write_calls["config"] += 1
                    raise PermissionError("denied")
                return original_write_text(self, text, encoding=encoding)

            with mock.patch.object(Path, "write_text", flaky_write_text):
                changed = patch_chunks.patch_font_runtime(assets)
                mirrored = patch_chunks.set_font_config_mirror()
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

        assert write_calls["index"] == 1
        assert write_calls["config"] == 1
        assert changed == 1
        assert mirrored is True
        assert "__CLAUDE_ZH_CN_FONT_PATCH__" in index.read_text(encoding="utf-8")
        data = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
        assert data["claudeZhCnFont"]["mode"] == "preset"


def test_chunk_patch_backup_copy_permission_error_is_retried() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn_backup_retry", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text("console.log('app');\n", encoding="utf-8")

        backup_dst = Path(os.environ.get("LOCALAPPDATA", str(assets))) / "Claude-zh-CN-official-backup" / "chunks" / "index-test.js"
        original_copy2 = patch_chunks.shutil.copy2
        copy_calls = {"count": 0}

        def flaky_copy2(src, dst, *args, **kwargs):
            if Path(dst).name == backup_dst.name and copy_calls["count"] == 0:
                copy_calls["count"] += 1
                raise PermissionError("denied")
            return original_copy2(src, dst, *args, **kwargs)

        with mock.patch.object(patch_chunks.shutil, "copy2", flaky_copy2):
            patch_chunks.backup_file(index, assets)

    assert copy_calls["count"] == 1


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


def test_restore_copy_permission_error_is_retried() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        resources.mkdir(parents=True)
        target = resources / "zh-CN.json"
        target.write_text('{"patched":true}', encoding="utf-8")

        backup_json = localappdata / "Claude-zh-CN-official-backup" / "json-only"
        backup_json.mkdir(parents=True)
        (backup_json / "zh-CN.json").write_text('{"original":true}', encoding="utf-8")

        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text('{"keep":true}', encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            restore = load_module("restore_claude_zh_cn_windowsapps_copy_retry", ROOT / "restore_claude_zh_cn_windowsapps.py")
            original_copy2 = restore.shutil.copy2
            copy_calls = {"count": 0}

            def flaky_copy2(src, dst, *args, **kwargs):
                if Path(dst) == target and copy_calls["count"] == 0:
                    copy_calls["count"] += 1
                    raise PermissionError("denied")
                return original_copy2(src, dst, *args, **kwargs)

            with mock.patch.object(restore.shutil, "copy2", flaky_copy2):
                restored = restore.restore_from(backup_json, resources)
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata

        assert copy_calls["count"] == 1
        assert restored == 1
        assert json.loads(target.read_text(encoding="utf-8")) == {"original": True}
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8")) == {"keep": True}


def main() -> int:
    tests = [
        test_font_runtime_replaces_legacy_injection,
        test_font_runtime_updates_marked_injection,
        test_frontend_resource_key_translations,
        test_brand_and_model_names_stay_in_english,
        test_desktop_menu_translations,
        test_powershell_has_manual_app_dir_fallback,
        test_noninteractive_scripts_support_app_dir,
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
