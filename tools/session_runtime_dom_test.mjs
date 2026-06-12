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
  values() {
    return String(this.node.className || "").split(/\s+/).filter(Boolean);
  }
  setValues(values) {
    this.node.className = [...new Set(values)].join(" ");
  }
  add(value) {
    this.setValues([...this.values(), value]);
  }
  remove(value) {
    this.setValues(this.values().filter((item) => item !== value));
  }
  contains(value) {
    return (` ${this.node.className || ""} `).includes(` ${value} `);
  }
  toggle(value, force) {
    const has = this.contains(value);
    const shouldAdd = force === undefined ? !has : !!force;
    if (shouldAdd) this.add(value);
    else this.remove(value);
    return shouldAdd;
  }
}

class Element {
  constructor(tagName, attrs = {}, text = "") {
    this.nodeType = 1;
    this.tagName = tagName.toUpperCase();
    this.attributes = { ...attrs };
    this.children = [];
    this.parentElement = null;
    this.style = {
      setProperty(name, value) {
        this[name] = String(value);
      },
    };
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
    notifyMutation("childList", "", this, [node], []);
    return node;
  }

  remove() {
    if (!this.parentElement) return;
    const parent = this.parentElement;
    const siblings = this.parentElement.children;
    const index = siblings.indexOf(this);
    if (index >= 0) siblings.splice(index, 1);
    this.parentElement = null;
    notifyMutation("childList", "", parent, [], [this]);
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
    if (name === "class") {
      this.className = String(value);
      this.classList = new ClassList(this);
    }
    notifyMutation("attributes", name, this, [], []);
  }

  getAttribute(name) {
    return this.attributes[name] ?? null;
  }

  addEventListener(type, handler) {
    (this.eventListeners[type] ||= []).push(handler);
  }

  removeEventListener(type, handler) {
    this.eventListeners[type] = (this.eventListeners[type] || []).filter((item) => item !== handler);
  }

