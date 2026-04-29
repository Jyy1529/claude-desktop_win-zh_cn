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
  ]);

  function shouldFixTextNode(node) {{
    const parent = node.parentElement;
    if (!parent || parent.closest("script,style,[contenteditable='true']")) return false;
    const scope = parent.closest("[role='dialog'],[role='menu'],[role='listbox'],main,section");
    if (!scope) return false;
    const context = scope.innerText || "";
    return /(Appearance|外观|颜色模式|Color mode|聊天字体|Chat font|Font|字体)/.test(context);
  }}

  function fixVisibleText(root = document.body) {{
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (nodes.length < 2000) {{
      const node = walker.nextNode();
      if (!node) break;
      nodes.push(node);
    }}
    nodes.forEach((node) => {{
      const text = node.nodeValue;
      if (!text) return;
      const trimmed = text.trim();
      const replacement = VISIBLE_TEXT_FIXES.get(trimmed);
      if (!replacement) return;
      if (!shouldFixTextNode(node)) return;
      node.nodeValue = text.replace(trimmed, replacement);
    }});
  }}

  let textFixScheduled = false;
  function scheduleFixVisibleText() {{
    if (textFixScheduled) return;
    textFixScheduled = true;
    const schedule = window.requestAnimationFrame || ((callback) => window.setTimeout(callback, 16));
    schedule(() => {{
      textFixScheduled = false;
      fixVisibleText();
    }});
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
  }}

  function mountPanel() {{
    return;
  }}

  const start = () => {{
    applyFont();
    mountFloatingButton();
    scheduleFixVisibleText();
    const observer = new MutationObserver(() => {{
      scheduleFixVisibleText();
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
                if write_text_best_effort(fpath, content, context="chunk replacement"):
                    total += changed
                    print(f"  {fpath.name}: {changed} replacements")

    font_patches = patch_font_runtime(assets_dir)
    config_mirrored = set_font_config_mirror()

    print(f"Done. Total chunk patches: {total}")
    print(f"Font runtime patches: {font_patches}")
    print(f"Font config mirrored: {config_mirrored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
