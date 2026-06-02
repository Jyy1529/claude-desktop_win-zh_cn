import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const script = readFileSync(resolve(root, "patch_chunks_zh_cn.py"), "utf8");
const start = script.indexOf(";(()=>{", script.indexOf("def session_delete_inject_script"));
const endMarker = "// __CLAUDE_ZH_CN_SESSION_DELETE_PATCH_END__";
const markerPos = script.indexOf(endMarker, start);
const end = script.lastIndexOf("})();", markerPos);
if (start < 0 || end < 0) throw new Error("session runtime script not found");
const runtime = script.slice(start, end + "})();".length);

class TextNode {
  constructor(value, parentElement) {
    this.nodeType = 3;
    this.nodeValue = value;
    this.parentElement = parentElement;
    this.textContent = value;
    this.innerText = value;
  }
}

class ClassList {
  constructor(node) {
    this.node = node;
  }
  contains(value) {
    return (` ${this.node.className || ""} `).includes(` ${value} `);
  }
}

class Element {
  constructor(tagName, attrs = {}, text = "") {
    this.nodeType = 1;
    this.tagName = tagName.toUpperCase();
    this.attributes = { ...attrs };
    this.children = [];
    this.parentElement = null;
    this.style = {};
    this.dataset = {};
    this.eventListeners = {};
    this.id = attrs.id || "";
    this._className = attrs.class || "";
    this.textContent = text;
    this.innerText = text;
    Object.defineProperty(this, "className", {
      get: () => this._className,
      set: (value) => {
        this._className = String(value || "");
        this.attributes.class = this._className;
        this.classList = new ClassList(this);
      },
    });
    this.className = this._className;
    if (text) this.children.push(new TextNode(text, this));
  }

  appendChild(node) {
    node.parentElement = this;
    this.children.push(node);
    notifyMutation("childList");
    return node;
  }

  remove() {
    if (!this.parentElement) return;
    const siblings = this.parentElement.children;
    const index = siblings.indexOf(this);
    if (index >= 0) siblings.splice(index, 1);
    this.parentElement = null;
    notifyMutation("childList");
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
    if (name === "class") {
      this.className = String(value);
      this.classList = new ClassList(this);
    }
    notifyMutation("attributes", name);
  }

  getAttribute(name) {
    return this.attributes[name] ?? null;
  }

  addEventListener(type, handler) {
    (this.eventListeners[type] ||= []).push(handler);
  }

  matches(selector) {
    return selector.split(",").some((part) => matchesSelector(this, part.trim()));
  }

  closest(selector) {
    for (let current = this; current; current = current.parentElement) {
      if (current.matches(selector)) return current;
    }
    return null;
  }

  contains(node) {
    for (let current = node; current; current = current.parentElement) {
      if (current === this) return true;
    }
    return false;
  }

