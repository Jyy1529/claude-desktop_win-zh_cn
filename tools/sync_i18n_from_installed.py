#!/usr/bin/env python3
"""Sync missing zh-CN i18n keys from the installed Claude resources.

This is a deterministic best-effort updater for version bumps. It keeps all
existing translations, reuses exact translation memory, then applies a compact
rule dictionary for newly added strings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_RESOURCES = ROOT / "resources"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import patch_windowsapps_json_only  # noqa: E402


RESOURCE_PAIRS = {
    "desktop": {
        "local": LOCAL_RESOURCES / "desktop-zh-CN.json",
        "installed_en": Path("resources/en-US.json"),
    },
    "frontend": {
        "local": LOCAL_RESOURCES / "frontend-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/en-US.json"),
    },
    "statsig": {
        "local": LOCAL_RESOURCES / "statsig-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/statsig/en-US.json"),
    },
}


EXACT_TRANSLATIONS = {
    "Active Claude Code users in this period": "此期间活跃的 Claude Code 用户",
    "Adds to this run's prompt:": "添加到本次运行的提示词：",
    "Adding marketplaces is blocked by your organization's policy. Contact your administrator.": "添加市场已被组织策略阻止。请联系管理员。",
    "Allow using Claude Design to generate design artifacts.": "允许使用 Claude Design 生成设计工件。",
    "Allow your team to run multi-agent workflows in Claude Code.": "允许你的团队在 Claude Code 中运行多智能体工作流。",
    "Always uses deep reasoning": "始终使用深度推理",
    "Already in this workspace": "已在此工作区中",
    "About discoverable domains": "关于可发现域名",
    "About this chart": "关于此图表",
    "Account executive": "客户经理",
    "Actuary": "精算师",
    "Academic": "学术人员",
    "AI engineer": "AI 工程师",
    "Artifcats that stay up to date": "保持更新的工件",
    "Artifacts that stay up to date": "保持更新的工件",
    "At limit": "已达限制",
    "Auto-accept permissions mode": "自动接受权限模式",
    "Balanced for everyday work": "适合日常工作的均衡模式",
    "Business owner": "企业主",
    "Business development": "业务拓展",
    "Buying agent": "采购代理",
    "By group / tier": "按组/层级",
    "By clicking to accept, you represent and warrant that: (i) you are the individual registered to this administrator account; (ii) you have full legal authority to bind {organization} to this BAA; (iii) you have read and understand this BAA and the Implementation Guide; and (iv) you agree, on behalf of your Organization, to the terms and conditions of this BAA.": "点击接受即表示你声明并保证：(i) 你是此管理员账号的注册个人；(ii) 你拥有让 {organization} 受此 BAA 约束的完整法律权限；(iii) 你已阅读并理解此 BAA 和实施指南；(iv) 你代表组织同意此 BAA 的条款和条件。",
    "Bypass permissions mode and auto mode controls for Claude Code Desktop are moving to Managed settings on June 5, 2026, alongside the CLI and IDE.": "Claude Code Desktop 的绕过权限模式和自动模式控制项将于 2026 年 6 月 5 日与 CLI 和 IDE 一起迁移到托管设置。",
    "Can think for more complex tasks": "可为更复杂的任务进行思考",
    "Change location for Cowork files?": "更改 Cowork 文件位置？",
    "Checking install status…": "正在检查安装状态…",
    "Choose Claude data folder": "选择 Claude 数据文件夹",
    "Claude Code analytics view": "Claude Code 分析视图",
    "Claude Code remote control": "Claude Code 远程控制",
    "Claude for Outlook": "Claude for Outlook",
    "Claude Pro is required to connect to Claude Code": "连接 Claude Code 需要 Claude Pro",
    "Claude Security requires usage credits to be turned on. Contact an organization admin to turn them on.": "Claude Security 需要开启用量额度。请联系组织管理员开启。",
    "Claude will keep these in mind across chats and Cowork within Anthropic's guidelines. Learn more": "Claude 会在 Anthropic 指南范围内，在聊天和 Cowork 中记住这些内容。了解更多",
    "Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic's guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>": "Claude 会在聊天和 Cowork 中记住这些内容，并遵循<aupLink>Anthropic 的指南</aupLink>。<learnMoreLink>了解更多</learnMoreLink>",
    "Claude is still working": "Claude 仍在工作",
    "Claude is working in {count, plural, one {# session} other {# sessions}}. Quitting now will interrupt that work.": "Claude 正在 {count, plural, one {# 个会话} other {# 个会话}} 中工作。现在退出会中断这些工作。",
    "Complex, detailed work": "复杂、细致的工作",
    "Connected · {latency}ms": "已连接 · {latency}ms",
    "Connector data hidden in shared chats": "共享聊天中已隐藏连接器数据",
    "Connector updated": "连接器已更新",
    "Connectors needed": "需要连接器",
    "Controls which repositories Claude can reach across your organization.": "控制 Claude 可访问组织中的哪些仓库。",
    "Connect your organization's GitHub Enterprise instances to enable code review and repository access.": "连接组织的 GitHub Enterprise 实例，以启用代码审查和仓库访问。",
    "Continue without answering": "不回答并继续",
    "Copy and restart": "复制并重启",
    "Copy organization ID": "复制组织 ID",
    "Copy relative path": "复制相对路径",
    "Couldn’t rotate the secret. Try again.": "无法轮换密钥。请重试。",
    "Crash reports and error diagnostics, so we can fix bugs": "崩溃报告和错误诊断，用于帮助修复问题",
    "Create API key": "创建 API 密钥",
    "Daily usage: {capped} of {total, plural, one {# day} other {# days}} hit the limit": "每日用量：{total, plural, one {# 天} other {# 天}}中有 {capped} 天达到限制",
    "Define a collection of users": "定义一组用户",
    "Detached comment": "分离的评论",
    "Digital marketer": "数字营销人员",
    "Dismiss session": "关闭会话",
    "Domain claim could not be started because one or more required settings were changed. Review the requirements and try again.": "由于一个或多个必需设置已更改，无法开始域名声明。请检查要求后重试。",
    "Domains where this credential can be sent. Wildcard only as the leftmost label (e.g. *.example.com).": "此凭据可发送到的域名。通配符只能作为最左侧标签使用（例如 *.example.com）。",
    "Discard Changes": "放弃更改",
    "Apply Changes": "应用更改",
    "Discard unsaved changes?": "放弃未保存的更改？",
    "Estimated usage cost": "预计用量成本",
    "Dynamic workflows": "动态工作流",
    "Empty": "空",
    "Extended": "扩展",
    "Extra": "超高",
    "Failed to remove source.": "移除来源失败。",
    "Failed to save rule. Check your inputs and try again.": "保存规则失败。请检查输入后重试。",
    "Failed to update Claude Code setting. You can try again.": "更新 Claude Code 设置失败。你可以重试。",
    "Feature requests ({count})": "功能请求（{count}）",
    "Faster": "更快",
    "Financial analyst": "金融分析师",
    "Filter projects (active)": "筛选项目（活跃）",
    "General restrictions": "通用限制",
    "Get Claude Code": "获取 Claude Code",
    "Get usage credits when you run it": "运行时获取用量额度",
    "Give your developers access to Claude Code": "向开发者开放 Claude Code 访问权限",
    "GitHub App installed": "GitHub App 已安装",
    "GitHub access check failed": "GitHub 访问检查失败",
    "GitHub App": "GitHub App",
    "GitHub credentials were rejected. Reconnect GitHub to continue.": "GitHub 凭据被拒绝。请重新连接 GitHub 后继续。",
    "Have a visual UI MCP App now? Email your carousel images to <link>{email}</link> and we'll attach them to your listing manually.": "已经有可视化 UI MCP App 了吗？请将轮播图发送到 <link>{email}</link>，我们会手动附加到你的列表。",
    "High-contrast dark theme": "高对比度深色主题",
    "Holding {keys}": "按住 {keys}",
    "Install Claude Code in your terminal or IDE": "在终端或 IDE 中安装 Claude Code",
    "Inference configuration": "推理配置",
    "Invite requested": "已请求邀请",
    "Invalid request": "无效请求",
    "Installation": "安装",
    "Intelligence analyst": "情报分析师",
    "Issuer URLs the OAuth sign-in may use, as a JSON array. Pre-filled by presets; ask your IdP admin if unsure.": "OAuth 登录可使用的颁发者 URL，格式为 JSON 数组。预设会自动填充；不确定时请询问你的 IdP 管理员。",
    "Keep chatting": "继续聊天",
    "Keep editing": "继续编辑",
    "Learn how to level up": "了解如何进阶",
    "Light, casual tasks": "轻量、日常任务",
    "Loading older messages": "正在加载较早消息",
    "Loading routines": "正在加载例程",
    "Loading devices…": "正在加载设备…",
    "Loading output…": "正在加载输出…",
    "Low": "低",
    "Longer chats draw down your usage faster": "较长聊天会更快消耗你的用量",
    "Match a writing style": "匹配写作风格",
    "Max": "最高",
    "Medium": "中",
    "Migrate accounts using your domains": "使用你的域名迁移账号",
    "Monthly limit": "每月限制",
    "More usage, SSO, advanced security, and dedicated support for your organization.": "为你的组织提供更多用量、SSO、高级安全和专属支持。",
    "Not in use — toggle on to fetch and apply this URL.": "未使用；开启后会获取并应用此 URL。",
    "Not delivered": "未送达",
    "Not synced yet": "尚未同步",
    "No active subscription": "没有活跃订阅",
    "No browsers connected": "没有已连接的浏览器",
    "No chats match “{query}”": "没有匹配“{query}”的聊天",
    "No limit": "无限制",
    "no limit": "无限制",
    "No limit set": "未设置限制",
    "No messages yet": "暂无消息",
    "No project": "没有项目",
    "No runs yet": "暂无运行",
    "No server selected.": "未选择服务器。",
    "No targets routed through this proxy yet.": "尚无目标通过此代理路由。",
    "Off": "关",
    "Offer 1M-context variant": "提供 1M 上下文变体",
    "Org default": "组织默认值",
    "Outline my pitch deck": "梳理我的路演演示结构",
    "Power user": "深度用户",
    "Photographer": "摄影师",
    "Physiotherapist": "物理治疗师",
    "Primary school teacher": "小学教师",
    "Private equity associate": "私募股权投资助理",
    "Product owner": "产品负责人",
    "Project ID": "项目 ID",
    "Project conversation view": "项目对话视图",
    "Program manager": "项目经理",
    "Public Projects": "公共项目",
    "Quick replies to simple questions": "适合简单问题的快速回复",
    "Reading console messages": "正在读取控制台消息",
    "Reading memory…": "正在读取记忆…",
    "Reading network requests": "正在读取网络请求",
    "Request usage credits": "请求用量额度",
    "Remove queued message": "移除排队消息",
    "Request is too large": "请求过大",
    "Restricted by your organization's Managed settings. Update Managed settings or your MDM-deployed configuration to change this.": "受组织的托管设置限制。请更新托管设置或 MDM 下发配置来更改此项。",
    "Restart to apply this configuration.": "重启以应用此配置。",
    "Running on this device": "正在此设备上运行",
    "Runs weekdays at {time} {tz}": "工作日 {time} {tz} 运行",
    "SCIM synced": "已通过 SCIM 同步",
    "Scanning…": "正在扫描…",
    "Search artifacts...": "搜索工件...",
    "Searching…": "正在搜索…",
    "Secure VM features": "安全虚拟机功能",
    "Secret copied to clipboard.": "密钥已复制到剪贴板。",
    "Shown in the model picker. Leave blank to auto-format from the ID.": "显示在模型选择器中。留空则根据 ID 自动格式化。",
    "Show fewer": "显示更少",
    "Sidebar pins and starred sessions survive sign-out": "侧边栏固定项和星标会话会在退出登录后保留",
    "Session was interrupted": "会话已中断",
    "Sessions you start will show up here": "你启动的会话会显示在这里",
    "Set up usage credits so anyone with a usage-based seat can use Claude.": "设置用量额度，让任何拥有按用量计费席位的人都可以使用 Claude。",
    "This capability is enabled but its required capability Chat is not.": "此能力已启用，但必需的 Chat 能力未启用。",
    "This capability is enabled but its required capability Claude Code is not.": "此能力已启用，但必需的 Claude Code 能力未启用。",
    "This capability is enabled but its required capability Cowork is not.": "此能力已启用，但必需的 Cowork 能力未启用。",
    "This connector doesn't use authentication. You can block individual tools instead.": "此连接器不使用身份验证。你可以改为阻止单个工具。",
    "This runner's token is invalidated immediately. Its next API call will be rejected.": "此运行器的令牌会立即失效。它的下一次 API 调用将被拒绝。",
    "Software architect": "软件架构师",
    "Solopreneur": "个体创业者",
    "Sports coach": "体育教练",
    "Something went wrong. Try again.": "出了点问题。请重试。",
    "Spend · {used}": "消耗 · {used}",
    "Spend · {used} of {limit}": "消耗 · {used} / {limit}",
    "Stop this task": "停止此任务",
    "Supply chain manager": "供应链经理",
    "Team": "团队",
    "Thinking": "思考",
    "The hardest problems. Takes longest.": "最困难的问题。耗时最长。",
    "Higher effort means more thorough responses, but takes longer and uses your limits faster.": "更高强度意味着回答更彻底，但耗时更长，也会更快消耗你的额度。",
    "May use excessive tokens resulting in long response times and may hit token limits. Use sparingly for the hardest tasks.": "可能使用大量 token，导致响应时间较长，并可能触及 token 限制。仅建议在最困难的任务中谨慎使用。",
    "This clears your current conversation and starts a new one.": "这会清空当前对话并开始一个新对话。",
    "Turn any idea into a diagram, chart, or visual you can click and explore.": "将任何想法变成可点击、可探索的图表、图形或可视化内容。",
    "Type or paste in emails separated by commas or new lines": "输入或粘贴邮箱，并用逗号或换行分隔",
    "Updated {time}": "已更新 {time}",
    "Usage-limit notices now say which limit you hit and when it resets": "用量限制通知现在会说明你触及了哪项限制以及何时重置",
    "Usage credits ({count})": "用量额度（{count}）",
    "Usage credits draw down as you go. Good for occasional busy days.": "用量额度会随使用扣减，适合偶尔忙碌的日子。",
    "Usage credits show up on your invoice at the end of each billing cycle.": "用量额度会在每个账单周期结束时显示在发票上。",
    "Visualize anything": "可视化任何内容",
    "We'll package up your conversations, projects, and settings for download. This might take some time to complete.": "我们会打包你的对话、项目和设置供下载。这可能需要一些时间。",
    "We're doing some quick maintenance on billing. Your current plan still works as usual — check back shortly to upgrade.": "我们正在进行账单快速维护。你的当前方案仍可正常使用，请稍后再回来升级。",
    "Which organization is this about?": "这是关于哪个组织？",
    "What do you want automated?": "你想自动化什么？",
    "Your GitHub credentials were rejected. Reconnect GitHub to continue.": "你的 GitHub 凭据被拒绝。请重新连接 GitHub 后继续。",
    "Your local time, next day": "你的本地时间，次日",
    "Your session has expired.": "你的会话已过期。",
    "Your session has expired. Sign in again from the home screen.": "你的会话已过期。请从主屏幕重新登录。",
    "Your session credentials expired.": "你的会话凭据已过期。",
    "Your organization hasn't provided plugins. Contact your organization administrator to add them.": "这是组织插件目录。当前组织尚未提供插件；本地/个人插件请前往“设置 > 自定义 > 个人插件”上传或管理。",
    "Your organization hasn’t provided plugins. Contact your organization administrator to add them.": "这是组织插件目录。当前组织尚未提供插件；本地/个人插件请前往“设置 > 自定义 > 个人插件”上传或管理。",
    "Your organization has disabled usage.": "你的组织已禁用用量。",
    "Registered nurse": "注册护士",
    "Payroll specialist": "薪资专员",
    "Psychiatrist": "精神科医生",
    "Therapist": "治疗师",
    "Vice president": "副总裁",
    "Sign in again": "重新登录",
    "Cancel": "取消",
    "Open": "打开",
    "Choose": "选择",
    "Leave": "离开",
    "Design": "设计",
    "Pro": "专业版",
    "Headers": "标头",
    "Header": "标头",
    "Invocations": "调用次数",
    "OAuth 2.0 JWT bearer": "OAuth 2.0 JWT bearer",
    "{pct} · resets {date}": "{pct} · {date} 重置",
    "{pct} · resets {when}": "{pct} · {when} 重置",
    "{product} grant": "{product} 授权额度",
    "{tier} plan": "{tier} 方案",
    "· in {dir}": "· 位于 {dir}",
    "<b>{category}</b> needs {count, plural, one {{label}} other {# fields}}": "<b>{category}</b> 需要 {count, plural, one {{label}} other {# 个字段}}",
}


FRAGMENT_TRANSLATIONS = {
    "absolute path": "绝对路径",
    "account": "账号",
    "accounts": "账号",
    "active subscription": "活跃订阅",
    "affected accounts": "受影响账号",
    "analytics": "分析",
    "API key": "API 密钥",
    "artifacts": "工件",
    "avatar": "头像",
    "billing": "账单",
    "browser": "浏览器",
    "browsers": "浏览器",
    "category": "类别",
    "chat": "聊天",
    "chats": "聊天",
    "Claude Code": "Claude Code",
    "code": "代码",
    "configuration": "配置",
    "console messages": "控制台消息",
    "conversation": "对话",
    "conversations": "对话",
    "connector": "连接器",
    "connectors": "连接器",
    "credential": "凭据",
    "credentials": "凭据",
    "dashboard": "仪表板",
    "device": "设备",
    "devices": "设备",
    "directory": "目录",
    "domain": "域名",
    "domains": "域名",
    "email": "邮箱",
    "emails": "邮箱",
    "file": "文件",
    "files": "文件",
    "folder": "文件夹",
    "GitHub App": "GitHub App",
    "group": "组",
    "groups": "组",
    "host": "主机",
    "hosts": "主机",
    "install status": "安装状态",
    "instructions": "指令",
    "key": "密钥",
    "keys": "密钥",
    "latest": "最新内容",
    "limit": "限制",
    "limits": "限制",
    "marketplace": "市场",
    "marketplaces": "市场",
    "memory": "记忆",
    "message": "消息",
    "messages": "消息",
    "model": "模型",
    "models": "模型",
    "network requests": "网络请求",
    "organization": "组织",
    "organization ID": "组织 ID",
    "output": "输出",
    "permissions": "权限",
    "Plan mode": "计划模式",
    "plugin": "插件",
    "plugins": "插件",
    "project": "项目",
    "Project ID": "项目 ID",
    "projects": "项目",
    "repository": "仓库",
    "repositories": "仓库",
    "relative path": "相对路径",
    "role": "角色",
    "routine": "例程",
    "routines": "例程",
    "rule": "规则",
    "rules": "规则",
    "run": "运行",
    "runs": "运行",
    "secret": "密钥",
    "server": "服务器",
    "session": "会话",
    "sessions": "会话",
    "settings": "设置",
    "skill": "技能",
    "skills": "技能",
    "source": "来源",
    "sources": "来源",
    "spend limit": "消费限制",
    "spend limits": "消费限制",
    "subscription": "订阅",
    "task": "任务",
    "tasks": "任务",
    "token": "令牌",
    "tokens": "令牌",
    "tool": "工具",
    "tools": "工具",
    "usage": "用量",
    "usage credits": "用量额度",
    "workspace": "工作区",
    "workspaces": "工作区",
    "workflow": "工作流",
    "workflows": "工作流",
}


PHRASE_REPLACEMENTS = [
    ("third-party returned an error", "第三方返回了错误"),
    ("Your connection works, but the provider rejected a test request.", "你的连接正常，但提供方拒绝了测试请求。"),
    ("Often a model-access or quota issue.", "这通常是模型访问权限或额度问题。"),
    ("Allowed outbound hosts", "允许的出站主机"),
    ("Allowed surfaces", "允许的界面"),
    ("General restrictions", "通用限制"),
    ("Offer 1M-context variant", "提供 1M 上下文变体"),
    ("Shown in the model picker", "显示在模型选择器中"),
    ("Leave blank to auto-format from the ID", "留空则根据 ID 自动格式化"),
    ("Cowork files", "Cowork 文件"),
    ("Dynamic workflows", "动态工作流"),
    ("High-contrast dark theme", "高对比度深色主题"),
    ("Discard unsaved changes", "放弃未保存的更改"),
    ("This configuration has changes that haven't been saved", "此配置有尚未保存的更改"),
    ("They will be lost", "这些更改将会丢失"),
    ("Apply Changes", "应用更改"),
    ("Discard Changes", "放弃更改"),
    ("Keep editing", "继续编辑"),
    ("Create API key", "创建 API 密钥"),
    ("Inference configuration", "推理配置"),
    ("Public Projects", "公共项目"),
    ("Secure VM features", "安全虚拟机功能"),
    ("Change location for Cowork files", "更改 Cowork 文件位置"),
    ("AWS config directory", "AWS 配置目录"),
    ("Couldn't save image", "无法保存图片"),
    ("What this URL is overriding", "此 URL 正在覆盖的内容"),
    ("The endpoint rejected the request", "端点拒绝了请求"),
    ("Check cert trust, IP allowlist, or auth headers", "请检查证书信任、IP 允许列表或认证标头"),
    ("Unsafe URL blocked", "已阻止不安全的 URL"),
    ("only http/https are allowed", "仅允许 http/https"),
    ("No usage data yet", "暂无用量数据"),
    ("plan usage appears once limits load", "限制加载后会显示方案用量"),
    ("session usage after Claude's first reply", "Claude 首次回复后会显示会话用量"),
    ("the Bedrock control-plane", "Bedrock 控制平面"),
    ("run a workflow", "运行工作流"),
    ("Read my eval metrics", "读取我的评估指标"),
    ("Move pane down", "下移窗格"),
    ("Log out of current session", "退出当前会话"),
    ("Select a role", "选择角色"),
    ("Select {email}", "选择 {email}"),
    ("Active Claude Code users in this period", "此期间活跃的 Claude Code 用户"),
    ("Allow your team to run multi-agent workflows in Claude Code", "允许你的团队在 Claude Code 中运行多智能体工作流"),
    ("Code with Claude on the go", "随时随地使用 Claude 编程"),
    ("run coding sessions in cloud environments", "在云环境中运行编码会话"),
    ("Career changer", "转行者"),
    ("Supply chain manager", "供应链经理"),
    ("Influencer", "影响者"),
    ("Gardener", "园艺师"),
    ("Receptionist", "接待员"),
    ("Team", "团队"),
    ("Leave", "离开"),
    ("Choose Claude data folder", "选择 Claude 数据文件夹"),
    ("The Chrome extension's session expired", "Chrome 扩展的会话已过期"),
    ("Open the Claude extension in Chrome and sign in again", "请在 Chrome 中打开 Claude 扩展并重新登录"),
    ("then retry", "然后重试"),
    ("Plan usage", "方案用量"),
    ("Usage image copied to clipboard", "用量图片已复制到剪贴板"),
    ("Wait for Claude", "等待 Claude"),
    ("Tap to open", "点按打开"),
    ("Weekly", "每周"),
    ("all models", "所有模型"),
    ("Version {version}", "版本 {version}"),
    ("Usage: {pct}", "用量：{pct}"),
    ("Sign back in to Claude in Chrome", "请在 Chrome 中重新登录 Claude"),
    ("5-hour limit", "5 小时限制"),
    ("Leave Design", "离开 Design"),
    ("Open link in another app", "在其他应用中打开链接"),
    ("Submit feedback and reinstall workspace", "提交反馈并重新安装工作区"),
    ("Your session has expired", "你的会话已过期"),
    ("Changes you made may not be saved", "你所做的更改可能不会保存"),
    ("Previous match", "上一个匹配项"),
    ("To exit full screen", "要退出全屏"),
    ("press {esc}", "请按 {esc}"),
    ("Quit anyway", "仍然退出"),
    ("Unlimited", "无限制"),
    ("Protected location", "受保护位置"),
    ("protected location", "受保护位置"),
    ("home/root directory", "主目录/根目录"),
    ("Choose a different folder", "请选择其他文件夹"),
    ("Thinking", "思考"),
    ("Always uses deep reasoning", "始终使用深度推理"),
    ("Complex, detailed work", "复杂、细致的工作"),
    ("Light, casual tasks", "轻量、日常任务"),
    ("Balanced for everyday work", "适合日常工作的均衡模式"),
    ("The hardest problems", "最困难的问题"),
    ("Takes longest", "耗时最长"),
    ("Quick replies to simple questions", "适合简单问题的快速回复"),
    ("Can think for more complex tasks", "可为更复杂的任务进行思考"),
    ("Higher effort means more thorough responses", "更高强度意味着回答更彻底"),
    ("takes longer", "耗时更长"),
    ("uses your limits faster", "更快消耗你的额度"),
    ("Default", "默认"),
    ("Extended", "扩展"),
    ("Medium", "中"),
    ("High", "高"),
    ("Low", "低"),
    ("Extra", "超高"),
    ("Faster", "更快"),
    ("Smarter", "更智能"),
    ("Off", "关"),
    ("Max", "最高"),
    ("Empty", "空"),
    ("Recheck", "重新检查"),
    ("Cancel", "取消"),
    ("Open", "打开"),
    ("Choose", "选择"),
    ("Design", "设计"),
    ("Headers", "标头"),
    ("Header", "标头"),
    ("role", "角色"),
    ("model", "模型"),
    ("workflow", "工作流"),
    ("workflows", "工作流"),
    ("architecture tradeoffs", "架构权衡"),
    ("Evaluate", "评估"),
    ("Build", "构建"),
    ("Write", "撰写"),
    ("Create", "创建"),
    ("Repurpose", "改写复用"),
    ("blog post", "博客文章"),
    ("across channels", "跨渠道"),
]


KNOWN_OK_EXACT = {
    "Claude",
    "Claude Code",
    "MCP",
    "GitHub",
    "Slack",
    "AWS",
    "API",
    "SDK",
    "URL",
    "SSH",
    "JSON",
    "OpenTelemetry",
    "X-Header-Name",
}


ASCII_WORD_RE = re.compile(r"[A-Za-z]{3,}")
PLACEHOLDER_ONLY_RE = re.compile(r"^[\s\d{}#%$.,:+\-_/()\\[\]<>|~]+$")
PLACEHOLDER_PREFIXES = ("待翻译：", "待补充翻译：")
QUOTED_JS_STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

ALLOWED_ENGLISH_WORDS = {
    "agent",
    "anthropic",
    "api",
    "aws",
    "azure",
    "baa",
    "bedrock",
    "chrome",
    "claude",
    "cli",
    "code",
    "cowork",
    "cpa",
    "fps",
    "github",
    "http",
    "https",
    "ide",
    "id",
    "json",
    "jwt",
    "linux",
    "macos",
    "mcp",
    "mdm",
    "oauth",
    "oidc",
    "opentelemetry",
    "pip",
    "psc",
    "scim",
    "sdk",
    "ssh",
    "sse",
    "ui",
    "url",
    "uri",
    "vertex",
    "vpc",
    "windows",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_placeholder_translation(value: object) -> bool:
    return isinstance(value, str) and value.startswith(PLACEHOLDER_PREFIXES)


def placeholder_source(value: str) -> str:
    for prefix in PLACEHOLDER_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def decode_js_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value


def quoted_values(pattern: str) -> list[str]:
    return [decode_js_string(match.group(1)) for match in QUOTED_JS_STRING_RE.finditer(pattern)]


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def changed_quoted_translation(old: str, new: str) -> tuple[str, str] | None:
    old_values = quoted_values(old)
    new_values = quoted_values(new)
    if not old_values or len(old_values) != len(new_values):
        return None

    changed = [(source, target) for source, target in zip(old_values, new_values) if source != target]
    if len(changed) != 1:
        return None

    source, target = changed[0]
    if source and target and has_cjk(target):
        return source, target
    return None


def quoted_whole_translation(old: str, new: str) -> tuple[str, str] | None:
    if old.startswith('"') and old.endswith('"') and new.startswith('"') and new.endswith('"'):
        source = decode_js_string(old[1:-1])
        target = decode_js_string(new[1:-1])
        if source != target and has_cjk(target):
            return source, target
    return None


def patch_translation_memory() -> dict[str, str]:
    memory: dict[str, str] = {}
    try:
        import patch_chunks_zh_cn
    except (ImportError, KeyError, OSError):
        return memory

    for replacements in patch_chunks_zh_cn.PATCHES.values():
        for old, new in replacements:
            translated = quoted_whole_translation(old, new) or changed_quoted_translation(old, new)
            if translated:
                memory.setdefault(translated[0], translated[1])
    return memory


def translation_memory(installed_resources: Path) -> dict[str, str]:
    memory: dict[str, str] = patch_translation_memory()
    for spec in RESOURCE_PAIRS.values():
        local_path = spec["local"]
        en_path = installed_resources.parent / spec["installed_en"]
        if not local_path.exists() or not en_path.exists():
            continue
        local_data = load_json(local_path)
        en_data = load_json(en_path)
        for key, source in en_data.items():
            translated = local_data.get(key)
            if (
                isinstance(source, str)
                and isinstance(translated, str)
                and translated
                and source != translated
                and not is_placeholder_translation(translated)
            ):
                memory.setdefault(source, translated)
    return memory


def looks_technical_or_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped in KNOWN_OK_EXACT:
        return True
    if stripped.startswith(("http://", "https://")):
        return True
    if re.fullmatch(r"\{[^{}]+\}", stripped):
        return True
    if PLACEHOLDER_ONLY_RE.match(stripped):
        return True
    if re.fullmatch(r"[A-Za-z]:[\\/].+", stripped):
        return True
    if stripped.startswith(("~/", "./", "../", "/", "[")):
        return True
    if re.fullmatch(r"\{[^{}]+\}\s*(ms|FPS|tokens?)", stripped, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"[~×x→·\s{}#%$.,:+\-_/()\\[\]<>|A-Z0-9]+", stripped):
        return True
    if re.fullmatch(r"[A-Z0-9_./:+-]{2,}", stripped):
        return True
    return False


def untranslated_words(value: str) -> list[str]:
    words = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9.+-]*", value):
        normalized = word.strip(".+-").lower()
        if len(normalized) < 3:
            continue
        if normalized in ALLOWED_ENGLISH_WORDS:
            continue
        words.append(word)
    return words


def translation_looks_complete(value: str) -> bool:
    if looks_technical_or_placeholder(value):
        return True
    if not has_cjk(value):
        return False
    return len(untranslated_words(value)) <= 1


def translate_fragment(value: str) -> str:
    translated = value.strip()
    if translated in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[translated]

    for source, target in sorted(FRAGMENT_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(source)}\b", target, translated, flags=re.IGNORECASE)
    return translated


def complete_fragment(value: str) -> str | None:
    translated = translate_fragment(value)
    if translated != value and translation_looks_complete(translated):
        return translated
    return None


def pattern_translation(value: str) -> str | None:
    simple_patterns: list[tuple[str, str]] = [
        (r"^Add (.+)$", "添加{part}"),
        (r"^Set up (.+)$", "设置{part}"),
        (r"^Manage (.+)$", "管理{part}"),
        (r"^Request (.+)$", "请求{part}"),
        (r"^Authorize (.+)$", "授权{part}"),
        (r"^Enable (.+)$", "启用{part}"),
        (r"^Disable (.+)$", "禁用{part}"),
        (r"^Use (.+)$", "使用{part}"),
        (r"^Select (.+)$", "选择{part}"),
        (r"^Filter (.+)$", "筛选{part}"),
        (r"^Collapse (.+)$", "折叠{part}"),
        (r"^Expand (.+)$", "展开{part}"),
        (r"^Copy (.+)$", "复制{part}"),
        (r"^View (.+)$", "查看{part}"),
        (r"^Open (.+)$", "打开{part}"),
        (r"^Download as (.+)$", "下载为 {part}"),
        (r"^Remove (.+)$", "移除{part}"),
        (r"^Refresh (.+)$", "刷新{part}"),
        (r"^Hide (.+)$", "隐藏{part}"),
        (r"^Show (.+)$", "显示{part}"),
        (r"^Save (.+)$", "保存{part}"),
        (r"^Run (.+)$", "运行{part}"),
        (r"^Start (.+)$", "开始{part}"),
        (r"^Back to (.+)$", "返回{part}"),
        (r"^Next: (.+)$", "下一步：{part}"),
        (r"^No (.+)$", "没有{part}"),
        (r"^Invalid (.+)$", "无效{part}"),
        (r"^Loading (.+)…$", "正在加载{part}…"),
        (r"^Reading (.+)$", "正在读取{part}"),
        (r"^Reading (.+)…$", "正在读取{part}…"),
        (r"^Checking (.+)…$", "正在检查{part}…"),
        (r"^Searching(.+)?…$", "正在搜索…"),
        (r"^Scanning(.+)?…$", "正在扫描…"),
        (r"^Editing (.+)…$", "正在编辑{part}…"),
        (r"^Writing (.+)…$", "正在写入{part}…"),
        (r"^Using (.+)…$", "正在使用{part}…"),
        (r"^Starting (.+)…$", "正在启动{part}…"),
    ]
    for pattern, template in simple_patterns:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if not match:
            continue
        part = ""
        if match.lastindex:
            raw_part = match.group(1) or ""
            part = complete_fragment(raw_part) or translate_fragment(raw_part)
            if untranslated_words(part) and not looks_technical_or_placeholder(part):
                continue
        translated = template.format(part=part)
        if translation_looks_complete(translated):
            return translated

    copied = re.match(r"^(.+) copied to clipboard\.$", value, flags=re.IGNORECASE)
    if copied:
        part = complete_fragment(copied.group(1)) or translate_fragment(copied.group(1))
        translated = f"{part}已复制到剪贴板。"
        if translation_looks_complete(translated):
            return translated

    match = re.match(r"^\{(.+)\} configuration$", value, flags=re.IGNORECASE)
    if match:
        return f"{{{match.group(1)}}} 配置"

    for pattern, template in [
        (r"^(.+) updated$", "{part}已更新"),
        (r"^(.+) installed$", "{part}已安装"),
        (r"^(.+) saved\.$", "{part}已保存。"),
        (r"^(.+) deleted$", "{part}已删除"),
        (r"^Downloaded (.+)$", "已下载{part}"),
        (r"^Copied (.+)$", "已复制{part}"),
        (r"^Failed to save (.+)\. Check your inputs and try again\.$", "保存{part}失败。请检查输入后重试。"),
        (r"^Failed to remove (.+)\.$", "移除{part}失败。"),
        (r"^Failed to update (.+)\. You can try again\.$", "更新{part}失败。你可以重试。"),
        (r"^Couldn’t load (.+)\. Try again\.$", "无法加载{part}。请重试。"),
        (r"^Can't reach (.+) — check your connection\.$", "无法连接{part}；请检查连接。"),
    ]:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if not match:
            continue
        part = complete_fragment(match.group(1)) or translate_fragment(match.group(1))
        translated = template.format(part=part)
        if translation_looks_complete(translated):
            return translated

    return None


def apply_phrase_rules(value: str) -> str:
    translated = value
    for source, target in sorted(PHRASE_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)
    translated = translated.replace(" can't ", " 不能 ")
    translated = translated.replace(" can’t ", " 不能 ")
    translated = translated.replace("Couldn't", "无法")
    translated = translated.replace("couldn't", "无法")
    translated = translated.replace("Don't", "不要")
    translated = translated.replace("don't", "不要")
    translated = translated.replace("isn't", "不是")
    translated = translated.replace("isn’t", "不是")
    translated = translated.replace("—", "—")
    translated = re.sub(r"\s+([，。！？；：、）])", r"\1", translated)
    translated = re.sub(r"([（])\s+", r"\1", translated)
    translated = re.sub(r"\s+", " ", translated)
    return translated.strip()


def fallback_translation(value: str, mark_untranslated: bool = False) -> str:
    if looks_technical_or_placeholder(value):
        return value
    patterned = pattern_translation(value)
    if patterned:
        return patterned
    translated = apply_phrase_rules(value)
    if translated != value and translation_looks_complete(translated):
        return translated
    if not mark_untranslated:
        return value
    if len(value) <= 36 and ASCII_WORD_RE.search(value):
        return f"待翻译：{value}"
    return f"待补充翻译：{value}"


def translate_value(value: object, memory: dict[str, str], mark_untranslated: bool = False) -> object:
    if not isinstance(value, str):
        return value
    if value in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[value]
    if value in memory:
        return memory[value]
    return fallback_translation(value, mark_untranslated=mark_untranslated)


def sync_resources(app_dir: Path, dry_run: bool = False, mark_untranslated: bool = False) -> dict[str, dict[str, int]]:
    installed_resources = app_dir / "resources"
    memory = translation_memory(installed_resources)
    summary: dict[str, dict[str, int]] = {}

    for name, spec in RESOURCE_PAIRS.items():
        local_path = spec["local"]
        installed_en = installed_resources.parent / spec["installed_en"]
        local_data = load_json(local_path)
        en_data = load_json(installed_en)
        added = 0
        reused = 0
        updated = 0
        untranslated = 0
        for key, source in en_data.items():
            current = local_data.get(key)
            if key in local_data and not is_placeholder_translation(current) and current != source:
                continue
            translated = translate_value(source, memory, mark_untranslated=mark_untranslated)
            if is_placeholder_translation(current) and is_placeholder_translation(translated):
                translated = translate_value(placeholder_source(current), memory, mark_untranslated=mark_untranslated)
            if key in local_data and current == translated:
                continue
            if isinstance(source, str) and isinstance(translated, str) and translated == memory.get(source):
                reused += 1
            if isinstance(source, str) and translated == source and not looks_technical_or_placeholder(source):
                untranslated += 1
            if key in local_data:
                updated += 1
            else:
                added += 1
            local_data[key] = translated

        if not dry_run and (added or updated):
            write_json(local_path, local_data)
        summary[name] = {
            "en": len(en_data),
            "zh": len(local_data),
            "added": added,
            "updated": updated,
            "reused": reused,
            "untranslated": untranslated,
            "missing_after": len(set(en_data) - set(local_data)),
            "extra": len(set(local_data) - set(en_data)),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync missing zh-CN resource keys from installed Claude")
    parser.add_argument("--app-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mark-untranslated", action="store_true", help="write 待翻译 markers for review instead of English fallback")
    args = parser.parse_args()

    app_dir = Path(args.app_dir) if args.app_dir else patch_windowsapps_json_only.find_claude_package()
    if not app_dir:
        raise SystemExit("Claude app directory not found; pass --app-dir")

    summary = sync_resources(app_dir, dry_run=args.dry_run, mark_untranslated=args.mark_untranslated)
    print(f"Claude app: {app_dir}")
    for name, info in summary.items():
        print(
            f"{name}: en={info['en']} zh={info['zh']} "
            f"added={info['added']} updated={info['updated']} reused={info['reused']} untranslated={info['untranslated']} "
            f"missing_after={info['missing_after']} extra={info['extra']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
