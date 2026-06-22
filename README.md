# Claude Desktop Windows 中文补丁（zh-CN）

这是一个给 Windows 版 Claude Desktop 增加中文界面的本地补丁项目。

旧版说明已保留为 `README.old.md`。

## 重要说明

- 本项目不是 Anthropic 官方项目。
- 当前脚本会直接修改已安装 Claude app 目录里的资源文件和前端 JS chunk。
- 默认自动检测商店版 `C:\Program Files\WindowsApps` 和网页登录页安装版 `%LOCALAPPDATA%\AnthropicClaude`。
- 如果自动检测失败，可以在交互式脚本里手动指定 Claude 的 `app` 目录或安装根目录。
- 每次 Claude Desktop 更新后，通常都需要重新运行安装脚本。

## 功能概览

- 中文资源：写入桌面壳层、前端主界面和 Statsig 的 `zh-CN` 资源。
- 硬编码文案：修补 JS chunk 中没有进入 JSON 资源的设置页、第三方推理、任务、项目和会话文案。
- 字体面板：右下角提供中文字体切换、字体名输入和本地字体导入。
- 可见文本修复：运行时处理少量仍由 DOM 直接显示的英文文本。
- 会话增强：左侧历史会话悬停显示移动、导出、删除，当前对话显示右侧 Timeline 和底部居中宽度按钮。
- CDP 诊断：可通过 DevTools/CDP 临时注入运行时，并输出行识别、按钮数量和健康状态。

## 当前验证环境

- Claude Desktop：`1.14271.0.0` 已重新同步资源；支持 WindowsApps 包和 `%LOCALAPPDATA%\AnthropicClaude` 安装目录
- Windows：Windows 版 Claude Desktop
- Python：Python 3.12 已验证；理论上 Python 3.10+ 均可使用
- PowerShell：Windows PowerShell，安装和恢复需要管理员权限
- 回归测试：`python -B -m pytest tools\test_patch_behaviors.py -q -p no:cacheprovider`，当前 `70 passed`

Claude Desktop 更新后仍可尝试安装；资源目录或 JS chunk 结构变化时，需要更新补丁规则。

## 安装 Python 3

本项目的安装脚本会调用 Python。新机器必须先安装 Python 3。

推荐方式：

1. 打开 <https://www.python.org/downloads/windows/>
2. 下载最新版 Python 3 安装器。
3. 安装时勾选 `Add python.exe to PATH`。
4. 安装完成后重新打开 PowerShell。

检查 Python 是否可用：

```powershell
python --version
```

如果 `python` 不可用，也可以检查：

```powershell
py --version
```

只要其中一个命令能输出 Python 3 版本，脚本就可以继续运行。

## 文件结构

- `resources/desktop-zh-CN.json`：桌面壳层中文资源。
- `resources/frontend-zh-CN.json`：前端主界面中文资源。
- `resources/statsig-zh-CN.json`：Statsig 相关中文资源。
- `patch_windowsapps_json_only.py`：写入 JSON 资源、修补语言白名单、设置 `locale=zh-CN`。
- `patch_chunks_zh_cn.py`：修补 JS chunk 中的硬编码文案，并注入中文字体和可见文本修复运行时。
- `tools/cdp_session_delete_launcher.py`：通过 DevTools/CDP 临时注入会话增强运行时。
- `claude-cdp-session-delete.ps1`：启动 Claude 并执行会话增强 CDP 注入。
- `restore_claude_zh_cn_windowsapps.py`：从备份恢复官方文件并移除中文配置。
- `claude-zh-cn.ps1`：交互式安装、卸载、状态检查入口。
- `install-windowsapps-json-only.ps1`：非交互安装入口。
- `restore-windowsapps-zh-cn.ps1`：非交互恢复入口。
- `I18N-COVERAGE-REPORT.md`：最近一次 i18n 覆盖扫描报告。
- `tools/sync_i18n_from_installed.py`：从当前已安装 Claude 的 `en-US.json` 同步缺失 zh-CN key，并升级已有英文兜底。
- `tools/validate_resources.py`：校验资源 JSON。
- `tools/check_i18n_coverage.py`：扫描疑似未汉化资源。
- `tools/session_runtime_dom_test.mjs`：会话增强运行时 DOM 场景测试，覆盖按钮挂载范围和导出内容。
- `tools/test_patch_behaviors.py`：回归测试。

## 安装