  querySelectorAll(selector) {
    const out = [];
    visit(this, (node) => {
      if (node !== this && node.nodeType === 1 && node.matches(selector)) out.push(node);
    });
    return out;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  getBoundingClientRect() {
    const width = Number(this.attributes["data-width"] || 300);
    const height = Number(this.attributes["data-height"] || 32);
    const x = Number(this.attributes["data-x"] || 12);
    const y = Number(this.attributes["data-y"] || 20);
    return { x, y, left: x, top: y, right: x + width, bottom: y + height, width, height };
  }
}

function matchesSelector(node, selector) {
  if (!selector) return false;
  const parts = selector.split(/\s+/).filter(Boolean);
  if (!parts.length) return false;
  let current = node;
  for (let index = parts.length - 1; index >= 0; index -= 1) {
    if (index === parts.length - 1) {
      if (!matchesSingle(current, parts[index])) return false;
      current = current.parentElement;
      continue;
    }
    while (current && !matchesSingle(current, parts[index])) current = current.parentElement;
    if (!current) return false;
    current = current.parentElement;
  }
  return true;
}

function matchesSingle(node, selector) {
  if (!selector) return false;
  selector = selector.replace(/:not\([^)]*\)/g, "");
  if (selector === "*") return true;
  if (selector === "body") return node === document.body;
  if (/^[a-z]+$/i.test(selector)) return node.tagName.toLowerCase() === selector.toLowerCase();
  if (/^[a-z]+:not/.test(selector)) {
    const [tag] = selector.split(":");
    return node.tagName.toLowerCase() === tag.toLowerCase();
  }
  const attr = selector.match(/^\[([^=\]*~^$]+)([*^$]?=)?['"]?([^'"\]]*)['"]?\]$/);
  if (attr) {
    const [, name, op, expected] = attr;
    const actual = node.getAttribute(name);
    if (actual == null) return false;
    if (!op) return true;
    if (op === "=") return actual === expected;
    if (op === "^=") return actual.startsWith(expected);
    if (op === "*=") return actual.includes(expected);
    return false;
  }
  const tagExistsAttr = selector.match(/^([a-z]+)\[([^=\]*~^$]+)\]$/i);
  if (tagExistsAttr) {
    return node.tagName.toLowerCase() === tagExistsAttr[1].toLowerCase() && node.getAttribute(tagExistsAttr[2]) != null;
  }
  const tagAttr = selector.match(/^([a-z]+)\[([^=\]*~^$]+)([*^$]?=)?['"]?([^'"\]]*)['"]?\]$/i);
  if (tagAttr) {
    return node.tagName.toLowerCase() === tagAttr[1].toLowerCase() && matchesSingle(node, `[${tagAttr[2]}${tagAttr[3] || ""}"${tagAttr[4]}"]`);
  }
  if (selector.startsWith(".")) return node.classList.contains(selector.slice(1).split(":")[0]);
  if (selector.startsWith("#")) return node.id === selector.slice(1);
  return false;
}

function visit(node, fn) {
  for (const child of node.children || []) {
    fn(child);
    visit(child, fn);
  }
}

const mutationObservers = [];
function notifyMutation(type = "childList", attributeName = "") {
  for (const observer of mutationObservers) {
    if (type === "attributes" && !observer.options?.attributes) continue;
    if (type === "attributes" && observer.options?.attributeFilter && !observer.options.attributeFilter.includes(attributeName)) continue;
    if (type === "childList" && !observer.options?.childList) continue;
    observer.cb();
  }
}

class MapStorage {
  constructor() { this.map = new Map(); }
  getItem(key) { return this.map.get(key) ?? null; }
  setItem(key, value) { this.map.set(key, String(value)); }
  removeItem(key) { this.map.delete(key); }
  key(index) { return [...this.map.keys()][index] ?? null; }
  get length() { return this.map.size; }
}

globalThis.window = globalThis;
globalThis.globalThis = globalThis;
globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_DEBUG__ = true;
globalThis.location = { href: "https://claude.ai/chat/current123", pathname: "/chat/current123", search: "" };
globalThis.localStorage = new MapStorage();
globalThis.sessionStorage = new MapStorage();
globalThis.NodeFilter = { SHOW_TEXT: 4, FILTER_ACCEPT: 1, FILTER_REJECT: 2 };
globalThis.MutationObserver = class {
  constructor(cb) { this.cb = cb; }
  observe(target, options = {}) { this.options = options; mutationObservers.push(this); }
  disconnect() {}
};
globalThis.MouseEvent = class {};
globalThis.Event = class {};
const timers = [];
globalThis.setTimeout = (fn) => { timers.push(fn); return timers.length; };
globalThis.clearTimeout = () => {};
globalThis.setInterval = () => 1;
globalThis.clearInterval = () => {};
globalThis.addEventListener = () => {};
globalThis.removeEventListener = () => {};
globalThis.getComputedStyle = () => ({ display: "block", visibility: "visible" });

