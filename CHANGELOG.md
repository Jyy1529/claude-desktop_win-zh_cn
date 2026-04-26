# Changelog

## 2026-04-26

### Changed

- 项目主线收敛为 JSON-only 官方包 patch，不再碰 Configure Third-Party Inference。
- 主线 patch 脚本 `patch_windowsapps_json_only.py` 现在完整执行：
  - 备份原文件
  - 写入 3 个 zh-CN JSON 资源
  - patch 语言白名单
  - 设置 locale=zh-CN
- `restore_claude_zh_cn_windowsapps.py` 现在同时支持 json-only 和 full-patch 两种备份路径。

### Fixed

- 修复 6 个翻译质量问题（管道符断裂、URL 拼写错误、术语不准确等）。
- 修复根目录 `zh-CN.json` 与 `resources/desktop-zh-CN.json` 的 21 处 macOS/Windows 措辞不一致。

### Removed

- 删除 16 个历史实验脚本（导出副本、chunk patch、3P patch 等）。
- 删除 `Claude_zh-CN_Windows/` 导出的二进制副本（928 个文件）。
- 删除 5 个多余文档。
- 删除根目录重复的 `zh-CN.json` 和 macOS 参考文件 `Localizable.strings`。

### Coverage

- desktop-zh-CN.json: 355/355 keys (100%)
- frontend-zh-CN.json: 12326/12325 keys (100%)
- statsig-zh-CN.json: 46/46 keys (100%)

## Known Issues

- Windows console output may display Chinese text incorrectly under some code pages even when the actual files are valid UTF-8.
- If upstream Claude changes bundle structure or language whitelist layout, the patch script may need updates.
- After official Claude updates, the patch should usually be reinstalled.