  dispatchEvent(event) {
    event.target ||= this;
    for (const handler of this.eventListeners[event.type] || []) handler(event);
    return true;
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
function notifyMutation(type = "childList", attributeName = "", target = document.body, addedNodes = [], removedNodes = []) {
  for (const observer of mutationObservers) {
    if (type === "attributes" && !observer.options?.attributes) continue;
    if (type === "attributes" && observer.options?.attributeFilter && !observer.options.attributeFilter.includes(attributeName)) continue;
    if (type === "childList" && !observer.options?.childList) continue;
    observer.cb([{ type, attributeName, target, addedNodes, removedNodes }]);
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
globalThis.location = { href: "https://claude.ai/desktop", pathname: "/desktop", search: "" };
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
const humanMessage = new Element("div", { "data-testid": "human-message", "data-y": 136 }, "新版 DOM 用户问题");
main.appendChild(heading);
main.appendChild(userMessage);
main.appendChild(assistantMessage);
main.appendChild(humanMessage);
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
const nestedParent = new Element("div", { "data-chat-id": "nested123456", "data-y": 244 }, "");
const nestedChild = new Element("a", { href: "/chat/nested123456" }, "嵌套会话标题");
nestedParent.appendChild(nestedChild);
aside.appendChild(nestedParent);
const project = new Element("button", { "aria-label": "Gateway project", "data-y": 90 }, "Gateway");
body.appendChild(aside);
body.appendChild(project);

const loadingAside = new Element("div", { "data-testid": "history-sidebar-loading", "data-width": 320, "data-height": 180, "data-x": 24, "data-y": 720 });
const modeTabs = new Element("div", { role: "tablist", "data-y": 18, "data-height": 42 }, "");
const coworkTab = new Element("button", { role: "tab", title: "协作 Ctrl+1", "data-y": 20 }, "协作 Ctrl+1");
const codeTab = new Element("a", { role: "tab", href: "/code/coding_session_abcdef12", "aria-current": "page", "data-y": 20 }, "代码");
modeTabs.appendChild(coworkTab);
modeTabs.appendChild(codeTab);
loadingAside.appendChild(modeTabs);
const customNav = new Element("a", { href: "/settings/customize", "aria-label": "自定义", "data-y": 74 }, "自定义");
loadingAside.appendChild(customNav);
body.appendChild(loadingAside);

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
nestedChild.dispatchEvent({ type: "pointerover", target: nestedChild });
body.dispatchEvent({ type: "pointerover", target: nestedChild });
flushTimers();

const fresh = new Element("a", { href: "/chat/fresh123456", "data-y": 132 }, "新建会话标题");
aside.appendChild(fresh);
body.dispatchEvent({ type: "pointerover", target: fresh });
flushTimers();
const currentNew = new Element("div", { "aria-current": "page", "aria-label": "新建会话 ⌘N", "data-y": 156 }, "+ 新建会话 ⌘N");
aside.appendChild(currentNew);
body.dispatchEvent({ type: "pointerover", target: currentNew });
flushTimers();
const placeholder = new Element("div", { "data-y": 170 }, "占位会话");
aside.appendChild(placeholder);
body.dispatchEvent({ type: "pointerover", target: placeholder });
flushTimers();
placeholder.setAttribute("href", "/chat/placeholder123456");
placeholder.setAttribute("aria-current", "page");
placeholder.setAttribute("title", "新建会话标题");
placeholder.setAttribute("data-chat-id", "placeholder123456");
body.dispatchEvent({ type: "pointerover", target: placeholder });
flushTimers();
body.dispatchEvent({ type: "pointerover", target: codeTab });
flushTimers();
body.dispatchEvent({ type: "pointerover", target: customNav });
flushTimers();
const before = existing.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const projectButtons = project.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const longTitleButtons = longTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const slashTitleButtons = slashTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const filePathTitleButtons = filePathTitle.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const nestedParentButtons = nestedParent.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const nestedChildButtons = nestedChild.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const after = fresh.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const currentNewButtons = currentNew.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const placeholderButtons = placeholder.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const progressButtons = progressCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const filesButtons = filesCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const contextButtons = contextCard.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const modeTabButtons = modeTabs.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length
  + codeTab.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length
  + coworkTab.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const customNavButtons = customNav.children.filter((node) => String(node.className || "").includes("claude-zh-cn-session-action-button")).length;
const state = globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__;
const timelineCount = document.getElementById("claude-zh-cn-conversation-timeline")?.children.length || 0;
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
  nestedParentReason: debugApi?.sessionRowRejectReason?.(nestedParent),
  nestedChildReason: debugApi?.sessionRowRejectReason?.(nestedChild),
  placeholderReason: debugApi?.sessionRowRejectReason?.(placeholder),
  customNavReason: debugApi?.sessionRowRejectReason?.(customNav),
  panels: debugApi?.sessionPanelRoots?.().length,
  sections: debugApi?.recentSectionRoots?.().length,
};

if (before !== 3) throw new Error(`existing session buttons=${before} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (longTitleButtons !== 3) throw new Error(`long title session buttons=${longTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (slashTitleButtons !== 3) throw new Error(`slash title session buttons=${slashTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (nestedParentButtons !== 3) throw new Error(`nested parent session buttons=${nestedParentButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (nestedChildButtons !== 0) throw new Error(`nested child duplicate buttons=${nestedChildButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (after !== 3) throw new Error(`fresh session buttons=${after} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (currentNewButtons !== 0) throw new Error(`current new session command buttons=${currentNewButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (placeholderButtons !== 3) throw new Error(`placeholder session buttons=${placeholderButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (projectButtons !== 0) throw new Error(`project buttons=${projectButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (filePathTitleButtons !== 0) throw new Error(`file path title buttons=${filePathTitleButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (progressButtons !== 0) throw new Error(`progress buttons=${progressButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (filesButtons !== 0) throw new Error(`files buttons=${filesButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (contextButtons !== 0) throw new Error(`context buttons=${contextButtons} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (!state || state.candidateCount < 6) throw new Error(`bad state ${JSON.stringify(state)}`);
if (timelineCount < 2) throw new Error(`timeline missing count=${timelineCount} state=${JSON.stringify(state)} debug=${JSON.stringify(debugCounts)}`);
if (!exportMarkdown.includes("用户提出的问题")) throw new Error(`export missing user markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);
if (!exportMarkdown.includes("Claude 回复内容")) throw new Error(`export missing assistant markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);
if (!exportMarkdown.includes("新版 DOM 用户问题")) throw new Error(`export missing human markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);
if (!exportMarkdown.includes("## 用户") || !exportMarkdown.includes("## Claude")) throw new Error(`export missing roles markdown=${JSON.stringify(exportMarkdown)} roles=${JSON.stringify(exportRoles)}`);

console.log(JSON.stringify({ before, after, currentNewButtons, longTitleButtons, slashTitleButtons, nestedParentButtons, nestedChildButtons, placeholderButtons, projectButtons, filePathTitleButtons, progressButtons, filesButtons, contextButtons, modeTabButtons, customNavButtons, timelineCount, candidateCount: state.candidateCount, exportHasUser: exportMarkdown.includes("用户提出的问题"), exportHasAssistant: exportMarkdown.includes("Claude 回复内容"), exportRoles }));