function flushTimers(limit = 40) {
  let count = 0;
  while (timers.length && count < limit) {
    count += 1;
    timers.shift()();
  }
  timers.length = 0;
}

const documentElement = new Element("html", { "data-width": 1024, "data-height": 768 });
const body = new Element("body", { "data-width": 1024, "data-height": 768 });
documentElement.appendChild(body);
globalThis.document = {
  body,
  documentElement,
  scrollingElement: body,
  readyState: "complete",
  createElement: (tag) => new Element(tag),
  getElementById: (id) => {
    let found = null;
    visit(documentElement, (node) => { if (node.id === id) found = node; });
    return found;
  },
  querySelectorAll: (selector) => {
    const out = [];
    visit(documentElement, (node) => { if (node.nodeType === 1 && node.matches(selector)) out.push(node); });
    return out;
  },
  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  },
  createTreeWalker(root) {
    const nodes = [];
    const collect = (node) => {
      if (!node) return;
      if (node.nodeType === 3 && String(node.nodeValue || "").trim()) nodes.push(node);
      for (const child of node.children || []) collect(child);
    };
    collect(root);
    let index = 0;
    return { nextNode: () => nodes[index++] || null };
  },
  addEventListener: () => {},
};

const main = new Element("main", { "data-width": 680, "data-height": 520 });
const heading = new Element("h1", {}, "Export Fixture");
const userMessage = new Element("div", { "data-message-author-role": "user", "data-testid": "message", "data-y": 40 }, "用户提出的问题");
const assistantMessage = new Element("div", { class: "markdown prose", "data-y": 88 }, "Claude 回复内容");
main.appendChild(heading);
main.appendChild(userMessage);
main.appendChild(assistantMessage);
body.appendChild(main);

const aside = new Element("div", { "data-testid": "history-sidebar", "data-width": 320, "data-height": 640 });
const marker = new Element("div", { "data-y": 10, "data-height": 24 }, "最近");
const existing = new Element("a", { href: "/chat/existing123456", "data-y": 48 }, "已有会话标题");
aside.appendChild(marker);
aside.appendChild(existing);
const longTitle = new Element("a", { href: "/chat/longtitle123456", "data-y": 82, "data-height": 168 }, "这是一个很长很长的历史会话标题，用来模拟侧栏换行之后高度超过普通单行的真实会话");
aside.appendChild(longTitle);
const slashTitle = new Element("div", { "data-y": 194 }, "glos/agent-safety-kit");
aside.appendChild(slashTitle);
const filePathTitle = new Element("div", { "data-y": 218 }, "src/app/main.ts");
aside.appendChild(filePathTitle);
const project = new Element("button", { "aria-label": "Gateway project", "data-y": 90 }, "Gateway");
body.appendChild(aside);
body.appendChild(project);

const projectPanel = new Element("div", { "data-testid": "project-sidebar", "data-width": 320, "data-height": 640, "data-x": 360 });
const progressCard = new Element("div", { "data-y": 24 }, "进度 9 个");
const filesCard = new Element("div", { "data-y": 80, "data-height": 180 }, "aaaa 说明 · CLAUDE.md manage.py views.py");
const contextCard = new Element("div", { "data-y": 280, "data-height": 160 }, "上下文 跟踪此任务中使用的工具和引用文件。");
projectPanel.appendChild(progressCard);
projectPanel.appendChild(filesCard);
projectPanel.appendChild(contextCard);
body.appendChild(projectPanel);

eval(runtime);
flushTimers();

