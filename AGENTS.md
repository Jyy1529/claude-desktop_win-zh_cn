# AGENTS.md

## 项目定位
- 这是 Windows 版 Claude Desktop 的中文补丁仓库，不是常规 Python package 或 Node 项目；根目录脚本就是主入口，没有独立构建系统。
- `README.md` 同时保留了当前主线和大量历史路线。遇到 README 与脚本不一致时，以根目录 `*.ps1` / `*.py` 为准。

## 关键入口
- 推荐人工入口：`powershell -NoProfile -ExecutionPolicy Bypass -File .\claude-zh-cn.ps1`。`claude-zh-cn.bat` 只是自动提权包装器。
- `install-windowsapps-json-only.ps1` 名字虽然叫 `json-only`，但实际会依次执行 `patch_windowsapps_json_only.py` 和 `patch_chunks_zh_cn.py`；它不只改 JSON，还会改语言白名单、chunk 标签和字体自定义注入。
- 卸载入口是 `restore-windowsapps-zh-cn.ps1`，底层调用 `restore_claude_zh_cn_windowsapps.py`；它会先恢复备份，再删除安装时新增的 `zh-CN` 资源和白名单残留，并清理 `locale` 和 `claudeZhCnFont`。

## 目标路径与副作用
- 安装/卸载脚本都要求管理员权限，并依赖本机 Python 3。
- 自动检测目标目录 `C:\Program Files\WindowsApps\Claude_*_x64__*\app`；如果是手动指定路径，必须直接传 Claude 的 `app` 目录，且该目录下要有 `resources\en-US.json`。
- 备份固定写到 `%LOCALAPPDATA%\Claude-zh-CN-official-backup\json-only` 和 `%LOCALAPPDATA%\Claude-zh-CN-official-backup\chunks`。
- 用户配置文件是 `%APPDATA%\Claude-3p\config.json`；安装会写入 `locale=zh-CN`，恢复会删除 `locale`、`claudeZhCnFont`、`zh-CN` 资源和白名单残留。

## 资源与约束
- 翻译源文件只有 `resources/desktop-zh-CN.json`、`resources/frontend-zh-CN.json`、`resources/statsig-zh-CN.json`。
- 品牌名、模型名和技术词不是“漏翻译”，而是显式保留英文；现有回归测试会检查 `Claude`、`Claude Code`、`GitHub`、`MCP`、`Chrome`、`Opus`、`Sonnet`、`Haiku` 等仍为英文。
- `patch_chunks_zh_cn.py` 不只是替换文案，还会往 `index-*.js` 注入字体面板和可见文本修正逻辑；改这部分时要注意 `__CLAUDE_ZH_CN_FONT_PATCH__` 与 begin/end 标记不是普通文案。

## 验证命令
- 先跑 `python tools\validate_resources.py`；它只校验 3 个资源 JSON 是否存在、可解析且顶层为对象。
- 再跑 `$env:PYTHONPATH='.'; python tools\test_patch_behaviors.py`。直接运行 `python tools\test_patch_behaviors.py` 会因为 `import best_effort_io` 失败。
- `tools/test_patch_behaviors.py` 的 `main()` 只执行一组 smoke tests，不会自动覆盖文件里所有 `test_*`。
- `python tools\check_i18n_coverage.py` 会重写根目录 `I18N-COVERAGE-REPORT.md`；只有在接受该输出文件变更时再运行。

## 修改建议
- 如果新增了“应保留英文”的术语，通常还要同步更新 `tools/check_i18n_coverage.py` 里的 `KNOWN_OK_PATTERNS`，否则覆盖率脚本会把它报成疑似未翻译。
- 如果只是维护当前主线，优先改资源 JSON 和当前 patch/restore 脚本，不要把 README 里保留的旧导出方案当成现行实现。