以管理员身份打开 PowerShell，在项目目录执行：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1
```

交互式菜单说明：

- `[1] 安装 / 重新安装 / 更新中文补丁`：写入 JSON 资源、chunk 文案补丁、字体运行时、可见文本修复和会话增强，并尝试一次 CDP 追加注入。
- `[2] 卸载中文补丁（恢复英文）`：从备份恢复官方文件，移除中文资源、locale、字体镜像和 chunk 注入。
- `[3] 手动指定 Claude app 目录`：自动检测失败或需要在多个安装版本间切换时使用。
- `[4] 刷新状态`：重新显示当前安装状态。
- `[5] 管理 / 诊断面板`：集中查看 Claude 版本、安装路径、chunk 注入标记、后台删除桥进程和登录任务状态。
- `[0] 退出`：关闭菜单。

也可以直接运行非交互安装：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\install-windowsapps-json-only.ps1
```

交互式 `[1]` 会先关闭 Claude 进程，再写入资源、chunk 补丁和会话增强运行时，然后尝试通过 CDP 做一次临时追加注入。非交互安装脚本写入资源和 chunk 补丁，完成后重新打开 Claude Desktop 即可生效。

## 管理 / 诊断面板

参考 `milisp/plux` 的统一工作台思路，本项目先把常用诊断和后台任务控制收进 PowerShell 管理面板，避免每次手动拼命令。

在主菜单选择 `[5] 管理 / 诊断面板` 后可以看到：

- Claude 版本、来源、安装目录和资源目录。
- 中文资源、语言白名单、locale、备份状态。
- 当前 `index-*.js` chunk 数量、最新 chunk 路径、字体注入标记、会话增强标记和 `zh-CN` 白名单标记。
- 本地删除桥后台进程数量。
- `ClaudeZhCnLocalDeleteBridge` 登录任务是否已安装。

管理面板子菜单提供：

- `[2] 启动本地删除桥（后台）`：后台启动 `-LocalDeleteBridge -Background`，用于本地 `local_<uuid>` 会话隔离删除。
- `[3] 安装登录任务：后台桥`：注册 Windows 登录任务，登录后自动启动后台桥。
- `[4] 卸载登录任务：后台桥`：移除该登录任务。
- `[5] 运行 CDP 行诊断`：输出会话行识别、按钮挂载和 CDP target 信息。

## 会话增强按钮

会话列表悬停增强现在随 `[1] 安装中文补丁` 写入当前 Claude app 的入口 `index-*.js` chunk。当前 Claude WindowsApps build 会拦截未授权 CDP 调试启动，所以稳定路径采用 chunk 注入；CDP launcher 保留为可选诊断和未来兼容路径。

悬停左侧会话记录区时会显示：

- 移动：弹出“普通对话 + 项目列表”，调用 Claude 官方 `chat_conversations/move_many` 接口；组织或项目列表探测失败时回退到 Claude 自带移动/项目菜单，并记录诊断状态 `__CLAUDE_ZH_CN_SESSION_MOVE_STATE__`。
- 导出：读取当前页面 DOM，尽量同时提取用户消息和 Claude 回复，生成带时间戳的 `.md` 文件。
- 删除：显示确认框；普通会话优先调用 Claude 自带删除菜单，本地 `local_<uuid>` 会话可通过 `-LocalDeleteBridge` 移入隔离目录。

按钮只会挂到识别为历史会话的行上，会排除导航按钮、展开/收起、查看全部、项目、文件、Gateway、设置页和第三方供应商配置区域。行识别状态会写入 `__CLAUDE_ZH_CN_SESSION_DELETE_SCAN_STATE__`，包含候选数量、按钮数量、最近错误和扫描耗时。

当前会话页面还会显示右侧 Timeline。Timeline 默认以小点展示，鼠标悬停或键盘聚焦时展开为文本节点；节点来自用户提问，点击后跳到对应消息。底部会出现“居中关 / 居中 980”按钮，用于切换主对话区最大宽度；右键或双击该按钮可以自定义宽度，范围为 `640` 到 `1600`。

第三方供应商设置页会隐藏字体按钮和居中按钮，避免挡住设置页右下角控件。

单独调试 CDP 时可以运行：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-cdp-session-delete.ps1
```

脚本会先关闭已有 Claude 进程，再用 `--remote-debugging-port=9229` 启动 Claude，连接 CDP 后把会话增强运行时注入当前页面，并注册为后续页面加载脚本。若当前 Claude build 拦截 CDP target，使用 `[1] 安装中文补丁` 的 chunk 注入路径。

如果 Claude 已经带同一个调试端口启动，可以只连接注入：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-cdp-session-delete.ps1 -NoLaunch
```

可选参数：

