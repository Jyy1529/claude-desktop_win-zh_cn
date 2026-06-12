#!/usr/bin/env python3
"""Launch Claude with DevTools/CDP and inject the session delete runtime."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import patch_chunks_zh_cn  # noqa: E402


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9229
LOCAL_DELETE_QUEUE = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_REQUESTS__"
LOCAL_DELETE_RESULTS = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_RESULTS__"
LOCAL_DELETE_BRIDGE = "__CLAUDE_ZH_CN_LOCAL_SESSION_DELETE_BRIDGE__"
LOCAL_SESSION_ID_RE = re.compile(
    r"^local_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class CdpError(RuntimeError):
    """Raised when the CDP transport or command fails."""


class CdpClient:
    def __init__(self, websocket_url: str, *, timeout: float = 5.0) -> None:
        self.websocket_url = websocket_url
        self.timeout = timeout
        self._next_id = 0
        self._socket: socket.socket | ssl.SSLSocket | None = None
        self._connect()

    def __enter__(self) -> "CdpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._send_frame(0x8, b"")
        except OSError:
            pass
        try:
            self._socket.close()
        finally:
            self._socket = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        self._send_text(json.dumps({
            "id": message_id,
            "method": method,
            "params": params or {},
        }, separators=(",", ":")))

        while True:
            message = json.loads(self._recv_text())
            if message.get("id") != message_id:
                continue
            if "error" in message:
                raise CdpError(f"{method} failed: {message['error']}")
            return message.get("result", {})

    def _connect(self) -> None:
        parsed = urllib.parse.urlparse(self.websocket_url)
        if parsed.scheme not in {"ws", "wss"}:
            raise CdpError(f"Unsupported websocket scheme: {parsed.scheme}")

        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        host = parsed.hostname or "127.0.0.1"
        raw = socket.create_connection((host, port), timeout=self.timeout)
        raw.settimeout(self.timeout)
        sock: socket.socket | ssl.SSLSocket = raw
        if parsed.scheme == "wss":
            sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)

        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
        sock.sendall(request)

        header = b""
        while b"\r\n\r\n" not in header:
            chunk = sock.recv(4096)
            if not chunk:
                sock.close()
                raise CdpError("CDP websocket closed during handshake")
            header += chunk
            if len(header) > 65536:
                sock.close()
                raise CdpError("CDP websocket handshake header is too large")

        first_line = header.split(b"\r\n", 1)[0]
        if b" 101 " not in first_line:
            sock.close()
            raise CdpError(first_line.decode("latin-1", errors="replace"))

        self._socket = sock

    def _send_text(self, text: str) -> None:
        self._send_frame(0x1, text.encode("utf-8"))

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        if self._socket is None:
            raise CdpError("CDP websocket is not connected")

        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._socket.sendall(bytes(header) + mask + masked)

    def _recv_text(self) -> str:
        while True:
            opcode, payload = self._recv_frame()
            if opcode == 0x8:
                raise CdpError("CDP websocket closed")
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x1:
                return payload.decode("utf-8")
            if opcode == 0x2:
                return payload.decode("utf-8", errors="replace")

    def _recv_frame(self) -> tuple[int, bytes]:
        header = self._read_exact(2)
        first, second = header[0], header[1]
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]

        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length) if length else b""
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def _read_exact(self, length: int) -> bytes:
        if self._socket is None:
            raise CdpError("CDP websocket is not connected")
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._socket.recv(length - len(chunks))
            if not chunk:
                raise CdpError("CDP websocket closed while reading")
            chunks.extend(chunk)
        return bytes(chunks)


def inject_session_delete_runtime(client: Any) -> dict[str, Any]:
    script = patch_chunks_zh_cn.session_delete_inject_script()
    client.call("Runtime.enable")
    client.call("Page.enable")
    client.call("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    return client.call("Runtime.evaluate", {
        "expression": script,
        "awaitPromise": True,
        "userGesture": True,
    })


def read_session_delete_state(client: Any) -> Any:
    result = client.call("Runtime.evaluate", {
        "expression": "globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ || null",
        "returnByValue": True,
    })
    return result.get("result", {}).get("value")


def read_runtime_health(client: Any) -> Any:
    result = client.call("Runtime.evaluate", {
        "expression": (
            "({"
            "sessionDelete: globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__ || null,"
            "sessionDeletePatch: !!globalThis.__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__,"
            "fontPatch: !!globalThis.__CLAUDE_ZH_CN_FONT_PATCH__,"
            "visibleTextFixPatch: !!globalThis.__CLAUDE_ZH_CN_VISIBLE_TEXT_FIX_PATCH__"
            "})"
        ),
        "returnByValue": True,
    })
    return result.get("result", {}).get("value")


def local_session_roots() -> list[Path]:
    roots: list[Path] = []
    appdata = os.environ.get("APPDATA")
    localappdata = os.environ.get("LOCALAPPDATA")
    for base in [appdata, localappdata]:
        if not base:
            continue
        for profile in ["Claude", "Claude-3p"]:
            roots.append(Path(base) / profile / "local-agent-mode-sessions")
    if localappdata:
        package_root = Path(localappdata) / "Packages" / "Claude_pzs8sxrjxfjjc"
        roots.extend([
            package_root / "LocalCache" / "Roaming" / "Claude" / "local-agent-mode-sessions",
            package_root / "LocalCache" / "Local" / "Claude" / "local-agent-mode-sessions",
        ])

    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def normalize_local_session_id(value: Any) -> str:
    session_id = str(value or "").strip()
    if LOCAL_SESSION_ID_RE.fullmatch(session_id):
        return session_id
    return ""


def find_local_session_targets(session_id: str, roots: list[Path] | None = None) -> list[dict[str, str]]:
    normalized = normalize_local_session_id(session_id)
    if not normalized:
        raise CdpError(f"Invalid local session id: {session_id!r}")

    targets: list[dict[str, str]] = []
    for root in roots or local_session_roots():
        if not root.exists():
            continue
        try:
            account_dirs = list(root.iterdir())
        except OSError:
            continue
        for account_dir in account_dirs:
            if not account_dir.is_dir() or account_dir.name == "skills-plugin":
                continue
            try:
                space_dirs = list(account_dir.iterdir())
            except OSError:
                continue
            for space_dir in space_dirs:
                if not space_dir.is_dir():
                    continue
                metadata = space_dir / f"{normalized}.json"
                data_dir = space_dir / normalized
                if metadata.exists() or data_dir.exists():
                    targets.append({
                        "root": str(root),
                        "space": str(space_dir),
                        "metadata": str(metadata),
                        "dataDir": str(data_dir),
                    })
    return targets


def quarantine_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or str(ROOT)
    return Path(base) / "Claude-zh-CN-session-delete-quarantine"


def unique_quarantine_dir(session_id: str, base: Path | None = None) -> Path:
    parent = base or quarantine_root()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = parent / f"{timestamp}_{session_id}"
    index = 1
    while candidate.exists():
        index += 1
        candidate = parent / f"{timestamp}_{session_id}_{index}"
    return candidate


def quarantine_local_session(
    session_id: str,
    *,
    dry_run: bool = False,
    roots: list[Path] | None = None,
    quarantine_base: Path | None = None,
) -> dict[str, Any]:
    normalized = normalize_local_session_id(session_id)
    if not normalized:
        return {"ok": False, "sessionId": session_id, "error": "Only local_<uuid> sessions can be deleted locally."}

    targets = find_local_session_targets(normalized, roots=roots)
    if not targets:
        return {"ok": False, "sessionId": normalized, "error": "Local session files were not found."}

    existing_targets: list[dict[str, str]] = []
    for target in targets:
        existing = {
            key: value
            for key, value in target.items()
            if key in {"metadata", "dataDir"} and Path(value).exists()
        }
        if existing:
            existing_targets.append(existing)

    if dry_run:
        return {"ok": True, "sessionId": normalized, "dryRun": True, "targets": existing_targets}

    quarantine_dir = unique_quarantine_dir(normalized, quarantine_base)
    moved: list[dict[str, str]] = []
    for index, target in enumerate(existing_targets, start=1):
        target_quarantine = quarantine_dir / f"target-{index}"
        target_quarantine.mkdir(parents=True, exist_ok=True)
        for key, source_value in target.items():
            source = Path(source_value)
            destination = target_quarantine / source.name
            shutil.move(str(source), str(destination))
            moved.append({"kind": key, "from": str(source), "to": str(destination)})

    return {
        "ok": bool(moved),
        "sessionId": normalized,
        "mode": "quarantine",
        "quarantine": str(quarantine_dir),
        "moved": moved,
        "error": "" if moved else "No local session files were moved.",
    }


def local_delete_bridge_source() -> str:
    return (
        "(() => {"
        f"globalThis.{LOCAL_DELETE_QUEUE} = Array.isArray(globalThis.{LOCAL_DELETE_QUEUE}) ? globalThis.{LOCAL_DELETE_QUEUE} : [];"
        f"globalThis.{LOCAL_DELETE_RESULTS} = globalThis.{LOCAL_DELETE_RESULTS} || {{}};"
        f"globalThis.{LOCAL_DELETE_BRIDGE} = {{ enabled: true, mode: 'quarantine', startedAt: Date.now() }};"
        f"return globalThis.{LOCAL_DELETE_BRIDGE};"
        "})()"
    )


def enable_local_delete_bridge(client: Any) -> Any:
    source = local_delete_bridge_source()
    client.call("Page.addScriptToEvaluateOnNewDocument", {"source": source})
    return client.call("Runtime.evaluate", {
        "expression": source,
        "returnByValue": True,
    }).get("result", {}).get("value")


def read_local_delete_requests(client: Any) -> list[dict[str, Any]]:
    result = client.call("Runtime.evaluate", {
        "expression": (
            "(() => {"
            f"const queue = Array.isArray(globalThis.{LOCAL_DELETE_QUEUE}) ? globalThis.{LOCAL_DELETE_QUEUE} : [];"
            f"globalThis.{LOCAL_DELETE_QUEUE} = [];"
            "return queue.filter((item) => item && typeof item === 'object').slice(0, 16);"
            "})()"
        ),
        "returnByValue": True,
    })
    value = result.get("result", {}).get("value")
    return value if isinstance(value, list) else []


def write_local_delete_result(client: Any, result: dict[str, Any]) -> None:
    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    client.call("Runtime.evaluate", {
        "expression": (
            "(() => {"
            f"const result = {payload};"
            f"globalThis.{LOCAL_DELETE_RESULTS} = globalThis.{LOCAL_DELETE_RESULTS} || {{}};"
            f"globalThis.{LOCAL_DELETE_RESULTS}[String(result.requestId || '')] = result;"
            "window.dispatchEvent?.(new CustomEvent('claude-zh-cn-local-session-delete-result', { detail: result }));"
            "return true;"
            "})()"
        ),
        "returnByValue": True,
    })


def handle_local_delete_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = str(request.get("requestId") or "")
    session_id = request.get("sessionId") or request.get("id") or ""
    result = quarantine_local_session(str(session_id), dry_run=bool(request.get("dryRun")))
    result["requestId"] = request_id
    result["title"] = str(request.get("title") or "")[:160]
    return result


def run_local_delete_bridge(
    client: Any,
    *,
    poll_interval: float = 0.5,
    max_empty_polls: int | None = None,
) -> None:
    enable_local_delete_bridge(client)
    print("Local session delete bridge is running. Keep this window open; press Ctrl+C to stop.")
    empty_polls = 0
    try:
        while True:
            requests = read_local_delete_requests(client)
            if not requests:
                empty_polls += 1
                if max_empty_polls is not None and empty_polls >= max_empty_polls:
                    return
                time.sleep(poll_interval)
                continue

            empty_polls = 0
            for request in requests:
                try:
                    result = handle_local_delete_request(request)
                except Exception as exc:  # noqa: BLE001
                    result = {
                        "ok": False,
                        "requestId": str(request.get("requestId") or ""),
                        "sessionId": str(request.get("sessionId") or request.get("id") or ""),
                        "error": str(exc),
                    }
                write_local_delete_result(client, result)
                if result.get("ok"):
                    print(f"Local session quarantined: {result.get('sessionId')} -> {result.get('quarantine')}")
                else:
                    print(f"Local session delete failed: {result.get('sessionId')}: {result.get('error')}")
    except KeyboardInterrupt:
        print("Local session delete bridge stopped.")


def read_debug_port_summary(host: str, port: int) -> dict[str, Any]:
    summary: dict[str, Any] = {"host": host, "port": port, "targets": [], "error": ""}
    try:
        summary["targets"] = get_targets(host, port, timeout=2.0)
    except Exception as exc:  # noqa: BLE001
        summary["error"] = str(exc)
    return summary


def scan_debug_ports(host: str, start: int, end: int) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for port in range(start, end + 1):
        if not is_port_open(host, port):
            continue
        summary = read_debug_port_summary(host, port)
        targets = summary.get("targets") or []
        if targets or summary.get("error"):
            summaries.append(summary)
    return summaries


def read_recents_row_diagnostics(client: Any) -> Any:
    result = client.call("Runtime.evaluate", {
        "expression": (
            "(() => {"
            "  const rows = [...document.querySelectorAll('[data-claude-zh-cn-delete-row=\"true\"]')];"
            "  return rows.map((row) => ({"
            "    title: (row.querySelector('[data-thread-title], .truncate, [title]')?.getAttribute('title') || row.querySelector('[data-thread-title], .truncate, [title]')?.textContent || '').replace(/\\s+/g, ' ').trim(),"
            "    text: (row.textContent || '').replace(/\\s+/g, ' ').trim(),"
            "    id: row.getAttribute('data-session-id') || row.getAttribute('data-thread-id') || row.getAttribute('data-conversation-id') || row.getAttribute('data-chat-id') || row.getAttribute('data-app-action-sidebar-thread-id') || '',"
            "    href: row.getAttribute('href') || row.querySelector('a[href]')?.getAttribute('href') || '',"
            "    buttons: row.querySelectorAll('.claude-zh-cn-session-action-button').length,"
            "    rect: (() => { const r = row.getBoundingClientRect?.(); return r ? { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) } : null; })(),"
            "  }));"
            "})()"
        ),
        "returnByValue": True,
    })
    return result.get("result", {}).get("value")


def read_candidate_row_diagnostics(client: Any) -> Any:
    result = client.call("Runtime.evaluate", {
        "expression": (
            "(() => {"
            "  const out = [];"
            "  const panels = [...document.querySelectorAll('aside,nav,[role=\"navigation\"],[data-sidebar],[data-testid*=\"sidebar\"]')].filter((panel) => {"
            "    const text = (panel.innerText || '').replace(/\\s+/g, ' ').trim();"
            "    return /最近|历史|Recent|History|Chat|聊天|会话/i.test(text) || panel.querySelector('a[href*=\"/chat/\"],[data-app-action-sidebar-thread-id],[data-session-id],[data-thread-id],[data-conversation-id],[data-chat-id]');"
            "  });"
            "  const seen = new Set();"
            "  const selector = 'a[href],button,[role=\"button\"],[role=\"link\"],[role=\"treeitem\"],[role=\"listitem\"],li,[data-testid],div';"
            "  for (const panel of panels) {"
            "    for (const node of panel.querySelectorAll(selector)) {"
            "      if (seen.has(node) || out.length >= 80) continue;"
            "      seen.add(node);"
            "      const rect = node.getBoundingClientRect?.();"
            "      if (!rect || rect.width <= 0 || rect.height <= 0) continue;"
            "      const text = (node.innerText || node.textContent || '').replace(/\\s+/g, ' ').trim();"
            "      const href = node.getAttribute('href') || node.querySelector('a[href]')?.getAttribute('href') || '';"
            "      const id = node.getAttribute('data-session-id') || node.getAttribute('data-thread-id') || node.getAttribute('data-conversation-id') || node.getAttribute('data-chat-id') || node.getAttribute('data-app-action-sidebar-thread-id') || '';"
            "      const marked = node.closest('[data-claude-zh-cn-delete-row=\"true\"]') || node.querySelector('[data-claude-zh-cn-delete-row=\"true\"]');"
            "      const looksLikeChat = /\\/(chat|conversation|thread|session)\\/[A-Za-z0-9_.-]{8,}/i.test(href);"
            "      if (!marked && !looksLikeChat && !id && text.length < 3) continue;"
            "      out.push({"
            "        marked: !!marked,"
            "        text: text.slice(0, 140),"
            "        href,"
            "        id,"
            "        tag: node.tagName,"
            "        role: node.getAttribute('role') || '',"
            "        aria: node.getAttribute('aria-label') || '',"
            "        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },"
            "        buttons: node.querySelectorAll('.claude-zh-cn-session-action-button').length"
            "      });"
            "    }"
            "  }"
            "  return out;"
            "})()"
        ),
        "returnByValue": True,
    })
    return result.get("result", {}).get("value")


def wait_for_session_delete_state(client: Any, *, timeout: float) -> Any:
    deadline = time.monotonic() + timeout
    state = None
    while time.monotonic() < deadline:
        state = read_session_delete_state(client)
        if state:
            return state
        time.sleep(0.25)
    return state


def resolve_app_dir(app_dir: str | None) -> Path:
    if app_dir:
        path = Path(app_dir).expanduser().resolve()
    else:
        found = patch_chunks_zh_cn.find_claude_package()
        if found is None:
            raise CdpError("Claude app directory was not found; pass --app-dir")
        path = found

    if not (path / "resources" / "en-US.json").exists():
        raise CdpError(f"Invalid Claude app directory: {path}")
    return path


def close_existing_claude(*, timeout: float = 8.0) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process -Name Claude -ErrorAction SilentlyContinue | Stop-Process -Force"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "if (Get-Process -Name Claude -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode == 0:
            return
        time.sleep(0.25)


def list_claude_processes() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "$p = Get-CimInstance Win32_Process | "
                    "Where-Object { $_.Name -match 'Claude|Electron|msedgewebview2|chrome|Code' -or $_.ExecutablePath -like '*Claude*' -or $_.CommandLine -like '*Claude*' } | "
                    "Select-Object ProcessId,Name,ExecutablePath,CommandLine; "
                    "$p | ConvertTo-Json -Depth 4"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = completed.stdout.strip()
        if not payload:
            return result
        data = json.loads(payload)
        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    result.append(item)
    except Exception:
        return result
    return result


def launch_claude(app_dir: Path, *, port: int) -> subprocess.Popen:
    exe = app_dir / "claude.exe"
    if not exe.exists():
        raise CdpError(f"Claude executable was not found: {exe}")

    args = [str(exe)]
    proc = subprocess.Popen(
        args,
        cwd=str(app_dir),
        env=build_launch_env(port=port),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )
    print(f"Direct exe process started: pid={proc.pid}")
    return proc


def activate_claude_appx(*, port: int) -> int:
    script = r'''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

[Flags]
public enum ActivateOptions
{
    None = 0x00000000,
    DesignMode = 0x00000001,
    NoErrorUI = 0x00000002,
    NoSplashScreen = 0x00000004
}

[ComImport, Guid("2E941141-7F97-4756-BA1D-9DECDE894A3D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IApplicationActivationManager
{
    IntPtr ActivateApplication([In] string appUserModelId, [In] string arguments, [In] ActivateOptions options, [Out] out UInt32 processId);
    IntPtr ActivateForFile([In] string appUserModelId, [In] IntPtr itemArray, [In] string verb, [Out] out UInt32 processId);
    IntPtr ActivateForProtocol([In] string appUserModelId, [In] IntPtr itemArray, [Out] out UInt32 processId);
}

[ComImport, Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")]
public class ApplicationActivationManager : IApplicationActivationManager
{
    [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
    public extern IntPtr ActivateApplication([In] string appUserModelId, [In] string arguments, [In] ActivateOptions options, [Out] out UInt32 processId);
    [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
    public extern IntPtr ActivateForFile([In] string appUserModelId, [In] IntPtr itemArray, [In] string verb, [Out] out UInt32 processId);
    [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
    public extern IntPtr ActivateForProtocol([In] string appUserModelId, [In] IntPtr itemArray, [Out] out UInt32 processId);
}
"@
$manager = [ApplicationActivationManager]::new()
$processId = 0
$hr = $manager.ActivateApplication("Claude_pzs8sxrjxfjjc!Claude", $env:CLAUDE_CDP_ARGUMENTS, [ActivateOptions]::NoErrorUI, [ref]$processId)
if ($hr.ToInt64() -lt 0) {
    [Runtime.InteropServices.Marshal]::ThrowExceptionForHR($hr.ToInt32())
}
[Console]::WriteLine($processId)
'''
    arguments = webview2_additional_browser_arguments(port)
    env = dict(os.environ)
    env["CLAUDE_CDP_ARGUMENTS"] = arguments
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-EncodedCommand", encoded_script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise CdpError((completed.stderr or completed.stdout or "AppX activation failed").strip())
    output = completed.stdout.strip().splitlines()
    process_id = int(output[-1]) if output and output[-1].strip().isdigit() else 0
    print(f"AppX activation started Claude: pid={process_id}")
    return process_id


def webview2_additional_browser_arguments(port: int) -> str:
    return f"--remote-debugging-port={port} --remote-allow-origins=*"


def build_launch_env(*, port: int, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    extra_args = webview2_additional_browser_arguments(port)
    existing_args = env.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "").strip()
    env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
        f"{existing_args} {extra_args}".strip() if existing_args else extra_args
    )
    return env


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def find_free_port(host: str, start: int, end: int) -> int:
    for port in range(start, end + 1):
        if not is_port_open(host, port):
            return port
    raise CdpError(f"No free port found between {start} and {end}")


def read_json_url(url: str, *, timeout: float) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_targets(host: str, port: int, *, timeout: float) -> list[dict[str, Any]]:
    for path in ("json/list", "json"):
        data = read_json_url(f"http://{host}:{port}/{path}", timeout=timeout)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    return []


def choose_target(targets: list[dict[str, Any]], url_contains: str | None = None) -> dict[str, Any] | None:
    candidates = [target for target in targets if target.get("webSocketDebuggerUrl")]
    if url_contains:
        needle = url_contains.casefold()
        candidates = [
            target for target in candidates
            if needle in str(target.get("url", "")).casefold()
            or needle in str(target.get("title", "")).casefold()
        ]
    preferred = [target for target in candidates if target.get("type") in {"page", "webview"}]
    if preferred:
        return preferred[0]
    return candidates[0] if candidates else None


def wait_for_target(
    host: str,
    port: int,
    *,
    timeout: float,
    url_contains: str | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            target = choose_target(get_targets(host, port, timeout=1.5), url_contains)
            if target is not None:
                return target
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(0.4)

    detail = f": {last_error}" if last_error else ""
    raise CdpError(f"No CDP target found on {host}:{port}{detail}")


def launch_claude_with_cdp(app_dir: Path, *, host: str, port: int, timeout: float) -> int:
    chosen_port = port
    if is_port_open(host, port):
        chosen_port = find_free_port(host, max(9222, port), max(9230, port + 32))
        print(f"Port {port} is already in use; using free CDP port {chosen_port}")
    try:
        activate_claude_appx(port=chosen_port)
        print(f"Started Claude through AppX activation with CDP args on port {chosen_port}")
        wait_for_target(host, chosen_port, timeout=min(5.0, max(1.0, timeout)))
        return chosen_port
    except Exception as appx_exc:  # noqa: BLE001
        print(f"AppX activation did not expose a CDP target: {appx_exc}; falling back to direct exe launch")
        close_existing_claude()
        launch_claude(app_dir, port=chosen_port)
        print(f"Started Claude with direct exe launch and WebView2 CDP args on port {chosen_port}: {app_dir}")
        wait_for_target(host, chosen_port, timeout=min(5.0, max(1.0, timeout)))
        return chosen_port


def print_debug_port_diagnostics(
    host: str,
    port: int,
    *,
    scan_ports: bool = False,
    scan_start: int = 9222,
    scan_end: int = 9240,
) -> None:
    summary = read_debug_port_summary(host, port)
    if summary.get("error"):
        print(f"CDP port summary error: {summary['error']}")
    else:
        print(f"CDP targets discovered: {len(summary['targets'])}")
        for target in summary["targets"]:
            print(
                "  "
                f"type={target.get('type')} "
                f"title={target.get('title') or ''} "
                f"url={target.get('url') or ''}"
            )
    scanned = scan_debug_ports(host, scan_start, scan_end) if scan_ports else []
    if scanned:
        print(f"CDP port scan {scan_start}-{scan_end}:")
        for item in scanned:
            if item.get("error"):
                print(f"  port={item['port']} error={item['error']}")
                continue
            print(f"  port={item['port']} targets={len(item.get('targets') or [])}")
            for target in item.get("targets") or []:
                print(
                    "    "
                    f"type={target.get('type')} "
                    f"title={target.get('title') or ''} "
                    f"url={target.get('url') or ''}"
                )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inject the Claude session delete button through DevTools/CDP")
    parser.add_argument("--app-dir", type=str, default=None, help="Claude app directory containing resources/en-US.json")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--target-url-contains", type=str, default=None)
    parser.add_argument("--no-launch", action="store_true", help="Attach to an already running CDP endpoint")
    parser.add_argument("--no-close-existing", action="store_true", help="Do not close existing Claude processes before launch")
    parser.add_argument("--diagnose-rows", action="store_true", help="Print rows currently recognized as sidebar sessions")
    parser.add_argument("--scan-ports", action="store_true", help="Scan nearby CDP ports and print discovered targets")
    parser.add_argument("--scan-port-start", type=int, default=9222)
    parser.add_argument("--scan-port-end", type=int, default=9240)
    parser.add_argument(
        "--local-delete-bridge",
        action="store_true",
        help="Keep CDP attached and quarantine local_<uuid> sessions requested by the injected UI",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        active_port = args.port
        if not args.no_launch:
            app_dir = resolve_app_dir(args.app_dir)
            if not args.no_close_existing:
                print("Closing existing Claude processes before CDP launch...")
                close_existing_claude()
            active_port = launch_claude_with_cdp(app_dir, host=args.host, port=args.port, timeout=args.timeout)
        else:
            print(f"Attaching to existing CDP endpoint on {args.host}:{active_port}")

        processes = list_claude_processes()
        if processes:
            print(f"Claude processes: {len(processes)}")
            for proc in processes:
                process_id = proc.get("Id") or proc.get("ProcessId")
                process_path = proc.get("Path") or proc.get("ExecutablePath") or proc.get("Name") or ""
                print(
                    "  "
                    f"id={process_id} "
                    f"path={process_path}"
                )
        else:
            print("Claude processes: 0")
        print_debug_port_diagnostics(
            args.host,
            active_port,
            scan_ports=args.scan_ports,
            scan_start=args.scan_port_start,
            scan_end=args.scan_port_end,
        )

        target = wait_for_target(
            args.host,
            active_port,
            timeout=args.timeout,
            url_contains=args.target_url_contains,
        )
        websocket_url = target["webSocketDebuggerUrl"]
        print(f"CDP target: {target.get('title') or target.get('url') or target.get('id')}")

        with CdpClient(websocket_url, timeout=min(5.0, max(1.0, args.timeout))) as client:
            inject_session_delete_runtime(client)
            state = wait_for_session_delete_state(client, timeout=min(5.0, args.timeout))
            health = read_runtime_health(client)
            row_diagnostics = read_recents_row_diagnostics(client) if args.diagnose_rows else None
            candidate_diagnostics = read_candidate_row_diagnostics(client) if args.diagnose_rows else None
            if args.local_delete_bridge:
                print("Session delete button injected through CDP.")
                if isinstance(health, dict):
                    print(
                        "Runtime health: "
                        f"sessionDeletePatch={health.get('sessionDeletePatch')}, "
                        f"fontPatch={health.get('fontPatch')}, "
                        f"visibleTextFixPatch={health.get('visibleTextFixPatch')}"
                    )
                run_local_delete_bridge(client)
                return 0

        print("Session delete button injected through CDP.")
        if isinstance(health, dict):
            print(
                "Runtime health: "
                f"sessionDeletePatch={health.get('sessionDeletePatch')}, "
                f"fontPatch={health.get('fontPatch')}, "
                f"visibleTextFixPatch={health.get('visibleTextFixPatch')}"
            )
        if isinstance(state, dict):
            print(
                "Health: "
                f"panels={state.get('panelCount')}, "
                f"sections={state.get('sectionCount')}, "
                f"candidates={state.get('candidateCount')}, "
                f"attached={state.get('attachedCount')}, "
                f"portal={state.get('portalButton')}, "
                f"lastError={state.get('lastError')}"
            )
            candidates = state.get("candidates")
            if isinstance(candidates, list) and candidates:
                print("Runtime candidate samples:")
                for index, row in enumerate(candidates, start=1):
                    rect = row.get("rect") or {}
                    print(
                        f"  tag={row.get('tag')!r} "
                        f"  [{index}] title={row.get('title')!r} "
                        f"text={row.get('text')!r} "
                        f"id={row.get('id')!r} href={row.get('href')!r} "
                        f"signal={row.get('signal')} "
                        f"reject={row.get('rejectReason')!r} "
                        f"rect={rect.get('x')},{rect.get('y')},{rect.get('width')}x{rect.get('height')}"
                    )
        if isinstance(row_diagnostics, list):
            print("Recognized sidebar session rows:")
            for index, row in enumerate(row_diagnostics, start=1):
                rect = row.get("rect") or {}
                print(
                    f"  [{index}] title={row.get('title')!r} "
                    f"text={row.get('text')!r} "
                    f"id={row.get('id')!r} href={row.get('href')!r} "
                    f"buttons={row.get('buttons')} "
                    f"rect={rect.get('x')},{rect.get('y')},{rect.get('width')}x{rect.get('height')}"
                )
        if isinstance(candidate_diagnostics, list):
            print("Sidebar row candidates:")
            for index, row in enumerate(candidate_diagnostics, start=1):
                rect = row.get("rect") or {}
                print(
                    f"  [{index}] marked={row.get('marked')} "
                    f"text={row.get('text')!r} "
                    f"id={row.get('id')!r} href={row.get('href')!r} "
                    f"tag={row.get('tag')} role={row.get('role')!r} "
                    f"buttons={row.get('buttons')} "
                    f"rect={rect.get('x')},{rect.get('y')},{rect.get('width')}x{rect.get('height')}"
                )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"CDP session delete injection failed: {exc}", file=sys.stderr)
        try:
            if "args" in locals():
                print_debug_port_diagnostics(
                    args.host,
                    locals().get("active_port", args.port),
                    scan_ports=True,
                    scan_start=args.scan_port_start,
                    scan_end=args.scan_port_end,
                )
        except Exception as diagnostic_exc:  # noqa: BLE001
            print(f"CDP diagnostics failed: {diagnostic_exc}", file=sys.stderr)
        print("Close Claude and retry, or run with --no-launch after starting Claude with the same debug port.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
