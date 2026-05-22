# Claude Desktop Windows 中文补丁（zh-CN）

这是一个给 Windows 版 Claude Desktop 增加中文界面的本地补丁项目。

旧版说明已保留为 `README.old.md`。

## 重要说明

- 本项目不是 Anthropic 官方项目。
- 当前脚本会直接修改已安装 Claude app 目录里的资源文件和前端 JS chunk。
- 默认自动检测 `C:\Program Files\WindowsApps` 下的 Claude 包。
- 如果自动检测失败，可以在交互式脚本里手动指定 Claude 的 `app` 目录。
- 每次 Claude Desktop 更新后，通常都需要重新运行安装脚本。

## 文件结构

- `resources/desktop-zh-CN.json`：桌面壳层中文资源。
- `resources/frontend-zh-CN.json`：前端主界面中文资源。
- `resources/statsig-zh-CN.json`：Statsig 相关中文资源。
- `patch_windowsapps_json_only.py`：写入 JSON 资源、修补语言白名单、设置 `locale=zh-CN`。
- `patch_chunks_zh_cn.py`：修补 JS chunk 中的硬编码文案，并注入中文字体和可见文本修复运行时。
- `restore_claude_zh_cn_windowsapps.py`：从备份恢复官方文件并移除中文配置。
- `claude-zh-cn.ps1`：交互式安装、卸载、状态检查入口。
- `install-windowsapps-json-only.ps1`：非交互安装入口。
- `restore-windowsapps-zh-cn.ps1`：非交互恢复入口。
- `tools/validate_resources.py`：校验资源 JSON。
- `tools/check_i18n_coverage.py`：扫描疑似未汉化资源。
- `tools/test_patch_behaviors.py`：回归测试。

## 安装

以管理员身份打开 PowerShell，在项目目录执行：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1
```

交互式菜单里选择安装或重新安装中文补丁。

也可以直接运行非交互安装：

```powershell
cd C:\Users\JASOY\Desktop\claude-desktop_win-zh_cn
powershell -NoProfile -ExecutionPolicy Bypass -File .\install-windowsapps-json-only.ps1
```

安装脚本会先关闭 Claude 进程，再写入资源和补丁。安装完成后需要重新打开 Claude Desktop。

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

运行时会在界面右下角显示“字体”按钮，可切换推荐字体、输入本机字体名，或导入 `.ttf` / `.otf` 字体文件。

## 第三方推理

如果你把 Claude Desktop 接到第三方推理网关，例如本地代理或 `cc-switch`，推荐走 Claude Desktop 官方第三方推理入口，而不是直接改内部文件。

常见相关配置字段：

- `inferenceProvider`
- `inferenceGatewayBaseUrl`
- `inferenceGatewayApiKey`
- `inferenceModels`
- `isClaudeCodeForDesktopEnabled`

如果界面提示 `Configured model not available`，通常表示网关没有提供对应模型，或模型访问受限。

## 维护流程

修改资源或补丁后，建议运行：

```powershell
python tools\validate_resources.py
python tools\check_i18n_coverage.py
python -m pytest tools\test_patch_behaviors.py -q
```

当前已知覆盖检查里保留的一些可疑项通常是占位符、金额、快捷键、平台名或技术名，例如：

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

感谢 LINUX DO 社区的支持与分享，也感谢 `javaht/claude-desktop-zh-cn` 提供的早期参考。