- `-Port 9229`：指定 DevTools/CDP 端口。
- `-AppDir "C:\Program Files\WindowsApps\Claude_...\app"`：手动指定商店版 Claude app 目录。
- `-AppDir "$env:LOCALAPPDATA\AnthropicClaude"`：手动指定网页登录页安装版 Claude 根目录；脚本会自动解析其中的 `app` / `app-*` 目录。
- `-TimeoutSeconds 20`：等待 CDP 目标出现的秒数。
- `-DiagnoseRows`：打印当前识别到的会话行和候选行，适合排查某一行为什么没有显示移动、导出、删除。
- `-ScanPorts`：扫描附近 CDP 端口并列出可连接目标。
- `-LocalDeleteBridge`：保持 CDP 连接常驻，处理页面发出的 `local_<uuid>` 本地会话删除请求。它会把匹配的 `local_<uuid>.json` 和同名目录移动到 `%LOCALAPPDATA%\Claude-zh-CN-session-delete-quarantine`。
- `-Background`：配合 `-LocalDeleteBridge` 使用，用隐藏 PowerShell 后台启动本地删除桥。

本地会话删除推荐后台启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-cdp-session-delete.ps1 -LocalDeleteBridge -Background
```

调试时可以前台启动，方便查看日志：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-cdp-session-delete.ps1 -LocalDeleteBridge
```

诊断输出会包含运行时健康状态：

- `sessionDeletePatch`：会话增强运行时是否生效。
- `fontPatch`：字体运行时是否生效。
- `visibleTextFixPatch`：可见文本修复运行时是否生效。

## 插件目录空白

“目录 > 插件”是组织插件目录。截图里的“你的组织尚未提供插件”表示当前组织没有下发可浏览的组织插件，这不是中文补丁导致的列表加载失败。

要使用本地或个人插件，请进入 Claude 的“设置 > 自定义 > 个人插件”，再使用“上传本地插件”或“添加插件”。组织插件需要组织管理员在 Claude 管理端添加插件源或市场后才会出现在“目录 > 插件”里。

## 新机器使用

在新机器上使用当前项目时，只需要准备三件事：

- 已安装 Windows 版 Claude Desktop。
- 已安装 Python 3，并且 `python` 或 `py` 命令可用。
- 已克隆或下载本仓库。

推荐步骤：

```powershell
git clone https://github.com/Jyy1529/claude-desktop_win-zh_cn.git
cd claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1
```

如果新机器同时有两个 Claude 安装源，建议在菜单 `[3] 手动指定 Claude app 目录` 中明确选择实际使用的版本。脚本支持输入以下两类路径：

```text
C:\Program Files\WindowsApps\Claude_...\app
C:\Users\<用户名>\AppData\Local\AnthropicClaude
```

最终解析出的 Claude app 目录下必须存在：

```text
app\resources\en-US.json
```

当前项目不依赖旧机器上的缓存或手工改动。安装时会重新写入中文资源、补语言白名单、注入 chunk 文案补丁和运行时可见文本修复。

## 卸载与恢复

以管理员身份运行：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\restore-windowsapps-zh-cn.ps1
```

或者使用交互式菜单：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1
```

恢复脚本会尽量从备份目录恢复原文件，并移除 `locale=zh-CN` 和中文字体配置镜像。

备份目录位于：

```text
%LOCALAPPDATA%\Claude-zh-CN-official-backup
```

## 安装会修改什么

1. 复制中文 JSON 到 Claude app 资源目录。
2. 在前端语言白名单中加入 `zh-CN`。
3. 写入 `%APPDATA%\Claude-3p\config.json` 的 `locale=zh-CN`。
4. 对 `ion-dist\assets` 下发现的 JS chunk 做少量精确字符串替换。
5. 注入中文字体自定义运行时。
6. 注入可见文本修复运行时，用于处理部分没有进入 i18n JSON 的硬编码英文。

会话增强按钮由安装流程写入入口 chunk。卸载流程会从备份恢复 chunk，删除、导出、移动、Timeline 和居中宽度运行时会随之移除。

## 硬编码文案与图标修复

Claude Desktop 的部分界面文案不在 JSON 资源中，而是硬编码在前端 JS chunk 里。例如：

- 设置页部分字体、主题、任务、环境、排序项。
- 第三方推理提供方说明。
- `Live artifacts`、`Artifacts` 相关可见文本。
- `Create dynamic artifacts that stay up-to-date using live data from your connectors.`

这些文案通过 `patch_chunks_zh_cn.py` 处理。

注意：不要盲目把 JS 内部的 `label`、图标名、枚举值全部翻译。之前 `Live artifacts` 左侧图标丢失，就是因为内部导航标识被翻译后破坏了图标映射。当前策略是：

- 内部标识保留英文，例如 `label:"Live artifacts"`。
- DOM 可见文本在运行时替换成中文，例如 `Live artifacts` 显示为 `实时工件`。
- 旧补丁残留的 `label:"实时工件"`、`label:"实时 Artifacts"` 会在安装时还原为 `label:"Live artifacts"`。

## 字体设置

安装后会注入中文字体运行时。

默认字体策略：

- `Microsoft YaHei UI`
- `Microsoft YaHei`
- `Segoe UI`
- `sans-serif`

