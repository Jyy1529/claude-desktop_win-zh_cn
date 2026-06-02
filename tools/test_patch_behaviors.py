#!/usr/bin/env python3
"""Regression tests for patch scripts that do not need admin access."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
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
    assert "__CLAUDE_ZH_CN_VISIBLE_TEXT_FIX_PATCH__" in content
    assert "function isThirdPartyProviderSettingsPage" in content
    assert "function syncFloatingFontButtonVisibility" in content
    assert "Manage third-party" in content
    assert "第三方供应商" in content
    assert "测试模型发现" in content
    assert "Inference provider" in content
    assert "document.getElementById(FLOATING_PANEL_ID)?.remove();" in content
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


def test_session_delete_runtime_is_injected() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn_session_delete", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text("console.log('app');\n", encoding="utf-8")

        changed = patch_chunks.patch_session_delete_runtime(assets)
        content = index.read_text(encoding="utf-8")

    assert changed == 1
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_BEGIN__" in content
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_END__" in content
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__" in content
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_VERSION__" in content
    assert 'const VERSION = "29"' in content
    assert "claude-zh-cn-session-delete-button" in content
    assert "claude-zh-cn-session-export-button" in content
    assert "claude-zh-cn-session-move-button" in content
    assert "claude-zh-cn-conversation-timeline" in content
    assert "claude-zh-cn-timeline-summary" in content
    assert "width: 28px;" in content
    assert "#${TIMELINE_ID}:hover" in content
    assert "#${TIMELINE_ID}:focus-within" in content
    assert "background: #ffffff !important;" in content
    assert "background-color: #ffffff !important;" in content
    assert "opacity: 1 !important;" in content
    assert "backdrop-filter: none !important;" in content
    assert "color-mix(in srgb, var(--bg-000, #ffffff) 88%, transparent)" not in content
    assert "claude-zh-cn-centered-layout" in content
    assert "const CENTERED_WIDTH_KEY = \"claude-zh-cn-centered-layout-width\"" in content
    assert "--claude-zh-cn-centered-width" in content
    assert "function centeredLayoutWidth" in content
    assert "function isThirdPartyProviderSettingsPage" in content
    assert "function shouldShowCenteredLayoutControls" in content
    assert "function showCenteredWidthDialog" in content
    assert "claude-zh-cn-centered-width-dialog" in content
    assert "button.style.display = showControl ? \"\" : \"none\";" in content
    assert "const root = document.querySelector(\"main,[role='main']\") || document.body;" in content
    assert "hasProviderTitle && hasProviderFields" in content
    assert "return !isThirdPartyProviderSettingsPage();" in content
    assert "/settings|account|billing|organization|admin|manage/i.test(location.pathname)" not in content
    assert "自定义居中宽度" in content
    assert "window.prompt" not in content
    assert "contextmenu" in content
    assert "dblclick" in content
    assert "claude-zh-cn-session-delete-portal-button" in content
    assert "function cleanupPortalButton" in content
    assert "function cleanupRejectedRows" in content
    assert "bindPortalHover(row);" not in content
    assert "cleanupPortalButton();" in content
    assert "!node.classList.contains(ACTION_BUTTON_CLASS)" in content
    assert ".${BUTTON_CLASS} { right: 12px; }" in content
    assert ".${EXPORT_BUTTON_CLASS} { right: 44px; }" in content
    assert ".${MOVE_BUTTON_CLASS} { right: 76px; }" in content
    assert "查看\\s*全部" in content
    assert "展开|收起|折叠" in content
    assert "[data-app-action-sidebar-thread-id]" in content
    assert "[data-thread-id]" in content
    assert "a[href^='/chat/']" in content
    assert "function looksLikeSidebarSessionRow" in content
    assert "function sessionRowRejectReason" in content
    assert "function isInsideRecentsSection" in content
    assert "function recentSectionRoots" in content
    assert "rect.height < panelRect.height * 0.5" in content
    assert "function recentsRowContainer" in content
    assert "if (current.matches?.(\"[data-app-action-sidebar-thread-id],[data-session-id],[data-thread-id],[data-conversation-id],[data-chat-id],a[href],[role='link'],[role='treeitem'],[role='listitem'],li,button,[role='button']\")) break;" in content
    assert "function meaningfulRecentsTitle" in content
    assert "function recentsTitleNodes" in content
    assert "function recentsTitleText" in content
    assert "function hasReadableRecentsTitle" in content
    assert "function isInjectedActionText" in content
    assert "function isBlankOrStatusDotRow" in content
    assert "function hasNativeRowControl" in content
    assert "function isLikelyProjectOrGroupRow" in content
    assert "function looksLikeRecentsEntryRow" in content
    assert "Gateway|第三方" in content
    assert "function sessionRowRejectReason" in content
    assert "return \"not-session-title\";" in content
    assert "max-width: calc(100% - 128px)" not in content
    assert "word-break: break-word;" in content
    assert "text-overflow: clip !important;" in content
    assert "function sessionPanelRoots" in content
    assert "function panelHasModeTabs" in content
    assert "function hasRecentsSectionHint" in content
    assert "function invalidateScanCache" in content
    assert "function scanCache" in content
    assert "document.querySelectorAll(SIDEBAR_CONTAINER_SELECTORS)" in content
    assert "document.querySelectorAll(SESSION_SIGNAL_SELECTORS)" in content
    assert "document.querySelectorAll(\"button,[role='tab'],[role='button'],a,div\")" not in content
    assert "document.querySelectorAll(\"a[href],button,[role='button'],[role='link'],[role='treeitem'],[role='listitem'],li,div\")" not in content
    assert "signalCount >= 2" in content
    assert "if (!looksLikeRecentsEntryRow(node, text) && !hasSessionSignal(node) && !isCurrentSidebarItem(node)) return;" in content
    assert "current.querySelector?.(SESSION_SIGNAL_SELECTORS)" in content
    assert "sidebarContainers.forEach((container)" in content
    assert "container.querySelectorAll(\"button,[role='tab'],[role='button'],a,div\")" in content
    assert "container.querySelectorAll(\"a[href],button,[role='button'],[role='link'],[role='treeitem'],[role='listitem'],li,div\")" in content
    assert "function isHistorySectionMarker" in content
    assert "function isNonHistorySectionMarker" in content
    assert "^(?:最近|历史)(?:\\s|$)" in content
    assert "Recent(?:s| conversations| chats)?|History" in content
    assert "if (!section.marker) return hasSessionSignal(row);" in content
    assert "SESSION_SIGNAL_SELECTORS" in content
    assert "function hasSessionSignal" in content
    assert "function isCurrentSidebarItem" in content
    assert "function isCurrentRecentsItem" in content
    assert "function recentsRowKey" in content
    assert "function preferRecentsRow" in content
    assert "const isCurrentConversation = isCurrentRecentsItem(row, text);" in content
    assert "const hasConversationSignal = hasSessionSignal(row) || isCurrentConversation;" in content
    assert "if (!hasConversationSignal && looksLikeSidebarChrome(row, text)) return \"sidebar-chrome\";" in content
    assert "return sessionRowRejectReason(row) === \"\";" in content
    assert "return \"outside-recents-section\";" in content
    assert "rect.width > 560" in content
    assert "rect.height > 240" in content
    assert "rect.height < 16" in content
    assert "rect.height > 240" in content
    assert "candidateRect.width >= 180" in content
    assert "candidateRect.width > bestRect.width" in content
    assert "if (current.matches?.(\"button,[role='button']\") && !rowId(current) && !looksLikeChatHref(rowHref(current))) continue;" in content
    assert "if (!hasConversationSignal && hasNativeRowControl(row)) return false;" not in content
    assert "return \"project-or-group\";" in content
    assert "return \"blank-or-dot\";" in content
    assert "if (!hasConversationSignal && !hasReadableRecentsTitle(row)) return false;" not in content
    assert "const titles = new Map();" in content
    assert "if (!titles.has(key)) titles.set(key, node);" in content
    assert "return [...titles.values()];" in content
    assert "return recentsTitleNodes(row).length > 0;" in content
    assert "title.length > 600" not in content
    assert "titleOrText.length > 600" not in content
    assert "\"[data-testid*='title' i]\"" not in content
    assert "\"[aria-label]\"" not in content
    assert "function titleLooksLikeProjectGroup" in content
    assert "titleLooksLikeProjectGroup(text)" in content
    assert "function titleLooksLikeFilePath" in content
    assert "titleLooksLikeFilePath(text)" in content
    assert "(Gateway|第三方|project|folder|workspace|repo|repository|项目|文件夹|仓库|工作区|警告|warning)" not in content
    assert "if (!meaningfulRecentsTitle(row, title)) return false;" in content
    assert "^(移动|导出|删除|Move|Export|Delete)$" in content
    assert "function stripInjectedActionText" in content
    assert "looksLikeSidebarTextRow(row, text)" not in content
    assert "个人插件|Personal plugins|第三方|自定义|Custom|选择文件夹|Choose folder" in content
    assert "const leftLimit = Math.min(440, window.innerWidth * 0.45);" not in content
    assert "function candidateRows" in content
    candidate_start = content.index("function candidateRows")
    candidate_end = content.index("function userQuestionNodes", candidate_start)
    candidate_block = content[candidate_start:candidate_end]
    assert "recentSectionRoots().forEach" in candidate_block
    assert "RECENTS_ROW_CANDIDATE_SELECTORS" in candidate_block
    assert "const row = recentsRowContainer(node);" in candidate_block
    assert "const normalized = normalizeRecentsRow(row);" in candidate_block
    assert "const rows = new Map();" in candidate_block
    assert "rows.set(key, preferRecentsRow(rows.get(key), normalized));" in candidate_block
    assert "return [...rows.values()];" in candidate_block
    assert "document.querySelectorAll(ROW_SELECTORS)" not in candidate_block
    assert "document.querySelectorAll(SIDEBAR_CONTAINER_SELECTORS)" not in candidate_block
    assert "function attachRow" in content
    assert "function tryNativeDelete" in content
    assert "function showUndoToast" in content
    assert "pendingDeleteTimer" in content
    assert "row.dataset.claudeZhCnPendingDelete" in content
    assert "已删除" in content
    assert "已恢复" in content
    assert "function activateExport" in content
    assert "function buildConversationMarkdown" in content
    assert "function messageRoleSignal" in content
    assert "main [data-testid*='assistant']" in content
    assert "main [data-testid*='response']" in content
    assert "main [class*='markdown']" in content
    assert "function isAssistantContentNode" in content
    assert "main [class*='font-claude-message']" in content
    assert "if (!role && lastRole === \"用户\") role = \"Claude\"" in content
    assert "function renderTimeline" in content
    assert "function scheduleTimelineRender" in content
    assert "setTimeout(renderTimeline, 320)" in content
    assert "function handlePageMutations" in content
    assert "const MAIN_CONTAINER_SELECTORS = \"main,[role='main']\"" in content
    assert "if (!section.marker) return hasSessionSignal(row);" in content
    assert "Progress" in content
    assert "new MutationObserver(handlePageMutations)" in content
    assert "nodes.some(nodeTouchesSidebar)" in content
    assert "nodes.some(nodeTouchesMain)" in content
    assert "function rememberScrollPosition" in content
    assert "function toggleCenteredLayout" in content
    assert "function activateMove" in content
    assert "function showMoveDialog" in content
    assert "function moveConversationToProject" in content
    assert "function currentConversationUuid" in content
    assert "正在读取项目列表" in content
    assert "移动接口失败" in content
    assert "chat_conversations/move_many" in content
    assert "project_uuid: projectUuid || null" in content
    assert "SIDEBAR_CONTAINER_SELECTORS" in content
    assert "revealRowActions(row)" in content
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__" in content
    assert "portalVisible" in content
    assert "scanDurationMs" in content
    assert "renderTimeline();" not in content
    assert "setTimeout(scanRows, 180)" in content
    assert "setTimeout(scanRows, 80)" not in content
    assert "}, 4000);" in content
    assert "}, 2000);" not in content
    assert "lastError" in content
    assert "MutationObserver" in content
    assert "trashIconSvg" in content
    assert "panelCount" in content
    assert "sectionCount" in content
    assert "candidateRowSamples" in content
    assert "rejectReason" in content
    assert "tag: row.tagName" in content
    assert "console.log('app');" in content


def test_session_delete_runtime_updates_marked_injection() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn_session_delete_update", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        index = assets / "index-test.js"
        index.write_text(
            "console.log('app');\n"
            "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_BEGIN__\n"
            ";(()=>{globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__ = true; const old = true;})();\n"
            "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_END__\n"
            "console.log('after');\n",
            encoding="utf-8",
        )

        changed = patch_chunks.patch_session_delete_runtime(assets)
        content = index.read_text(encoding="utf-8")

    assert changed == 1
    assert "const old = true" not in content
    assert content.count("__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_BEGIN__") == 1
    assert "claude-zh-cn-session-delete-button" in content
    assert "console.log('after');" in content


def test_session_delete_runtime_recognizes_new_session_rows_in_dom() -> None:
    completed = subprocess.run(
        ["node", str(ROOT / "tools" / "session_runtime_dom_test.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    expected_counts = {
        "before": 3,
        "after": 3,
        "currentNewButtons": 3,
        "longTitleButtons": 3,
        "slashTitleButtons": 3,
        "placeholderButtons": 3,
        "projectButtons": 0,
        "filePathTitleButtons": 0,
        "progressButtons": 0,
        "filesButtons": 0,
        "contextButtons": 0,
        "candidateCount": 6,
    }
    for key, value in expected_counts.items():
        assert payload[key] == value
    assert payload["exportHasUser"] is True
    assert payload["exportHasAssistant"] is True
    assert len(payload["exportRoles"]) == 2
    assert payload["exportRoles"][1] == "Claude"


def test_cdp_session_delete_launcher_reuses_runtime_and_evaluates_script() -> None:
    launcher = load_module("cdp_session_delete_launcher_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeCdpClient:
        def __init__(self) -> None:
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params or {}))
            if method == "Runtime.evaluate":
                return {"result": {"type": "boolean", "value": True}}
            return {}

    client = FakeCdpClient()
    script = "globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__ = true;"

    with mock.patch.object(launcher.patch_chunks_zh_cn, "session_delete_inject_script", return_value=script):
        launcher.inject_session_delete_runtime(client)

    calls = client.calls
    assert calls[0] == ("Runtime.enable", {})
    assert calls[1] == ("Page.enable", {})
    assert calls[2] == ("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    assert calls[3][0] == "Runtime.evaluate"
    assert calls[3][1]["expression"] == script
    assert calls[3][1]["awaitPromise"] is True
    assert calls[3][1]["userGesture"] is True


def test_cdp_session_delete_launcher_reads_health_state() -> None:
    launcher = load_module("cdp_session_delete_launcher_health_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeCdpClient:
        def __init__(self) -> None:
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params or {}))
            return {
                "result": {
                    "type": "object",
                    "value": {
                        "enabled": True,
                        "candidateCount": 3,
                    },
                }
            }

    client = FakeCdpClient()
    state = launcher.read_session_delete_state(client)

    assert state == {"enabled": True, "candidateCount": 3}
    assert client.calls == [
        (
            "Runtime.evaluate",
            {
                "expression": "globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ || null",
                "returnByValue": True,
            },
        )
    ]


def test_cdp_launcher_reads_runtime_health_snapshot() -> None:
    launcher = load_module("cdp_runtime_health_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeCdpClient:
        def __init__(self) -> None:
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params or {}))
            return {
                "result": {
                    "value": {
                        "sessionDelete": {"candidateCount": 2, "lastError": ""},
                        "sessionDeletePatch": True,
                        "fontPatch": True,
                        "visibleTextFixPatch": True,
                    }
                }
            }

    client = FakeCdpClient()
    health = launcher.read_runtime_health(client)

    assert health["sessionDelete"]["candidateCount"] == 2
    assert health["sessionDeletePatch"] is True
    assert health["fontPatch"] is True
    assert health["visibleTextFixPatch"] is True
    assert client.calls[0][0] == "Runtime.evaluate"
    expression = client.calls[0][1]["expression"]
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__" in expression
    assert "__CLAUDE_ZH_CN_FONT_PATCH__" in expression
    assert "__CLAUDE_ZH_CN_VISIBLE_TEXT_FIX_PATCH__" in expression
    assert client.calls[0][1]["returnByValue"] is True


def test_cdp_launcher_reads_recents_row_diagnostics() -> None:
    launcher = load_module("cdp_recents_row_diagnostics_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeCdpClient:
        def __init__(self) -> None:
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params or {}))
            return {
                "result": {
                    "value": [
                        {
                            "title": "Stitch tool and Harm",
                            "text": "Stitch tool and Harm",
                            "id": "abc123",
                            "href": "/chat/abc123",
                            "buttons": 3,
                            "rect": {"x": 10, "y": 20, "width": 300, "height": 28},
                        }
                    ]
                }
            }

    client = FakeCdpClient()
    diagnostics = launcher.read_recents_row_diagnostics(client)

    assert diagnostics[0]["buttons"] == 3
    assert diagnostics[0]["title"] == "Stitch tool and Harm"
    assert client.calls[0][0] == "Runtime.evaluate"
    expression = client.calls[0][1]["expression"]
    assert "querySelectorAll('[data-claude-zh-cn-delete-row=\"true\"]')" in expression
    assert "getBoundingClientRect" in expression
    assert "data-thread-title" in expression
    assert "data-session-id" in expression
    assert "data-conversation-id" in expression


def test_cdp_launcher_reads_candidate_row_diagnostics() -> None:
    launcher = load_module("cdp_candidate_row_diagnostics_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeCdpClient:
        def __init__(self) -> None:
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params or {}))
            return {
                "result": {
                    "value": [
                        {
                            "marked": False,
                            "text": "Long missed conversation",
                            "id": "",
                            "href": "/chat/abc123456",
                            "rect": {"x": 12, "y": 40, "width": 320, "height": 40},
                        }
                    ]
                }
            }

    client = FakeCdpClient()
    diagnostics = launcher.read_candidate_row_diagnostics(client)

    assert diagnostics[0]["href"] == "/chat/abc123456"
    assert diagnostics[0]["marked"] is False
    expression = client.calls[0][1]["expression"]
    assert "Sidebar row candidates" not in expression
    assert "marked" in expression
    assert "a[href]" in expression
    assert "getBoundingClientRect" in expression


def test_cdp_launcher_diagnose_rows_option_prints_rows(capsys) -> None:
    launcher = load_module("cdp_diagnose_rows_option_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            self.websocket_url = websocket_url
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    target = {"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1", "title": "Claude"}

    with mock.patch.object(launcher, "resolve_app_dir", return_value=ROOT), \
        mock.patch.object(launcher, "close_existing_claude"), \
        mock.patch.object(launcher, "activate_claude_appx"), \
        mock.patch.object(launcher, "launch_claude"), \
        mock.patch.object(launcher, "read_debug_port_summary", return_value={"targets": [target], "error": ""}), \
        mock.patch.object(launcher, "list_claude_processes", return_value=[{"ProcessId": 123, "ExecutablePath": "C:\\Claude\\claude.exe"}]), \
        mock.patch.object(launcher, "wait_for_target", return_value=target), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime"), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={"panelCount": 1, "sectionCount": 1, "candidateCount": 1, "attachedCount": 3, "portalButton": True, "lastError": "", "candidates": [{"tag": "A", "title": "Current project analysis", "text": "Current project analysis", "id": "", "href": "/chat/abc12345", "signal": True, "rejectReason": "", "rect": {"x": 10, "y": 20, "width": 300, "height": 32}}]}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={"sessionDeletePatch": True, "fontPatch": True, "visibleTextFixPatch": True}), \
        mock.patch.object(launcher, "read_recents_row_diagnostics", return_value=[{"title": "Current project analysis", "text": "Current project analysis", "id": "", "href": "/chat/abc12345", "buttons": 3, "rect": {"x": 10, "y": 20, "width": 300, "height": 32}}]), \
        mock.patch.object(launcher, "read_candidate_row_diagnostics", return_value=[{"marked": False, "text": "Missed row", "id": "", "href": "/chat/def67890", "tag": "A", "role": "link", "buttons": 0, "rect": {"x": 10, "y": 60, "width": 300, "height": 32}}]):
        result = launcher.main(["--app-dir", str(ROOT), "--diagnose-rows"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Recognized sidebar session rows:" in output
    assert "Claude processes: 1" in output
    assert "id=123 path=C:\\Claude\\claude.exe" in output
    assert "CDP targets discovered: 1" in output
    assert "Current project analysis" in output
    assert "buttons=3" in output
    assert "Sidebar row candidates:" in output
    assert "Missed row" in output
    assert "Runtime candidate samples:" in output
    assert "reject=''" in output
    assert "tag='A'" in output


def test_cdp_launcher_injects_webview2_args_for_direct_exe(capsys) -> None:
    launcher = load_module("cdp_direct_launch_env_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            self.websocket_url = websocket_url
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    target = {"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1", "title": "Claude"}

    with mock.patch.object(launcher, "resolve_app_dir", return_value=ROOT), \
        mock.patch.object(launcher, "close_existing_claude"), \
        mock.patch.object(launcher, "activate_claude_appx") as appx_activate, \
        mock.patch.object(launcher, "launch_claude") as direct_launch, \
        mock.patch.object(launcher, "read_debug_port_summary", return_value={"targets": [target], "error": ""}), \
        mock.patch.object(launcher, "list_claude_processes", return_value=[{"Id": 123, "Path": "C:\\Claude\\claude.exe"}]), \
        mock.patch.object(launcher, "wait_for_target", return_value=target), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime"), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={"candidateCount": 1, "attachedCount": 3, "portalButton": True, "lastError": ""}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={"sessionDeletePatch": True, "fontPatch": True, "visibleTextFixPatch": True}):
        result = launcher.main(["--app-dir", str(ROOT)])

    output = capsys.readouterr().out
    assert result == 0
    appx_activate.assert_called_once_with(port=9229)
    direct_launch.assert_not_called()
    assert "Started Claude through AppX activation" in output


def test_cdp_launcher_passes_webview2_env_to_direct_exe() -> None:
    launcher = load_module("cdp_webview2_env_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            self.websocket_url = websocket_url
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    env = launcher.build_launch_env(port=9229, base_env={"PATH": "x"})
    assert env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] == "--remote-debugging-port=9229 --remote-allow-origins=*"
    assert env["PATH"] == "x"


def test_cdp_launcher_appx_activation_uses_encoded_command_env_argument() -> None:
    launcher = load_module("cdp_appx_encoded_command_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    with mock.patch.object(launcher.subprocess, "run") as run_mock:
        run_mock.return_value = mock.Mock(returncode=0, stdout="1234\n", stderr="")
        process_id = launcher.activate_claude_appx(port=9229)

    args = run_mock.call_args.args[0]
    kwargs = run_mock.call_args.kwargs
    assert process_id == 1234
    assert "-EncodedCommand" in args
    assert "--remote-debugging-port=9229 --remote-allow-origins=*" in kwargs["env"]["CLAUDE_CDP_ARGUMENTS"]
    assert "--remote-debugging-port=9229" not in args


def test_cdp_launcher_falls_back_to_direct_exe_when_appx_has_no_target(capsys) -> None:
    launcher = load_module("cdp_appx_fallback_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            self.websocket_url = websocket_url
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    target = {"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1", "title": "Claude"}

    with mock.patch.object(launcher, "resolve_app_dir", return_value=ROOT), \
        mock.patch.object(launcher, "close_existing_claude"), \
        mock.patch.object(launcher, "activate_claude_appx", side_effect=launcher.CdpError("No CDP target found")), \
        mock.patch.object(launcher, "launch_claude") as direct_launch, \
        mock.patch.object(launcher, "wait_for_target", return_value=target), \
        mock.patch.object(launcher, "read_debug_port_summary", return_value={"targets": [target], "error": ""}), \
        mock.patch.object(launcher, "list_claude_processes", return_value=[{"Id": 123, "Path": "C:\\Claude\\claude.exe"}]), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime"), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={"candidateCount": 1, "attachedCount": 3, "portalButton": True, "lastError": ""}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={"sessionDeletePatch": True, "fontPatch": True, "visibleTextFixPatch": True}):
        result = launcher.main(["--app-dir", str(ROOT)])

    output = capsys.readouterr().out
    assert result == 0
    direct_launch.assert_called_once()
    assert "AppX activation did not expose a CDP target" in output


def test_cdp_launcher_chooses_free_port_when_requested_port_is_busy() -> None:
    launcher = load_module("cdp_free_port_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            self.websocket_url = websocket_url
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    target = {"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1", "title": "Claude"}
    debug_summary = mock.Mock(return_value={"targets": [target], "error": ""})

    with mock.patch.object(launcher, "is_port_open", side_effect=lambda host, port: port == 9229), \
        mock.patch.object(launcher, "activate_claude_appx") as appx_activate, \
        mock.patch.object(launcher, "launch_claude") as launch_mock, \
        mock.patch.object(launcher, "wait_for_target", return_value=target), \
        mock.patch.object(launcher, "close_existing_claude"), \
        mock.patch.object(launcher, "resolve_app_dir", return_value=ROOT), \
        mock.patch.object(launcher, "read_debug_port_summary", debug_summary), \
        mock.patch.object(launcher, "list_claude_processes", return_value=[]), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime"), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={"candidateCount": 1}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={"sessionDeletePatch": True}):
        appx_activate.return_value = 1234
        result = launcher.main(["--app-dir", str(ROOT), "--no-close-existing"])

    assert result == 0
    appx_activate.assert_called_once()
    assert appx_activate.call_args.kwargs["port"] != 9229
    launch_mock.assert_not_called()
    debug_summary.assert_called_once_with("127.0.0.1", appx_activate.call_args.kwargs["port"])


def test_cdp_launcher_lists_claude_like_processes() -> None:
    launcher = load_module("cdp_process_list_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    payload = [
        {
            "ProcessId": 111,
            "Name": "Claude.exe",
            "ExecutablePath": r"C:\\Program Files\\WindowsApps\\Claude_1.9659.2.0_x64__pzs8sxrjxfjjc\\app\\Claude.exe",
            "CommandLine": "Claude",
        }
    ]

    with mock.patch.object(launcher.subprocess, "run") as run_mock:
        run_mock.return_value = mock.Mock(stdout=json.dumps(payload), returncode=0)
        processes = launcher.list_claude_processes()

    assert processes[0]["ProcessId"] == 111
    assert processes[0]["Name"] == "Claude.exe"
    assert "Get-CimInstance Win32_Process" in run_mock.call_args[0][0][-1]
    assert "*Claude*" in run_mock.call_args[0][0][-1]


def test_cdp_launcher_reads_debug_port_summary_error() -> None:
    launcher = load_module("cdp_debug_port_summary_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    with mock.patch.object(launcher, "get_targets", side_effect=launcher.CdpError("timed out")):
        summary = launcher.read_debug_port_summary("127.0.0.1", 9229)

    assert summary["host"] == "127.0.0.1"
    assert summary["port"] == 9229
    assert summary["targets"] == []
    assert "timed out" in summary["error"]


def test_cdp_launcher_scans_open_debug_ports_only() -> None:
    launcher = load_module("cdp_port_scan_test", ROOT / "tools" / "cdp_session_delete_launcher.py")

    with mock.patch.object(launcher, "is_port_open", side_effect=lambda host, port: port in {9222, 9229}), \
        mock.patch.object(launcher, "read_debug_port_summary", side_effect=lambda host, port: {"host": host, "port": port, "targets": [{"title": f"target-{port}"}], "error": ""}):
        summaries = launcher.scan_debug_ports("127.0.0.1", 9222, 9230)

    assert [item["port"] for item in summaries] == [9222, 9229]
    assert summaries[1]["targets"][0]["title"] == "target-9229"


def test_cdp_launcher_closes_existing_claude_before_launch() -> None:
    launcher = load_module("cdp_close_existing_test", ROOT / "tools" / "cdp_session_delete_launcher.py")
    events = []

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            events.append(("client", websocket_url, timeout))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    with mock.patch.object(launcher, "resolve_app_dir", return_value=Path(r"C:\Claude\app")), \
        mock.patch.object(launcher, "close_existing_claude", side_effect=lambda: events.append(("close",))), \
        mock.patch.object(launcher, "activate_claude_appx", side_effect=lambda port: events.append(("activate", port))), \
        mock.patch.object(launcher, "launch_claude", side_effect=lambda app_dir, port: events.append(("launch", app_dir, port))), \
        mock.patch.object(launcher, "wait_for_target", return_value={"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1"}), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime", side_effect=lambda client: events.append(("inject",))), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={"candidateCount": 1}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={"sessionDeletePatch": True}):
        result = launcher.main(["--app-dir", r"C:\Claude\app"])

    assert result == 0
    assert events[0] == ("close",)
    assert events[1] == ("activate", 9229)


def test_cdp_launcher_can_skip_closing_existing_claude() -> None:
    launcher = load_module("cdp_skip_close_existing_test", ROOT / "tools" / "cdp_session_delete_launcher.py")
    events = []

    class FakeClient:
        def __init__(self, websocket_url, *, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    with mock.patch.object(launcher, "resolve_app_dir", return_value=Path(r"C:\Claude\app")), \
        mock.patch.object(launcher, "close_existing_claude", side_effect=lambda: events.append(("close",))), \
        mock.patch.object(launcher, "activate_claude_appx", side_effect=lambda port: events.append(("activate",))), \
        mock.patch.object(launcher, "launch_claude", side_effect=lambda app_dir, port: events.append(("launch",))), \
        mock.patch.object(launcher, "wait_for_target", return_value={"webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/1"}), \
        mock.patch.object(launcher, "CdpClient", FakeClient), \
        mock.patch.object(launcher, "inject_session_delete_runtime"), \
        mock.patch.object(launcher, "wait_for_session_delete_state", return_value={}), \
        mock.patch.object(launcher, "read_runtime_health", return_value={}):
        result = launcher.main(["--app-dir", r"C:\Claude\app", "--no-close-existing"])

    assert result == 0
    assert ("close",) not in events
    assert ("activate",) in events


def test_cdp_session_delete_powershell_wrapper_invokes_launcher() -> None:
    content = (ROOT / "claude-cdp-session-delete.ps1").read_text(encoding="utf-8-sig")

    assert "tools\\cdp_session_delete_launcher.py" in content
    assert "--port" in content
    assert "--app-dir" in content
    assert "--no-launch" in content
    assert "--diagnose-rows" in content
    assert "--scan-ports" in content
    assert "--no-close-existing" not in content
    assert "python" in content
    assert "-B" in content


def test_interactive_menu_runs_cdp_session_delete_from_install() -> None:
    content = (ROOT / "claude-zh-cn.ps1").read_text(encoding="utf-8-sig")

    assert "function Invoke-SessionDeleteCdp" in content
    assert "claude-cdp-session-delete.ps1" in content
    assert "-AppDir" in content
    assert "$appDir" in content
    install_start = content.index("function Invoke-Install")
    cdp_section = content.index("# ── CDP 注入会话删除按钮")
    install_block = content[install_start:cdp_section]
    uninstall_start = content.index("function Invoke-Uninstall")
    menu_block = content[content.index("function Show-Menu"):]

    assert "Invoke-SessionDeleteCdp" in install_block
    assert "正在执行 chunk 界面标签、字体和会话增强 patch" in install_block
    assert "正在尝试通过 CDP 追加注入会话增强" in install_block
    assert "运行时注入已随 Claude 关闭失效" in content[uninstall_start:]
    assert "[5] 注入会话删除按钮（CDP）" not in menu_block
    assert "请输入 0-4" in content
    assert "请输入 0-5" not in content


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
    assert data["aDVRC23jKg"] == "技能已移至<link>自定义</link>。"
    assert data["gshbVTjZni"] == "连接器已移至<link>自定义</link>。前往那里浏览、连接和管理连接器。"
    assert data["tgkg69DKCl"] == "你正在通过组织自己的推理提供方 ({providerDisplayName}) 运行 Claude。你的对话会发送到该提供方，而不是 Anthropic，并受你的组织与该提供方之间协议的约束。"
    assert data["ha5HbvlDOk"] == "第三方无法提供 {model}。该模型可能未在第三方上配置，或访问权限受限。"
    assert data["2GURQYNPp3"] == "组织横幅"
    assert data["jA6GVIoYuc"] == "使用来自<link>你的连接器</link>的实时数据，创建保持更新的动态工件。"
    assert data["4LM6AdGWNg"] == "思考{minutes}分钟{seconds}秒"
    assert data["vJn4YbbGd1"] == "{minutes}分钟 {seconds}秒"
    assert data["dc/vp/cKwc"] == "已过去 {minutes} 分钟"
    assert data["2Oz8jH5TAw"] == "已过去 {hours} 小时 {minutes} 分钟"
    assert data["zElqHZzItw"] == "发一个讯息…"
    assert data["5oTa1gWQsk"] == "允许的出站主机"
    assert data["CCUxBOb3va"] == "禁用 claude:// 深度链接处理"
    assert data["/CJhBsAo9W"] == "复制插件"
    assert data["0Urq2aeRGH"] == "复制技能"
    assert data["4FdR+5IiDU"] == "复制"
    assert data["4fHiNliQw2"] == "复制"
    assert data["960gdhmel/"] == "复制配置"
    assert data["uTR9Wyzw/s"] == "复制..."


def test_frontend_organization_config_translations() -> None:
    data = json.loads((ROOT / "resources" / "frontend-zh-CN.json").read_text(encoding="utf-8-sig"))

    assert data["KtZV9pULgo"] == "连接"
    assert data["6T78KTXhBM"] == "自定义推理标头"
    assert data["jU4z+3Uk7+"] == "模型发现"
    assert data["g8BMTiGHB6"] == "凭据类型"
    assert data["CwADEGuH8H"] == "工作区限制"
    assert data["y/6sGoi9YF"] == "连接器与扩展"
    assert data["Ba3MtjwP5h"] == "遥测与更新"
    assert data["KZbdbvaU9V"] == "插件与技能"
    assert data["xY1EE6Ndl5"] == "出站要求"
    assert data["Lpq+8Nau5X"].startswith("你的网络防火墙必须允许的主机")
    assert data["JQs8c3pGcl"] == "第三方 URL"
    assert data["NA4SBfPMeA"] == "第三方 API 密钥"
    assert data["tmwK1KjFte"] == "第三方认证方案"
    assert data["+zZ6KeQPTP"] == "显示横幅"
    assert data["47aHGyWFid"] == "单行显示，溢出时截断。最多 200 个字符。"
    assert data["HuIg1+BeMP"] == "可选 HTTPS URL。设置后，横幅文本会变成链接。"
    assert data["WbM+LbvT9p"] == "六位十六进制颜色值 (#RRGGBB)。将完全按配置应用，不会适配主题。"
    assert data["DnXPcFgmqb"] == "辅助脚本"
    assert data["8c6iN3kiDX"] == "交互式登录"
    assert data["K9q4XwLJd2"] == "MCP 服务器"
    assert data["rhPs8UtdHq"] == "工具名称"
    assert data["slIZF8X6Sk"] == "+ 添加服务器策略"
    assert data["QredwIagLx"] == "遥测配置冲突"
    assert data["fO2poeLmt6"] == "OpenTelemetry 导出器标头"
    assert data["7+U8x5o7v9"] == "本地 MCP 服务器"
    assert data["GtTy+dALpT"] == "你的 MCP 服务器"
    assert data["LMGYthp0hQ"] == "使用限制"
    assert data["OsIhLl7KpD"] == "链接 URL（可选）"
    assert data["HAlOn1ZsuY"] == "名称"
    assert data["KwHBKRwf8M"] == "连接方式"
    assert data["9a9+wwWy4u"] == "Headers"
    assert data["Wm+KUdH7c0"] == "Headers"
    assert data["x+MG25XWVf"] == "Headers 辅助脚本"
    assert data["StnRZmM3Xn"] == "绝对路径"
    assert data["uSQ/bLKBIp"] == "工具策略"
    assert data["iFhBHMeCjp"] == "工具名称"
    assert data["bS7WElxrrh"] == "锁定特定工具的审批状态。未列出的工具仍由用户控制。"
    assert data["N5hOiMqiZn"] == "自动注册（动态客户端注册）"
    assert data["SZXkm24sDA"] == "使用自己的客户端"
    assert data["xWvR0pm1jC"] == "流式 HTTP"
    assert data["micfwa1L0h"] == "SSE（旧版）"
    assert data["JJVljnyegG"] == "本地命令（stdio）"
    assert "Authorization: Bearer" in data["WsT/E/qNoC"]
    assert "x-api-key" in data["WsT/E/qNoC"]
    assert data["EvwX+qKToR"] == "服务器名称"
    assert "{url}" in data["xWiIy0pAlB"]


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
        (resources / "en-US.json").write_text(
            json.dumps(
                {
                    "7fdcqxofEs": "Exit",
                    "DQTgg21B7g": "Show App",
                    "dKX0bpR+a2": "Quit",
                    "oQuOiX24pp": "Quit",
                    "keep": "Keep",
                }
            ),
            encoding="utf-8",
        )
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
        en_us = json.loads((resources / "en-US.json").read_text(encoding="utf-8-sig"))
        assert en_us["7fdcqxofEs"] == "退出"
        assert en_us["DQTgg21B7g"] == "显示应用"
        assert en_us["dKX0bpR+a2"] == "退出"
        assert en_us["oQuOiX24pp"] == "退出"
        assert en_us["keep"] == "Keep"
        assert (localappdata / "Claude-zh-CN-official-backup" / "json-only" / "zh-CN.json").exists()
        assert (localappdata / "Claude-zh-CN-official-backup" / "json-only" / "en-US.json").exists()


def test_json_patch_translates_main_process_debugger_labels() -> None:
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
        index.write_text(
            'const labels=["Enable Main Process Debugger","Record Performance Trace","Write Main Process Heap Snapshot","Record Memory Trace (auto-stop)"];',
            encoding="utf-8",
        )

        old_localappdata = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        os.environ["APPDATA"] = str(appdata)
        try:
            patch_json = load_module("patch_windowsapps_json_only_main_process", ROOT / "patch_windowsapps_json_only.py")
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

        content = index.read_text(encoding="utf-8")

    assert result == 0
    assert "启用主进程调试器" in content
    assert "记录性能跟踪" in content
    assert "写入主进程堆快照" in content
    assert "记录内存跟踪（自动停止）" in content


def test_desktop_en_us_fallback_patch_only_updates_tray_labels() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        localappdata = tmp_path / "localappdata"
        app_resources = tmp_path / "Claude" / "app" / "resources"
        app_resources.mkdir(parents=True)
        en_us_path = app_resources / "en-US.json"
        en_us_path.write_text(
            json.dumps(
                {
                    "7fdcqxofEs": "Exit",
                    "DQTgg21B7g": "Show App",
                    "dKX0bpR+a2": "Quit",
                    "oQuOiX24pp": "Quit",
                    "PW5U8NgTto": "Open MCP Log File...",
                }
            ),
            encoding="utf-8",
        )

        old_localappdata = os.environ.get("LOCALAPPDATA")
        os.environ["LOCALAPPDATA"] = str(localappdata)
        try:
            patch_json = load_module("patch_windowsapps_json_only_fallback", ROOT / "patch_windowsapps_json_only.py")
            changed = patch_json.patch_desktop_en_us_fallback(app_resources)
        finally:
            if old_localappdata is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = old_localappdata

        data = json.loads(en_us_path.read_text(encoding="utf-8-sig"))

    assert changed == 4
    assert data["7fdcqxofEs"] == "退出"
    assert data["DQTgg21B7g"] == "显示应用"
    assert data["dKX0bpR+a2"] == "退出"
    assert data["oQuOiX24pp"] == "退出"
    assert data["PW5U8NgTto"] == "Open MCP Log File..."


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


def test_assets_tree_injects_session_tools_runtime() -> None:
    patch_chunks = load_module("patch_chunks_zh_cn_session_tools_auto", ROOT / "patch_chunks_zh_cn.py")

    with tempfile.TemporaryDirectory() as tmp:
        resources = Path(tmp) / "resources"
        assets = resources / "ion-dist" / "assets" / "v1"
        assets.mkdir(parents=True)
        index = assets / "index-test.js"
        index.write_text("console.log('app');\n", encoding="utf-8")

        changed = patch_chunks.patch_assets_tree(resources)
        content = index.read_text(encoding="utf-8")

    assert changed == 2
    assert "__CLAUDE_ZH_CN_FONT_PATCH__" in content
    assert "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__" in content
    assert "claude-zh-cn-session-delete-button" in content
    assert "claude-zh-cn-session-export-button" in content
    assert "claude-zh-cn-conversation-timeline" in content
    assert 'const VERSION = "29"' in content


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
                    'const f_discard="Discard Changes";',
                    'const f_discard_lower="Discard changes";',
                    'const f_discard_question="Discard changes?";',
                    'const f_apply="Apply Changes";',
                    'const f_apply_lower="Apply changes";',
                    'const model_hint="Shown in the model picker. Leave blank to auto-format from the ID.";',
                    'const model_variant="Offer 1M-context variant";',
                    'const model_id="Model ID";',
                    'const surfaces="Allowed surfaces";',
                    'const cowork_hint="Enable the Cowork tab. Claude works on longer tasks like research, analysis, and documents.";',
                    'const code_hint="Enable the Code tab. Claude writes and runs code.";',
                    'const restrictions="General restrictions";',
                    'const restrictions_hint="These apply regardless of which surfaces are enabled.";',
                    'const egress="Egress Requirements";',
                    'const host_hint="Hostnames the agent\'s tools may reach from the Cowork and Code tabs. Also surfaced under Egress Requirements.";',
                    'const help_a="Applies to both the Cowork and Code tabs.";',
                    'const help_b="Only affects **tool calls**. Inference and MCP traffic are covered by their own allowlists elsewhere.";',
                    'const help_c="When unset, only the inference endpoint is reachable from the sandbox; the agent\'s package installs (pip/npm) and web fetches will fail with a 403.";',
                    'const help_d="Accepts exact hostnames (`api.github.com`), wildcards (`*.corp.com` matches one subdomain level), and `*` to allow all.";',
                    'const help_e="Wildcards don\'t cross schemes. `*.corp.com` matches `docs.corp.com` but not `corp.com` itself; add both if you need the apex.";',
                    'const help_f="IP literals and localhost always resolve regardless of this list; this is a public-egress filter, not a sandbox.";',
                    'const help_g="Hosts you add here also need to be open on your network firewall. See Egress Requirements for the full allowlist.";',
                    'const help_body={body:"Applies to both the Cowork and Code tabs.\\n\\nOnly affects **tool calls**. Inference and MCP traffic are covered by their own allowlists elsewhere.\\n\\nWhen unset, only the inference endpoint is reachable from the sandbox; the agent\'s package installs (pip/npm) and web fetches will fail with a 403.\\n\\nAccepts exact hostnames (`api.github.com`), wildcards (`*.corp.com` matches one subdomain level), and `*` to allow all.\\n\\nWildcards don\'t cross schemes. `*.corp.com` matches `docs.corp.com` but not `corp.com` itself; add both if you need the apex.\\n\\nIP literals and localhost always resolve regardless of this list; this is a public-egress filter, not a sandbox.\\n\\nHosts you add here also need to be open on your network firewall. See Egress Requirements for the full allowlist."};',
                    'const unsaved_title="Discard unsaved changes?";',
                    'const unsaved_body="This configuration has changes that haven\'t been saved. They will be lost.";',
                    'const keep_editing="Keep editing";',
                    'const keep_editing_default={defaultMessage:"Keep editing",id:"nZCHBxEAlK"};',
                    'const discard_id={defaultMessage:"Discard",id:"nmpevlUATU"};',
                    'const contrast="High-contrast dark theme";',
                    'const contrast_hint="Use a darker, near-black background when dark mode is on.";',
                    'const theme_size=[{value:"s",label:a.formatMessage({defaultMessage:"Small",id:"BPnT3TVya+"})},{value:"m",label:a.formatMessage({defaultMessage:"Medium",id:"ovJ26CKo4Q"})},{value:"l",label:a.formatMessage({defaultMessage:"Large",id:"/06iwcQHPz"})}];',
                    'const workflows="Dynamic workflows";',
                    'const workflows_hint="Let Claude run multiple agents in parallel for complex tasks. Workflows can use a lot of your usage limit quickly.";',
                    'const workflows_warning="Dynamic workflows run many subagents in parallel and can use a lot of your usage limit. Stop them any time from the <link>tasks panel</link>.";',
                    'const workflows_disabled="Dynamic workflows are disabled by your organization\'s policy.";',
                    'const cowork_files="Cowork files";',
                    'const cowork_files_hint="Your artifacts and scheduled tasks are stored at {path}.";',
                    'const cowork_files_change="Change location for Cowork files?";',
                    'const cowork_files_copy="Copy files to {location} and restart the app. Your existing files will remain in {previousLocation}.";',
                    'const provider_error="{provider} returned an error";',
                    'const provider_error_body="Your connection works, but the provider rejected a test request. Often a model-access or quota issue.";',
                    'const g="Connectors have moved to Customize. Head there to browse, connect, and manage them.";',
                    'const g2="Connectors have moved to <link>Customize</link>. Head there to browse, connect, and manage them.";',
                    'const h="Skills have moved to Customize.";',
                    'const h2="Skills have moved to <link>Customize</link>.";',
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
                    'const s_linked="Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic\'s guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>";',
                    'const t="You\u2019re running Claude through your organization\u2019s own inference provider (cc.freemodel.dev). Your conversations are sent there, not to Anthropic, and are governed by your organization\u2019s agreement with that provider.";',
                    'const u="Live artifacts";',
                    'const u_old="工件";',
                    'const u_label={label:"实时工件"};',
                    'const gateway="Your gateway couldn\u2019t serve {model}. This model may not be configured on your gateway, or access may be restricted.";',
                    'const project_nav={label:"Projects"};',
                    'const project_old={label:"项目"};',
                    'const project_group=["project","Project"];',
                    'const project_group_old=["project","项目"];',
                    'const v="Generate code, documents, and designs in a dedicated window alongside your conversation.";',
                    'const w1="Create dynamic artifacts that stay up-to-date using live data from your connectors.";',
                    'const w2="Create dynamic artifacts that stay up-to-date using live data from <link>your connectors</link>.";',
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
                    'const policy={allow:"allow",ask:"ask",blocked:"blocked"};',
                    'const greeting="Hi, I\'m Claude. How can I help you today?";',
                    'const greeting_bad="Hi, I\'m Claude. How can I helpyou today?";',
                    'const dev_menu="Enable Main Process Debugger";',
                    'const perf="Record Performance Trace";',
                    'const heap="Write Main Process Heap Snapshot";',
                    'const memory="Record Memory Trace (auto-stop)";',
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
        assert "Discard Changes" not in content
        assert "Discard changes" not in content
        assert "Discard changes?" not in content
        assert "Apply Changes" not in content
        assert "Apply changes" not in content
        assert "\u653e\u5f03\u66f4\u6539" in content
        assert "\u653e\u5f03\u66f4\u6539\uff1f" in content
        assert "\u5e94\u7528\u66f4\u6539" in content
        for untranslated in [
            "Shown in the model picker. Leave blank to auto-format from the ID.",
            "Offer 1M-context variant",
            "Model ID",
            "Allowed surfaces",
            "Enable the Cowork tab. Claude works on longer tasks like research, analysis, and documents.",
            "Enable the Code tab. Claude writes and runs code.",
            "General restrictions",
            "These apply regardless of which surfaces are enabled.",
            "Egress Requirements",
            "Hostnames the agent's tools may reach from the Cowork and Code tabs. Also surfaced under Egress Requirements.",
            "Applies to both the Cowork and Code tabs.",
            "Only affects **tool calls**. Inference and MCP traffic are covered by their own allowlists elsewhere.",
            "When unset, only the inference endpoint is reachable from the sandbox; the agent's package installs (pip/npm) and web fetches will fail with a 403.",
            "Accepts exact hostnames (`api.github.com`), wildcards (`*.corp.com` matches one subdomain level), and `*` to allow all.",
            "Wildcards don't cross schemes. `*.corp.com` matches `docs.corp.com` but not `corp.com` itself; add both if you need the apex.",
            "IP literals and localhost always resolve regardless of this list; this is a public-egress filter, not a sandbox.",
            "Hosts you add here also need to be open on your network firewall. See Egress Requirements for the full allowlist.",
            "Discard unsaved changes?",
            "This configuration has changes that haven't been saved. They will be lost.",
            "Keep editing",
            "Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic's guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>",
            'defaultMessage:"Discard",id:"nmpevlUATU"',
            "High-contrast dark theme",
            "Use a darker, near-black background when dark mode is on.",
            'defaultMessage:"Small",id:"BPnT3TVya+"',
            'defaultMessage:"Medium",id:"ovJ26CKo4Q"',
            'defaultMessage:"Large",id:"/06iwcQHPz"',
            "Dynamic workflows",
            "Let Claude run multiple agents in parallel for complex tasks. Workflows can use a lot of your usage limit quickly.",
            "Dynamic workflows run many subagents in parallel and can use a lot of your usage limit. Stop them any time from the <link>tasks panel</link>.",
            "Dynamic workflows are disabled by your organization's policy.",
            "Cowork files",
            "Your artifacts and scheduled tasks are stored at {path}.",
            "Change location for Cowork files?",
            "Copy files to {location} and restart the app. Your existing files will remain in {previousLocation}.",
            "{provider} returned an error",
            "Your connection works, but the provider rejected a test request. Often a model-access or quota issue.",
        ]:
            assert untranslated not in content
        for translated in [
            "\u663e\u793a\u5728\u6a21\u578b\u9009\u62e9\u5668\u4e2d",
            "\u63d0\u4f9b 1M \u4e0a\u4e0b\u6587\u53d8\u4f53",
            "\u6a21\u578b ID",
            "\u5141\u8bb8\u7684\u529f\u80fd\u754c\u9762",
            "\u542f\u7528 Cowork \u6807\u7b7e\u9875",
            "\u542f\u7528 Code \u6807\u7b7e\u9875",
            "\u901a\u7528\u9650\u5236",
            "\u51fa\u53e3\u8981\u6c42",
            "\u653e\u5f03\u672a\u4fdd\u5b58\u7684\u66f4\u6539\uff1f",
            "\u7ee7\u7eed\u7f16\u8f91",
            'defaultMessage:"\u653e\u5f03",id:"nmpevlUATU"',
            "\u9ad8\u5bf9\u6bd4\u5ea6\u6df1\u8272\u4e3b\u9898",
            'defaultMessage:"\u5c0f",id:"BPnT3TVya+"',
            'defaultMessage:"\u4e2d",id:"ovJ26CKo4Q"',
            'defaultMessage:"\u5927",id:"/06iwcQHPz"',
            "\u52a8\u6001\u5de5\u4f5c\u6d41",
            "Cowork \u6587\u4ef6",
            "\u66f4\u6539 Cowork \u6587\u4ef6\u4f4d\u7f6e\uff1f",
            "Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa<aupLink>Anthropic \u7684\u6307\u5357</aupLink>\u3002<learnMoreLink>\u4e86\u89e3\u66f4\u591a</learnMoreLink>",
            "{provider} \u8fd4\u56de\u9519\u8bef",
        ]:
            assert translated in content
        assert "界面字体" in content
        assert "对话记录文字大小" in content
        assert "代码外观" in content
        assert "本地会话" in content
        assert "默认启用远程控制" in content
        assert "连接器已移至" in content
        assert "连接器已移至<link>自定义</link>" in content
        assert "技能已移至" in content
        assert "技能已移至<link>自定义</link>" in content
        assert "第三方无法提供 {model}" in content
        assert "Create dynamic artifacts that stay up-to-date using live data from <link>your connectors</link>." not in content
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
        assert "使用来自<link>你的连接器</link>的实时数据，创建保持更新的动态工件。" in content
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
        assert "你好，我是 Claude。今天我能帮你什么？" in content
        assert "Hi, I'm Claude. How can I help" not in content
        assert "启用主进程调试器" in content
        assert "记录性能跟踪" in content
        assert "写入主进程堆快照" in content
        assert "记录内存跟踪（自动停止）" in content
        assert 'const policy={allow:"allow",ask:"ask",blocked:"blocked"};' in content
        assert '["allow", "允许"]' in content
        assert '["ask", "询问"]' in content
        assert '["blocked", "已阻止"]' in content


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
        (resources / "app.asar").write_text("current-official-asar", encoding="utf-8")
        (assets / "index-test.js").write_text("patched", encoding="utf-8")

        backup_base = localappdata / "Claude-zh-CN-official-backup"
        backup_json = backup_base / "json-only"
        backup_chunks = backup_base / "chunks"
        backup_json.mkdir(parents=True)
        backup_chunks.mkdir(parents=True)
        (backup_json / "zh-CN.json").write_text('{"original":true}', encoding="utf-8")
        (backup_json / "app.asar").write_text("stale-backed-up-asar", encoding="utf-8")
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
        assert (resources / "app.asar").read_text(encoding="utf-8") == "current-official-asar"
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
