#!/usr/bin/env python3
"""Regression tests for patch scripts that do not need admin access."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from unittest import mock
from pathlib import Path

import best_effort_io


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
    assert "nav,aside" in content
    assert "Create dynamic artifacts that stay up-to-date using live data from your connectors." in content
    assert "使用来自连接器的实时数据，创建保持更新的动态工件。" in content
    assert "VISIBLE_TEXT_SUBSTRING_FIXES" in content
    assert "\\bArtifacts\\b" in content
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


def test_frontend_custom_label_is_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["WHcySsrbNk"] == "自定义"


def test_frontend_google_connector_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["7qYF66c9/s"] == "Google 文档"
    assert data["GKdaNw6TF5"] == "Google 云端硬盘"
    assert data["kjenxGoM59"] == "Google 日历"


def test_frontend_platform_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["97ZyLDa56/"] == "Linux（x64）"


def test_frontend_short_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["/XN7yFRPEj"] == "持续集成"
    assert data["SlryxY5wVT"] == "持续集成 {done}/{total}"
    assert data["WGlDvlB8U9"] == "本月至今"
    assert data["t0clKd0XbN"] == "Windows（arm64）"
    assert data["UfB5Krvt4G"] == "Windows（x64）"


def test_frontend_google_brand_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["+1VvTZ4Z9R"] == "Google Play 商店"
    assert data["4b42RZpF6C"] == "GitHub 企业版"
    assert data["g+MI9/sOCK"] == "Google 标志"
    assert data["lzgH40+3EL"] == "谷歌"


def test_frontend_foundry_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["LPT6OcwxnK"] == "Azure AI 工坊"
    assert data["dyvIkP3vGQ"] == "Microsoft 工坊"


def test_frontend_cloud_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["GIh+053to7"] == "谷歌 Vertex AI"
    assert data["Iu7EbVgyNK"] == "谷歌 Vertex AI"
    assert data["QlBsxMNFtc"] == "谷歌云"
    assert data["3dX6WT/wMl"] == "亚马逊云科技"
    assert data["voYGE9Q356"] == "亚马逊 Bedrock"


def test_frontend_provider_entry_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["2hslSeuDXe"] == "谷歌邮箱"
    assert data["VCayjOoQll"] == "MCP"
    assert data["wRHZIadJ0A"] == "工坊"


def test_frontend_remaining_english_usage_labels_are_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["5RasbgfW2t"] == "研究实验室：{before, number} → {after, number}"
    assert data["FPiM1VWudZ"] == "高级版：{before, number} → {after, number}"
    assert data["FvNS5NICAF"] == "非营利版：{before, number} → {after, number}"
    assert data["TvOAFWIHcJ"] == "标准版：{before, number} → {after, number}"
    assert data["gcZsjEP/3M"] == "高级非营利版：{before, number} → {after, number}"
    assert data["u6WcCZIyyg"] == "研究实验室高级版：{before, number} → {after, number}"
    assert data["Stq39HkM0l"] == "你使用的 token 约为 {book} 的 {times} 倍。"
    assert data["m4VXIz3JrC"] == "你使用的 token 数量大约相当于 {book}。"


def test_frontend_text_size_extreme_label_is_translated_as_extra_high() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["kDEj60CmLq"] == "超高"
    assert data["kkjl2vQekD"] == "超高"


def test_frontend_webhook_label_is_translated() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))
    assert data["GnZZHNfzw2"] == "网络钩子"
    assert data["hf7LJXNeKT"] == "网络钩子"


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


def test_powershell_status_distinguishes_cleanup_states() -> None:
    content = (ROOT / "claude-zh-cn.ps1").read_text(encoding="utf-8-sig")

    assert "HasArtifacts" in content
    assert "State" in content
    assert "中文补丁状态: 已安装（locale 未设置）" in content
    assert "中文补丁状态: 部分残留" in content
    assert "中文补丁状态: 已卸载（备份保留）" in content
    assert "if (-not $s.HasArtifacts -and -not $s.Backup)" in content


def test_readme_no_longer_describes_dual_locale_modes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "keep-locale" not in readme
    assert "no-locale" not in readme
    assert "保留 locale" not in readme
    assert "不保留 locale" not in readme
    assert "install-windows-zh-cn" not in readme
    assert "uninstall-windows-zh-cn" not in readme
    assert "patch_claude_zh_cn_windowsapps.py" not in readme
    assert "`locale=zh-CN`" in readme
    assert "当前脚本会直接修改已安装 Claude app 目录" in readme


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
        index_2 = assets / "index-other.js"
        index_2.write_text('const locales=["en-US","de-DE"];', encoding="utf-8")
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
        assert '"zh-CN"' in index_2.read_text(encoding="utf-8")
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8"))["locale"] == "zh-CN"
        assert json.loads((resources / "zh-CN.json").read_text(encoding="utf-8-sig"))
        assert (localappdata / "Claude-zh-CN-official-backup" / "json-only" / "zh-CN.json").exists()


def test_json_patch_creates_config_and_locale_when_missing() -> None:
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

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_json = load_module("patch_windowsapps_json_only_missing_config", ROOT / "patch_windowsapps_json_only.py")
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

        config_path = appdata / "Claude-3p" / "config.json"
        assert result == 0
        assert config_path.exists()
        assert json.loads(config_path.read_text(encoding="utf-8")) == {"locale": "zh-CN"}


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


def test_chunk_patch_translates_keep_awake_label() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        assets = app_dir / "resources" / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        index = assets / "index-test.js"
        index.write_text('const label="Keep awake";', encoding="utf-8")

        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text("{}", encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_chunks = load_module("patch_chunks_zh_cn_keep_awake", ROOT / "patch_chunks_zh_cn.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_chunks_zh_cn.py", "--app-dir", str(app_dir)]
            try:
                result = patch_chunks.main()
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
        assert "Keep awake" not in index.read_text(encoding="utf-8")
        assert "保持唤醒" in index.read_text(encoding="utf-8")


def test_chunk_patch_translates_custom_label() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        assets = app_dir / "resources" / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        index = assets / "index-test.js"
        index.write_text('const label="Custom";', encoding="utf-8")

        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text("{}", encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_chunks = load_module("patch_chunks_zh_cn_custom_label", ROOT / "patch_chunks_zh_cn.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_chunks_zh_cn.py", "--app-dir", str(app_dir)]
            try:
                result = patch_chunks.main()
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
        assert 'const label="Custom";' not in index.read_text(encoding="utf-8")
        assert "自定义" in index.read_text(encoding="utf-8")


def test_chunk_patch_translates_settings_hardcoded_ui() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        assets = app_dir / "resources" / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        index = assets / "index-test.js"
        sidebar = assets / "cbc59a8af-DbOQVv5S.js"
        index.write_text(
            "\n".join(
                [
                    'const a="Theme";',
                    'const b="Interface font";',
                    'const c="Transcript text size";',
                    'const d="Code appearance";',
                    'const e="Local sessions";',
                    'const f="Enable remote control by default";',
                    'const g="Connectors have moved to Customize. Head there to browse, connect, and manage them.";',
                    'const h="Skills have moved to Customize.";',
                    'const i="Configured model not available";',
                    'const j="Open Setup";',
                    'const k="Sort by";',
                    'const l="Alphabetically";',
                    'const m="Created time";',
                    'const n="Custom groups";',
                    'const o="Avatar";',
                    'const p="Instructions for Claude";',
                    'const q="Preferences";',
                    'const r="What Anthropic doesn\u2019t see";',
                    'const s="Claude will keep these in mind across chats and Cowork within Anthropic\'s guidelines. Learn more";',
                    'const t="You\u2019re running Claude through your organization\u2019s own inference provider (cc.freemodel.dev). Your conversations are sent there, not to Anthropic, and are governed by your organization\u2019s agreement with that provider.";',
                    'const u="Live artifacts";',
                    'const u_old="工件";',
                    'const u_label={label:"实时工件"};',
                    'const project_nav={label:"Projects"};',
                    'const project_old={label:"项目"};',
                    'const project_group=["project","Project"];',
                    'const project_group_old=["project","项目"];',
                    'const v="Generate code, documents, and designs in a dedicated window alongside your conversation.";',
                    'const w1="Create dynamic artifacts that stay up-to-date using live data from your connectors.";',
                    'const w="Tasks";',
                    'const x="Active";',
                    'const y="Archived";',
                    'const z="All";',
                    'const aa="Local";',
                    'const ab="Cloud";',
                    'const ac="Environment";',
                    'const ad="Recents";',
                    'const ae="Run tasks on a schedule or whenever you need them. Type /schedule in any existing task to set one up.";',
                    'const af="Create your first scheduled task";',
                    'const ag="Daily brief";',
                    'const ah="Weekly review";',
                    'const ai="New Projects";',
                    'const aj="All projects";',
                    'const ak="View all";',
                    'const al="None";',
                    'const am="1d";',
                    'const an="3d";',
                    'const ao="7d";',
                    'const ap="30d";',
                    'const mode="system";',
                ]
            ),
            encoding="utf-8",
        )
        sidebar.write_text('const nav={label:"项目"};\n', encoding="utf-8")

        config_dir = appdata / "Claude-3p"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text("{}", encoding="utf-8")

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_chunks = load_module("patch_chunks_zh_cn_settings_ui", ROOT / "patch_chunks_zh_cn.py")
            old_argv = os.sys.argv[:]
            os.sys.argv = ["patch_chunks_zh_cn.py", "--app-dir", str(app_dir)]
            try:
                result = patch_chunks.main()
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

        content = index.read_text(encoding="utf-8")
        sidebar_content = sidebar.read_text(encoding="utf-8")
        assert result == 0
        assert "界面字体" in content
        assert "对话记录文字大小" in content
        assert "代码外观" in content
        assert "本地会话" in content
        assert "默认启用远程控制" in content
        assert "连接器已移至" in content
        assert "技能已移至" in content
        assert "配置的模型不可用" in content
        assert "打开设置向导" in content
        assert "排序方式" in content
        assert "按字母顺序" in content
        assert "创建时间" in content
        assert "自定义分组" in content
        assert "头像" in content
        assert "给 Claude 的指令" in content
        assert "偏好设置" in content
        assert "Anthropic 不会看到的内容" in content
        assert "Claude 会在聊天和 Cowork 中记住这些内容" in content
        assert "组织自己的推理提供方" in content
        assert "实时工件" in content
        assert "生成代码、文档和设计" in content
        assert "创建保持更新的动态工件" in content
        assert "任务" in content
        assert "活跃" in content
        assert "已归档" in content
        assert "全部" in content
        assert "本地" in content
        assert "云端" in content
        assert "环境" in content
        assert "最近" in content
        assert "按计划或在需要时运行任务" in content
        assert "创建你的第一个计划任务" in content
        assert "每日简报" in content
        assert "每周回顾" in content
        assert "新建项目" in content
        assert "所有项目" in content
        assert "查看全部" in content
        assert "无" in content
        assert "1天" in content
        assert "3天" in content
        assert "7天" in content
        assert "30天" in content
        assert "Live artifacts" in content
        assert 'const u_old="Artifacts";' in content
        assert 'const u_label={label:"Live artifacts"};' in content
        assert 'const project_nav={label:"Projects"};' in content
        assert 'const project_old={label:"Projects"};' in content
        assert 'const project_group=["project","Project"];' in content
        assert 'const project_group_old=["project","Project"];' in content
        assert 'label:"项目"' not in content
        assert '["project","项目"]' not in content
        assert 'label:"Projects"' in sidebar_content
        assert 'label:"项目"' not in sidebar_content
        assert 'const mode="system";' in content


def test_chunk_patch_backup_copy_permission_error_is_retried() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn_backup_retry", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        localappdata = Path(tmp) / "localappdata"
        old_localappdata = os.environ.get("LOCALAPPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text("console.log('app');\n", encoding="utf-8")

        backup_dst = localappdata / "Claude-zh-CN-official-backup" / "chunks" / "index-test.js"
        original_copy2 = best_effort_io.shutil.copy2
        copy_calls = {"count": 0}

        def flaky_copy2(src, dst, *args, **kwargs):
            if Path(dst) == backup_dst and copy_calls["count"] == 0:
                copy_calls["count"] += 1
                raise PermissionError("denied")
            return original_copy2(src, dst, *args, **kwargs)

        try:
            patch_chunks.BACKUP_ROOT = backup_dst.parent
            with mock.patch.object(best_effort_io.shutil, "copy2", flaky_copy2):
                patch_chunks.backup_file(index, assets)
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata

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
        assert not (resources / "zh-CN.json").exists()
        assert (assets / "index-test.js").read_text(encoding="utf-8") == "original"


def test_restore_main_removes_installed_zh_cn_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)

        (resources / "zh-CN.json").write_text('{"patched":true}', encoding="utf-8")
        (resources / "ion-dist" / "i18n").mkdir(parents=True)
        (resources / "ion-dist" / "i18n" / "zh-CN.json").write_text('{"patched":true}', encoding="utf-8")
        (resources / "ion-dist" / "i18n" / "statsig").mkdir(parents=True)
        (resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json").write_text('{"patched":true}', encoding="utf-8")
        (assets / "index-test.js").write_text('const locales=["en-US","fr-FR","zh-CN"];', encoding="utf-8")

        backup_base = localappdata / "Claude-zh-CN-official-backup"
        backup_json = backup_base / "json-only"
        backup_chunks = backup_base / "chunks"
        backup_json.mkdir(parents=True)
        backup_chunks.mkdir(parents=True)
        (backup_json / "ion-dist" / "assets" / "v1").mkdir(parents=True)
        (backup_json / "ion-dist" / "assets" / "v1" / "index-test.js").write_text('const locales=["en-US","fr-FR"];', encoding="utf-8")
        (backup_chunks / "ion-dist" / "assets" / "v1").mkdir(parents=True)
        (backup_chunks / "ion-dist" / "assets" / "v1" / "index-test.js").write_text('const locales=["en-US","fr-FR","zh-CN"];', encoding="utf-8")

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
            restore = load_module("restore_for_cleanup_test", ROOT / "restore_claude_zh_cn_windowsapps.py")
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
        assert not (resources / "zh-CN.json").exists()
        assert not (resources / "ion-dist" / "i18n" / "zh-CN.json").exists()
        assert not (resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json").exists()
        assert '"zh-CN"' not in (assets / "index-test.js").read_text(encoding="utf-8")
        assert json.loads((config_dir / "config.json").read_text(encoding="utf-8")) == {"keep": True}


def test_restore_ignores_legacy_full_patch_when_current_backups_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)

        (resources / "zh-CN.json").write_text('{"patched":true}', encoding="utf-8")
        (assets / "index-test.js").write_text('children:"新建任务"', encoding="utf-8")

        backup_base = localappdata / "Claude-zh-CN-official-backup"
        backup_json = backup_base / "json-only"
        backup_chunks = backup_base / "chunks"
        backup_json.mkdir(parents=True)
        backup_chunks.mkdir(parents=True)
        (backup_chunks / "index-test.js").write_text('children:"New task"', encoding="utf-8")

        legacy_full = backup_base / "Claude_legacy"
        (legacy_full / "ion-dist" / "assets" / "v1").mkdir(parents=True)
        (legacy_full / "ion-dist" / "assets" / "v1" / "index-test.js").write_text('children:"新建任务"', encoding="utf-8")

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
            restore = load_module("restore_ignores_legacy_full_patch", ROOT / "restore_claude_zh_cn_windowsapps.py")
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
        assert 'children:"New task"' in (assets / "index-test.js").read_text(encoding="utf-8")
        assert 'children:"新建任务"' not in (assets / "index-test.js").read_text(encoding="utf-8")


def test_restore_reverts_stale_chunk_backup_translations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        appdata = tmp_path / "appdata"
        app_dir = tmp_path / "Claude" / "app"
        resources = app_dir / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)

        stale_content = 'children:"\u65b0\u5efa\u4efb\u52a1";children:"\u9879\u76ee";label:"\u5df2\u5b89\u6392";'
        (assets / "index-test.js").write_text(stale_content, encoding="utf-8")

        backup_base = localappdata / "Claude-zh-CN-official-backup"
        backup_chunks = backup_base / "chunks"
        backup_chunks.mkdir(parents=True)
        (backup_chunks / "index-test.js").write_text(stale_content, encoding="utf-8")

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
            restore = load_module("restore_reverts_stale_chunk_backup", ROOT / "restore_claude_zh_cn_windowsapps.py")
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

        content = (assets / "index-test.js").read_text(encoding="utf-8")
        assert result == 0
        assert 'children:"New task"' in content
        assert 'children:"\u65b0\u5efa\u4efb\u52a1"' not in content
        assert 'children:"\u9879\u76ee"' not in content
        assert 'label:"\u5df2\u5b89\u6392"' not in content


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
        test_powershell_status_distinguishes_cleanup_states,
        test_readme_no_longer_describes_dual_locale_modes,
        test_restore_removes_font_mirror_and_locale,
        test_chunk_patch_translates_keep_awake_label,
        test_json_patch_copies_resources_and_patches_locale_whitelist,
        test_json_patch_creates_config_and_locale_when_missing,
        test_restore_restores_json_and_chunk_backups,
        test_restore_main_removes_installed_zh_cn_artifacts,
        test_restore_ignores_legacy_full_patch_when_current_backups_exist,
        test_restore_reverts_stale_chunk_backup_translations,
    ]
    for test in tests:
        test()
        print(f"OK {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
