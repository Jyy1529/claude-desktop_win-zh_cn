#!/usr/bin/env python3
"""Patch JS chunks with Chinese UI labels.

This script applies safe string replacements to hardcoded UI labels
in Claude Desktop's JS bundle files. It backs up original files before
modifying and only replaces exact string patterns.

Run after patch_windowsapps_json_only.py.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


BACKUP_ROOT = Path(os.environ["LOCALAPPDATA"]) / "Claude-zh-CN-official-backup" / "chunks"
CONFIG_PATH = Path(os.environ["APPDATA"]) / "Claude-3p" / "config.json"
FONT_KEY = "claudeZhCnFont"


FONT_PRESETS = [
    {
        "id": "windows-modern",
        "label": "Windows 现代默认",
        "family": "Microsoft YaHei UI, Microsoft YaHei, Segoe UI, sans-serif",
    },
    {
        "id": "yahei",
        "label": "微软雅黑",
        "family": "Microsoft YaHei, Microsoft YaHei UI, Segoe UI, sans-serif",
    },
    {
        "id": "dengxian",
        "label": "等线",
        "family": "DengXian, Microsoft YaHei UI, Segoe UI, sans-serif",
    },
]


def font_inject_script() -> str:
    presets_json = json.dumps(FONT_PRESETS, ensure_ascii=False, separators=(",", ":"))
    body = f'''
;(()=>{{
  if (globalThis.__CLAUDE_ZH_CN_FONT_PATCH__) return;
  globalThis.__CLAUDE_ZH_CN_FONT_PATCH__ = true;
  globalThis.__CLAUDE_ZH_CN_VISIBLE_TEXT_FIX_PATCH__ = true;
  const KEY = "{FONT_KEY}";
  const PRESETS = {presets_json};
  const DEFAULT = PRESETS[0].family;
  const STYLE_ID = "claude-zh-cn-font-style";
  const PANEL_ID = "claude-zh-cn-font-panel";
  const FLOATING_PANEL_ID = "claude-zh-cn-font-floating-panel";
  const FAB_ID = "claude-zh-cn-font-fab";
  const FALLBACK = "Microsoft YaHei UI, Microsoft YaHei, Segoe UI, Arial, sans-serif";
  const state = {{ fontFaceUrl: "" }};

  const readConfig = () => {{
    try {{
      const raw = localStorage.getItem(KEY);
      if (!raw) return {{ mode: "preset", presetId: "windows-modern", family: DEFAULT }};
      const data = JSON.parse(raw);
      return {{
        mode: data.mode || "preset",
        presetId: data.presetId || "windows-modern",
        family: data.family || DEFAULT,
        fontName: data.fontName || "",
        importedName: data.importedName || "",
        importedCss: data.importedCss || ""
      }};
    }} catch {{
      return {{ mode: "preset", presetId: "windows-modern", family: DEFAULT }};
    }}
  }};

  const saveConfig = (cfg) => {{
    const current = readConfig();
    const next = {{ ...current, ...cfg }};
    localStorage.setItem(KEY, JSON.stringify(next));
    applyFont(next);
    return next;
  }};

  const cssFamily = (cfg) => {{
    if (cfg.mode === "custom" && cfg.fontName) return `"${{cfg.fontName.replaceAll('"', '\\"')}}", ${{FALLBACK}}`;
    if (cfg.mode === "imported" && cfg.importedName) return `"${{cfg.importedName.replaceAll('"', '\\"')}}", ${{FALLBACK}}`;
    const preset = PRESETS.find((item) => item.id === cfg.presetId);
    return (preset && preset.family) || cfg.family || DEFAULT;
  }};

  function applyFont(cfg = readConfig()) {{
    let style = document.getElementById(STYLE_ID);
    if (!style) {{
      style = document.createElement("style");
      style.id = STYLE_ID;
      document.head.appendChild(style);
    }}
    const family = cssFamily(cfg);
    const importedCss = cfg.mode === "imported" && cfg.importedCss ? cfg.importedCss : "";
    style.textContent = `
${{importedCss}}
:root {{ --claude-zh-cn-font-family: ${{family}}; }}
html, body, #root, #__next, #app {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
body :is(div,span,p,h1,h2,h3,h4,h5,h6,a,button,label,legend,li,dt,dd,th,td,caption,small,strong,em,b,i,input,textarea,select,option,[role="dialog"],[role="menu"],[role="tooltip"],[role="listbox"],[role="option"],[contenteditable="true"]):not(svg):not(svg *):not([aria-hidden="true"]):not([data-icon]):not([class*="icon" i]):not([class*="lucide" i]):not([class*="codicon" i]):not([class*="material" i]):not([class*="fa-" i]) {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
pre, code, kbd, samp, .monaco-editor, .monaco-editor *, .xterm, .xterm * {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
svg text, svg tspan {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
`;
    document.documentElement.style.setProperty("--claude-zh-cn-font-family", family);
    window.dispatchEvent(new CustomEvent("claude-zh-cn-font-changed", {{ detail: cfg }}));
  }}

  const labelStyle = "display:block;margin:8px 0 4px;font-size:12px;color:var(--text-300,#666);";
  const inputStyle = "width:100%;box-sizing:border-box;border:1px solid var(--border-300,#ddd);border-radius:8px;padding:8px;background:var(--bg-000,#fff);color:inherit;";
  const buttonStyle = "border:1px solid var(--border-300,#ddd);border-radius:8px;padding:6px 9px;background:var(--bg-100,#f7f7f7);color:inherit;cursor:pointer;";
  const panelStyle = "margin:0;padding:10px;border:1px solid var(--border-200,#e6e6e6);border-radius:12px;background:var(--bg-000,#fff);box-shadow:0 12px 30px rgba(0,0,0,.13);backdrop-filter:blur(10px);";
  const mutedText = "font-size:11px;line-height:1.4;color:var(--text-300,#666);";
  const sectionStyle = "padding:9px;border:1px solid var(--border-200,#e6e6e6);border-radius:10px;background:var(--bg-050,#fafafa);";
  const sectionAltStyle = "padding:9px;border:1px solid var(--border-300,#ddd);border-radius:10px;background:var(--bg-000,#fff);";
  const previewStyle = "padding:12px;border:1px solid var(--border-300,#ddd);border-radius:12px;background:linear-gradient(180deg,var(--bg-000,#fff),var(--bg-050,#fafafa));min-height:130px;";
  const segmentBase = "flex:1;min-width:0;border:0;border-radius:7px;padding:6px 7px;background:transparent;color:var(--text-300,#666);cursor:pointer;font-size:11px;font-weight:600;text-align:center;transition:background .12s ease,color .12s ease,box-shadow .12s ease;";
  const segmentActive = "background:var(--bg-000,#fff);color:var(--text-500,#111);box-shadow:0 1px 2px rgba(0,0,0,.07),inset 0 0 0 1px var(--border-300,#ddd);";

  const VISIBLE_TEXT_FIXES = new Map([
    ["auto", "自动"],
    ["Auto", "自动"],
    ["light", "浅色"],
    ["Light", "浅色"],
    ["dark", "深色"],
    ["Dark", "深色"],
    ["sans", "无衬线"],
    ["Sans", "无衬线"],
    ["New task", "新建任务"],
    ["New session", "新建会话"],
    ["Projects", "项目"],
    ["New Projects", "新建项目"],
    ["Scheduled", "已安排"],
    ["Customize", "自定义"],
    ["Status", "状态"],
    ["Project", "项目"],
    ["Last activity", "最近活动"],
    ["Group by", "分组方式"],
    ["Date", "日期"],
    ["Environment", "环境"],
    ["Custom groups", "自定义分组"],
    ["None", "无"],
    ["1d", "1天"],
    ["3d", "3天"],
    ["7d", "7天"],
    ["30d", "30天"],
    ["All", "全部"],
    ["All projects", "所有项目"],
    ["View all", "查看全部"],
    ["Viewall", "查看全部"],
    ["Cowork", "协作"],
    ["Code", "代码"],
    ["Create your first scheduled task", "创建你的第一个计划任务"],
    ["Daily brief", "每日简报"],
    ["Weekly review", "每周回顾"],
    ["Skills have moved to Customize.", "技能已移至“自定义”。"],
    ["Skills have moved to", "技能已移至"],
    ["Connectors have moved to Customize. Head there to browse, connect, and manage them.", "连接器已移至“自定义”。前往那里浏览、连接和管理连接器。"],
    ["Connectors have moved to", "连接器已移至"],
    ["Head there to browse, connect, and manage them.", "前往那里浏览、连接和管理连接器。"],
    ["Run tasks on a schedule or whenever you need them. Type /schedule in any existing task to set one up.", "按计划或在需要时运行任务。在任何现有任务中输入 /schedule 即可设置。"],
    ["Live artifacts", "实时工件"],
    ["实时 Artifacts", "实时工件"],
    ["allow", "允许"],
    ["ask", "询问"],
    ["blocked", "已阻止"],
    ["Create dynamic artifacts that stay up-to-date using live data from your connectors.", "使用来自连接器的实时数据，创建保持更新的动态工件。"],
    ["Create dynamic artifacts that stay up-to-date using live data from your connectors", "使用来自连接器的实时数据，创建保持更新的动态工件"],
    ["Create dynamic artifacts that stay up to date using live data from your connectors.", "使用来自连接器的实时数据，创建保持更新的动态工件。"],
  ]);

  const VISIBLE_TEXT_SUBSTRING_FIXES = [
    [/实时\\s+Artifacts/g, "实时工件"],
    [/实时\\s+Artifact/g, "实时工件"],
    [/\\bArtifacts\\b/g, "工件"],
    [/\\bArtifact\\b/g, "工件"],
  ];
  const TEXT_FIX_INITIAL_LIMIT = 900;
  const TEXT_FIX_MUTATION_LIMIT = 180;
  const TEXT_FIX_ROOT_LIMIT = 24;
  const TEXT_FIX_MIN_INTERVAL_MS = 900;
  let textFixScheduled = false;
  let pendingTextFixRoots = [];
  let lastTextFixAt = 0;
  let fontVisibilityTimer = 0;
  let fontProviderSettingsCache = {{ key: "", at: 0, value: false }};

  function shouldFixTextNode(node) {{
    const parent = node.parentElement;
    if (!parent || parent.closest("script,style,[contenteditable='true']")) return false;
    const scope = parent.closest("[role='dialog'],[role='menu'],[role='listbox'],[role='navigation'],main,section,nav,aside");
    if (!scope) return false;
    const context = scope.textContent || "";
    return /(Appearance|外观|颜色模式|Color mode|聊天字体|Chat font|Font|字体|Artifact|Artifacts|Live artifacts|实时 Artifacts|实时工件|dynamic artifacts|动态工件|connectors|连接器|Scheduled|已安排|Customize|自定义)/.test(context);
  }}

  function fixVisibleText(root = document.body) {{
    if (!root) return;
    const limit = root === document.body || root === document.documentElement ? TEXT_FIX_INITIAL_LIMIT : TEXT_FIX_MUTATION_LIMIT;
    if (root.nodeType === Node.TEXT_NODE) {{
      processTextNode(root);
      return;
    }}
    if (root.nodeType !== 1) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (nodes.length < limit) {{
      const node = walker.nextNode();
      if (!node) break;
      nodes.push(node);
    }}
    nodes.forEach(processTextNode);
  }}

  function processTextNode(node) {{
    const text = node.nodeValue;
    if (!text) return;
    const trimmed = text.trim();
    const replacement = VISIBLE_TEXT_FIXES.get(trimmed);
    if (replacement) {{
      node.nodeValue = text.replace(trimmed, replacement);
      return;
    }}
    if (!shouldFixTextNode(node)) return;
    let next = text;
    VISIBLE_TEXT_SUBSTRING_FIXES.forEach(([pattern, value]) => {{
      next = next.replace(pattern, value);
    }});
    if (next !== text) node.nodeValue = next;
  }}

  function runTextFixQueue() {{
    textFixScheduled = false;
    lastTextFixAt = performance?.now?.() || Date.now();
    const roots = pendingTextFixRoots.splice(0, pendingTextFixRoots.length);
    if (!roots.length) roots.push(document.body);
    roots.forEach((root) => fixVisibleText(root));
  }}

  function scheduleFixVisibleText(root = document.body) {{
    if (root && !pendingTextFixRoots.includes(root)) {{
      if (root === document.body || root === document.documentElement) pendingTextFixRoots = [root];
      else if (pendingTextFixRoots.length < TEXT_FIX_ROOT_LIMIT) pendingTextFixRoots.push(root);
    }}
    if (textFixScheduled) return;
    textFixScheduled = true;
    const now = performance?.now?.() || Date.now();
    const delay = Math.max(0, TEXT_FIX_MIN_INTERVAL_MS - (now - lastTextFixAt));
    window.setTimeout(() => {{
      const idle = window.requestIdleCallback || ((callback) => window.setTimeout(callback, 60));
      idle(runTextFixQueue, {{ timeout: 1000 }});
    }}, delay);
  }}

  function buildPanel(expanded = false, mode = "inline") {{
    const panel = document.createElement("section");
    panel.id = mode === "floating" ? FLOATING_PANEL_ID : PANEL_ID;
    panel.dataset.fontPanelMode = mode;
    panel.style.cssText = panelStyle + (mode === "floating" ? "width:min(520px,calc(100vw - 40px));" : "width:100%;box-sizing:border-box;");
    panel.innerHTML = `
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
        <div>
          <h3 style="margin:0;font-size:13px;font-weight:700;letter-spacing:-0.01em;">中文字体</h3>
          <p style="margin:4px 0 0;${{mutedText}}">调整 Claude 界面的中文字体。</p>
        </div>
        <button data-font-toggle style="${{buttonStyle}};white-space:nowrap;font-size:11px;">${{expanded ? "收起" : "字体"}}</button>
      </div>

      <div data-font-body style="display:${{expanded ? "block" : "none"}};margin-top:8px;">
      <div data-font-layout style="display:grid;grid-template-columns:minmax(0,1.25fr) minmax(150px,.75fr);gap:10px;align-items:stretch;">
      <div style="display:flex;flex-direction:column;gap:8px;">
      <div style="${{sectionStyle}}">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px;">
          <label style="margin:0;font-size:11px;font-weight:600;color:var(--text-400,#444);">内置推荐</label>
          <span data-font-status style="font-size:11px;color:var(--text-300,#666);"></span>
        </div>
        <div data-font-preset-group style="display:flex;gap:1px;padding:2px;border:1px solid var(--border-300,#ddd);border-radius:10px;background:var(--bg-100,#f5f5f5);box-shadow:inset 0 1px 2px rgba(0,0,0,.04);">
          ${{PRESETS.map((item) => `<button type="button" data-font-preset-btn="${{item.id}}" style="${{segmentBase}}">${{item.label}}</button>`).join("")}}
        </div>
        <p style="margin:5px 0 0;${{mutedText}}">推荐字体，直接切换。</p>
      </div>

      <div style="${{sectionAltStyle}}">
        <label style="margin:0 0 5px;display:block;font-size:11px;font-weight:600;color:var(--text-400,#444);">自定义系统字体名</label>
        <div style="display:flex;gap:5px;align-items:center;">
          <input data-font-name placeholder="已安装字体名称" style="${{inputStyle}};min-width:0;padding:6px 7px;font-size:11px;" />
          <button data-font-apply-custom style="${{buttonStyle}};white-space:nowrap;font-size:11px;">应用</button>
        </div>
        <p style="margin:5px 0 0;${{mutedText}}">输入已安装字体名。</p>
      </div>

      <div style="${{sectionStyle}}">
        <label style="margin:0 0 5px;display:block;font-size:11px;font-weight:600;color:var(--text-400,#444);">导入本地字体文件</label>
        <input data-font-file type="file" accept=".ttf,.otf,font/ttf,font/otf" style="${{inputStyle}};padding:4px 5px;font-size:11px;" />
        <p style="margin:5px 0 0;${{mutedText}}">选择本地 .ttf / .otf。</p>
      </div>
      </div>

      <div style="${{previewStyle}}">
        <div style="margin:0 0 8px;font-size:11px;font-weight:600;color:var(--text-400,#444);">预览</div>
        <div style="font-size:16px;line-height:1.45;font-weight:600;color:var(--text-500,#111);">中文字体预览</div>
        <div style="margin-top:8px;${{mutedText}}">Claude Desktop 中文补丁</div>
        <div style="margin-top:14px;font-size:11px;color:var(--text-300,#666);">Aa 你好 Claude</div>
      </div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px;">
        <button data-font-reset style="${{buttonStyle}};white-space:nowrap;font-size:11px;">恢复默认</button>
      </div>
      </div>
    `;

    const presetButtons = [...panel.querySelectorAll("[data-font-preset-btn]")];
    const fontName = panel.querySelector("[data-font-name]");
    const status = panel.querySelector("[data-font-status]");
    const updateLayout = () => {{
      const layout = panel.querySelector("[data-font-layout]");
      if (!layout) return;
      layout.style.gridTemplateColumns = panel.getBoundingClientRect().width < 430 ? "1fr" : "minmax(0,1.25fr) minmax(150px,.75fr)";
    }};
    panel.querySelector("[data-font-toggle]").addEventListener("click", () => {{
      if (panel.dataset.fontPanelMode === "floating") {{
        panel.remove();
        return;
      }}
      const body = panel.querySelector("[data-font-body]");
      const willExpand = body.style.display === "none";
      body.style.display = willExpand ? "block" : "none";
      panel.querySelector("[data-font-toggle]").textContent = willExpand ? "收起" : "字体";
      if (willExpand) updateLayout();
    }});
    const setActivePreset = (presetId) => {{
      presetButtons.forEach((button) => {{
        const active = button.getAttribute("data-font-preset-btn") === presetId;
        button.style.cssText = `${{segmentBase}}${{active ? segmentActive : ""}}`;
      }});
    }};
    const sync = () => {{
      const cfg = readConfig();
      const currentPreset = cfg.presetId || "windows-modern";
      setActivePreset(currentPreset);
      fontName.value = cfg.fontName || "";
      status.textContent = cfg.mode === "custom" ? `当前：${{cfg.fontName}}` : cfg.mode === "imported" ? `当前：${{cfg.importedName}}` : `当前：${{PRESETS.find((item) => item.id === cfg.presetId)?.label || "Windows 现代默认"}}`;
    }};
    presetButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        const item = PRESETS.find((entry) => entry.id === button.getAttribute("data-font-preset-btn")) || PRESETS[0];
        saveConfig({{ mode: "preset", presetId: item.id, family: item.family }});
        sync();
      }});
    }});
    panel.querySelector("[data-font-apply-custom]").addEventListener("click", () => {{
      const name = fontName.value.trim();
      if (!name) return;
      saveConfig({{ mode: "custom", fontName: name }});
      sync();
    }});
    panel.querySelector("[data-font-file]").addEventListener("change", async (event) => {{
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
      const b64 = btoa(binary);
      const name = `ClaudeZhCnImported-${{Date.now()}}`;
      const format = file.name.toLowerCase().endsWith(".otf") ? "opentype" : "truetype";
      const css = `@font-face{{font-family:"${{name}}";src:url(data:font/${{format}};base64,${{b64}}) format("${{format}}");font-display:swap;}}`;
      saveConfig({{ mode: "imported", importedName: name, importedCss: css }});
      sync();
    }});
    panel.querySelector("[data-font-reset]").addEventListener("click", () => {{
      localStorage.removeItem(KEY);
      applyFont();
      sync();
    }});
    sync();
    updateLayout();
    return panel;
  }}

  function openFloatingPanel() {{
    let panel = document.getElementById(FLOATING_PANEL_ID);
    if (!panel) {{
      panel = buildPanel(true, "floating");
      panel.style.position = "fixed";
      panel.style.right = "20px";
      panel.style.bottom = "76px";
      panel.style.zIndex = "2147483647";
      panel.style.width = "min(520px, calc(100vw - 40px))";
      panel.style.boxShadow = "0 18px 60px rgba(0,0,0,.24)";
      document.body.appendChild(panel);
    }} else {{
      panel.remove();
    }}
  }}

  function isThirdPartyProviderSettingsPage() {{
    const root = document.querySelector("main,[role='main']") || document.body;
    const now = performance?.now?.() || Date.now();
    const key = `${{location.pathname}}:${{root?.textContent?.length || 0}}`;
    if (fontProviderSettingsCache.key === key && now - fontProviderSettingsCache.at < 1200) return fontProviderSettingsCache.value;
    const text = (root?.textContent || "").slice(0, 12000);
    const hasProviderTitle = /(管理第三方供应商|第三方供应商|Manage third-party|Inference provider)/i.test(text);
    const hasProviderFields = /(第三方认证方案|自定义推理标头|Authorization|x-api-key|模型发现|测试模型发现|Gateway base URL|Gateway API key)/i.test(text);
    fontProviderSettingsCache = {{ key, at: now, value: hasProviderTitle && hasProviderFields }};
    return fontProviderSettingsCache.value;
  }}

  function syncFloatingFontButtonVisibility() {{
    const button = document.getElementById(FAB_ID);
    if (!button) return;
    const hidden = isThirdPartyProviderSettingsPage();
    button.style.display = hidden ? "none" : "";
    if (hidden) document.getElementById(FLOATING_PANEL_ID)?.remove();
  }}

  function scheduleFloatingFontButtonVisibility() {{
    if (fontVisibilityTimer) return;
    fontVisibilityTimer = window.setTimeout(() => {{
      fontVisibilityTimer = 0;
      syncFloatingFontButtonVisibility();
    }}, 700);
  }}

  function mountFloatingButton() {{
    if (!document.body || document.getElementById(FAB_ID)) return;
    const button = document.createElement("button");
    button.id = FAB_ID;
    button.type = "button";
    button.textContent = "字体";
    button.title = "中文字体设置";
    button.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647;border:1px solid var(--border-300,#ddd);border-radius:999px;padding:8px 12px;background:var(--bg-000,#fff);color:inherit;box-shadow:0 8px 28px rgba(0,0,0,.18);cursor:pointer;font-size:13px;";
    button.addEventListener("click", openFloatingPanel);
    document.body.appendChild(button);
    syncFloatingFontButtonVisibility();
  }}

  function mountPanel() {{
    return;
  }}

  const start = () => {{
    applyFont();
    mountFloatingButton();
    scheduleFixVisibleText(document.body);
    const observer = new MutationObserver((mutations) => {{
      scheduleFloatingFontButtonVisibility();
      let queued = 0;
      for (const mutation of Array.from(mutations || []).slice(0, 24)) {{
        for (const node of Array.from(mutation.addedNodes || []).slice(0, 12)) {{
          const root = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
          if (!root || root.nodeType !== 1) continue;
          scheduleFixVisibleText(root);
          queued += 1;
          if (queued >= TEXT_FIX_ROOT_LIMIT) return;
        }}
      }}
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});
  }};
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, {{ once: true }});
  else start();
}})();
'''.strip()
    return "\n".join([
        "// __CLAUDE_ZH_CN_FONT_PATCH_BEGIN__",
        body,
        "// __CLAUDE_ZH_CN_FONT_PATCH_END__",
    ])


def session_delete_inject_script() -> str:
    body = r'''
;(()=>{
  const VERSION = "40";
  try {
  if (globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_VERSION__ === VERSION) return;
  globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__ = true;
  globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_VERSION__ = VERSION;

  const STYLE_ID = "claude-zh-cn-session-delete-style";
  const ACTION_BUTTON_CLASS = "claude-zh-cn-session-action-button";
  const BUTTON_CLASS = "claude-zh-cn-session-delete-button";
  const EXPORT_BUTTON_CLASS = "claude-zh-cn-session-export-button";
  const MOVE_BUTTON_CLASS = "claude-zh-cn-session-move-button";
  const PORTAL_BUTTON_CLASS = "claude-zh-cn-session-delete-portal-button";
  const TOOLTIP_CLASS = "claude-zh-cn-session-delete-tooltip";
  const TOAST_CLASS = "claude-zh-cn-session-delete-toast";
  const TIMELINE_ID = "claude-zh-cn-conversation-timeline";
  const CENTERED_CLASS = "claude-zh-cn-centered-layout";
  const CENTERED_TOGGLE_ID = "claude-zh-cn-centered-layout-toggle";
  const CENTERED_WIDTH_KEY = "claude-zh-cn-centered-layout-width";
  const SCROLL_STORAGE_PREFIX = "claude-zh-cn-scroll:";
  const LOCAL_DELETE_QUEUE = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_REQUESTS__";
  const LOCAL_DELETE_RESULTS = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_RESULTS__";
  const LOCAL_DELETE_BRIDGE = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_BRIDGE__";
  const ROW_FLAG = "data-claude-zh-cn-delete-row";
  const ROW_SELECTORS = [
    "[data-app-action-sidebar-thread-id]",
    "[data-session-id]",
    "[data-thread-id]",
    "[data-conversation-id]",
    "[data-chat-id]",
    "[data-testid*='conversation']",
    "[data-testid*='chat']",
    "[aria-current]",
    "a[href^='/chat/']",
    "a[href^='/conversation/']",
    "a[href^='/thread/']",
    "a[href^='/session/']",
    "a[href*='://claude.ai/chat/']",
    "aside a[href*='/chat/']",
    "aside a[href*='/conversation/']",
    "aside a[href*='/thread/']",
    "aside button",
    "aside [role='button']",
    "aside [role='link']",
    "aside [role='treeitem']",
    "aside [role='listitem']",
    "aside [tabindex]:not([tabindex='-1'])",
    "nav a[href*='/chat/']",
    "nav a[href*='/conversation/']",
    "nav a[href*='/thread/']",
    "nav button",
    "nav [role='button']",
    "nav [role='link']",
    "nav [role='treeitem']",
    "nav [role='listitem']",
    "nav [tabindex]:not([tabindex='-1'])",
    "[role='navigation'] a[href*='/chat/']",
    "[role='navigation'] a[href*='/conversation/']",
    "[role='navigation'] a[href*='/thread/']",
    "[role='navigation'] button",
    "[role='navigation'] [role='button']",
    "[role='navigation'] [role='link']",
    "[role='navigation'] [role='treeitem']",
    "[role='navigation'] [role='listitem']",
    "[role='navigation'] [tabindex]:not([tabindex='-1'])"
  ].join(",");
  const SESSION_SIGNAL_SELECTORS = [
    "[data-app-action-sidebar-thread-id]",
    "[data-session-id]",
    "[data-thread-id]",
    "[data-conversation-id]",
    "[data-chat-id]",
    "a[href^='/chat/']",
    "a[href^='/conversation/']",
    "a[href^='/thread/']",
    "a[href^='/session/']",
    "a[href*='://claude.ai/chat/']"
  ].join(",");
  const INTERACTIVE_ROW_SELECTORS = [
    "a[href]",
    "button",
    "[role='button']",
    "[role='link']",
    "[role='treeitem']",
    "[role='listitem']",
    "[tabindex]:not([tabindex='-1'])"
  ].join(",");
  const RECENTS_ROW_CANDIDATE_SELECTORS = [
    ROW_SELECTORS,
    INTERACTIVE_ROW_SELECTORS,
    "[data-testid]",
    "[class*='conversation']",
    "[class*='Conversation']",
    "[class*='thread']",
    "[class*='Thread']",
    "[class*='chat']",
    "[class*='Chat']",
    "li",
    "div"
  ].join(",");
  const SIDEBAR_CONTAINER_SELECTORS = [
    "aside",
    "nav",
    "[role='navigation']",
    "[data-sidebar]",
    "[data-testid*='sidebar']",
    "[data-testid*='history']",
    "[data-testid*='conversation']",
    "[data-testid*='chat']",
    "[class*='sidebar']",
    "[class*='Sidebar']",
    "[class*='history']",
    "[class*='History']"
  ].join(",");
  const MAIN_CONTAINER_SELECTORS = "main,[role='main']";
  let activeRow = null;
  let portalButton = null;
  let hidePortalTimer = 0;
  let pendingDeleteTimer = 0;
  let rootsCache = null;
  const TEXT_CACHE_LIMIT = 2500;
  const MAX_RECENTS_CANDIDATE_NODES = 96;
  const MAX_RECENTS_FALLBACK_VISITS = 160;
  const SCAN_DELAY_MS = 5200;
  const SCAN_MIN_INTERVAL_MS = 24000;
  const TIMELINE_DELAY_MS = 6200;
  const TIMELINE_MIN_INTERVAL_MS = 30000;
  const STARTUP_SCAN_DELAY_MS = 4200;
  const STARTUP_TIMELINE_DELAY_MS = 1800;
  const POINTER_ATTACH_DELAY_MS = 70;
  const MUTATION_RECORD_LIMIT = 24;
  const MUTATION_NODE_LIMIT = 36;
  let visibleTextCache = new WeakMap();
  let visibleTextCacheSize = 0;
  let timelineSummaryCache = new WeakMap();
  let lastTimelineSignature = "";
  let lastMutationSummary = { records: 0, inspectedRecords: 0, inspectedNodes: 0, skippedInjected: 0, capped: false };
  let providerSettingsCache = { key: "", at: 0, value: false };

  function invalidateScanCache() {
    rootsCache = null;
  }

  function scanCache() {
    if (!rootsCache) rootsCache = {};
    return rootsCache;
  }

  function resetVisibleTextCache() {
    visibleTextCache = new WeakMap();
    visibleTextCacheSize = 0;
  }

  function installStyle() {
    const existing = document.getElementById(STYLE_ID);
    if (existing?.dataset.sessionDeleteVersion === VERSION) return;
    existing?.remove();
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.dataset.sessionDeleteVersion = VERSION;
    style.textContent = `
      [${ROW_FLAG}="true"] {
        position: relative !important;
      }
      .${ACTION_BUTTON_CLASS} {
        position: absolute;
        top: 50%;
        z-index: 30;
        width: 26px;
        height: 26px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transform: translateY(-50%);
        border: 0;
        border-radius: 6px;
        background: color-mix(in srgb, var(--bg-000, #ffffff) 90%, transparent);
        color: var(--text-300, #6b7280);
        opacity: 0;
        pointer-events: none;
        cursor: default;
        transition: opacity .12s ease, background .12s ease, color .12s ease;
      }
      .${ACTION_BUTTON_CLASS} svg {
        width: 15px;
        height: 15px;
        display: block;
      }
      .${BUTTON_CLASS} { right: 12px; }
      .${EXPORT_BUTTON_CLASS} { right: 44px; }
      .${MOVE_BUTTON_CLASS} { right: 76px; }
      [${ROW_FLAG}="true"]:hover .${ACTION_BUTTON_CLASS},
      [${ROW_FLAG}="true"]:focus-within .${ACTION_BUTTON_CLASS} {
        opacity: 1;
        pointer-events: auto;
      }
      [${ROW_FLAG}="true"]:has(.${ACTION_BUTTON_CLASS}) {
        padding-right: 108px !important;
      }
      [${ROW_FLAG}="true"][data-claude-zh-cn-pending-delete="true"] {
        display: none !important;
      }
      .${ACTION_BUTTON_CLASS}:hover,
      .${ACTION_BUTTON_CLASS}:focus-visible {
        background: color-mix(in srgb, #0ea5e9 14%, var(--bg-000, #ffffff));
        color: #0369a1;
        outline: none;
      }
      .${BUTTON_CLASS}:hover,
      .${BUTTON_CLASS}:focus-visible {
        background: color-mix(in srgb, #ef4444 16%, var(--bg-000, #ffffff));
        color: #dc2626;
        outline: none;
      }
      .${ACTION_BUTTON_CLASS}.${PORTAL_BUTTON_CLASS} {
        position: fixed;
        right: auto;
        z-index: 2147483199;
        opacity: 0;
        pointer-events: none;
      }
      .${ACTION_BUTTON_CLASS}.${PORTAL_BUTTON_CLASS}[data-visible="true"] {
        opacity: 0 !important;
        pointer-events: none !important;
        display: none !important;
      }
      [${ROW_FLAG}="true"]:hover [data-thread-title],
      [${ROW_FLAG}="true"]:focus-within [data-thread-title],
      [${ROW_FLAG}="true"]:hover .truncate,
      [${ROW_FLAG}="true"]:focus-within .truncate {
        max-width: none !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
        word-break: break-word;
      }
      .${TOOLTIP_CLASS},
      .${TOAST_CLASS} {
        position: fixed;
        z-index: 2147483201;
        border-radius: 8px;
        background: #242628;
        color: #f4f4f5;
        font: 13px/18px system-ui, sans-serif;
        box-shadow: 0 14px 40px rgba(0,0,0,.28);
        pointer-events: none;
      }
      .${TOOLTIP_CLASS} {
        padding: 7px 9px;
        white-space: nowrap;
      }
      .${TOAST_CLASS} {
        right: 18px;
        bottom: 56px;
        max-width: min(420px, calc(100vw - 36px));
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .${TOAST_CLASS} button {
        border: 0;
        border-radius: 6px;
        background: #f4f4f5;
        color: #18181b;
        font: 12px/16px system-ui, sans-serif;
        padding: 4px 7px;
        cursor: default;
      }
      .claude-zh-cn-session-delete-confirm-overlay {
        position: fixed;
        inset: 0;
        z-index: 2147483200;
        display: grid;
        place-items: center;
        background: rgba(0,0,0,.28);
      }
      .claude-zh-cn-session-delete-confirm-content {
        width: min(360px, calc(100vw - 32px));
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 12px;
        background: var(--bg-000, #ffffff);
        color: var(--text-500, #111827);
        box-shadow: 0 18px 60px rgba(0,0,0,.28);
        padding: 16px;
      }
      .claude-zh-cn-session-delete-confirm-title {
        font: 600 15px/22px system-ui, sans-serif;
      }
      .claude-zh-cn-session-delete-confirm-message {
        margin-top: 8px;
        color: var(--text-300, #6b7280);
        font: 13px/20px system-ui, sans-serif;
      }
      .claude-zh-cn-session-delete-confirm-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 16px;
      }
      .claude-zh-cn-session-delete-confirm-actions button {
        border: 1px solid var(--border-300, #d1d5db);
        border-radius: 8px;
        background: var(--bg-000, #ffffff);
        color: inherit;
        font: 13px/18px system-ui, sans-serif;
        padding: 7px 10px;
        cursor: default;
      }
      .claude-zh-cn-session-delete-confirm-actions [data-claude-delete-confirm] {
        border-color: #ef4444;
        background: #dc2626;
        color: #ffffff;
      }
      .claude-zh-cn-session-move-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-height: min(360px, calc(100vh - 220px));
        overflow: auto;
        margin-top: 12px;
      }
      .claude-zh-cn-session-move-list button {
        width: 100%;
        border: 1px solid var(--border-300, #d1d5db);
        border-radius: 8px;
        background: var(--bg-000, #ffffff);
        color: inherit;
        text-align: left;
        font: 13px/18px system-ui, sans-serif;
        padding: 8px 10px;
        cursor: default;
      }
      .claude-zh-cn-session-move-list button:hover,
      .claude-zh-cn-session-move-list button:focus-visible {
        background: color-mix(in srgb, var(--text-500, #111827) 8%, transparent);
        outline: none;
      }
      #${TIMELINE_ID} {
        position: fixed;
        right: 0;
        top: 86px;
        z-index: 2147482000;
        width: 28px;
        max-height: min(520px, calc(100vh - 160px));
        overflow: auto;
        padding: 8px 5px;
        border: 1px solid var(--border-300, rgba(0,0,0,.14));
        border-right: 0;
        border-radius: 8px 0 0 8px;
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: var(--text-300, #52525b);
        font: 12px/16px system-ui, sans-serif;
        box-shadow: 0 8px 26px rgba(0,0,0,.16);
        transition: width .16s ease, padding .16s ease;
        opacity: 1 !important;
        backdrop-filter: none !important;
      }
      #${TIMELINE_ID}:empty {
        display: none;
      }
      #${TIMELINE_ID}:hover,
      #${TIMELINE_ID}:focus-within {
        width: 240px;
        padding: 8px 8px;
      }
      #${TIMELINE_ID} button {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        min-height: 24px;
        margin: 0 0 6px;
        border: 0;
        border-radius: 6px;
        background: transparent;
        color: inherit;
        text-align: left;
        font: inherit;
        padding: 5px 4px;
        cursor: default;
      }
      #${TIMELINE_ID} button::before {
        content: "";
        flex: 0 0 8px;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: currentColor;
        opacity: .86;
      }
      #${TIMELINE_ID} .claude-zh-cn-timeline-summary {
        display: block;
        min-width: 0;
        max-width: 0;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        opacity: 0;
        transition: max-width .16s ease, opacity .12s ease;
      }
      #${TIMELINE_ID}:hover .claude-zh-cn-timeline-summary,
      #${TIMELINE_ID}:focus-within .claude-zh-cn-timeline-summary {
        max-width: 200px;
        opacity: 1;
      }
      #${TIMELINE_ID} button:hover,
      #${TIMELINE_ID} button:focus-visible {
        background: color-mix(in srgb, var(--text-500, #111827) 8%, transparent);
        outline: none;
      }
      .${CENTERED_CLASS} main,
      .${CENTERED_CLASS} [role="main"],
      .${CENTERED_CLASS} form {
        max-width: var(--claude-zh-cn-centered-width, 980px) !important;
        margin-left: auto !important;
        margin-right: auto !important;
      }
      #${CENTERED_TOGGLE_ID} {
        position: fixed;
        right: 20px;
        bottom: 64px;
        z-index: 2147483100;
        border: 1px solid var(--border-300,#ddd);
        border-radius: 999px;
        padding: 7px 10px;
        background: var(--bg-000,#fff);
        color: inherit;
        box-shadow: 0 8px 28px rgba(0,0,0,.14);
        cursor: default;
        font: 12px/16px system-ui, sans-serif;
      }
      .claude-zh-cn-centered-width-dialog {
        position: fixed;
        right: 20px;
        bottom: 108px;
        z-index: 2147483200;
        width: 232px;
        border: 1px solid var(--border-300,#d1d5db);
        border-radius: 8px;
        background: #ffffff;
        color: var(--text-500,#111827);
        box-shadow: 0 16px 48px rgba(0,0,0,.18);
        padding: 12px;
        font: 12px/16px system-ui, sans-serif;
      }
      .claude-zh-cn-centered-width-dialog label {
        display: block;
        margin-bottom: 8px;
        font-weight: 600;
      }
      .claude-zh-cn-centered-width-dialog input {
        width: 100%;
        box-sizing: border-box;
        border: 1px solid var(--border-300,#d1d5db);
        border-radius: 6px;
        padding: 7px 8px;
        font: 13px/18px system-ui, sans-serif;
      }
      .claude-zh-cn-centered-width-dialog-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 10px;
      }
      .claude-zh-cn-centered-width-dialog button {
        border: 1px solid var(--border-300,#d1d5db);
        border-radius: 6px;
        background: #ffffff;
        color: inherit;
        padding: 5px 8px;
        font: 12px/16px system-ui, sans-serif;
        cursor: default;
      }
    `;
    document.documentElement.appendChild(style);
  }

  function rowHref(row) {
    return row.getAttribute("href") || row.querySelector("a[href]")?.getAttribute("href") || "";
  }

  function looksLikeChatHref(value) {
    if (!value) return false;
    try {
      const url = new URL(value, window.location.href);
      return /^\/(chat|conversation|thread|session)\/[A-Za-z0-9_.-]{8,}/i.test(url.pathname);
    } catch {
      return /\/(chat|conversation|thread|session)\/[A-Za-z0-9_.-]{8,}/i.test(value);
    }
  }

  function rowId(row) {
    const href = rowHref(row);
    const explicitId = row.getAttribute("data-app-action-sidebar-thread-id")
      || row.getAttribute("data-session-id")
      || row.getAttribute("data-thread-id")
      || row.getAttribute("data-conversation-id")
      || row.getAttribute("data-chat-id");
    if (explicitId) return explicitId;
    const idMatch = href.match(/(?:chat|conversation|thread|session)(?:\/|=|:|-)([A-Za-z0-9_.-]+)/i);
    return (idMatch && idMatch[1]) || "";
  }

  function localSessionId(row) {
    const values = [
      rowId(row),
      rowHref(row),
      row.getAttribute?.("aria-label"),
      row.getAttribute?.("title"),
      row.dataset?.sessionId,
      row.dataset?.threadId,
      row.dataset?.conversationId,
      row.dataset?.chatId,
      rowVisibleText(row)
    ];
    for (const value of values) {
      const match = String(value || "").match(/\blocal_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i);
      if (match?.[0]) return match[0];
    }
    return "";
  }

  function currentConversationUuid() {
    const candidates = [location.pathname, location.href];
    for (const value of candidates) {
      const match = String(value || "").match(/(?:chat|conversation|thread|session)\/([A-Za-z0-9_.-]{8,})/i);
      if (match?.[1]) return match[1];
    }
    return "";
  }

  function hasSidebarAncestor(node) {
    for (let current = node; current && current !== document.body; current = current.parentElement) {
      const tag = current.tagName?.toLowerCase?.() || "";
      if (tag === "aside" || tag === "nav") return true;
      if (current.getAttribute?.("role") === "navigation") return true;
      const attrs = [
        current.getAttribute?.("data-testid"),
        current.getAttribute?.("data-sidebar"),
        current.getAttribute?.("aria-label"),
        typeof current.className === "string" ? current.className : "",
      ].filter(Boolean).join(" ").toLowerCase();
      if (/(sidebar|side-bar|navigation|recents|history|chats|conversations|侧边栏|导航|最近|历史|聊天|会话)/.test(attrs)) return true;
    }
    return false;
  }

  function isHistorySectionMarker(text) {
    const value = String(text || "").trim();
    return /^(?:最近|历史)(?:\s|$)/.test(value) || /^(?:Recent(?:s| conversations| chats)?|History)\b/i.test(value);
  }

  function isNonHistorySectionMarker(text) {
    return /^(项目|Projects|文件|Files|说明|Docs|模型|Models|Gateway|用例|Cases|进度|Progress|上下文|Context|规范|Specs|工具|Tools|个人插件|Personal plugins|第三方|自定义|Custom|选择文件夹|Choose folder)\b/i.test(String(text || "").trim());
  }

  function panelHasModeTabs(panel) {
    const text = rowVisibleText(panel).slice(0, 400);
    return /(协作|Collaborate)/i.test(text) && /(代码|Code)/i.test(text);
  }

  function looksLikeModeOrToolbarChrome(row, text) {
    const value = [
      row.getAttribute?.("aria-label"),
      row.getAttribute?.("title"),
      text || rowVisibleText(row)
    ].filter(Boolean).join(" ");
    const hasModeWords = /(协作|代码|Collaborate|Code)/i.test(value);
    const hasModeShortcut = /(?:Ctrl|Cmd|Command)\s*\+\s*[12]/i.test(value);
    if (!hasModeWords && !hasModeShortcut) return false;
    if (row.matches?.("[role='tab'],[role='tablist']")) return true;
    if (row.closest?.("[role='tablist']")) return true;
    if ((row.querySelectorAll?.("[role='tab'],button,[role='button']")?.length || 0) >= 2 && hasModeWords) return true;
    return false;
  }

  function hasRecentsSectionHint(panel) {
    const text = rowVisibleText(panel).slice(0, 1200);
    return /(?:最近|历史|Recent(?:s| conversations| chats)?|History|聊天|Chat|会话)/i.test(text);
  }

  function sessionPanelRoots() {
    const cache = scanCache();
    if (cache.panelRoots) return cache.panelRoots;
    const roots = new Set();
    const addRoot = (panel) => {
      if (!panel) return;
      if (hasRecentsSectionHint(panel) || panel.querySelector?.(SESSION_SIGNAL_SELECTORS)) roots.add(panel);
    };
    const sidebarContainers = [...document.querySelectorAll(SIDEBAR_CONTAINER_SELECTORS)].filter(visible);
    sidebarContainers.forEach(addRoot);
    document.querySelectorAll(SESSION_SIGNAL_SELECTORS).forEach((signal) => {
      for (let current = signal.parentElement; current && current !== document.body; current = current.parentElement) {
        const rect = current.getBoundingClientRect?.();
        if (!rect || rect.width < 160 || rect.height < 120 || rect.width > 840) continue;
        const signalCount = current.querySelectorAll?.(SESSION_SIGNAL_SELECTORS)?.length || 0;
        if (current.matches?.(SIDEBAR_CONTAINER_SELECTORS) || signalCount >= 2 || (signalCount >= 1 && rect.left <= Math.max(560, window.innerWidth * 0.45))) {
          addRoot(current);
          break;
        }
      }
    });
    const unresolvedContainers = sidebarContainers.filter((container) => !roots.has(container));
    unresolvedContainers.forEach((container) => {
      container.querySelectorAll("button,[role='tab'],[role='button'],a,div").forEach((node) => {
        const text = rowVisibleText(node);
        if (!/(最近|历史|Recent|History|聊天|Chat|会话|Conversation)/i.test(text)) return;
        addRoot(container);
      });
    });
    unresolvedContainers.forEach((container) => {
      if (roots.has(container)) return;
      container.querySelectorAll("a[href],button,[role='button'],[role='link'],[role='treeitem'],[role='listitem'],li,div").forEach((node) => {
        const text = rowVisibleText(node);
        if (!looksLikeRecentsEntryRow(node, text) && !hasSessionSignal(node) && !isCurrentSidebarItem(node)) return;
        for (let current = node.parentElement; current && current !== document.body; current = current.parentElement) {
          const rect = current.getBoundingClientRect?.();
          if (!rect || rect.width < 160 || rect.height < 120 || rect.left > Math.max(560, window.innerWidth * 0.6)) break;
          if (current === container || current.matches?.(SIDEBAR_CONTAINER_SELECTORS) || current.querySelector?.(SESSION_SIGNAL_SELECTORS)) {
            addRoot(current === container ? container : current);
            break;
          }
        }
      });
    });
    cache.panelRoots = [...roots];
    return cache.panelRoots;
  }

  function recentSectionRoots() {
    const cache = scanCache();
    if (cache.recentSectionRoots) return cache.recentSectionRoots;
    const roots = [];
    sessionPanelRoots().forEach((panel) => {
      const markers = [];
      for (const node of panel.querySelectorAll("button,[role='button'],[role='heading'],[aria-label],a,div,span")) {
        if (markers.length >= 3) break;
        if (!visible(node)) continue;
        if (node === panel) continue;
        if (node.querySelector?.(SESSION_SIGNAL_SELECTORS)) continue;
        const fitsPanel = (() => {
          const rect = node.getBoundingClientRect?.();
          const panelRect = panel.getBoundingClientRect?.();
          return !rect || !panelRect || rect.height < panelRect.height * 0.5;
        })();
        if (fitsPanel && isHistorySectionMarker(rowVisibleText(node))) markers.push(node);
      }
      if (markers.length) roots.push(...markers.map((marker) => ({ panel, marker })));
      else roots.push({ panel, marker: null });
    });
    cache.recentSectionRoots = roots;
    return roots;
  }

  function isInsideRecentsSection(row) {
    const rect = row.getBoundingClientRect?.();
    if (!rect) return false;
    const section = recentSectionRoots().find(({ panel, marker }) => {
      if (!panel.contains(row)) return false;
      if (!marker) return true;
      const markerRect = marker.getBoundingClientRect?.();
      return markerRect && markerRect.bottom <= rect.top + 1;
    });
    if (!section) return false;
    if (!section.marker) return hasSessionSignal(row);
    const cache = scanCache();
    const sectionKey = section.marker;
    const markerRect = section.marker.getBoundingClientRect?.();
    if (!markerRect) return false;
    if (!cache.nonHistoryMarkers) cache.nonHistoryMarkers = new WeakMap();
    let nodes = cache.nonHistoryMarkers.get(sectionKey);
    if (!nodes) {
      nodes = [...section.panel.querySelectorAll("button,[role='button'],[role='heading'],[aria-label],a,div,span")]
        .filter(visible)
        .filter((node) => isNonHistorySectionMarker(rowVisibleText(node)));
      cache.nonHistoryMarkers.set(sectionKey, nodes);
    }
    for (const node of nodes) {
      const nodeRect = node.getBoundingClientRect?.();
      if (!nodeRect || nodeRect.bottom <= markerRect.bottom + 1 || nodeRect.top >= rect.top - 1) continue;
      return false;
    }
    return true;
  }

  function looksLikeRecentsEntryRow(row, text) {
    const title = recentsTitleText(row) || text;
    if (!title || title.length < 2) return false;
    if (looksLikeSidebarChrome(row, text)) return false;
    if (isHistorySectionMarker(title) || isNonHistorySectionMarker(title)) return false;
    if (!meaningfulRecentsTitle(row, title)) return false;
    if (row.matches?.("input,textarea,select,[contenteditable='true']")) return false;
    if (row.querySelector?.("input,textarea,select,[contenteditable='true']")) return false;
    return true;
  }

  function hasNativeRowControl(row) {
    return [...row.querySelectorAll?.("button,[role='button'],[aria-haspopup],[data-radix-menu-trigger]") || []]
      .some((node) => !node.classList?.contains(ACTION_BUTTON_CLASS));
  }

  function isLikelyProjectOrGroupRow(row, text) {
    if (titleLooksLikeFilePath(text) && !rowId(row) && !looksLikeChatHref(rowHref(row))) return true;
    if (titleLooksLikeProjectGroup(text) && !rowId(row) && !looksLikeChatHref(rowHref(row))) return true;
    const label = [
      row.getAttribute?.("aria-label"),
      row.getAttribute?.("title")
    ].filter(Boolean).join(" ");
    return /(Gateway|第三方|folder|workspace|repo|repository|文件夹|仓库|工作区|警告|warning)/i.test(label)
      && !rowId(row)
      && !looksLikeChatHref(rowHref(row));
  }

  function stripNewSessionCommandChrome(value) {
    return stripInjectedActionText(value)
      .replace(/(?:Ctrl|Cmd|Command)\s*\+\s*N/gi, " ")
      .replace(/[+＋⌘]/g, " ")
      .replace(/\b(?:Ctrl|Cmd|Command|Alt|Shift|N)\b/gi, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function looksLikeNewSessionCommand(row, text) {
    if (rowId(row) || looksLikeChatHref(rowHref(row)) || row.querySelector?.(SESSION_SIGNAL_SELECTORS)) return false;
    const labels = [
      row.getAttribute?.("aria-label"),
      row.getAttribute?.("title"),
      text
    ].filter(Boolean);
    return labels.some((label) => {
      const value = stripNewSessionCommandChrome(label);
      const compact = value.replace(/\s+/g, "");
      return /^(?:新建会话|新建聊天)$/.test(compact)
        || /^(?:New chat|New session)$/i.test(value);
    });
  }

  function titleLooksLikeProjectGroup(text) {
    return /^(?:Gateway|第三方|Projects?|项目)(?:\s|$)/i.test(String(text || "").trim());
  }

  function titleLooksLikeFilePath(text) {
    const value = stripInjectedActionText(text).trim();
    if (/^[A-Za-z]:[\\/]/.test(value)) return true;
    if (/^(?:\.{1,2}|~)[\\/]/.test(value)) return true;
    if (/^[\\/][^\\/]+[\\/]/.test(value)) return true;
    return /[\\/].+\.(?:c|cc|cpp|cs|css|go|h|hpp|html|java|js|jsx|json|kt|md|mjs|py|rs|scss|swift|toml|ts|tsx|txt|xml|yaml|yml)$/i.test(value);
  }

  function isInjectedActionText(value) {
    return /^(移动|导出|删除|Move|Export|Delete)$/.test(String(value || "").trim());
  }

  function stripInjectedActionText(value) {
    return String(value || "")
      .replace(/\b(Move|Export|Delete)\b/gi, " ")
      .replace(/移动|导出|删除/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function meaningfulRecentsTitle(row, text) {
    const value = stripInjectedActionText(text);
    if (!value) return false;
    if (isInjectedActionText(value)) return false;
    if (/^[•·◦○\u25e6\u25cb\u2022]+$/.test(value)) return false;
    if (value.length < 3 && !rowId(row) && !looksLikeChatHref(rowHref(row))) return false;
    if (/^[\p{P}\p{S}\s]+$/u.test(value)) return false;
    return true;
  }

  function recentsTitleNodes(row) {
    if (!row || row.nodeType !== 1) return [];
    const selectors = [
      "[data-thread-title]",
      ".truncate",
      "[title]"
    ].join(",");
    const titles = new Map();
    [...row.querySelectorAll?.(selectors) || []].forEach((node) => {
      if (node.classList?.contains(ACTION_BUTTON_CLASS)) return false;
      if (node.closest?.(`.${ACTION_BUTTON_CLASS},.${PORTAL_BUTTON_CLASS}`)) return false;
      if (node.matches?.("button,[role='button']")) return false;
      const title = stripInjectedActionText(node.getAttribute?.("title") || rowVisibleText(node));
      if (!title) return;
      if (isInjectedActionText(title)) return;
      if (looksLikeSidebarChrome(node, title)) return;
      if (isHistorySectionMarker(title) || isNonHistorySectionMarker(title)) return;
      if (!meaningfulRecentsTitle(row, title)) return;
      const key = title.replace(/\s+/g, " ").trim().toLowerCase();
      if (!titles.has(key)) titles.set(key, node);
    });
    return [...titles.values()];
  }

  function recentsTitleText(row) {
    const node = recentsTitleNodes(row)[0];
    if (!node) return "";
    return stripInjectedActionText(node.getAttribute?.("title") || rowVisibleText(node));
  }

  function hasReadableRecentsTitle(row) {
    return recentsTitleNodes(row).length > 0;
  }

  function hasSessionSignal(row) {
    return !!rowId(row)
      || looksLikeChatHref(rowHref(row))
      || !!row.querySelector?.(SESSION_SIGNAL_SELECTORS);
  }

  function isCurrentSidebarItem(row) {
    return row.getAttribute?.("aria-current") === "page"
      || row.getAttribute?.("aria-current") === "true";
  }

  function isCurrentRecentsItem(row, text) {
    return isCurrentSidebarItem(row)
      && isInsideRecentsSection(row)
      && !isLikelyProjectOrGroupRow(row, text || rowVisibleText(row));
  }

  function recentsRowKey(row) {
    return rowId(row) || rowHref(row) || recentsTitleText(row) || rowVisibleText(row).slice(0, 120);
  }

  function addCandidateNode(nodes, node) {
    if (!node || node.nodeType !== 1 || nodes.has(node)) return nodes.size < MAX_RECENTS_CANDIDATE_NODES;
    if (node.classList?.contains(ACTION_BUTTON_CLASS)) return true;
    nodes.add(node);
    return nodes.size < MAX_RECENTS_CANDIDATE_NODES;
  }

  function fallbackRecentsTextNodes(panel, marker) {
    const fallback = [];
    const markerRect = marker?.getBoundingClientRect?.();
    let visits = 0;
    const walk = (node) => {
      if (!node || node.nodeType !== 1) return false;
      visits += 1;
      if (visits > MAX_RECENTS_FALLBACK_VISITS || fallback.length >= MAX_RECENTS_CANDIDATE_NODES) return true;
      const rect = node.getBoundingClientRect?.();
      if (rect) {
        if (rect.width > 560 || rect.height > 260) {
          for (const child of Array.from(node.children || [])) {
            if (walk(child)) return true;
          }
          return false;
        }
        if (markerRect && rect.top <= markerRect.bottom) return false;
      }
      const text = rowVisibleText(node);
      if ((hasReadableRecentsTitle(node) || looksLikeRecentsEntryRow(node, text) || isCurrentSidebarItem(node)) && !isHistorySectionMarker(text) && !isNonHistorySectionMarker(text)) fallback.push(node);
      for (const child of Array.from(node.children || [])) {
        if (walk(child)) return true;
      }
      return false;
    };
    walk(panel);
    return fallback;
  }

  function candidateNodesForSection(panel, marker) {
    const nodes = new Set();
    for (const node of panel.querySelectorAll(ROW_SELECTORS)) {
      if (!addCandidateNode(nodes, node)) break;
    }
    if (nodes.size < MAX_RECENTS_CANDIDATE_NODES) {
      for (const node of panel.querySelectorAll("[data-thread-title],.truncate,[title],li,[role='listitem'],[role='treeitem']")) {
        if (!addCandidateNode(nodes, node)) break;
      }
    }
    if (nodes.size < MAX_RECENTS_CANDIDATE_NODES) fallbackRecentsTextNodes(panel, marker).forEach((node) => addCandidateNode(nodes, node));
    return [...nodes];
  }

  function preferRecentsRow(existing, next) {
    if (!existing) return next;
    if (!next) return existing;
    if (next.contains?.(existing)) return next;
    if (existing.contains?.(next)) return existing;
    const existingSignal = (hasSessionSignal(existing) ? 4 : 0) + (hasReadableRecentsTitle(existing) ? 2 : 0) + (existing.matches?.("li,[role='listitem'],[role='treeitem']") ? 1 : 0);
    const nextSignal = (hasSessionSignal(next) ? 4 : 0) + (hasReadableRecentsTitle(next) ? 2 : 0) + (next.matches?.("li,[role='listitem'],[role='treeitem']") ? 1 : 0);
    if (nextSignal !== existingSignal) return nextSignal > existingSignal ? next : existing;
    const existingInteractive = existing.matches?.("a[href],button,[role='button']") ? 1 : 0;
    const nextInteractive = next.matches?.("a[href],button,[role='button']") ? 1 : 0;
    if (nextInteractive !== existingInteractive) return nextInteractive < existingInteractive ? next : existing;
    const existingRect = existing.getBoundingClientRect?.();
    const nextRect = next.getBoundingClientRect?.();
    const existingArea = existingRect ? existingRect.width * existingRect.height : 0;
    const nextArea = nextRect ? nextRect.width * nextRect.height : 0;
    return nextArea > existingArea ? next : existing;
  }

  function isBlankOrStatusDotRow(row, text) {
    const value = stripInjectedActionText(text || rowVisibleText(row));
    if (!value) return true;
    if (/^[•·◦○\u25e6\u25cb\u2022]+$/.test(value)) return true;
    return false;
  }

  function recentsRowContainer(node) {
    const selectors = "[data-app-action-sidebar-thread-id],[data-session-id],[data-thread-id],[data-conversation-id],[data-chat-id],a[href],button,[role='button'],[role='link'],[role='treeitem'],[role='listitem'],li";
    const direct = node.closest?.(selectors);
    if (direct) {
      const directText = rowVisibleText(direct);
      if (direct.matches?.("button,[role='button']") && !rowId(direct) && !looksLikeChatHref(rowHref(direct))) return node;
      if (hasReadableRecentsTitle(direct) || rowId(direct) || looksLikeChatHref(rowHref(direct)) || isCurrentRecentsItem(direct, directText)) return direct;
    }
    let best = node;
    for (let current = node; current && current !== document.body; current = current.parentElement) {
      if (current.matches?.("button,[role='button']") && !rowId(current) && !looksLikeChatHref(rowHref(current))) continue;
      const rect = current.getBoundingClientRect?.();
      if (!rect || rect.width < 120 || rect.width > 440 || rect.height < 16 || rect.height > 240) continue;
      const candidateText = rowVisibleText(current);
      if (isHistorySectionMarker(candidateText) || isNonHistorySectionMarker(candidateText)) continue;
      if (!hasReadableRecentsTitle(current) && !rowId(current) && !looksLikeChatHref(rowHref(current)) && !isCurrentRecentsItem(current, candidateText) && !looksLikeRecentsEntryRow(current, candidateText)) continue;
      const bestRect = best.getBoundingClientRect?.();
      const candidateRect = rect;
      if (!bestRect || candidateRect.width > bestRect.width) best = current;
      if (candidateRect.width >= 180) return current;
    }
    return best;
  }

  function normalizeRecentsRow(row) {
    if (!row || row.nodeType !== 1) return row;
    let best = row;
    for (let current = row; current && current !== document.body; current = current.parentElement) {
      const rect = current.getBoundingClientRect?.();
      if (!rect || rect.width < 120 || rect.width > 560 || rect.height < 16 || rect.height > 240) continue;
      const text = rowVisibleText(current);
      if (isHistorySectionMarker(text) || isNonHistorySectionMarker(text) || isLikelyProjectOrGroupRow(current, text)) continue;
      if (!hasSessionSignal(current) && !hasReadableRecentsTitle(current) && !looksLikeRecentsEntryRow(current, text)) continue;
      best = current;
      if (current.matches?.("[data-app-action-sidebar-thread-id],[data-session-id],[data-thread-id],[data-conversation-id],[data-chat-id],[role='treeitem'],[role='listitem'],li")) break;
    }
    return best;
  }

  function looksLikeSidebarSessionRow(row) {
    return sessionRowRejectReason(row) === "";
  }

  function sessionRowRejectReason(row) {
    if (!row || row.nodeType !== 1) return "invalid";
    const rect = row.getBoundingClientRect?.();
    if (!rect || rect.width <= 0 || rect.height <= 0) return "invisible";
    const text = rowVisibleText(row);
    const title = recentsTitleText(row);
    const titleOrText = title || text;
    const isCurrentConversation = isCurrentRecentsItem(row, text);
    const hasConversationSignal = hasSessionSignal(row) || isCurrentConversation;
    if (isBlankOrStatusDotRow(row, text)) return "blank-or-dot";
    if (looksLikeModeOrToolbarChrome(row, text)) return "mode-or-toolbar";
    if (looksLikeNewSessionCommand(row, text)) return "new-session-command";
    if (!hasConversationSignal && looksLikeSidebarChrome(row, text)) return "sidebar-chrome";
    if (!hasSidebarAncestor(row) && !sessionPanelRoots().some((panel) => panel.contains(row))) return "outside-session-panel";
    if (rect.width > 560) return "too-wide";
    if (rect.height < 16) return "too-short";
    if (rect.height > 240) return "too-tall";
    if (!titleOrText) return "missing-title";
    if (!hasConversationSignal && isLikelyProjectOrGroupRow(row, text)) return "project-or-group";
    if (!hasConversationSignal && !looksLikeRecentsEntryRow(row, text)) return "not-session-title";
    if (!isInsideRecentsSection(row)) return "outside-recents-section";
    return "";
  }

  function rowVisibleText(row) {
    if (!row) return "";
    const cached = visibleTextCache.get(row);
    if (cached !== undefined) return cached;
    const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const value = String(node.nodeValue || "").replace(/\s+/g, " ").trim();
        if (!value) return NodeFilter.FILTER_REJECT;
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest?.(`.${ACTION_BUTTON_CLASS},.${TOOLTIP_CLASS},.${TOAST_CLASS},.${PORTAL_BUTTON_CLASS},[aria-hidden="true"],[hidden]`)) return NodeFilter.FILTER_REJECT;
        const style = window.getComputedStyle?.(parent);
        if (style && (style.display === "none" || style.visibility === "hidden")) return NodeFilter.FILTER_REJECT;
        const rect = parent.getBoundingClientRect?.();
        if (rect && (rect.width <= 0 || rect.height <= 0)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const parts = [];
    for (let node = walker.nextNode(); node; node = walker.nextNode()) parts.push(node.nodeValue);
    const value = stripInjectedActionText(parts.join(" ")).replace(/\s+/g, " ").trim();
    if (visibleTextCacheSize < TEXT_CACHE_LIMIT) {
      visibleTextCache.set(row, value);
      visibleTextCacheSize += 1;
    }
    return value;
  }

  function looksLikeSidebarChrome(row, text) {
    const label = [
      row.getAttribute?.("aria-label"),
      row.getAttribute?.("title"),
      text
    ].filter(Boolean).join(" ");
    return /new chat|search|settings|help|upgrade|profile|account|view\s*all|show\s*more|show\s*less|expand|collapse|新建|搜索|设置|帮助|升级|账户|个人资料|查看\s*全部|展开|收起|折叠/i.test(label);
  }

  function rowTitle(row) {
    const titleNode = row.querySelector("[data-thread-title], .truncate, [title]");
    return (
      titleNode?.getAttribute("title")
      || titleNode?.textContent
      || row.getAttribute("aria-label")
      || row.textContent
      || "当前会话"
    ).replace(/\s*(删除|Delete|导出|Export|移动|Move|归档|Archive|更多|More)\s*$/g, "").trim().slice(0, 120);
  }

  function visible(node) {
    const rect = node?.getBoundingClientRect?.();
    return !!rect && rect.width > 0 && rect.height > 0;
  }

  function mainRoot() {
    return document.querySelector("main,[role='main']") || document.body;
  }

  function isCurrentRow(row) {
    if (row.getAttribute("aria-current") === "page" || row.getAttribute("aria-current") === "true") return true;
    const href = rowHref(row);
    if (!href) return false;
    try {
      const url = new URL(href, window.location.href);
      return url.href === window.location.href || url.pathname === window.location.pathname;
    } catch {
      return window.location.href.includes(href);
    }
  }

  function stopButtonEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
  }

  function hideTooltip() {
    document.querySelectorAll(`.${TOOLTIP_CLASS}`).forEach((node) => node.remove());
  }

  function showTooltip(button, text) {
    hideTooltip();
    const tooltip = document.createElement("div");
    tooltip.className = TOOLTIP_CLASS;
    tooltip.textContent = text || button.getAttribute("aria-label") || "操作";
    document.body.appendChild(tooltip);
    const buttonRect = button.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    tooltip.style.left = `${Math.max(8, Math.min(window.innerWidth - tooltipRect.width - 8, buttonRect.left + buttonRect.width / 2 - tooltipRect.width / 2))}px`;
    tooltip.style.top = `${Math.max(8, buttonRect.bottom + 8)}px`;
  }

  function showToast(message) {
    document.querySelectorAll(`.${TOAST_CLASS}`).forEach((node) => node.remove());
    const toast = document.createElement("div");
    toast.className = TOAST_CLASS;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
  }

  function showUndoToast(message, onUndo) {
    document.querySelectorAll(`.${TOAST_CLASS}`).forEach((node) => node.remove());
    const toast = document.createElement("div");
    toast.className = TOAST_CLASS;
    const text = document.createElement("span");
    text.textContent = message;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "撤销";
    button.addEventListener("click", (event) => {
      stopButtonEvent(event);
      toast.remove();
      onUndo?.();
    }, true);
    toast.appendChild(text);
    toast.appendChild(button);
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4600);
  }

  function trashIconSvg() {
    return `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 6h18"></path>
        <path d="M8 6V4h8v2"></path>
        <path d="M19 6l-1 14H6L5 6"></path>
        <path d="M10 11v5"></path>
        <path d="M14 11v5"></path>
      </svg>
    `;
  }

  function exportIconSvg() {
    return `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3v12"></path>
        <path d="m7 10 5 5 5-5"></path>
        <path d="M5 21h14"></path>
      </svg>
    `;
  }

  function moveIconSvg() {
    return `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 7h6l2 2h10v10H3z"></path>
        <path d="M14 13h5"></path>
        <path d="m17 10 3 3-3 3"></path>
      </svg>
    `;
  }

  function ensurePortalButton() {
    const existing = document.querySelector(`.${BUTTON_CLASS}.${PORTAL_BUTTON_CLASS}`);
    if (existing?.dataset.sessionDeleteVersion === VERSION) {
      portalButton = existing;
      return existing;
    }
    existing?.remove();
    const button = document.createElement("button");
    button.type = "button";
    button.className = `${ACTION_BUTTON_CLASS} ${BUTTON_CLASS} ${PORTAL_BUTTON_CLASS}`;
    button.dataset.sessionDeleteVersion = VERSION;
    button.setAttribute("aria-label", "删除");
    button.innerHTML = trashIconSvg();
    ["pointerdown", "mousedown", "mouseup", "touchstart"].forEach((eventName) => {
      button.addEventListener(eventName, stopButtonEvent, true);
    });
    button.addEventListener("pointerenter", () => {
      clearTimeout(hidePortalTimer);
      showTooltip(button, "删除");
    });
    button.addEventListener("pointerleave", () => scheduleHidePortal());
    button.addEventListener("focus", () => showTooltip(button));
    button.addEventListener("blur", () => scheduleHidePortal());
    button.addEventListener("click", (event) => {
      if (activeRow) activateDelete(activeRow, event);
      else stopButtonEvent(event);
    }, true);
    document.body.appendChild(button);
    portalButton = button;
    return button;
  }

  function cleanupPortalButton() {
    document.querySelectorAll(`.${BUTTON_CLASS}.${PORTAL_BUTTON_CLASS}`).forEach((node) => node.remove());
    portalButton = null;
    activeRow = null;
  }

  function positionPortalButton(row) {
    const button = ensurePortalButton();
    const rect = row.getBoundingClientRect?.();
    if (!rect) return;
    const left = Math.max(8, Math.min(window.innerWidth - 34, rect.right - 34));
    const top = Math.max(8, Math.min(window.innerHeight - 34, rect.top + rect.height / 2 - 13));
    button.style.left = `${left}px`;
    button.style.top = `${top}px`;
    button.dataset.visible = "true";
    activeRow = row;
  }

  function hidePortalButton() {
    hideTooltip();
    if (portalButton) portalButton.dataset.visible = "false";
    activeRow = null;
  }

  function scheduleHidePortal() {
    clearTimeout(hidePortalTimer);
    hidePortalTimer = setTimeout(() => {
      const hoveredRow = activeRow?.matches?.(":hover");
      const hoveredButton = portalButton?.matches?.(":hover");
      if (!hoveredRow && !hoveredButton) hidePortalButton();
    }, 120);
  }

  function bindPortalHover(row) {
    if (row.dataset.claudeZhCnDeleteHoverBound === VERSION) return;
    row.dataset.claudeZhCnDeleteHoverBound = VERSION;
    row.addEventListener("pointerenter", () => {
      clearTimeout(hidePortalTimer);
      positionPortalButton(row);
    });
    row.addEventListener("pointermove", () => positionPortalButton(row));
    row.addEventListener("pointerleave", () => scheduleHidePortal());
    row.addEventListener("focusin", () => positionPortalButton(row));
    row.addEventListener("focusout", () => scheduleHidePortal());
  }

  function menuCandidateText(node) {
    return [
      node.getAttribute?.("aria-label"),
      node.getAttribute?.("title"),
      node.getAttribute?.("aria-keyshortcuts"),
      node.dataset?.state,
      node.textContent
    ].filter(Boolean).join(" ").trim();
  }

  function isNativeDeleteControl(node) {
    const text = menuCandidateText(node);
    if (!/(delete|remove|删除)/i.test(text)) return false;
    if (/(deleted|delete older|remove from|archive|归档|较旧)/i.test(text)) return false;
    if (node.matches?.("[role='menuitem'],[role='option'],button,[cmdk-item]")) return true;
    return /(^|\s|>)(delete|remove|删除)\s*(?:$|\b|D\b|⌘D|Ctrl\+D)/i.test(text);
  }

  function isMenuTrigger(node) {
    const text = menuCandidateText(node).toLowerCase();
    return /more|options|menu|ellipsis|conversation options|chat options|更多|选项|菜单|会话选项|聊天选项|⋯|…/.test(text)
      || (node.textContent || "").trim() === "..."
      || (node.textContent || "").trim() === "⋯";
  }

  function possibleNativeControls(row) {
    return [...row.querySelectorAll("button,[role='button'],[aria-label],[title],[tabindex]:not([tabindex='-1'])")]
      .filter((node) => !node.classList.contains(ACTION_BUTTON_CLASS));
  }

  function clickNode(node) {
    ["pointerdown", "mousedown", "pointerup", "mouseup", "click"].forEach((type) => {
      node.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    });
  }

  function revealRowActions(row) {
    ["pointerover", "pointerenter", "mouseover", "mouseenter"].forEach((type) => {
      row.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    });
  }

  function dispatchContextMenu(row) {
    const rect = row.getBoundingClientRect?.();
    const clientX = rect ? Math.max(1, Math.round(rect.left + Math.min(rect.width - 8, Math.max(8, rect.width - 32)))) : 12;
    const clientY = rect ? Math.max(1, Math.round(rect.top + rect.height / 2)) : 12;
    row.dispatchEvent(new MouseEvent("pointerdown", { bubbles: true, cancelable: true, view: window, button: 2, buttons: 2, clientX, clientY }));
    row.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, view: window, button: 2, buttons: 2, clientX, clientY }));
    row.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, view: window, button: 2, buttons: 2, clientX, clientY }));
    row.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true, view: window, button: 2, buttons: 0, clientX, clientY }));
  }

  function clickDialogConfirm() {
    const dialogs = [...document.querySelectorAll("[role='dialog'],[data-radix-dialog-content],div")].filter((node) => {
      const text = node.textContent || "";
      return visible(node) && /(delete|remove|删除)/i.test(text);
    });
    for (const dialog of dialogs) {
      const buttons = [...dialog.querySelectorAll("button,[role='button']")].filter(visible);
      const confirm = buttons.find((button) => /(delete|remove|确认|删除)/i.test(menuCandidateText(button)));
      if (confirm) {
        clickNode(confirm);
        return true;
      }
    }
    return false;
  }

  function clickDeleteMenuItem() {
    const menus = [...document.querySelectorAll("[role='menu'],[data-radix-menu-content],[cmdk-list],body")];
    for (const menu of menus) {
      const item = [...menu.querySelectorAll("button,[role='menuitem'],[role='option'],[cmdk-item],div")]
        .filter(visible)
        .find(isNativeDeleteControl);
      if (item) {
        clickNode(item);
        setTimeout(clickDialogConfirm, 160);
        setTimeout(clickDialogConfirm, 420);
        return true;
      }
    }
    return false;
  }

  async function tryNativeDelete(row) {
    revealRowActions(row);
    await new Promise((resolve) => setTimeout(resolve, 120));
    const directDelete = possibleNativeControls(row).find((node) => isNativeDeleteControl(node));
    if (directDelete) {
      clickNode(directDelete);
      setTimeout(clickDialogConfirm, 160);
      return true;
    }

    const triggers = possibleNativeControls(row).filter(isMenuTrigger);
    for (const trigger of triggers) {
      clickNode(trigger);
      for (const delay of [80, 180, 360, 700]) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        if (clickDeleteMenuItem()) return true;
      }
    }
    dispatchContextMenu(row);
    for (const delay of [80, 180, 360, 700, 1100]) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      if (clickDeleteMenuItem()) return true;
    }
    return false;
  }

  function localDeleteBridgeReady() {
    return !!globalThis[LOCAL_DELETE_BRIDGE]?.enabled;
  }

  async function tryLocalSessionDelete(row) {
    const sessionId = localSessionId(row);
    if (!sessionId) return { ok: false, error: "不是本地会话" };
    if (!localDeleteBridgeReady()) return { ok: false, error: "本地删除桥未运行" };

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    globalThis[LOCAL_DELETE_QUEUE] = Array.isArray(globalThis[LOCAL_DELETE_QUEUE]) ? globalThis[LOCAL_DELETE_QUEUE] : [];
    globalThis[LOCAL_DELETE_RESULTS] = globalThis[LOCAL_DELETE_RESULTS] || {};
    globalThis[LOCAL_DELETE_QUEUE].push({
      requestId,
      sessionId,
      title: rowTitle(row),
      href: rowHref(row)
    });

    const deadline = Date.now() + 12000;
    while (Date.now() < deadline) {
      const result = globalThis[LOCAL_DELETE_RESULTS]?.[requestId];
      if (result) {
        delete globalThis[LOCAL_DELETE_RESULTS][requestId];
        return result;
      }
      await new Promise((resolve) => setTimeout(resolve, 240));
    }
    return { ok: false, sessionId, error: "本地删除桥无响应" };
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function confirmDelete(title) {
    document.querySelectorAll(".claude-zh-cn-session-delete-confirm-overlay").forEach((node) => node.remove());
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "claude-zh-cn-session-delete-confirm-overlay";
      overlay.innerHTML = `
        <div class="claude-zh-cn-session-delete-confirm-content" role="dialog" aria-modal="true" aria-label="删除会话">
          <div class="claude-zh-cn-session-delete-confirm-title">删除会话</div>
          <div class="claude-zh-cn-session-delete-confirm-message">删除“${escapeHtml(title || "当前会话")}”？</div>
          <div class="claude-zh-cn-session-delete-confirm-actions">
            <button type="button" data-claude-delete-cancel>取消</button>
            <button type="button" data-claude-delete-confirm>删除</button>
          </div>
        </div>
      `;
      const finish = (value, event) => {
        event?.preventDefault();
        event?.stopPropagation();
        overlay.remove();
        resolve(value);
      };
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay || event.target.closest("[data-claude-delete-cancel]")) finish(false, event);
        if (event.target.closest("[data-claude-delete-confirm]")) finish(true, event);
      }, true);
      overlay.addEventListener("keydown", (event) => {
        if (event.key === "Escape") finish(false, event);
      }, true);
      document.body.appendChild(overlay);
      overlay.querySelector("[data-claude-delete-cancel]")?.focus();
    });
  }

  async function activateDelete(row, event) {
    stopButtonEvent(event);
    hideTooltip();
    const title = rowTitle(row);
    if (!(await confirmDelete(title))) return;
    clearTimeout(pendingDeleteTimer);
    row.dataset.claudeZhCnPendingDelete = "true";
    showUndoToast(`已删除“${title || "当前会话"}”`, () => {
      clearTimeout(pendingDeleteTimer);
      pendingDeleteTimer = 0;
      row.dataset.claudeZhCnPendingDelete = "false";
      showToast("已恢复");
    });
    pendingDeleteTimer = setTimeout(async () => {
      pendingDeleteTimer = 0;
      const localId = localSessionId(row);
      if (localId && localDeleteBridgeReady()) {
        const localDeleted = await tryLocalSessionDelete(row);
        if (localDeleted?.ok) {
          showToast("本地会话已移入隔离目录");
          if (isCurrentRow(row)) setTimeout(() => window.dispatchEvent(new Event("resize")), 300);
          return;
        }
        row.dataset.claudeZhCnPendingDelete = "false";
        showToast(localDeleted?.error || "本地会话删除失败");
        return;
      }

      const nativeDeleted = await tryNativeDelete(row);
      if (nativeDeleted) {
        if (isCurrentRow(row)) setTimeout(() => window.dispatchEvent(new Event("resize")), 300);
        return;
      }

      if (localId) {
        const localDeleted = await tryLocalSessionDelete(row);
        if (localDeleted?.ok) {
          showToast("本地会话已移入隔离目录");
          if (isCurrentRow(row)) setTimeout(() => window.dispatchEvent(new Event("resize")), 300);
          return;
        }
        row.dataset.claudeZhCnPendingDelete = "false";
        showToast(localDeleted?.error || "本地会话删除失败");
        return;
      }

      row.dataset.claudeZhCnPendingDelete = "false";
      showToast("未找到 Claude 自带删除入口");
    }, 4000);
  }

  function messageNodes() {
    const root = mainRoot();
    const selectors = [
      "[data-testid*='message']",
      "[data-message-author-role]",
      "[data-author]",
      "[data-testid*='human']",
      "[data-testid*='prompt']",
      "[data-testid*='question']",
      "[data-testid*='request']",
      "[data-testid*='assistant']",
      "[data-testid*='response']",
      "[data-testid*='answer']",
      "[data-testid*='user']",
      "[class*='font-claude-message']",
      "[class*='claude-message']",
      "[class*='human-message']",
      "[class*='user-message']",
      "[class*='prompt-message']",
      "[class*='claude-response']",
      "[class*='assistant']",
      "[class*='response']",
      "[class*='markdown']",
      "[class*='prose']",
      "[data-is-streaming]",
      "[class*='message']",
      "article",
      "[role='listitem']"
    ].join(",");
    return [...root.querySelectorAll(selectors)].filter((node) => {
      if (!visible(node)) return false;
      if (node.closest?.("aside,nav,[role='navigation']")) return false;
      if (node.querySelector?.("[data-message-author-role],[data-author]") && !messageRoleSignal(node)) return false;
      const text = rowVisibleText(node);
      return text.length >= 2 && text.length <= 20000;
    });
  }

  function messageRoleSignal(node) {
    const carrier = node.closest?.("[data-message-author-role],[data-author],[data-testid*='message'],article,[role='listitem']") || node;
    const data = [
      carrier.getAttribute?.("data-message-author-role"),
      carrier.getAttribute?.("data-author"),
      carrier.getAttribute?.("aria-label"),
      typeof carrier.className === "string" ? carrier.className : "",
      node.getAttribute?.("data-message-author-role"),
      node.getAttribute?.("data-author"),
      node.getAttribute?.("data-testid"),
      node.getAttribute?.("aria-label"),
      typeof node.className === "string" ? node.className : ""
    ].filter(Boolean).join(" ").toLowerCase();
    if (/user|human|you|我|用户/.test(data)) return "用户";
    if (/assistant|claude|model|助手/.test(data)) return "Claude";
    return "";
  }

  function isAssistantContentNode(node) {
    const data = [
      node.getAttribute?.("data-testid"),
      node.getAttribute?.("data-is-streaming"),
      node.getAttribute?.("aria-label"),
      typeof node.className === "string" ? node.className : ""
    ].filter(Boolean).join(" ").toLowerCase();
    return /assistant|claude|model|response|answer|markdown|prose|streaming|助手|回复/.test(data);
  }

  function messageRole(node) {
    const signal = messageRoleSignal(node);
    if (signal) return signal;
    if (isAssistantContentNode(node)) return "Claude";
    const text = rowVisibleText(node).slice(0, 80);
    if (/^(you|你|我)[:：]/i.test(text)) return "用户";
    if (/^claude[:：]/i.test(text)) return "Claude";
    return "";
  }

  function currentConversationTitle() {
    const heading = mainRoot().querySelector?.("h1") || document.querySelector("h1");
    return (heading?.textContent || document.title || "Claude 会话").replace(/\s+/g, " ").trim();
  }

  function buildConversationMarkdown() {
    const title = currentConversationTitle();
    const parts = [`# ${title}`, "", `导出时间：${new Date().toLocaleString()}`, ""];
    const nodes = messageNodes();
    const seen = new Set();
    let lastRole = "";
    nodes.forEach((node) => {
      const text = rowVisibleText(node);
      if (!text || seen.has(text)) return;
      seen.add(text);
      let role = messageRole(node);
      if (!role && lastRole === "用户") role = "Claude";
      role = role || "消息";
      lastRole = role;
      parts.push(`## ${role}`, "", text, "");
    });
    if (parts.length <= 4) {
      const fallback = rowVisibleText(mainRoot());
      if (fallback) parts.push("## 内容", "", fallback, "");
    }
    return parts.join("\n").replace(/\n{4,}/g, "\n\n\n");
  }

  function safeFileName(value) {
    return String(value || "Claude 会话")
      .replace(/[\\/:*?"<>|]+/g, "-")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 80) || "Claude 会话";
  }

  function timestampForFile() {
    const pad = (value) => String(value).padStart(2, "0");
    const date = new Date();
    return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}-${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
  }

  function downloadMarkdown(markdown) {
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${safeFileName(currentConversationTitle())}-${timestampForFile()}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function activateExport(row, event) {
    stopButtonEvent(event);
    hideTooltip();
    downloadMarkdown(buildConversationMarkdown());
    showToast(`已导出：${rowTitle(row) || currentConversationTitle()}`);
  }

  function isNativeMoveControl(node) {
    return /move|project|移动|移至|项目/i.test(menuCandidateText(node));
  }

  function discoverOrganizationUuid() {
    const patterns = [
      /\/api\/organizations\/([0-9a-f-]{12,})/i,
      /"activeOrganization"\s*:\s*\{[^}]*"uuid"\s*:\s*"([0-9a-f-]{12,})"/i,
      /"organization_uuid"\s*:\s*"([0-9a-f-]{12,})"/i,
      /"orgUuid"\s*:\s*"([0-9a-f-]{12,})"/i
    ];
    const sources = [location.href, document.documentElement.innerHTML.slice(0, 300000)];
    for (const storage of [localStorage, sessionStorage]) {
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);
        if (!key) continue;
        const value = storage.getItem(key) || "";
        if (/org|organization|account|user|auth/i.test(key + value.slice(0, 200))) sources.push(`${key}:${value}`);
      }
    }
    for (const source of sources) {
      for (const pattern of patterns) {
        const match = source.match(pattern);
        if (match?.[1]) return match[1];
      }
    }
    return "";
  }

  async function fetchProjects(orgUuid) {
    const params = new URLSearchParams({
      include_harmony_projects: "true",
      limit: "100",
      offset: "0",
      order_by: "updated_at"
    });
    const response = await fetch(`/api/organizations/${orgUuid}/projects?${params}`, {
      credentials: "include",
      headers: { "Accept": "application/json" }
    });
    if (!response.ok) throw new Error(`projects ${response.status}`);
    const data = await response.json();
    const projects = Array.isArray(data) ? data : Array.isArray(data.data) ? data.data : Array.isArray(data.projects) ? data.projects : [];
    return projects
      .filter((project) => project && !project.archived_at && project.uuid && project.name)
      .map((project) => ({ uuid: project.uuid, name: project.name }));
  }

  async function moveConversationToProject(conversationUuid, projectUuid) {
    const orgUuid = discoverOrganizationUuid();
    if (!orgUuid) throw new Error("missing organization uuid");
    const response = await fetch(`/api/organizations/${orgUuid}/chat_conversations/move_many`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ conversation_uuids: [conversationUuid], project_uuid: projectUuid || null })
    });
    if (!response.ok) throw new Error(`move ${response.status}`);
    return response.json();
  }

  function showMoveDialog(row, projects) {
    document.querySelectorAll(".claude-zh-cn-session-delete-confirm-overlay").forEach((node) => node.remove());
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "claude-zh-cn-session-delete-confirm-overlay";
      const buttons = [
        `<button type="button" data-claude-move-project="">普通对话</button>`,
        ...projects.map((project) => `<button type="button" data-claude-move-project="${escapeHtml(project.uuid)}">${escapeHtml(project.name)}</button>`)
      ].join("");
      overlay.innerHTML = `
        <div class="claude-zh-cn-session-delete-confirm-content" role="dialog" aria-modal="true" aria-label="移动会话">
          <div class="claude-zh-cn-session-delete-confirm-title">移至项目</div>
          <div class="claude-zh-cn-session-delete-confirm-message">移动“${escapeHtml(rowTitle(row) || "当前会话")}”</div>
          <div class="claude-zh-cn-session-move-list">${buttons}</div>
          <div class="claude-zh-cn-session-delete-confirm-actions">
            <button type="button" data-claude-delete-cancel>取消</button>
          </div>
        </div>
      `;
      const finish = (value, event) => {
        event?.preventDefault();
        event?.stopPropagation();
        overlay.remove();
        resolve(value);
      };
      overlay.addEventListener("click", (event) => {
        const moveButton = event.target.closest("[data-claude-move-project]");
        if (moveButton) finish(moveButton.getAttribute("data-claude-move-project") || null, event);
        if (event.target === overlay || event.target.closest("[data-claude-delete-cancel]")) finish(undefined, event);
      }, true);
      overlay.addEventListener("keydown", (event) => {
        if (event.key === "Escape") finish(undefined, event);
      }, true);
      document.body.appendChild(overlay);
      overlay.querySelector("[data-claude-move-project]")?.focus();
    });
  }

  async function tryNativeMove(row) {
    revealRowActions(row);
    await new Promise((resolve) => setTimeout(resolve, 120));
    const directMove = possibleNativeControls(row).find((node) => isNativeMoveControl(node));
    if (directMove) {
      clickNode(directMove);
      return true;
    }
    const triggers = possibleNativeControls(row).filter(isMenuTrigger);
    for (const trigger of triggers) {
      clickNode(trigger);
      for (const delay of [80, 180, 360, 700]) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        const menus = [...document.querySelectorAll("[role='menu'],[data-radix-menu-content],[cmdk-list],body")];
        for (const menu of menus) {
          const item = [...menu.querySelectorAll("button,[role='menuitem'],[role='option'],[cmdk-item],div")]
            .filter(visible)
            .find(isNativeMoveControl);
          if (item) {
            clickNode(item);
            return true;
          }
        }
      }
    }
    return false;
  }

  async function activateMove(row, event) {
    stopButtonEvent(event);
    hideTooltip();
    const conversationUuid = rowId(row) || currentConversationUuid();
    if (conversationUuid) {
      try {
        const orgUuid = discoverOrganizationUuid();
        if (!orgUuid) throw new Error("missing organization uuid");
        showToast("正在读取项目列表…");
        const projectUuid = await showMoveDialog(row, await fetchProjects(orgUuid));
        if (projectUuid !== undefined) {
          await moveConversationToProject(conversationUuid, projectUuid);
          showToast(projectUuid ? "已移动到项目" : "已移至普通对话");
          scheduleScan();
          return;
        }
        return;
      } catch (error) {
        globalThis.__CLAUDE_ZH_CN_SESSION_MOVE_STATE__ = {
          title: rowTitle(row),
          id: conversationUuid,
          href: rowHref(row),
          updatedAt: new Date().toISOString(),
          lastError: String(error?.message || error)
        };
        showToast(`移动接口失败：${String(error?.message || error)}`);
      }
    }
    showToast("正在打开 Claude 自带移动入口…");
    if (await tryNativeMove(row)) return;
    globalThis.__CLAUDE_ZH_CN_SESSION_MOVE_STATE__ = {
      title: rowTitle(row),
      id: rowId(row),
      href: rowHref(row),
      updatedAt: new Date().toISOString(),
      lastError: "未找到 Claude 自带移动入口"
    };
    showToast("未找到 Claude 自带移动入口，已记录诊断信息");
  }

  function actionButton(className, label, icon, handler, row) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `${ACTION_BUTTON_CLASS} ${className}`;
    button.dataset.sessionDeleteVersion = VERSION;
    button.setAttribute("aria-label", label);
    button.innerHTML = icon;
    ["pointerdown", "mousedown", "mouseup", "touchstart"].forEach((eventName) => {
      button.addEventListener(eventName, stopButtonEvent, true);
    });
    button.addEventListener("pointerenter", () => showTooltip(button, label));
    button.addEventListener("pointerleave", hideTooltip);
    button.addEventListener("focus", () => showTooltip(button, label));
    button.addEventListener("blur", hideTooltip);
    button.addEventListener("click", (event) => handler(row, event), true);
    return button;
  }

  function directActionButtons(row) {
    return Array.from(row?.children || []).filter((node) => node.classList?.contains(ACTION_BUTTON_CLASS) && !node.classList?.contains(PORTAL_BUTTON_CLASS));
  }

  function removeDirectActionButtons(row) {
    directActionButtons(row).forEach((node) => node.remove());
  }

  function attachedAncestorActionRow(row) {
    for (let current = row?.parentElement; current && current !== document.body; current = current.parentElement) {
      if (current.getAttribute?.(ROW_FLAG) === "true" && directActionButtons(current).length) return current;
      const rect = current.getBoundingClientRect?.();
      if (rect && (rect.width > 620 || rect.height > 280)) return null;
    }
    return null;
  }

  function cleanupNestedActionRows(row) {
    row.querySelectorAll?.(`[${ROW_FLAG}="true"]`).forEach((nested) => {
      if (nested === row) return;
      nested.removeAttribute(ROW_FLAG);
      removeDirectActionButtons(nested);
    });
  }

  function attachRow(row) {
    if (!looksLikeSidebarSessionRow(row)) return;
    if (attachedAncestorActionRow(row)) {
      removeDirectActionButtons(row);
      row.removeAttribute(ROW_FLAG);
      return;
    }
    cleanupNestedActionRows(row);
    row.setAttribute(ROW_FLAG, "true");
    const existing = directActionButtons(row)[0];
    if (existing?.dataset.sessionDeleteVersion === VERSION) return;
    removeDirectActionButtons(row);
    row.appendChild(actionButton(MOVE_BUTTON_CLASS, "移动", moveIconSvg(), activateMove, row));
    row.appendChild(actionButton(EXPORT_BUTTON_CLASS, "导出", exportIconSvg(), activateExport, row));
    row.appendChild(actionButton(BUTTON_CLASS, "删除", trashIconSvg(), activateDelete, row));
  }

  function cleanupRejectedRows() {
    document.querySelectorAll(`[${ROW_FLAG}="true"]`).forEach((row) => {
      if (looksLikeSidebarSessionRow(row)) return;
      row.removeAttribute(ROW_FLAG);
      removeDirectActionButtons(row);
    });
  }

  function candidateRows() {
    const rows = new Map();
    recentSectionRoots().forEach(({ panel, marker }) => {
      candidateNodesForSection(panel, marker).forEach((node) => {
        const row = recentsRowContainer(node);
        const normalized = normalizeRecentsRow(row);
        if (!looksLikeSidebarSessionRow(normalized)) return;
        const key = recentsRowKey(normalized);
        if (!key) return;
        rows.set(key, preferRecentsRow(rows.get(key), normalized));
      });
    });
    return [...rows.values()];
  }

  function candidateRowSamples(rows) {
    return rows.slice(0, 12).map((row) => {
      const rect = row.getBoundingClientRect?.();
      return {
        tag: row.tagName,
        title: rowTitle(row),
        text: rowVisibleText(row).slice(0, 120),
        id: rowId(row),
        href: rowHref(row),
        signal: hasSessionSignal(row),
        rejectReason: sessionRowRejectReason(row),
        rect: rect ? { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) } : null
      };
    });
  }

  function userQuestionNodes() {
    const direct = [...mainRoot().querySelectorAll("[data-message-author-role='user'],[data-author='user'],[data-testid*='human'],[data-testid*='prompt'],[data-testid*='question'],[class*='human-message'],[class*='user-message'],[class*='prompt-message']")]
      .filter(visible)
      .filter((node) => messageRole(node) === "用户" || !messageRole(node));
    if (direct.length) return direct;
    return messageNodes().filter((node) => messageRole(node) === "用户");
  }

  function summarizeQuestion(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 64);
  }

  function timelineSummaryFor(node) {
    const raw = String(node?.textContent || "");
    const cached = timelineSummaryCache.get(node);
    if (cached && cached.raw === raw) return cached.summary;
    const summary = summarizeQuestion(rowVisibleText(node));
    timelineSummaryCache.set(node, { raw, summary });
    return summary;
  }

  function ensureTimeline() {
    let timeline = document.getElementById(TIMELINE_ID);
    if (timeline) return timeline;
    timeline = document.createElement("div");
    timeline.id = TIMELINE_ID;
    timeline.setAttribute("aria-label", "对话时间线");
    document.body.appendChild(timeline);
    return timeline;
  }

  function renderTimeline() {
    lastTimelineRunAt = performance?.now?.() || Date.now();
    const timeline = ensureTimeline();
    const questions = userQuestionNodes().slice(0, 80);
    const items = [];
    questions.forEach((node, index) => {
      if (!node.id) node.id = `claude-zh-cn-user-question-${index + 1}`;
      const summary = timelineSummaryFor(node);
      if (!summary) return;
      items.push({ node, index, summary });
    });
    const signature = items.map((item) => `${item.node.id}:${item.summary}`).join("|");
    if (signature && signature === lastTimelineSignature && timeline.children.length === items.length) {
      globalThis.__CLAUDE_ZH_CN_CONVERSATION_TIMELINE_STATE__ = {
        version: VERSION,
        count: timeline.children.length,
        updatedAt: new Date().toISOString(),
        skipped: true
      };
      return;
    }
    lastTimelineSignature = signature;
    const buttons = [];
    items.forEach(({ node, summary }) => {
      const button = document.createElement("button");
      button.type = "button";
      const summaryNode = document.createElement("span");
      summaryNode.className = "claude-zh-cn-timeline-summary";
      summaryNode.textContent = summary;
      button.appendChild(summaryNode);
      button.title = summary;
      button.addEventListener("click", (event) => {
        stopButtonEvent(event);
        node.scrollIntoView({ block: "center", behavior: "smooth" });
      }, true);
      buttons.push(button);
    });
    if (timeline.replaceChildren) timeline.replaceChildren(...buttons);
    else {
      timeline.querySelectorAll("button").forEach((node) => node.remove());
      buttons.forEach((button) => timeline.appendChild(button));
    }
    globalThis.__CLAUDE_ZH_CN_CONVERSATION_TIMELINE_STATE__ = {
      version: VERSION,
      count: timeline.children.length,
      questionCount: questions.length,
      messageCount: messageNodes().length,
      updatedAt: new Date().toISOString()
    };
  }

  let timelineTimer = 0;
  let timelineTimerDueAt = 0;
  let lastTimelineRunAt = 0;
  let lastMainMutationAt = 0;
  function hasQuickConversationContent() {
    return !!mainRoot().querySelector?.("[data-message-author-role='user'],[data-author='user'],[data-testid*='message'],[data-testid*='human'],[data-testid*='prompt'],[data-testid*='question'],[class*='font-claude-message'],[class*='claude-message'],[class*='human-message'],[class*='user-message'],article");
  }

  function hasConversationContent() {
    return userQuestionNodes().length > 0;
  }

  function isConversationPage() {
    return !!currentConversationUuid()
      || /\/(?:chat|conversation|thread|session)\//i.test(location.pathname || location.href || "")
      || hasQuickConversationContent();
  }

  function runTimelineRenderWhenIdle() {
    timelineTimer = 0;
    timelineTimerDueAt = 0;
    if (!isConversationPage()) {
      document.getElementById(TIMELINE_ID)?.remove();
      globalThis.__CLAUDE_ZH_CN_CONVERSATION_TIMELINE_STATE__ = {
        version: VERSION,
        count: 0,
        questionCount: 0,
        messageCount: 0,
        updatedAt: new Date().toISOString()
      };
      return;
    }
    const now = performance?.now?.() || Date.now();
    if (lastMainMutationAt && now - lastMainMutationAt < 900) {
      scheduleTimelineRender(900 - (now - lastMainMutationAt));
      return;
    }
    const idle = window.requestIdleCallback || ((callback) => setTimeout(callback, 80));
    idle(renderTimeline, { timeout: 900 });
  }

  function scheduleTimelineRender(delay = TIMELINE_DELAY_MS) {
    if (!isConversationPage()) {
      runTimelineRenderWhenIdle();
      return;
    }
    const now = performance?.now?.() || Date.now();
    const timeline = document.getElementById(TIMELINE_ID);
    const hasVisibleTimeline = !!(timeline && timeline.children.length);
    if (lastTimelineRunAt && hasVisibleTimeline) delay = Math.max(delay, TIMELINE_MIN_INTERVAL_MS - (now - lastTimelineRunAt));
    const dueAt = now + delay;
    if (timelineTimer) {
      if (!hasVisibleTimeline && dueAt < timelineTimerDueAt - 50) {
        clearTimeout(timelineTimer);
        timelineTimer = 0;
      } else {
        return;
      }
    }
    timelineTimerDueAt = dueAt;
    timelineTimer = setTimeout(runTimelineRenderWhenIdle, delay);
  }

  function currentScrollKey() {
    return `${SCROLL_STORAGE_PREFIX}${location.pathname}${location.search}`;
  }

  function scrollContainer() {
    const candidates = [
      document.querySelector("main"),
      document.querySelector("[role='main']"),
      document.scrollingElement,
      document.documentElement
    ].filter(Boolean);
    return candidates.find((node) => node.scrollHeight > node.clientHeight + 20) || document.scrollingElement || document.documentElement;
  }

  function rememberScrollPosition() {
    try {
      const container = scrollContainer();
      sessionStorage.setItem(currentScrollKey(), String(container.scrollTop || window.scrollY || 0));
    } catch {
      return;
    }
  }

  let scrollSaveTimer = 0;
  function scheduleRememberScrollPosition() {
    if (scrollSaveTimer) return;
    scrollSaveTimer = setTimeout(() => {
      scrollSaveTimer = 0;
      rememberScrollPosition();
    }, 450);
  }

  function restoreScrollPosition() {
    try {
      const stored = sessionStorage.getItem(currentScrollKey());
      if (stored == null) return;
      const value = Number(stored);
      if (!Number.isFinite(value)) return;
      const container = scrollContainer();
      setTimeout(() => {
        container.scrollTop = value;
        if (container === document.scrollingElement || container === document.documentElement) window.scrollTo(window.scrollX, value);
      }, 160);
    } catch {
      return;
    }
  }

  function centeredLayoutWidth() {
    const raw = localStorage.getItem(CENTERED_WIDTH_KEY) || "980";
    const value = Number(String(raw).replace(/[^\d.]/g, ""));
    if (!Number.isFinite(value)) return 980;
    return Math.max(640, Math.min(1600, Math.round(value)));
  }

  function isThirdPartyProviderSettingsPage() {
    const root = document.querySelector("main,[role='main']") || document.body;
    const now = performance?.now?.() || Date.now();
    const key = `${location.pathname}:${root?.textContent?.length || 0}`;
    if (providerSettingsCache.key === key && now - providerSettingsCache.at < 1200) return providerSettingsCache.value;
    const text = (root?.textContent || "").slice(0, 12000);
    const hasProviderTitle = /(管理第三方供应商|第三方供应商|Manage third-party|Inference provider)/i.test(text);
    const hasProviderFields = /(第三方认证方案|自定义推理标头|Authorization|x-api-key|模型发现|测试模型发现|Gateway base URL|Gateway API key)/i.test(text);
    providerSettingsCache = { key, at: now, value: hasProviderTitle && hasProviderFields };
    return providerSettingsCache.value;
  }

  function shouldShowCenteredLayoutControls() {
    return !isThirdPartyProviderSettingsPage();
  }

  function applyCenteredLayout(enabled) {
    document.documentElement.style.setProperty("--claude-zh-cn-centered-width", `${centeredLayoutWidth()}px`);
    document.documentElement.classList.toggle(CENTERED_CLASS, !!enabled);
    const button = document.getElementById(CENTERED_TOGGLE_ID);
    if (button) {
      const showControl = shouldShowCenteredLayoutControls();
      button.style.display = showControl ? "" : "none";
      if (!showControl) document.querySelectorAll(".claude-zh-cn-centered-width-dialog").forEach((node) => node.remove());
      button.textContent = enabled ? `居中 ${centeredLayoutWidth()}` : "居中关";
      button.title = "点击开关，右键或双击设置宽度";
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
    }
  }

  function centeredLayoutEnabled() {
    return localStorage.getItem("claude-zh-cn-centered-layout") === "1";
  }

  function toggleCenteredLayout(event) {
    event?.preventDefault();
    event?.stopPropagation();
    const next = !centeredLayoutEnabled();
    localStorage.setItem("claude-zh-cn-centered-layout", next ? "1" : "0");
    applyCenteredLayout(next);
  }

  function showCenteredWidthDialog(event) {
    event?.preventDefault();
    event?.stopPropagation();
    document.querySelectorAll(".claude-zh-cn-centered-width-dialog").forEach((node) => node.remove());
    const dialog = document.createElement("div");
    dialog.className = "claude-zh-cn-centered-width-dialog";
    dialog.innerHTML = `
      <label>自定义居中宽度</label>
      <input type="number" min="640" max="1600" step="20" value="${centeredLayoutWidth()}" aria-label="居中宽度">
      <div class="claude-zh-cn-centered-width-dialog-actions">
        <button type="button" data-centered-cancel>取消</button>
        <button type="button" data-centered-save>保存</button>
      </div>
    `;
    const close = () => dialog.remove();
    const save = () => {
      const input = dialog.querySelector("input");
      const next = Number(String(input?.value || "").replace(/[^\d.]/g, ""));
      if (Number.isFinite(next)) localStorage.setItem(CENTERED_WIDTH_KEY, String(Math.max(640, Math.min(1600, Math.round(next)))));
      localStorage.setItem("claude-zh-cn-centered-layout", "1");
      applyCenteredLayout(true);
      close();
    };
    dialog.addEventListener("click", (clickEvent) => {
      clickEvent.stopPropagation();
      if (clickEvent.target.closest("[data-centered-save]")) save();
      if (clickEvent.target.closest("[data-centered-cancel]")) close();
    }, true);
    dialog.addEventListener("keydown", (keyEvent) => {
      if (keyEvent.key === "Enter") save();
      if (keyEvent.key === "Escape") close();
    }, true);
    document.body.appendChild(dialog);
    dialog.querySelector("input")?.focus();
  }

  function ensureCenteredLayoutToggle() {
    if (document.getElementById(CENTERED_TOGGLE_ID)) return;
    const button = document.createElement("button");
    button.id = CENTERED_TOGGLE_ID;
    button.type = "button";
    button.addEventListener("click", toggleCenteredLayout, true);
    button.addEventListener("contextmenu", showCenteredWidthDialog, true);
    button.addEventListener("dblclick", showCenteredWidthDialog, true);
    document.body.appendChild(button);
    applyCenteredLayout(centeredLayoutEnabled());
  }

  function scanRows() {
    const startedAt = performance?.now?.() || Date.now();
    lastScanRunAt = startedAt;
    try {
      invalidateScanCache();
      resetVisibleTextCache();
      installStyle();
      cleanupPortalButton();
      ensureCenteredLayoutToggle();
      cleanupRejectedRows();
      const rows = candidateRows();
      rows.forEach(attachRow);
      globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ = {
        version: VERSION,
        panelCount: sessionPanelRoots().length,
        sectionCount: recentSectionRoots().length,
        candidateCount: rows.length,
        attachedCount: document.querySelectorAll(`.${ACTION_BUTTON_CLASS}:not(.${PORTAL_BUTTON_CLASS})`).length,
        candidates: globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_DEBUG__ ? candidateRowSamples(rows) : [],
        portalButton: !!portalButton,
        portalVisible: portalButton?.dataset.visible === "true",
        localDeleteBridge: localDeleteBridgeReady(),
        activeTitle: activeRow ? rowTitle(activeRow) : "",
        exportButtonCount: document.querySelectorAll(`.${EXPORT_BUTTON_CLASS}`).length,
        moveButtonCount: document.querySelectorAll(`.${MOVE_BUTTON_CLASS}`).length,
        timelineCount: document.getElementById(TIMELINE_ID)?.children.length || 0,
        centeredLayout: centeredLayoutEnabled(),
        mutationRecords: lastMutationSummary.records,
        mutationInspectedRecords: lastMutationSummary.inspectedRecords,
        mutationInspectedNodes: lastMutationSummary.inspectedNodes,
        mutationSkippedInjected: lastMutationSummary.skippedInjected,
        mutationCapped: lastMutationSummary.capped,
        scanDurationMs: Math.round(((performance?.now?.() || Date.now()) - startedAt) * 10) / 10,
        lastError: "",
        updatedAt: new Date().toISOString()
      };
    } catch (error) {
      const lastError = String(error?.message || error);
      globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ = {
        version: VERSION,
        panelCount: 0,
        sectionCount: 0,
        candidateCount: 0,
        attachedCount: document.querySelectorAll(`.${ACTION_BUTTON_CLASS}:not(.${PORTAL_BUTTON_CLASS})`).length,
        candidates: [],
        portalButton: !!portalButton,
        portalVisible: portalButton?.dataset.visible === "true",
        localDeleteBridge: localDeleteBridgeReady(),
        activeTitle: activeRow ? rowTitle(activeRow) : "",
        exportButtonCount: document.querySelectorAll(`.${EXPORT_BUTTON_CLASS}`).length,
        moveButtonCount: document.querySelectorAll(`.${MOVE_BUTTON_CLASS}`).length,
        timelineCount: document.getElementById(TIMELINE_ID)?.children.length || 0,
        centeredLayout: centeredLayoutEnabled(),
        mutationRecords: lastMutationSummary.records,
        mutationInspectedRecords: lastMutationSummary.inspectedRecords,
        mutationInspectedNodes: lastMutationSummary.inspectedNodes,
        mutationSkippedInjected: lastMutationSummary.skippedInjected,
        mutationCapped: lastMutationSummary.capped,
        lastError,
        updatedAt: new Date().toISOString()
      };
    }
  }

  let scanTimer = 0;
  let lastScanRunAt = 0;
  function runScanWhenIdle() {
    scanTimer = 0;
    const idle = window.requestIdleCallback || ((callback) => setTimeout(callback, 80));
    idle(scanRows, { timeout: 900 });
  }

  function scheduleScan(delay = SCAN_DELAY_MS) {
    if (scanTimer) return;
    const now = performance?.now?.() || Date.now();
    if (lastScanRunAt) delay = Math.max(delay, SCAN_MIN_INTERVAL_MS - (now - lastScanRunAt));
    scanTimer = setTimeout(runScanWhenIdle, delay);
  }

  function isInjectedRuntimeNode(node) {
    if (!node || node.nodeType !== 1) return false;
    if (node.id === TIMELINE_ID || node.id === CENTERED_TOGGLE_ID) return true;
    if (node.classList?.contains(ACTION_BUTTON_CLASS)) return true;
    if (node.classList?.contains(TOOLTIP_CLASS) || node.classList?.contains(TOAST_CLASS)) return true;
    if (node.classList?.contains("claude-zh-cn-session-delete-confirm-overlay")) return true;
    if (node.classList?.contains("claude-zh-cn-centered-width-dialog")) return true;
    return !!node.closest?.(`#${TIMELINE_ID},#${CENTERED_TOGGLE_ID},.${ACTION_BUTTON_CLASS},.${TOOLTIP_CLASS},.${TOAST_CLASS},.claude-zh-cn-session-delete-confirm-overlay,.claude-zh-cn-centered-width-dialog`);
  }

  function nodeTouchesSidebar(node) {
    if (!node || node.nodeType !== 1) return false;
    if (node.closest?.(SIDEBAR_CONTAINER_SELECTORS) || node.matches?.(SIDEBAR_CONTAINER_SELECTORS)) return true;
    if (node.closest?.(MAIN_CONTAINER_SELECTORS) || node.matches?.(MAIN_CONTAINER_SELECTORS)) return false;
    return scopedSelectorMatch(node, SIDEBAR_CONTAINER_SELECTORS)
      || scopedSelectorMatch(node, SESSION_SIGNAL_SELECTORS);
  }

  function nodeTouchesMain(node) {
    if (!node || node.nodeType !== 1) return false;
    if (node.closest?.(MAIN_CONTAINER_SELECTORS) || node.matches?.(MAIN_CONTAINER_SELECTORS)) return true;
    if (node.closest?.(SIDEBAR_CONTAINER_SELECTORS) || node.matches?.(SIDEBAR_CONTAINER_SELECTORS)) return false;
    return scopedSelectorMatch(node, MAIN_CONTAINER_SELECTORS);
  }

  function isLargeMutationScope(node) {
    if (!node || node.nodeType !== 1) return false;
    if (node === document.body || node === document.documentElement) return true;
    const childCount = node.childElementCount || 0;
    if (childCount > 120) return true;
    const rect = node.getBoundingClientRect?.();
    const widthLimit = Math.max(720, (window.innerWidth || 1200) * 0.75);
    const heightLimit = Math.max(520, (window.innerHeight || 800) * 0.75);
    return !!rect && rect.width > widthLimit && rect.height > heightLimit;
  }

  function scopedSelectorMatch(node, selector) {
    if (!node || node.nodeType !== 1) return false;
    if (node.matches?.(selector)) return true;
    if (isLargeMutationScope(node)) {
      const children = Array.from(node.children || []).slice(0, 24);
      return children.some((child) => child.matches?.(selector));
    }
    return !!node.querySelector?.(selector);
  }

  function mutationElementNodes(mutation, remaining) {
    const nodes = [];
    const push = (node) => {
      if (nodes.length >= remaining) return;
      if (!node || node.nodeType !== 1 || nodes.includes(node)) return;
      nodes.push(node);
    };
    if (mutation.type === "attributes") {
      push(mutation.target);
    } else {
      for (const node of mutation.addedNodes || []) push(node);
      for (const node of mutation.removedNodes || []) push(node);
    }
    return nodes;
  }

  function handlePageMutations(mutations) {
    const list = Array.from(mutations || []);
    if (!list.length) {
      scheduleScan();
      scheduleTimelineRender();
      return;
    }
    let sidebarChanged = false;
    let mainChanged = false;
    let inspectedRecords = 0;
    let inspectedNodes = 0;
    let skippedInjected = 0;
    let capped = list.length > MUTATION_RECORD_LIMIT;
    for (const mutation of list.slice(0, MUTATION_RECORD_LIMIT)) {
      inspectedRecords += 1;
      const remaining = MUTATION_NODE_LIMIT - inspectedNodes;
      if (remaining <= 0) {
        capped = true;
        break;
      }
      const nodes = mutationElementNodes(mutation, remaining);
      inspectedNodes += nodes.length;
      if (nodes.length && nodes.every(isInjectedRuntimeNode)) {
        skippedInjected += 1;
        continue;
      }
      if (!sidebarChanged && nodes.some(nodeTouchesSidebar)) sidebarChanged = true;
      if (!mainChanged && nodes.some(nodeTouchesMain)) mainChanged = true;
      if (sidebarChanged && mainChanged) break;
    }
    lastMutationSummary = {
      records: list.length,
      inspectedRecords,
      inspectedNodes,
      skippedInjected,
      capped
    };
    if (sidebarChanged) scheduleScan();
    if (mainChanged) {
      lastMainMutationAt = performance?.now?.() || Date.now();
      scheduleTimelineRender(900);
    }
  }

  let pointerAttachTimer = 0;
  let pointerAttachTarget = null;
  let lastPointerAttachRow = null;
  function attachPointerTarget() {
    pointerAttachTimer = 0;
    const target = pointerAttachTarget;
    pointerAttachTarget = null;
    if (!target || target.nodeType !== 1 || isInjectedRuntimeNode(target) || !nodeTouchesSidebar(target)) return;
    const row = normalizeRecentsRow(recentsRowContainer(target));
    if (row === lastPointerAttachRow && row.getAttribute?.(ROW_FLAG) === "true" && directActionButtons(row).length) return;
    lastPointerAttachRow = row;
    if (looksLikeModeOrToolbarChrome(row, rowVisibleText(row))) return;
    if (looksLikeSidebarSessionRow(row)) attachRow(row);
  }

  function handleSidebarPointer(event) {
    const target = event.target;
    if (!target || target.nodeType !== 1 || isInjectedRuntimeNode(target)) return;
    pointerAttachTarget = target;
    if (pointerAttachTimer) return;
    pointerAttachTimer = setTimeout(attachPointerTarget, POINTER_ATTACH_DELAY_MS);
  }

  function start() {
    installStyle();
    ensureCenteredLayoutToggle();
    scheduleScan(STARTUP_SCAN_DELAY_MS);
    scheduleTimelineRender(STARTUP_TIMELINE_DELAY_MS);
    restoreScrollPosition();
    document.body?.removeEventListener?.("pointerover", handleSidebarPointer, true);
    document.body?.addEventListener?.("pointerover", handleSidebarPointer, true);
    window.removeEventListener("scroll", scheduleRememberScrollPosition, true);
    window.addEventListener("scroll", scheduleRememberScrollPosition, true);
    window.removeEventListener("beforeunload", rememberScrollPosition, true);
    window.addEventListener("beforeunload", rememberScrollPosition, true);
    window.__CLAUDE_ZH_CN_SESSION_DELETE_OBSERVER__?.disconnect?.();
    window.__CLAUDE_ZH_CN_SESSION_DELETE_OBSERVER__ = new MutationObserver(handlePageMutations);
    window.__CLAUDE_ZH_CN_SESSION_DELETE_OBSERVER__.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true
    });
    window.__CLAUDE_ZH_CN_SESSION_DELETE_INTERVAL__ && clearInterval(window.__CLAUDE_ZH_CN_SESSION_DELETE_INTERVAL__);
    window.__CLAUDE_ZH_CN_SESSION_DELETE_INTERVAL__ = setInterval(() => {
      rememberScrollPosition();
    }, 4000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
  if (globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_DEBUG__) {
    globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_DEBUG_API__ = {
      sessionPanelRoots,
      recentSectionRoots,
      sessionRowRejectReason,
      candidateRows,
      looksLikeSidebarSessionRow,
      normalizeRecentsRow,
      recentsRowContainer,
      hasSessionSignal,
      isCurrentSidebarItem,
      isInsideRecentsSection,
      localSessionId,
      localDeleteBridgeReady,
      messageNodes,
      messageRole,
      buildConversationMarkdown
    };
  }
  } catch (error) {
    try {
      globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__ = false;
      globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH_VERSION__ = VERSION;
      globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ = {
        version: VERSION,
        enabled: false,
        candidateCount: 0,
        attachedCount: 0,
        timelineCount: 0,
        lastError: String(error?.message || error),
        updatedAt: new Date().toISOString()
      };
      console.warn?.("[claude-zh-cn] session controls disabled:", error);
    } catch {}
  }
})();
'''.strip()
    return "\n".join([
        "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_BEGIN__",
        body,
        "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_END__",
    ])


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


def find_claude_package() -> Path | None:
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


def find_patch_targets(assets_dir: Path, pattern: str, replacements: list[tuple[str, str]]) -> list[Path]:
    files = sorted(assets_dir.glob(pattern))
    if files:
        return files

    needles = [old for old, new in replacements if old != new]
    if not needles:
        return []

    targets: list[Path] = []
    for path in sorted(assets_dir.glob("*.js")):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(needle in content for needle in needles):
            targets.append(path)
    return targets


def backup_file(path: Path, assets_dir: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(assets_dir)
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
            print(f"Warning: cannot copy {context} from {src} to {dst}: {e}; skipping")
            return False
    except OSError as e:
        print(f"Warning: cannot copy {context} from {src} to {dst}: {e}; skipping")
        return False


def set_font_config_mirror() -> bool:
    """Mirror default font config into Claude config without changing app behavior."""
    if not CONFIG_PATH.exists():
        return False

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    data.setdefault(
        FONT_KEY,
        {
            "mode": "preset",
            "presetId": "windows-modern",
            "family": FONT_PRESETS[0]["family"],
        },
    )
    return write_text_best_effort(
        CONFIG_PATH,
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        context="font config mirror",
    )


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


def patch_font_runtime(assets_dir: Path) -> int:
    """Inject runtime font customizer into the entry bundle."""
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        print("Warning: no index-*.js found; skipping font runtime patch")
        return 0

    script = font_inject_script()
    marker = "__CLAUDE_ZH_CN_FONT_PATCH__"
    begin_marker = "// __CLAUDE_ZH_CN_FONT_PATCH_BEGIN__"
    end_marker = "// __CLAUDE_ZH_CN_FONT_PATCH_END__"
    changed = 0
    for path in candidates:
        backup_file(path, assets_dir)
        content = path.read_text(encoding="utf-8")
        if begin_marker in content and end_marker in content:
            start = content.index(begin_marker)
            end = content.index(end_marker, start) + len(end_marker)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "updated font runtime"
        elif marker in content:
            marker_pos = content.index(marker)
            start = content.rfind(";(()=>{", 0, marker_pos)
            if start == -1:
                start = marker_pos
            legacy_end = content.find("})();", marker_pos)
            end = legacy_end + len("})();") if legacy_end != -1 else len(content)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "replaced legacy font runtime"
        else:
            new_content = content.rstrip() + "\n" + script + "\n"
            action = "injected font runtime"

        if new_content == content:
            continue
        if write_text_best_effort(path, new_content, context="font runtime patch"):
            changed += 1
            print(f"  {path.name}: {action}")
    return changed


def patch_session_delete_runtime(assets_dir: Path) -> int:
    """Inject hover delete action into the entry bundle."""
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        print("Warning: no index-*.js found; skipping session delete runtime patch")
        return 0

    script = session_delete_inject_script()
    marker = "__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__"
    begin_marker = "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_BEGIN__"
    end_marker = "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_END__"
    changed = 0
    for path in candidates:
        backup_file(path, assets_dir)
        content = path.read_text(encoding="utf-8")
        if begin_marker in content and end_marker in content:
            start = content.index(begin_marker)
            end = content.index(end_marker, start) + len(end_marker)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "updated session delete runtime"
        elif marker in content:
            marker_pos = content.index(marker)
            start = content.rfind(";(()=>{", 0, marker_pos)
            if start == -1:
                start = marker_pos
            legacy_end = content.find("})();", marker_pos)
            end = legacy_end + len("})();") if legacy_end != -1 else len(content)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "replaced legacy session delete runtime"
        else:
            new_content = content.rstrip() + "\n" + script + "\n"
            action = "injected session delete runtime"

        if new_content == content:
            continue
        if write_text_best_effort(path, new_content, context="session delete runtime patch"):
            changed += 1
            print(f"  {path.name}: {action}")
    return changed


def patch_assets_tree(app_resources: Path) -> int:
    """Patch every discovered assets version directory."""
    assets_dirs = iter_assets_dirs(app_resources)
    if not assets_dirs:
        print("Warning: assets root not found; skipping chunk patches")
        return 0

    total = 0
    for assets_dir in assets_dirs:
        for pattern, replacements in PATCHES.items():
            files = find_patch_targets(assets_dir, pattern, replacements)

            for fpath in files:
                backup_file(fpath, assets_dir)
                content = fpath.read_text(encoding="utf-8")
                changed = 0
                for old, new in replacements:
                    if old in content and old != new:
                        content = content.replace(old, new)
                        changed += 1
                if changed > 0 and write_text_best_effort(fpath, content, context="chunk replacement"):
                    total += changed
                    print(f"  {fpath.name}: {changed} replacements")

        font_patches = patch_font_runtime(assets_dir)
        if font_patches:
            total += font_patches

        session_patches = patch_session_delete_runtime(assets_dir)
        if session_patches:
            total += session_patches

    return total


PATCHES: dict[str, list[tuple[str, str]]] = {}

# === 3P settings page (c71860c77-DNv5VYLZ.js) ===
PATCHES["c71860c77-DNv5VYLZ.js"] = [
    ('"Egress Requirements"', '"\u51fa\u53e3\u8981\u6c42"'),
    ('"Gateway base URL"', '"\u7b2c\u4e09\u65b9 URL"'),
    ('"Gateway API key"', '"\u7b2c\u4e09\u65b9 API Key"'),
    ('"Gateway auth scheme"', '"\u7b2c\u4e09\u65b9\u8ba4\u8bc1\u65b9\u5f0f"'),
    ('"Gateway extra headers"', '"\u7b2c\u4e09\u65b9\u989d\u5916\u8bf7\u6c42\u5934"'),
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
    ('gateway:"\u81ea\u5b9a\u4e49"', 'gateway:"\u7b2c\u4e09\u65b9"'),
    ('gateway:"Gateway"', 'gateway:"\u7b2c\u4e09\u65b9"'),
]

# === Hardcoded UI strings that moved out of i18n JSON in recent builds ===
# Use a deliberately non-matching file name so find_patch_targets scans JS chunks
# and only touches files that actually contain one of these exact needles.
PATCHES["__claude_zh_cn_hardcoded_ui__.js"] = [
    ('"\u5de5\u4ef6"', '"Artifacts"'),
    ('label:"\u9879\u76ee"', 'label:"Projects"'),
    ('["project","\u9879\u76ee"]', '["project","Project"]'),
    ('label:"\u5b9e\u65f6\u5de5\u4ef6"', 'label:"Live artifacts"'),
    ('label:"\u5b9e\u65f6 Artifacts"', 'label:"Live artifacts"'),
    ('"Theme"', '"\u4e3b\u9898"'),
    ('"Interface font"', '"\u754c\u9762\u5b57\u4f53"'),
    ('"Font for the Claude Code interface \u2014 menus, sidebar, and chat."', '"Claude Code \u754c\u9762\u5b57\u4f53\uff0c\u7528\u4e8e\u83dc\u5355\u3001\u4fa7\u8fb9\u680f\u548c\u804a\u5929\u3002"'),
    ('"Transcript text size"', '"\u5bf9\u8bdd\u8bb0\u5f55\u6587\u5b57\u5927\u5c0f"'),
    ('"Size of the conversation transcript text."', '"\u5bf9\u8bdd\u8bb0\u5f55\u6587\u5b57\u7684\u5927\u5c0f\u3002"'),
    ('"Code appearance"', '"\u4ee3\u7801\u5916\u89c2"'),
    ('"Set a custom monospace font for code and terminal."', '"\u4e3a\u4ee3\u7801\u548c\u7ec8\u7aef\u8bbe\u7f6e\u81ea\u5b9a\u4e49\u7b49\u5bbd\u5b57\u4f53\u3002"'),
    ('"Local sessions"', '"\u672c\u5730\u4f1a\u8bdd"'),
    ('"Enable remote control by default"', '"\u9ed8\u8ba4\u542f\u7528\u8fdc\u7a0b\u63a7\u5236"'),
    ('"Automatically connect new local sessions to Remote Control so you can continue them from the CLI or claude.ai/code."', '"\u81ea\u52a8\u5c06\u65b0\u7684\u672c\u5730\u4f1a\u8bdd\u8fde\u63a5\u5230\u8fdc\u7a0b\u63a7\u5236\uff0c\u4ee5\u4fbf\u4f60\u53ef\u4ee5\u4ece CLI \u6216 claude.ai/code \u7ee7\u7eed\u4f7f\u7528\u3002"'),
    ('"When Claude pushes changes to a branch, it automatically opens a pull request without asking first. Applies to remote sessions only."', '"Claude \u5c06\u66f4\u6539\u63a8\u9001\u5230\u5206\u652f\u65f6\uff0c\u4f1a\u81ea\u52a8\u6253\u5f00\u62c9\u53d6\u8bf7\u6c42\uff0c\u800c\u4e0d\u4f1a\u5148\u8be2\u95ee\u3002\u4ec5\u9002\u7528\u4e8e\u8fdc\u7a0b\u4f1a\u8bdd\u3002"'),
    ('"Discard Changes"', '"\u653e\u5f03\u66f4\u6539"'),
    ('"Discard changes"', '"\u653e\u5f03\u66f4\u6539"'),
    ('"Discard changes?"', '"\u653e\u5f03\u66f4\u6539\uff1f"'),
    ('"Apply Changes"', '"\u5e94\u7528\u66f4\u6539"'),
    ('"Apply changes"', '"\u5e94\u7528\u66f4\u6539"'),
    ('"Shown in the model picker. Leave blank to auto-format from the ID."', '"\u663e\u793a\u5728\u6a21\u578b\u9009\u62e9\u5668\u4e2d\u3002\u7559\u7a7a\u5c06\u6839\u636e ID \u81ea\u52a8\u683c\u5f0f\u5316\u3002"'),
    ('"Offer 1M-context variant"', '"\u63d0\u4f9b 1M \u4e0a\u4e0b\u6587\u53d8\u4f53"'),
    ('"Model ID"', '"\u6a21\u578b ID"'),
    ('"Allowed surfaces"', '"\u5141\u8bb8\u7684\u529f\u80fd\u754c\u9762"'),
    ('"Enable the Cowork tab. Claude works on longer tasks like research, analysis, and documents."', '"\u542f\u7528 Cowork \u6807\u7b7e\u9875\u3002Claude \u53ef\u5904\u7406\u7814\u7a76\u3001\u5206\u6790\u548c\u6587\u6863\u7b49\u957f\u4efb\u52a1\u3002"'),
    ('"Enable the Code tab. Claude writes and runs code."', '"\u542f\u7528 Code \u6807\u7b7e\u9875\u3002Claude \u53ef\u7f16\u5199\u5e76\u8fd0\u884c\u4ee3\u7801\u3002"'),
    ('"General restrictions"', '"\u901a\u7528\u9650\u5236"'),
    ('"These apply regardless of which surfaces are enabled."', '"\u65e0\u8bba\u542f\u7528\u54ea\u4e9b\u529f\u80fd\u754c\u9762\uff0c\u8fd9\u4e9b\u9650\u5236\u90fd\u4f1a\u751f\u6548\u3002"'),
    ('"Hostnames the agent\'s tools may reach from the Cowork and Code tabs. Also surfaced under Egress Requirements."', '"Agent \u5de5\u5177\u53ef\u4ece Cowork \u548c Code \u6807\u7b7e\u9875\u8bbf\u95ee\u7684\u4e3b\u673a\u540d\u3002\u4e5f\u4f1a\u663e\u793a\u5728\u51fa\u53e3\u8981\u6c42\u4e2d\u3002"'),
    ('"Applies to both the Cowork and Code tabs."', '"\u540c\u65f6\u9002\u7528\u4e8e Cowork \u548c Code \u6807\u7b7e\u9875\u3002"'),
    ('Applies to both the Cowork and Code tabs.', '\u540c\u65f6\u9002\u7528\u4e8e Cowork \u548c Code \u6807\u7b7e\u9875\u3002'),
    ('"Only affects **tool calls**. Inference and MCP traffic are covered by their own allowlists elsewhere."', '"\u4ec5\u5f71\u54cd **\u5de5\u5177\u8c03\u7528**\u3002\u63a8\u7406\u548c MCP \u6d41\u91cf\u7531\u5176\u4ed6\u4f4d\u7f6e\u7684\u5141\u8bb8\u5217\u8868\u63a7\u5236\u3002"'),
    ('Only affects **tool calls**. Inference and MCP traffic are covered by their own allowlists elsewhere.', '\u4ec5\u5f71\u54cd **\u5de5\u5177\u8c03\u7528**\u3002\u63a8\u7406\u548c MCP \u6d41\u91cf\u7531\u5176\u4ed6\u4f4d\u7f6e\u7684\u5141\u8bb8\u5217\u8868\u63a7\u5236\u3002'),
    ('"When unset, only the inference endpoint is reachable from the sandbox; the agent\'s package installs (pip/npm) and web fetches will fail with a 403."', '"\u672a\u8bbe\u7f6e\u65f6\uff0c\u6c99\u76d2\u53ea\u80fd\u8bbf\u95ee\u63a8\u7406\u7aef\u70b9\uff1bAgent \u7684\u5305\u5b89\u88c5\uff08pip/npm\uff09\u548c\u7f51\u9875\u6293\u53d6\u5c06\u56e0 403 \u5931\u8d25\u3002"'),
    ('When unset, only the inference endpoint is reachable from the sandbox; the agent\'s package installs (pip/npm) and web fetches will fail with a 403.', '\u672a\u8bbe\u7f6e\u65f6\uff0c\u6c99\u76d2\u53ea\u80fd\u8bbf\u95ee\u63a8\u7406\u7aef\u70b9\uff1bAgent \u7684\u5305\u5b89\u88c5\uff08pip/npm\uff09\u548c\u7f51\u9875\u6293\u53d6\u5c06\u56e0 403 \u5931\u8d25\u3002'),
    ('"Accepts exact hostnames (`api.github.com`), wildcards (`*.corp.com` matches one subdomain level), and `*` to allow all."', '"\u63a5\u53d7\u7cbe\u786e\u4e3b\u673a\u540d\uff08`api.github.com`\uff09\u3001\u901a\u914d\u7b26\uff08`*.corp.com` \u5339\u914d\u4e00\u7ea7\u5b50\u57df\uff09\u548c `*`\uff08\u5141\u8bb8\u5168\u90e8\uff09\u3002"'),
    ('Accepts exact hostnames (`api.github.com`), wildcards (`*.corp.com` matches one subdomain level), and `*` to allow all.', '\u63a5\u53d7\u7cbe\u786e\u4e3b\u673a\u540d\uff08`api.github.com`\uff09\u3001\u901a\u914d\u7b26\uff08`*.corp.com` \u5339\u914d\u4e00\u7ea7\u5b50\u57df\uff09\u548c `*`\uff08\u5141\u8bb8\u5168\u90e8\uff09\u3002'),
    ('"Wildcards don\'t cross schemes. `*.corp.com` matches `docs.corp.com` but not `corp.com` itself; add both if you need the apex."', '"\u901a\u914d\u7b26\u4e0d\u8de8\u8d8a\u5c42\u7ea7\u3002`*.corp.com` \u5339\u914d `docs.corp.com`\uff0c\u4e0d\u5339\u914d `corp.com` \u672c\u8eab\uff1b\u9700\u8981\u9876\u7ea7\u57df\u65f6\u8bf7\u540c\u65f6\u6dfb\u52a0\u4e24\u8005\u3002"'),
    ('Wildcards don\'t cross schemes. `*.corp.com` matches `docs.corp.com` but not `corp.com` itself; add both if you need the apex.', '\u901a\u914d\u7b26\u4e0d\u8de8\u8d8a\u5c42\u7ea7\u3002`*.corp.com` \u5339\u914d `docs.corp.com`\uff0c\u4e0d\u5339\u914d `corp.com` \u672c\u8eab\uff1b\u9700\u8981\u9876\u7ea7\u57df\u65f6\u8bf7\u540c\u65f6\u6dfb\u52a0\u4e24\u8005\u3002'),
    ('"IP literals and localhost always resolve regardless of this list; this is a public-egress filter, not a sandbox."', '"IP \u5b57\u9762\u91cf\u548c localhost \u59cb\u7ec8\u53ef\u89e3\u6790\uff0c\u4e0d\u53d7\u6b64\u5217\u8868\u5f71\u54cd\uff1b\u8fd9\u662f\u516c\u5171\u51fa\u7ad9\u8fc7\u6ee4\u5668\uff0c\u4e0d\u662f\u6c99\u76d2\u3002"'),
    ('IP literals and localhost always resolve regardless of this list; this is a public-egress filter, not a sandbox.', 'IP \u5b57\u9762\u91cf\u548c localhost \u59cb\u7ec8\u53ef\u89e3\u6790\uff0c\u4e0d\u53d7\u6b64\u5217\u8868\u5f71\u54cd\uff1b\u8fd9\u662f\u516c\u5171\u51fa\u7ad9\u8fc7\u6ee4\u5668\uff0c\u4e0d\u662f\u6c99\u76d2\u3002'),
    ('"Hosts you add here also need to be open on your network firewall. See Egress Requirements for the full allowlist."', '"\u4f60\u5728\u6b64\u6dfb\u52a0\u7684\u4e3b\u673a\u4e5f\u9700\u5728\u7f51\u7edc\u9632\u706b\u5899\u4e0a\u5f00\u653e\u3002\u5b8c\u6574\u5141\u8bb8\u5217\u8868\u8bf7\u67e5\u770b\u51fa\u53e3\u8981\u6c42\u3002"'),
    ('Hosts you add here also need to be open on your network firewall. See Egress Requirements for the full allowlist.', '\u4f60\u5728\u6b64\u6dfb\u52a0\u7684\u4e3b\u673a\u4e5f\u9700\u5728\u7f51\u7edc\u9632\u706b\u5899\u4e0a\u5f00\u653e\u3002\u5b8c\u6574\u5141\u8bb8\u5217\u8868\u8bf7\u67e5\u770b\u51fa\u53e3\u8981\u6c42\u3002'),
    ('"Discard unsaved changes?"', '"\u653e\u5f03\u672a\u4fdd\u5b58\u7684\u66f4\u6539\uff1f"'),
    ('"This configuration has changes that haven\'t been saved. They will be lost."', '"\u6b64\u914d\u7f6e\u6709\u672a\u4fdd\u5b58\u7684\u66f4\u6539\u3002\u8fd9\u4e9b\u66f4\u6539\u5c06\u4e22\u5931\u3002"'),
    ('"Keep editing"', '"\u7ee7\u7eed\u7f16\u8f91"'),
    ('defaultMessage:"Discard",id:"nmpevlUATU"', 'defaultMessage:"\u653e\u5f03",id:"nmpevlUATU"'),
    ('"High-contrast dark theme"', '"\u9ad8\u5bf9\u6bd4\u5ea6\u6df1\u8272\u4e3b\u9898"'),
    ('"Use a darker, near-black background when dark mode is on."', '"\u6df1\u8272\u6a21\u5f0f\u5f00\u542f\u65f6\u4f7f\u7528\u66f4\u6df1\u3001\u63a5\u8fd1\u7eaf\u9ed1\u7684\u80cc\u666f\u3002"'),
    ('defaultMessage:"Small",id:"BPnT3TVya+"', 'defaultMessage:"\u5c0f",id:"BPnT3TVya+"'),
    ('defaultMessage:"Medium",id:"ovJ26CKo4Q"', 'defaultMessage:"\u4e2d",id:"ovJ26CKo4Q"'),
    ('defaultMessage:"Large",id:"/06iwcQHPz"', 'defaultMessage:"\u5927",id:"/06iwcQHPz"'),
    ('"Dynamic workflows"', '"\u52a8\u6001\u5de5\u4f5c\u6d41"'),
    ('"Let Claude run multiple agents in parallel for complex tasks. Workflows can use a lot of your usage limit quickly."', '"\u5141\u8bb8 Claude \u4e3a\u590d\u6742\u4efb\u52a1\u5e76\u884c\u8fd0\u884c\u591a\u4e2a Agent\u3002\u5de5\u4f5c\u6d41\u53ef\u80fd\u5f88\u5feb\u6d88\u8017\u4f60\u7684\u4f7f\u7528\u989d\u5ea6\u3002"'),
    ('"Dynamic workflows run many subagents in parallel and can use a lot of your usage limit. Stop them any time from the <link>tasks panel</link>."', '"\u52a8\u6001\u5de5\u4f5c\u6d41\u4f1a\u5e76\u884c\u8fd0\u884c\u591a\u4e2a\u5b50 Agent\uff0c\u5e76\u53ef\u80fd\u6d88\u8017\u5927\u91cf\u4f7f\u7528\u989d\u5ea6\u3002\u4f60\u53ef\u968f\u65f6\u4ece<link>\u4efb\u52a1\u9762\u677f</link>\u505c\u6b62\u5b83\u4eec\u3002"'),
    ('"Dynamic workflows are disabled by your organization\'s policy."', '"\u52a8\u6001\u5de5\u4f5c\u6d41\u5df2\u88ab\u4f60\u7684\u7ec4\u7ec7\u7b56\u7565\u7981\u7528\u3002"'),
    ('"Cowork files"', '"Cowork \u6587\u4ef6"'),
    ('"Your artifacts and scheduled tasks are stored at {path}."', '"\u4f60\u7684\u5de5\u4ef6\u548c\u8ba1\u5212\u4efb\u52a1\u5b58\u50a8\u5728 {path}\u3002"'),
    ('"Change location for Cowork files?"', '"\u66f4\u6539 Cowork \u6587\u4ef6\u4f4d\u7f6e\uff1f"'),
    ('"Copy files to {location} and restart the app. Your existing files will remain in {previousLocation}."', '"\u5c06\u6587\u4ef6\u590d\u5236\u5230 {location} \u5e76\u91cd\u542f\u5e94\u7528\u3002\u4f60\u7684\u73b0\u6709\u6587\u4ef6\u5c06\u4fdd\u7559\u5728 {previousLocation}\u3002"'),
    ('"{provider} returned an error"', '"{provider} \u8fd4\u56de\u9519\u8bef"'),
    ('"Your connection works, but the provider rejected a test request. Often a model-access or quota issue."', '"\u8fde\u63a5\u6b63\u5e38\uff0c\u4f46\u63d0\u4f9b\u5546\u62d2\u7edd\u4e86\u6d4b\u8bd5\u8bf7\u6c42\u3002\u8fd9\u901a\u5e38\u662f\u6a21\u578b\u8bbf\u95ee\u6743\u9650\u6216\u914d\u989d\u95ee\u9898\u3002"'),
    ('"Connectors have moved to Customize. Head there to browse, connect, and manage them."', '"\u8fde\u63a5\u5668\u5df2\u79fb\u81f3\u201c\u81ea\u5b9a\u4e49\u201d\u3002\u524d\u5f80\u90a3\u91cc\u6d4f\u89c8\u3001\u8fde\u63a5\u548c\u7ba1\u7406\u8fde\u63a5\u5668\u3002"'),
    ('Connectors have moved to Customize. Head there to browse, connect, and manage them.', '\u8fde\u63a5\u5668\u5df2\u79fb\u81f3\u201c\u81ea\u5b9a\u4e49\u201d\u3002\u524d\u5f80\u90a3\u91cc\u6d4f\u89c8\u3001\u8fde\u63a5\u548c\u7ba1\u7406\u8fde\u63a5\u5668\u3002'),
    ('"Connectors have moved to <link>Customize</link>. Head there to browse, connect, and manage them."', '"\u8fde\u63a5\u5668\u5df2\u79fb\u81f3<link>\u81ea\u5b9a\u4e49</link>\u3002\u524d\u5f80\u90a3\u91cc\u6d4f\u89c8\u3001\u8fde\u63a5\u548c\u7ba1\u7406\u8fde\u63a5\u5668\u3002"'),
    ('"Skills have moved to Customize."', '"\u6280\u80fd\u5df2\u79fb\u81f3\u201c\u81ea\u5b9a\u4e49\u201d\u3002"'),
    ('Skills have moved to Customize.', '\u6280\u80fd\u5df2\u79fb\u81f3\u201c\u81ea\u5b9a\u4e49\u201d\u3002'),
    ('"Skills have moved to <link>Customize</link>."', '"\u6280\u80fd\u5df2\u79fb\u81f3<link>\u81ea\u5b9a\u4e49</link>\u3002"'),
    ('"Generate code, documents, and designs in a dedicated window alongside your conversation."', '"\u5728\u5bf9\u8bdd\u65c1\u7684\u4e13\u7528\u7a97\u53e3\u4e2d\u751f\u6210\u4ee3\u7801\u3001\u6587\u6863\u548c\u8bbe\u8ba1\u3002"'),
    ('Generate code, documents, and designs in a dedicated window alongside your conversation.', '\u5728\u5bf9\u8bdd\u65c1\u7684\u4e13\u7528\u7a97\u53e3\u4e2d\u751f\u6210\u4ee3\u7801\u3001\u6587\u6863\u548c\u8bbe\u8ba1\u3002'),
    ('"Create dynamic artifacts that stay up-to-date using live data from your connectors."', '"\u4f7f\u7528\u6765\u81ea\u8fde\u63a5\u5668\u7684\u5b9e\u65f6\u6570\u636e\uff0c\u521b\u5efa\u4fdd\u6301\u66f4\u65b0\u7684\u52a8\u6001\u5de5\u4ef6\u3002"'),
    ('Create dynamic artifacts that stay up-to-date using live data from your connectors.', '\u4f7f\u7528\u6765\u81ea\u8fde\u63a5\u5668\u7684\u5b9e\u65f6\u6570\u636e\uff0c\u521b\u5efa\u4fdd\u6301\u66f4\u65b0\u7684\u52a8\u6001\u5de5\u4ef6\u3002'),
    ('"Create dynamic artifacts that stay up-to-date using live data from <link>your connectors</link>."', '"\u4f7f\u7528\u6765\u81ea<link>\u4f60\u7684\u8fde\u63a5\u5668</link>\u7684\u5b9e\u65f6\u6570\u636e\uff0c\u521b\u5efa\u4fdd\u6301\u66f4\u65b0\u7684\u52a8\u6001\u5de5\u4ef6\u3002"'),
    ('"Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic\'s guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>"', '"Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa<aupLink>Anthropic \u7684\u6307\u5357</aupLink>\u3002<learnMoreLink>\u4e86\u89e3\u66f4\u591a</learnMoreLink>"'),
    ('Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic\'s guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>', 'Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa<aupLink>Anthropic \u7684\u6307\u5357</aupLink>\u3002<learnMoreLink>\u4e86\u89e3\u66f4\u591a</learnMoreLink>'),
    ('"Claude will keep these in mind across chats and Cowork within Anthropic\'s guidelines. Learn more"', '"Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa Anthropic \u7684\u6307\u5357\u3002\u4e86\u89e3\u66f4\u591a"'),
    ('Claude will keep these in mind across chats and Cowork within Anthropic\'s guidelines. Learn more', 'Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa Anthropic \u7684\u6307\u5357\u3002\u4e86\u89e3\u66f4\u591a'),
    ('"Claude will keep these in mind across chats and Cowork within Anthropic\u2019s guidelines. Learn more"', '"Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa Anthropic \u7684\u6307\u5357\u3002\u4e86\u89e3\u66f4\u591a"'),
    ('Claude will keep these in mind across chats and Cowork within Anthropic\u2019s guidelines. Learn more', 'Claude \u4f1a\u5728\u804a\u5929\u548c Cowork \u4e2d\u8bb0\u4f4f\u8fd9\u4e9b\u5185\u5bb9\uff0c\u5e76\u9075\u5faa Anthropic \u7684\u6307\u5357\u3002\u4e86\u89e3\u66f4\u591a'),
    ('"Configured model not available"', '"\u914d\u7f6e\u7684\u6a21\u578b\u4e0d\u53ef\u7528"'),
    ('"Your gateway couldn\'t serve {model}. This model may not be configured on your gateway, or access may be restricted."', '"\u7b2c\u4e09\u65b9\u65e0\u6cd5\u63d0\u4f9b {model}\u3002\u8be5\u6a21\u578b\u53ef\u80fd\u672a\u5728\u7b2c\u4e09\u65b9\u914d\u7f6e\uff0c\u6216\u8bbf\u95ee\u53d7\u9650\u3002"'),
    ('"Your gateway couldn\u2019t serve {model}. This model may not be configured on your gateway, or access may be restricted."', '"\u7b2c\u4e09\u65b9\u65e0\u6cd5\u63d0\u4f9b {model}\u3002\u8be5\u6a21\u578b\u53ef\u80fd\u672a\u5728\u7b2c\u4e09\u65b9\u914d\u7f6e\uff0c\u6216\u8bbf\u95ee\u53d7\u9650\u3002"'),
    ('"Gateway base URL"', '"\u7b2c\u4e09\u65b9 URL"'),
    ('"Gateway API key"', '"\u7b2c\u4e09\u65b9 API Key"'),
    ('"Gateway auth scheme"', '"\u7b2c\u4e09\u65b9\u8ba4\u8bc1\u65b9\u5f0f"'),
    ('"Gateway extra headers"', '"\u7b2c\u4e09\u65b9\u989d\u5916\u8bf7\u6c42\u5934"'),
    ('"Gateway SSO IdP (OIDC)"', '"\u7b2c\u4e09\u65b9 SSO IdP (OIDC)"'),
    ('"Gateway sign-in (OIDC)"', '"\u7b2c\u4e09\u65b9\u767b\u5f55 (OIDC)"'),
    ('"Interactive sign-in"', '"\u4ea4\u4e92\u5f0f\u767b\u5f55"'),
    ('"Helper script"', '"\u8f85\u52a9\u811a\u672c"'),
    ('"Link URL"', '"\u94fe\u63a5 URL"'),
    ('"Optional HTTPS URL. The banner text becomes a link when set."', '"\u53ef\u9009 HTTPS URL\u3002\u8bbe\u7f6e\u540e\uff0c\u6a2a\u5e45\u6587\u672c\u4f1a\u53d8\u6210\u94fe\u63a5\u3002"'),
    ('"Show banner"', '"\u663e\u793a\u6a2a\u5e45"'),
    ('"Banner text"', '"\u6a2a\u5e45\u6587\u672c"'),
    ('"Single line, truncated on overflow. Maximum 200 characters."', '"\u5355\u884c\u663e\u793a\uff0c\u6ea2\u51fa\u65f6\u622a\u65ad\u3002\u6700\u591a 200 \u4e2a\u5b57\u7b26\u3002"'),
    ('"Internal use only"', '"\u4ec5\u4f9b\u5185\u90e8\u4f7f\u7528"'),
    ('"Background color"', '"\u80cc\u666f\u989c\u8272"'),
    ('"Six-digit hex (#RRGGBB). Applied exactly as configured; not theme-adapted."', '"\u516d\u4f4d\u5341\u516d\u8fdb\u5236\u989c\u8272\uff08#RRGGBB\uff09\u3002\u5c06\u5b8c\u5168\u6309\u914d\u7f6e\u5e94\u7528\uff0c\u4e0d\u4f1a\u9002\u914d\u4e3b\u9898\u3002"'),
    ('"Text color"', '"\u6587\u672c\u989c\u8272"'),
    ('"Appearance"', '"\u7ec4\u7ec7\u6a2a\u5e45"'),
    ('"MCP servers"', '"MCP \u670d\u52a1\u5668"'),
    ('"Blank"', '"\u7a7a\u767d"'),
    ('"Microsoft365"', '"Microsoft 365"'),
    ('"OpenTelemetry"', '"OpenTelemetry"'),
    ('"OpenTelemetry collector endpoint"', '"OpenTelemetry \u91c7\u96c6\u5668\u7aef\u70b9"'),
    ('"OpenTelemetry exporter headers"', '"OpenTelemetry \u5bfc\u51fa\u5668\u6807\u5934"'),
    ('"Telemetry config conflict"', '"\u9065\u6d4b\u914d\u7f6e\u51b2\u7a81"'),
    ('"Local MCP servers"', '"\u672c\u5730 MCP \u670d\u52a1\u5668"'),
    ('"Known MCP servers"', '"\u5df2\u77e5 MCP \u670d\u52a1\u5668"'),
    ('"Your MCP servers"', '"\u4f60\u7684 MCP \u670d\u52a1\u5668"'),
    ('"Usage limits"', '"\u4f7f\u7528\u9650\u5236"'),
    ('"Max tokens per window"', '"\u6bcf\u4e2a\u7a97\u53e3\u7684\u6700\u5927\u4ee4\u724c\u6570"'),
    ('"Require signed extensions"', '"\u9700\u8981\u7b7e\u540d\u7684\u6269\u5c55"'),
    ('"Allow Claude Code tab"', '"\u5141\u8bb8 Claude Code \u9009\u9879\u5361"'),
    ('"No organization plugins found"', '"\u6ca1\u6709\u7ec4\u7ec7\u63d2\u4ef6"'),
    ('"Add desktop extensions"', '"\u6dfb\u52a0\u684c\u9762\u6269\u5c55"'),
    ('"Link URL (optional)"', '"\u94fe\u63a5 URL\uff08\u53ef\u9009\uff09"'),
    ('"Headers helper script"', '"Headers \u8f85\u52a9\u811a\u672c"'),
    ('"Absolute path"', '"\u7edd\u5bf9\u8def\u5f84"'),
    ('"Tool policy"', '"\u5de5\u5177\u7b56\u7565"'),
    ('"Lock the approval state for specific tools. Unlisted tools stay user-controlled."', '"\u9501\u5b9a\u7279\u5b9a\u5de5\u5177\u7684\u5ba1\u6279\u72b6\u6001\u3002\u672a\u5217\u51fa\u7684\u5de5\u5177\u4ecd\u7531\u7528\u6237\u63a7\u5236\u3002"'),
    ('"Auto-register (dynamic client registration)"', '"\u81ea\u52a8\u6ce8\u518c\uff08\u52a8\u6001\u5ba2\u6237\u7aef\u6ce8\u518c\uff09"'),
    ('"Bring your own client"', '"\u4f7f\u7528\u81ea\u5df1\u7684\u5ba2\u6237\u7aef"'),
    ('"Streamable HTTP"', '"\u6d41\u5f0f HTTP"'),
    ('"SSE (legacy)"', '"SSE\uff08\u65e7\u7248\uff09"'),
    ('"Local command (stdio)"', '"\u672c\u5730\u547d\u4ee4\uff08stdio\uff09"'),
    ('"Item 1"', '"\u9879 1"'),
    ('"Invalid configuration"', '"\u65e0\u6548\u914d\u7f6e"'),
    ('"Hi, I\'m Claude. How can I help you today?"', '"\u4f60\u597d\uff0c\u6211\u662f Claude\u3002\u4eca\u5929\u6211\u80fd\u5e2e\u4f60\u4ec0\u4e48\uff1f"'),
    ('"Hi, I\u2019m Claude. How can I help you today?"', '"\u4f60\u597d\uff0c\u6211\u662f Claude\u3002\u4eca\u5929\u6211\u80fd\u5e2e\u4f60\u4ec0\u4e48\uff1f"'),
    ('"Hi, I\'m Claude. How can I helpyou today?"', '"\u4f60\u597d\uff0c\u6211\u662f Claude\u3002\u4eca\u5929\u6211\u80fd\u5e2e\u4f60\u4ec0\u4e48\uff1f"'),
    ('"Hi, I\u2019m Claude. How can I helpyou today?"', '"\u4f60\u597d\uff0c\u6211\u662f Claude\u3002\u4eca\u5929\u6211\u80fd\u5e2e\u4f60\u4ec0\u4e48\uff1f"'),
    ('"Allowed egress hosts"', '"\u5141\u8bb8\u7684\u51fa\u7ad9\u4e3b\u673a"'),
    ('"Disable claude:// deep-link handling"', '"\u7981\u7528 claude:// \u6df1\u5ea6\u94fe\u63a5\u5904\u7406"'),
    ('"Enable Main Process Debugger"', '"\u542f\u7528\u4e3b\u8fdb\u7a0b\u8c03\u8bd5\u5668"'),
    ('"Record Performance Trace"', '"\u8bb0\u5f55\u6027\u80fd\u8ddf\u8e2a"'),
    ('"Write Main Process Heap Snapshot"', '"\u5199\u5165\u4e3b\u8fdb\u7a0b\u5806\u5feb\u7167"'),
    ('"Record Memory Trace (auto-stop)"', '"\u8bb0\u5f55\u5185\u5b58\u8ddf\u8e2a\uff08\u81ea\u52a8\u505c\u6b62\uff09"'),
    ('"server-name"', '"\u670d\u52a1\u5668\u540d\u79f0"'),
    ('"tool name"', '"\u5de5\u5177\u540d\u79f0"'),
    ('"+ Add server policy"', '"+ \u6dfb\u52a0\u670d\u52a1\u5668\u7b56\u7565"'),
    ('"Open Setup"', '"\u6253\u5f00\u8bbe\u7f6e\u5411\u5bfc"'),
    ('"Sort by"', '"\u6392\u5e8f\u65b9\u5f0f"'),
    ('"Recency"', '"\u6700\u8fd1"'),
    ('"Alphabetically"', '"\u6309\u5b57\u6bcd\u987a\u5e8f"'),
    ('"Created time"', '"\u521b\u5efa\u65f6\u95f4"'),
    ('"Custom groups"', '"\u81ea\u5b9a\u4e49\u5206\u7ec4"'),
    ('"Avatar"', '"\u5934\u50cf"'),
    ('"Instructions for Claude"', '"\u7ed9 Claude \u7684\u6307\u4ee4"'),
    ('"Preferences"', '"\u504f\u597d\u8bbe\u7f6e"'),
    ('"Get notified when Claude has finished a response. Useful for long-running tasks."', '"Claude \u5b8c\u6210\u56de\u590d\u65f6\u63a5\u6536\u901a\u77e5\u3002\u5bf9\u957f\u65f6\u95f4\u8fd0\u884c\u7684\u4efb\u52a1\u5f88\u6709\u7528\u3002"'),
    ('"You\u2019re running Claude through your organization\u2019s own inference provider (cc.freemodel.dev). Your conversations are sent there, not to Anthropic, and are governed by your organization\u2019s agreement with that provider."', '"\u4f60\u6b63\u5728\u901a\u8fc7\u7ec4\u7ec7\u81ea\u5df1\u7684\u63a8\u7406\u63d0\u4f9b\u65b9 (cc.freemodel.dev) \u8fd0\u884c Claude\u3002\u4f60\u7684\u5bf9\u8bdd\u4f1a\u53d1\u9001\u5230\u8be5\u63d0\u4f9b\u65b9\uff0c\u800c\u4e0d\u662f Anthropic\uff0c\u5e76\u53d7\u4f60\u7684\u7ec4\u7ec7\u4e0e\u8be5\u63d0\u4f9b\u65b9\u4e4b\u95f4\u534f\u8bae\u7684\u7ea6\u675f\u3002"'),
    ('You\u2019re running Claude through your organization\u2019s own inference provider (cc.freemodel.dev). Your conversations are sent there, not to Anthropic, and are governed by your organization\u2019s agreement with that provider.', '\u4f60\u6b63\u5728\u901a\u8fc7\u7ec4\u7ec7\u81ea\u5df1\u7684\u63a8\u7406\u63d0\u4f9b\u65b9 (cc.freemodel.dev) \u8fd0\u884c Claude\u3002\u4f60\u7684\u5bf9\u8bdd\u4f1a\u53d1\u9001\u5230\u8be5\u63d0\u4f9b\u65b9\uff0c\u800c\u4e0d\u662f Anthropic\uff0c\u5e76\u53d7\u4f60\u7684\u7ec4\u7ec7\u4e0e\u8be5\u63d0\u4f9b\u65b9\u4e4b\u95f4\u534f\u8bae\u7684\u7ea6\u675f\u3002'),
    ('"What Anthropic doesn\u2019t see"', '"Anthropic \u4e0d\u4f1a\u770b\u5230\u7684\u5185\u5bb9"'),
    ('"Your prompts, Claude\u2019s responses, or any conversation content"', '"\u4f60\u7684\u63d0\u793a\u3001Claude \u7684\u56de\u590d\u6216\u4efb\u4f55\u5bf9\u8bdd\u5185\u5bb9"'),
    ('"Your files, code, or workspace contents"', '"\u4f60\u7684\u6587\u4ef6\u3001\u4ee3\u7801\u6216\u5de5\u4f5c\u533a\u5185\u5bb9"'),
    ('"Your identity or account details"', '"\u4f60\u7684\u8eab\u4efd\u6216\u8d26\u53f7\u8be6\u60c5"'),
    ('"What Anthropic may receive (configured by your organization)"', '"Anthropic \u53ef\u80fd\u6536\u5230\u7684\u5185\u5bb9\uff08\u7531\u4f60\u7684\u7ec4\u7ec7\u914d\u7f6e\uff09"'),
    ('"Crash reports and error diagnostics, so we can fix bugs"', '"\u5d29\u6e83\u62a5\u544a\u548c\u9519\u8bef\u8bca\u65ad\uff0c\u7528\u4e8e\u4fee\u590d\u95ee\u9898"'),
    ('"Anonymous usage metrics including usage counts (not conversation content)"', '"\u5305\u542b\u4f7f\u7528\u6b21\u6570\u7684\u533f\u540d\u4f7f\u7528\u6307\u6807\uff08\u4e0d\u5305\u542b\u5bf9\u8bdd\u5185\u5bb9\uff09"'),
    ('"Update-check requests, so the app can stay current"', '"\u66f4\u65b0\u68c0\u67e5\u8bf7\u6c42\uff0c\u7528\u4e8e\u4fdd\u6301\u5e94\u7528\u4e3a\u6700\u65b0\u7248\u672c"'),
    ('"A diagnostic report, only if you explicitly choose \u201cSend to Anthropic\u201d"', '"\u8bca\u65ad\u62a5\u544a\uff0c\u4ec5\u5f53\u4f60\u660e\u786e\u9009\u62e9\u201c\u53d1\u9001\u7ed9 Anthropic\u201d\u65f6\u624d\u4f1a\u53d1\u9001"'),
    ('"New task"', '"\u65b0\u5efa\u4efb\u52a1"'),
    ('"New session"', '"\u65b0\u5efa\u4f1a\u8bdd"'),
    ('"New Projects"', '"\u65b0\u5efa\u9879\u76ee"'),
    ('"Scheduled"', '"\u5df2\u5b89\u6392"'),
    ('"Customize"', '"\u81ea\u5b9a\u4e49"'),
    ('"Status"', '"\u72b6\u6001"'),
    ('"Last activity"', '"\u6700\u8fd1\u6d3b\u52a8"'),
    ('"Group by"', '"\u5206\u7ec4\u65b9\u5f0f"'),
    ('"Date"', '"\u65e5\u671f"'),
    ('"Custom groups"', '"\u81ea\u5b9a\u4e49\u5206\u7ec4"'),
    ('"None"', '"\u65e0"'),
    ('"1d"', '"1\u5929"'),
    ('"3d"', '"3\u5929"'),
    ('"7d"', '"7\u5929"'),
    ('"30d"', '"30\u5929"'),
    ('"All projects"', '"\u6240\u6709\u9879\u76ee"'),
    ('"View all"', '"\u67e5\u770b\u5168\u90e8"'),
    ('"Viewall"', '"\u67e5\u770b\u5168\u90e8"'),
    ('"Cowork"', '"\u534f\u4f5c"'),
    ('"Code"', '"\u4ee3\u7801"'),
    ('"Create your first scheduled task"', '"\u521b\u5efa\u4f60\u7684\u7b2c\u4e00\u4e2a\u8ba1\u5212\u4efb\u52a1"'),
    ('"Daily brief"', '"\u6bcf\u65e5\u7b80\u62a5"'),
    ('"Weekly review"', '"\u6bcf\u5468\u56de\u987e"'),
    ('"Run tasks on a schedule or whenever you need them. Type /schedule in any existing task to set one up."', '"\u6309\u8ba1\u5212\u6216\u5728\u9700\u8981\u65f6\u8fd0\u884c\u4efb\u52a1\u3002\u5728\u4efb\u4f55\u73b0\u6709\u4efb\u52a1\u4e2d\u8f93\u5165 /schedule \u5373\u53ef\u8bbe\u7f6e\u3002"'),
    ('"Tasks"', '"\u4efb\u52a1"'),
    ('"Active"', '"\u6d3b\u8dc3"'),
    ('"Archived"', '"\u5df2\u5f52\u6863"'),
    ('"All"', '"\u5168\u90e8"'),
    ('"Local"', '"\u672c\u5730"'),
    ('"Cloud"', '"\u4e91\u7aef"'),
    ('"Environment"', '"\u73af\u5883"'),
    ('"Recents"', '"\u6700\u8fd1"'),
]

# === Sidebar navigation (cbc59a8af-DbOQVv5S.js) ===
PATCHES["cbc59a8af-DbOQVv5S.js"] = [
    ('label:"\u804a\u5929"', 'label:"\u804a\u5929"'),
    ('label:"Chat"', 'label:"\u804a\u5929"'),
    ('label:"Cowork"', 'label:"\u534f\u4f5c"'),
    ('label:"Code"', 'label:"\u4ee3\u7801"'),
    ('label:"Operon"', 'label:"\u5b9e\u9a8c\u5ba4"'),
    ('label:"\u9879\u76ee"', 'label:"Projects"'),
    ('label:"\u5df2\u5b89\u6392"', 'label:"\u5df2\u5b89\u6392"'),
    ('label:"Scheduled"', 'label:"\u5df2\u5b89\u6392"'),
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
    ('"Custom"', '"\u81ea\u5b9a\u4e49"'),
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
    ('["project","\u9879\u76ee"]', '["project","Project"]'),
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
    ('Keep awake', '\u4fdd\u6301\u5524\u9192'),
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

    assets_root = app_dir / "resources" / "ion-dist" / "assets"
    if not assets_root.exists():
        raise SystemExit(f"Assets root not found: {assets_root}")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    total = patch_assets_tree(app_dir / "resources")
    config_mirrored = set_font_config_mirror()

    print(f"Done. Total chunk patches: {total}")
    print(f"Font config mirrored: {config_mirrored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