const fresh = new Element("a", { href: "/chat/fresh123456", "data-y": 132 }, "新建会话标题");
aside.appendChild(fresh);
flushTimers();
const currentNew = new Element("div", { "aria-current": "page", "data-y": 156 }, "新建聊天");
aside.appendChild(currentNew);
flushTimers();
const placeholder = new Element("div", { "data-y": 170 }, "占位会话");
aside.appendChild(placeholder);
flushTimers();
placeholder.setAttribute("href", "/chat/placeholder123456");
placeholder.setAttribute("aria-current", "page");
placeholder.setAttribute("title", "新建会话标题");
placeholder.setAttribute("data-chat-id", "placeholder123456");
flushTimers();
const before = existing.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const projectButtons = project.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const longTitleButtons = longTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const slashTitleButtons = slashTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const filePathTitleButtons = filePathTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const after = fresh.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const currentNewButtons = currentNew.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const placeholderButtons = placeholder.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const progressButtons = progressCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const filesButtons = filesCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const contextButtons = contextCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const state = globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__;
const debugApi = globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_DEBUG_API__;
const exportMarkdown = debugApi?.buildConversationMarkdown?.() || "";
const exportRoles = debugApi?.messageNodes?.().map((node) => debugApi?.messageRole?.(node));
const debugCounts = {
  anchors: aside.querySelectorAll("a[href]").length,
  chatAnchors: aside.querySelectorAll("a[href^='/chat/']").length,
  panels: document.querySelectorAll("aside,nav,[role='navigation'],[data-sidebar],[data-testid*='sidebar'],[data-testid*='history'],[data-testid*='conversation'],[data-testid*='chat'],[class*='sidebar'],[class*='Sidebar'],[class*='history'],[class*='History']").length,
  existingChildren: existing.children.map((child) => `${child.tagName || "TEXT"}:${child.className || ""}`),
  freshReason: debugApi?.sessionRowRejectReason?.(fresh),
  freshInside: debugApi?.isInsideRecentsSection?.(fresh),
  freshSignal: debugApi?.hasSessionSignal?.(fresh),
  currentNewReason: debugApi?.sessionRowRejectReason?.(currentNew),
  longTitleReason: debugApi?.sessionRowRejectReason?.(longTitle),
  slashTitleReason: debugApi?.sessionRowRejectReason?.(slashTitle),
  filePathTitleReason: debugApi?.sessionRowRejectReason?.(filePathTitle),
  placeholderReason: debugApi?.sessionRowRejectReason?.(placeholder),
  panels: debugApi?.sessionPanelRoots?.().length,
  sections: debugApi?.recentSectionRoots?.().length,
};

if (before !== 3) throw new Error(`existing session buttons=${before} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (longTitleButtons !== 3) throw new Error(`long title session buttons=${longTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (slashTitleButtons !== 3) throw new Error(`slash title session buttons=${slashTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (after !== 3) throw new Error(`fresh session buttons=${after} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (currentNewButtons !== 3) throw new Error(`current new session buttons=${currentNewButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (placeholderButtons !== 3) throw new Error(`placeholder session buttons=${placeholderButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (projectButtons !== 0) throw new Error(`project buttons=${projectButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (filePathTitleButtons !== 0) throw new Error(`file path title buttons=${filePathTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (progressButtons !== 0) throw new Error(`progress buttons=${progressButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (filesButtons !== 0) throw new Error(`files buttons=${filesButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (contextButtons !== 0) throw new Error(`context buttons=${contextButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (!state || state.candidateCount < 6) throw new Error(`bad state ${JSON.stringify(state)}`);
if (!exportMarkdown.includes("用户提出的问题")) throw new Error(`export missing user markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);
if (!exportMarkdown.includes("Claude 回复内容")) throw new Error(`export missing assistant markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);
if (!exportMarkdown.includes("## 用户") || !exportMarkdown.includes("## Claude")) throw new Error(`export missing roles markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);

console.log(JSON.stringify({ before, after, currentNewButtons, longTitleButtons, slashTitleButtons, placeholderButtons, projectButtons, filePathTitleButtons, progressButtons, filesButtons, contextButtons, candidateCount: state.candidateCount, exportHasUser: exportMarkdown.includes("用户提出的问题"), exportHasAssistant: exportMarkdown.includes("Claude 回复内容"), exportRoles }));