运行时会在界面右下角显示“字体”按钮，可切换推荐字体、输入本机字体名，或导入 `.ttf` / `.otf` 字体文件。第三方供应商设置页会自动隐藏该按钮。字体配置保存在浏览器侧 `localStorage` 的 `claudeZhCnFont` 中。

## 第三方推理

如果你把 Claude Desktop 接到第三方推理网关，例如本地代理或 `cc-switch`，推荐走 Claude Desktop 官方第三方推理入口，而不是直接改内部文件。

常见相关配置字段：

- `inferenceProvider`
- `inferenceGatewayBaseUrl`
- `inferenceGatewayApiKey`
- `inferenceModels`
- `isClaudeCodeForDesktopEnabled`

如果界面提示 `Configured model not available`，通常表示网关没有提供对应模型，或模型访问受限。当前补丁会把设置页里的 `Gateway` 可见文案尽量显示为“第三方”，同时保留内部配置字段名。

## 维护流程

Claude Desktop 更新后，先同步当前安装版新增的 i18n key：

```powershell
python -B tools\sync_i18n_from_installed.py --dry-run
python -B tools\sync_i18n_from_installed.py
```

默认会保留已有中文翻译，复用 `patch_chunks_zh_cn.py` 的硬编码翻译表，并把没有确定翻译的新文案保留为英文兜底。需要审校标记时可以加：

```powershell
python -B tools\sync_i18n_from_installed.py --mark-untranslated
```

修改资源或补丁后，建议运行：

```powershell
python tools\validate_resources.py
python tools\check_i18n_coverage.py
node tools\session_runtime_dom_test.mjs
python -B -m pytest tools\test_patch_behaviors.py -q -p no:cacheprovider
```

`tools/session_runtime_dom_test.mjs` 会验证历史会话行能挂上移动、导出、删除三个按钮，也会确认项目、文件、进度、上下文等非历史区域不会挂按钮，并检查 Markdown 导出同时包含用户和 Claude 回复。

当前 `I18N-COVERAGE-REPORT.md` 里保留的一些可疑项通常是占位符、金额、快捷键、平台名或技术名，例如：

- `{size} MB`
- `{percent}%`
- `Ctrl+Enter`
- `SSH · {sshHost}`
- `Windows (x64)`

这些不一定需要翻译。

## 排查

如果安装后仍有英文：

1. 确认已使用管理员 PowerShell 重新安装。
2. 确认 Claude 已完全退出并重新打开。
3. 如果是 JSON 资源漏翻，在 `resources/frontend-zh-CN.json` 中补 key。
4. 如果是 JS chunk 硬编码英文，在 `patch_chunks_zh_cn.py` 中补精确替换或可见文本运行时替换。
5. 如果某个图标消失，优先怀疑内部 `label`、枚举或图标名被翻译，应该保留内部英文标识，只翻译可见文本。

如果左侧会话没有出现移动、导出、删除：

1. 重新运行 `[1] 安装中文补丁`，关闭 Claude 后从开始菜单重新打开。
2. 打开 CDP 诊断：`powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-cdp-session-delete.ps1 -DiagnoseRows -ScanPorts`。
3. 查看输出里的 `attached`、`exportButtonCount`、`moveButtonCount`、`lastError`。
4. 某一行显示在候选列表里但没有挂按钮时，优先检查它是否被识别成项目、Gateway、设置项、查看全部、展开/收起或其它导航区域。

如果导出的 Markdown 缺少 Claude 回复：

1. 确认当前对话页面已经完整加载，长回复滚动到可见区域后再导出。
2. 导出逻辑来自页面 DOM，Claude 虚拟列表未挂载的旧消息可能无法一次性读取。
3. 当前回归测试覆盖了用户消息和 Claude 回复同时导出的基础场景。

如果 CDP 注入失败：

1. 直接使用 `[1] 安装中文补丁` 的 chunk 注入路径。
2. 使用 `-ScanPorts` 查看可连接的 DevTools 目标。
3. Claude 已经以调试端口启动时，加 `-NoLaunch` 只连接现有端口。

如果自动检测不到 Claude 安装目录，可以在 `claude-zh-cn.ps1` 中选择“手动指定 Claude app 目录”。目录下应存在：

```text
app\resources\en-US.json
```

## 风险与免责声明

- 本项目会修改本机已安装的 Claude Desktop 资源文件。
- 使用前请确认你接受本地补丁、备份恢复和应用更新带来的风险。
- 不建议在公司受管设备上绕过组织策略使用。
- Claude Desktop 更新后，补丁可能失效或需要重新适配。

## 致谢

感谢 [LINUX DO](https://linux.do/) 社区的支持与分享，也感谢 `javaht/claude-desktop-zh-cn` 提供的早期参考。
