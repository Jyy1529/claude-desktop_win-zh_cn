# Claude Desktop 中文资源与 Windows 补丁（zh-CN）

这是一个面向 Windows 版 Claude Desktop 的中文资源维护项目。

## 当前主线

- `resources/desktop-zh-CN.json`
- `resources/frontend-zh-CN.json`
- `resources/statsig-zh-CN.json`
- `patch_windowsapps_json_only.py`
- `patch_chunks_zh_cn.py`
- `restore_claude_zh_cn_windowsapps.py`
- `claude-zh-cn.ps1`
- `install-windowsapps-json-only.ps1`
- `restore-windowsapps-zh-cn.ps1`
- `tools/validate_resources.py`
- `tools/check_i18n_coverage.py`
- `tools/test_patch_behaviors.py`

## 快速开始

以管理员身份运行 PowerShell，然后在项目目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1
```

脚本会自动检测 Claude 安装路径，或者在检测失败时让你手动指定 `app` 目录。

## 安装后会做什么

1. 复制官方包里的 `app` 目录到本地固定目录。
2. 写入中文桌面层资源 `resources\zh-CN.json`。
3. 合并前端 `ion-dist\i18n\zh-CN.json`。
4. 写入 `statsig\zh-CN.json`。
5. 修补前端语言白名单，加入 `zh-CN`。
6. 设置 `locale=zh-CN`。
7. 对少量 JS chunk 做字符串替换，并注入中文字体自定义运行时。

安装结果会放到：

```text
C:\Users\<your-user>\AppData\Local\Claude-zh-CN
```

其中包含：

- `app\`：补丁后的可运行副本
- `claude-zh-cn.ps1`：交互式安装 / 卸载入口
- `claude-zh-cn.bat`：自动提权包装器
- `install-windowsapps-json-only.ps1`：非交互安装入口
- `restore-windowsapps-zh-cn.ps1`：非交互恢复入口
- `README.md`

安装脚本执行完成后，固定安装目录中会自动生成对应的卸载器，无需手动复制。

## 安装与恢复

- 安装：`powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1`
- 安装（非交互）：`powershell -ExecutionPolicy Bypass -File .\install-windowsapps-json-only.ps1`
- 恢复：`powershell -ExecutionPolicy Bypass -File .\restore-windowsapps-zh-cn.ps1`

## 约定

- 不直接修改 `C:\Program Files\WindowsApps` 的官方安装目录。
- 不替换官方可执行文件。
- 安装脚本会写入 `locale=zh-CN`；如果 `%APPDATA%\Claude-3p\config.json` 不存在，会自动创建。
- 运行时继续使用原版 Claude 的用户数据目录，避免切换到一套新的空配置。
- `ion-dist\assets` 下的版本目录通过递归发现，不再依赖固定 `v1`。

## 第三方推理

如果你要把 Desktop 接到本地代理，例如 `cc-switch`，推荐走官方的第三方推理入口，而不是直接改内部配置文件。

关键点：

- `cc-switch` 一定要开启本地代理。
- Desktop 固定连本地入口，`cc-switch` 负责转发给当前选中的 provider。
- 如果直接把 Desktop 的 Gateway base URL 填成某个固定 provider，后续切换 provider 时还要重复改配置。

推荐检查的配置字段：

- `inferenceProvider`
- `inferenceGatewayBaseUrl`
- `inferenceGatewayApiKey`
- `inferenceModels`
- `isClaudeCodeForDesktopEnabled`

## 维护要点

- 关注 `resources\ion-dist\assets\*\index-*.js` 中语言白名单写法是否变化。
- 关注 `resources\ion-dist\i18n\en-US.json` 的 key 增减。
- 关注 `resources\en-US.json` 的 key 增减。
- 更新 Claude Desktop 后，通常需要重新运行安装脚本。

## 免责声明

- 本项目不是 Anthropic 官方发布内容。
- 请仅在你自己的设备和你能接受的风险范围内使用。
- 使用前请自行评估与本地环境、公司策略和软件更新机制的兼容性。

## 致谢

感谢 LINUX DO 社区的支持与分享，也感谢 `javaht/claude-desktop-zh-cn` 提供的早期参考。
