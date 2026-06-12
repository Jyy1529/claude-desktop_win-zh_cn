<#
.SYNOPSIS
  Claude Desktop 中文补丁 - 安装 / 卸载 / 状态检查
.DESCRIPTION
  交互式菜单，自动检测 Claude 安装路径，执行对应操作。
  WindowsApps 版需要以管理员身份运行；AppData\Local\AnthropicClaude 版也建议用管理员运行。
  需要 Python 3。
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 颜色辅助 ──────────────────────────────────────────────
function Write-Title  { param($t) Write-Host "`n  $t" -ForegroundColor Cyan }
function Write-OK     { param($t) Write-Host "  [OK] $t" -ForegroundColor Green }
function Write-Warn   { param($t) Write-Host "  [!]  $t" -ForegroundColor Yellow }
function Write-Err    { param($t) Write-Host "  [X]  $t" -ForegroundColor Red }
function Write-Info   { param($t) Write-Host "  $t" -ForegroundColor Gray }

# ── 管理员检查 ────────────────────────────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
  Write-Host ''
  Write-Err '需要以管理员身份运行此脚本。'
  Write-Info '右键 PowerShell -> 以管理员身份运行，然后重新执行。'
  Write-Host ''
  Read-Host '按 Enter 退出'
  exit 1
}

# ── Python 检查 ───────────────────────────────────────────
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Host ''
  Write-Err '未找到 Python 3。'
  Write-Info '请先安装 Python 3：https://www.python.org/downloads/'
  Write-Host ''
  Read-Host '按 Enter 退出'
  exit 1
}

# ── 自动检测 Claude 包路径 ────────────────────────────────
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-ClaudeAppPath {
  param([string]$InputPath)

  if ([string]::IsNullOrWhiteSpace($InputPath)) {
    return $null
  }

  try {
    $resolved = [System.IO.Path]::GetFullPath($InputPath.Trim())
  } catch {
    return $null
  }

  $app = $resolved.TrimEnd('\\/')
  $candidateApps = @(
    $app,
    (Join-Path $app 'app')
  )
  if (Test-Path $app) {
    $candidateApps += @(Get-ChildItem $app -Directory -Filter 'app*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
  }

  foreach ($candidate in $candidateApps) {
    $res = Join-Path $candidate 'resources'
    $desktop = Join-Path $res 'en-US.json'
    if ((Test-Path $candidate) -and (Test-Path $desktop)) {
      return @{ AppDir = $candidate; ResourcesDir = $res; PackageName = ('manual:' + $candidate) }
    }
  }

  return $null
}

function Find-ClaudePackage {
  $running = Get-Process -Name claude -ErrorAction SilentlyContinue |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_.Path) } |
    ForEach-Object { Resolve-ClaudeAppPath (Split-Path -Parent $_.Path) } |
    Where-Object { $_ } |
    Select-Object -First 1
  if ($running) {
    $running['PackageName'] = ('running:' + $running['AppDir'])
    return $running
  }

  $appx = Get-AppxPackage -Name Claude -ErrorAction SilentlyContinue |
    Sort-Object Version -Descending |
    Select-Object -First 1
  if ($appx -and $appx.InstallLocation) {
    $manual = Resolve-ClaudeAppPath (Join-Path $appx.InstallLocation 'app')
    if ($manual) {
      $manual['PackageName'] = $appx.PackageFullName
      return $manual
    }
  }

  $base = 'C:\Program Files\WindowsApps'
  $dirs = Get-ChildItem $base -Directory -Filter 'Claude_*_x64__*' -ErrorAction SilentlyContinue |
          Sort-Object Name -Descending
  foreach ($d in $dirs) {
    $app = Join-Path $d.FullName 'app'
    $res = Join-Path $app 'resources'
    if (Test-Path (Join-Path $res 'en-US.json')) {
      return @{ AppDir = $app; ResourcesDir = $res; PackageName = $d.Name }
    }
  }

  $local = Resolve-ClaudeAppPath (Join-Path $env:LOCALAPPDATA 'AnthropicClaude')
  if ($local) {
    $local['PackageName'] = ('AnthropicClaude:' + $local['AppDir'])
    return $local
  }
  return $null
}

function Resolve-ClaudePackage {
  $detected = Find-ClaudePackage
  if ($detected) { return $detected }

  Write-Host ''
  Write-Warn '未检测到 Claude 安装。'
  Write-Info '支持商店版 WindowsApps，也支持网页登录页下载的 AppData\Local\AnthropicClaude。'
  Write-Info '请手动输入 Claude app 目录或安装根目录。'
  Write-Info '示例: C:\Users\你的用户名\AppData\Local\AnthropicClaude'
  Write-Host ''

  while ($true) {
    $inputPath = Read-Host '  请输入 Claude app 目录（留空则退出）'
    if ([string]::IsNullOrWhiteSpace($inputPath)) {
      return $null
    }

    $manual = Resolve-ClaudeAppPath $inputPath
    if ($manual) { return $manual }

    Write-Warn '该目录下未找到 resources\en-US.json，请确认输入的是 Claude app 目录或安装根目录。'
  }
}

function Get-AssetsVersionDirs {
  param([string]$ResourcesDir)

  $assetsRoot = Join-Path $ResourcesDir 'ion-dist\assets'
  if (-not (Test-Path $assetsRoot)) {
    return @()
  }

  $dirs = Get-ChildItem $assetsRoot -Recurse -File -Filter 'index-*.js' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Directory.FullName } |
    Sort-Object -Unique -Descending
  return @($dirs)
}

function Set-ClaudePackageManual {
  Write-Host ''
  Write-Info '手动指定 Claude app 目录'
  Write-Info '示例: C:\Program Files\WindowsApps\Claude_...\app'
  Write-Info '示例: C:\Users\你的用户名\AppData\Local\AnthropicClaude'
  Write-Host ''

  while ($true) {
    $inputPath = Read-Host '  请输入 Claude app 目录（留空则取消）'
    if ([string]::IsNullOrWhiteSpace($inputPath)) {
      Write-Info '已取消。'
      return $false
    }

    $manual = Resolve-ClaudeAppPath $inputPath
    if ($manual) {
      $script:pkg = $manual
      $script:appDir = $manual.AppDir
      $script:resDir = $manual.ResourcesDir
      $script:pkgName = $manual.PackageName
      Write-OK "已切换到手动路径: $appDir"
      return $true
    }

    Write-Warn '该目录下未找到 app\resources\en-US.json，请确认输入的是 Claude 的 app 目录。'
  }
}

$pkg = Resolve-ClaudePackage
if (-not $pkg) {
  Write-Host ''
  Write-Err '未找到可用的 Claude 安装目录。'
  Write-Info '请确认已安装 Claude Desktop，或手动提供解压运行版本的 app 目录。'
  Write-Host ''
  Read-Host '按 Enter 退出'
  exit 1
}

$appDir      = $pkg.AppDir
$resDir      = $pkg.ResourcesDir
$pkgName     = $pkg.PackageName
$backupRoot  = Join-Path $env:LOCALAPPDATA 'Claude-zh-CN-official-backup\json-only'
$configPath  = Join-Path $env:APPDATA 'Claude-3p\config.json'

# ── 状态检测 ──────────────────────────────────────────────
function Get-PatchStatus {
  $zhDesktop  = Join-Path $resDir 'zh-CN.json'
  $zhFrontend = Join-Path $resDir 'ion-dist\i18n\zh-CN.json'
  $zhStatsig  = Join-Path $resDir 'ion-dist\i18n\statsig\zh-CN.json'

  $hasZhFiles = (Test-Path $zhDesktop) -and (Test-Path $zhFrontend) -and (Test-Path $zhStatsig)

  # 检查白名单
  $hasWhitelist = $false
  $indexFiles = Get-ChildItem (Join-Path $resDir 'ion-dist\assets') -Recurse -File -Filter 'index-*.js' -ErrorAction SilentlyContinue
  foreach ($f in $indexFiles) {
    $content = [System.IO.File]::ReadAllText($f.FullName)
    if ($content.Contains('"zh-CN"')) { $hasWhitelist = $true; break }
  }

  # 检查 locale
  $hasLocale = $false
  if (Test-Path $configPath) {
    try {
      $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
      if ($cfg.locale -eq 'zh-CN') { $hasLocale = $true }
    } catch {}
  }

  # 检查备份
  $hasBackup = (Test-Path $backupRoot) -and ((Get-ChildItem $backupRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
  $hasArtifacts = $hasZhFiles -or $hasWhitelist -or $hasLocale

  $state = if ($hasZhFiles -and $hasWhitelist) {
    if ($hasLocale) { 'Installed' } else { 'InstalledNoLocale' }
  } elseif ($hasArtifacts) {
    'Partial'
  } elseif ($hasBackup) {
    'CleanWithBackup'
  } else {
    'Clean'
  }

  return @{
    ZhFiles    = $hasZhFiles
    Whitelist  = $hasWhitelist
    Locale     = $hasLocale
    Backup     = $hasBackup
    HasArtifacts = $hasArtifacts
    State      = $state
    Installed  = $hasZhFiles -and $hasWhitelist
  }
}

# ── 显示状态 ──────────────────────────────────────────────
function Show-Status {
  $s = Get-PatchStatus

  Write-Title '当前状态'
  Write-Info  "Claude 来源: $pkgName"
  Write-Info  "安装路径:  $appDir"
  Write-Host ''

  if ($s.ZhFiles)   { Write-OK   '中文资源文件已写入' }   else { Write-Info '中文资源文件未写入' }
  if ($s.Whitelist)  { Write-OK   '语言白名单已包含 zh-CN' } else { Write-Info '语言白名单未包含 zh-CN' }
  if ($s.Locale)     { Write-OK   'locale 已设为 zh-CN' }   else { Write-Info 'locale 未设置' }
  if ($s.Backup)     { Write-OK   '备份存在' }             else { Write-Info '无备份' }

  Write-Host ''
  switch ($s.State) {
    'Installed' { Write-OK   '中文补丁状态: 已安装' }
    'InstalledNoLocale' { Write-Warn '中文补丁状态: 已安装（locale 未设置）' }
    'Partial' { Write-Warn '中文补丁状态: 部分残留' }
    'CleanWithBackup' { Write-Info '中文补丁状态: 已卸载（备份保留）' }
    default { Write-Info '中文补丁状态: 未安装' }
  }

  return $s
}

# ── 安装 ──────────────────────────────────────────────────
function Invoke-Install {
  Write-Title '安装中文补丁'
  Write-Host ''

  Write-Info '正在关闭 Claude 进程...'
  Get-Process -Name claude -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2

  Write-Info '正在执行 JSON 资源 patch...'
  Write-Host ''
  & $python.Source "$scriptDir\patch_windowsapps_json_only.py" --app-dir "$appDir"

  if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Err 'JSON 资源 patch 失败。请检查上面的错误信息。'
    return
  }

  Write-Host ''
  Write-Info '正在执行 chunk 界面标签、字体和会话增强 patch...'
  Write-Host ''
  & $python.Source "$scriptDir\patch_chunks_zh_cn.py" --app-dir "$appDir"

  Write-Host ''
  Write-Info '正在尝试通过 CDP 追加注入会话增强（失败不影响已写入的 chunk 补丁）...'
  Invoke-SessionDeleteCdp

  Write-Host ''
  Write-OK '安装完成！'
  Write-Host ''
  Write-Info '下一步：'
  Write-Info '  1. 界面应该已经是中文'
  Write-Info '  2. 左侧会话列表悬停时应显示移动、导出、删除按钮'
  Write-Info '  3. 右侧会显示对话 Timeline，底部可切换居中宽度'
  Write-Info '  4. 可在设置 / 外观区域使用中文字体设置'
  Write-Info ''
  Write-Warn '注意: 部分第三方推理配置页面文案来自 JS chunk，已尽量汉化，仍可能有少量英文残留'
  Write-Warn '注意: Claude 更新版本后需要重新运行此脚本'
}

# ── CDP 注入会话删除按钮 ───────────────────────────────────
function Invoke-SessionDeleteCdp {
  Write-Title '注入会话删除按钮（CDP）'
  Write-Host ''
  Write-Info '脚本会通过 DevTools/CDP 临时注入会话增强；稳定安装路径已写入 WindowsApps 入口 chunk。'
  Write-Host ''

  $launcher = Join-Path $scriptDir 'claude-cdp-session-delete.ps1'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -AppDir "$appDir"

  if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Warn 'CDP 注入失败。已安装的 chunk 会话增强仍然有效，请关闭 Claude 后从开始菜单重新打开。'
    return
  }

  Write-Host ''
  Write-OK 'CDP 注入完成。'
}

# ── 管理 / 诊断面板 ───────────────────────────────────────
$bridgeTaskName = 'ClaudeZhCnLocalDeleteBridge'

function Get-ClaudeVersionLabel {
  $exe = Join-Path $appDir 'claude.exe'
  if (Test-Path $exe) {
    try {
      $info = (Get-Item $exe).VersionInfo
      if (-not [string]::IsNullOrWhiteSpace($info.ProductVersion)) { return $info.ProductVersion }
      if (-not [string]::IsNullOrWhiteSpace($info.FileVersion)) { return $info.FileVersion }
    } catch {}
  }

  if ($pkgName -match 'Claude_([^_]+)_') {
    return $Matches[1]
  }

  return '未知'
}

function Get-IndexChunkFiles {
  $assetsRoot = Join-Path $resDir 'ion-dist\assets'
  if (-not (Test-Path $assetsRoot)) {
    return @()
  }
  return @(Get-ChildItem $assetsRoot -Recurse -File -Filter 'index-*.js' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
}

function Get-ChunkPatchSummary {
  $indexFiles = Get-IndexChunkFiles
  $fontMarkers = 0
  $sessionMarkers = 0
  $zhWhitelistMarkers = 0
  foreach ($f in $indexFiles) {
    try {
      $content = [System.IO.File]::ReadAllText($f.FullName)
      if ($content.Contains('__CLAUDE_ZH_CN_FONT_PATCH__')) { $fontMarkers++ }
      if ($content.Contains('__CLAUDE_ZH_CN_SESSION_DELETE_PATCH__')) { $sessionMarkers++ }
      if ($content.Contains('"zh-CN"')) { $zhWhitelistMarkers++ }
    } catch {}
  }

  $currentChunk = if ($indexFiles.Count -gt 0) { $indexFiles[0].FullName } else { '未找到' }
  return @{
    IndexCount = $indexFiles.Count
    CurrentChunk = $currentChunk
    FontMarkers = $fontMarkers
    SessionMarkers = $sessionMarkers
    ZhWhitelistMarkers = $zhWhitelistMarkers
  }
}

function Get-LocalDeleteBridgeProcesses {
  try {
    $items = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object {
        $_.CommandLine -like '*claude-cdp-session-delete.ps1*' -and
        $_.CommandLine -like '*LocalDeleteBridge*'
      } |
      Select-Object ProcessId,Name,CommandLine
    return @($items)
  } catch {
    return @()
  }
}

function Get-LocalDeleteBridgeTask {
  try {
    return Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
  } catch {
    return $null
  }
}

function Start-LocalDeleteBridgeBackground {
  Write-Title '启动本地删除桥（后台）'
  $launcher = Join-Path $scriptDir 'claude-cdp-session-delete.ps1'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -AppDir "$appDir" -LocalDeleteBridge -Background
  if ($LASTEXITCODE -eq 0) {
    Write-OK '后台桥启动命令已提交。'
  } else {
    Write-Warn '后台桥启动失败，请在前台模式查看日志。'
  }
}

function Install-LocalDeleteBridgeTask {
  Write-Title '安装登录后台任务'
  $launcher = Join-Path $scriptDir 'claude-cdp-session-delete.ps1'
  $arguments = @(
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    ('"{0}"' -f $launcher),
    '-AppDir',
    ('"{0}"' -f $appDir),
    '-LocalDeleteBridge',
    '-Background'
  ) -join ' '

  try {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DisallowStartIfOnBatteries:$false -StartWhenAvailable
    Register-ScheduledTask -TaskName $bridgeTaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Claude zh-CN local session delete bridge' -Force | Out-Null
    Write-OK "已安装登录任务: $bridgeTaskName"
  } catch {
    Write-Warn "安装登录任务失败: $_"
  }
}

function Uninstall-LocalDeleteBridgeTask {
  Write-Title '卸载登录后台任务'
  try {
    if (Get-LocalDeleteBridgeTask) {
      Unregister-ScheduledTask -TaskName $bridgeTaskName -Confirm:$false
      Write-OK "已卸载登录任务: $bridgeTaskName"
    } else {
      Write-Info "未安装登录任务: $bridgeTaskName"
    }
  } catch {
    Write-Warn "卸载登录任务失败: $_"
  }
}

function Invoke-CdpRowDiagnostics {
  Write-Title '运行 CDP 行诊断'
  $launcher = Join-Path $scriptDir 'claude-cdp-session-delete.ps1'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -AppDir "$appDir" -DiagnoseRows -ScanPorts
  if ($LASTEXITCODE -ne 0) {
    Write-Warn 'CDP 行诊断失败，请确认 Claude 可以用同一调试端口启动。'
  }
}

function Show-ManagementSnapshot {
  $s = Get-PatchStatus
  $chunk = Get-ChunkPatchSummary
  $bridgeProcesses = Get-LocalDeleteBridgeProcesses
  $bridgeTask = Get-LocalDeleteBridgeTask
  $version = Get-ClaudeVersionLabel

  Write-Title '管理 / 诊断面板'
  Write-Info "Claude 版本: $version"
  Write-Info "Claude 来源: $pkgName"
  Write-Info "安装路径:  $appDir"
  Write-Info "资源目录:  $resDir"
  Write-Host ''
  Write-Info "中文资源:  $($s.ZhFiles)"
  Write-Info "语言白名单: $($s.Whitelist)"
  Write-Info "locale:    $($s.Locale)"
  Write-Info "备份:      $($s.Backup)"
  Write-Host ''
  Write-Info "index chunk 数量: $($chunk.IndexCount)"
  Write-Info "当前 chunk: $($chunk.CurrentChunk)"
  Write-Info "字体注入标记: $($chunk.FontMarkers)"
  Write-Info "会话增强标记: $($chunk.SessionMarkers)"
  Write-Info "zh-CN 白名单标记: $($chunk.ZhWhitelistMarkers)"
  Write-Host ''
  Write-Info "本地删除桥进程: $($bridgeProcesses.Count)"
  foreach ($p in $bridgeProcesses | Select-Object -First 3) {
    Write-Info "  pid=$($p.ProcessId) $($p.Name)"
  }
  if ($bridgeTask) {
    Write-OK "登录任务: 已安装 ($bridgeTaskName)"
  } else {
    Write-Info "登录任务: 未安装 ($bridgeTaskName)"
  }
}

function Show-ManagementPanel {
  while ($true) {
    Clear-Host
    Show-ManagementSnapshot
    Write-Host ''
    Write-Host '  ─────────────────────────────────────────────' -ForegroundColor DarkGray
    Write-Host '  [1] 刷新诊断' -ForegroundColor White
    Write-Host '  [2] 启动本地删除桥（后台）' -ForegroundColor White
    Write-Host '  [3] 安装登录任务：后台桥' -ForegroundColor White
    Write-Host '  [4] 卸载登录任务：后台桥' -ForegroundColor White
    Write-Host '  [5] 运行 CDP 行诊断' -ForegroundColor White
    Write-Host '  [0] 返回主菜单' -ForegroundColor White
    Write-Host ''

    $choice = Read-Host '  请选择'
    switch ($choice) {
      '1' {}
      '2' {
        Start-LocalDeleteBridgeBackground
        Write-Host ''
        Read-Host '按 Enter 返回管理面板'
      }
      '3' {
        Install-LocalDeleteBridgeTask
        Write-Host ''
        Read-Host '按 Enter 返回管理面板'
      }
      '4' {
        Uninstall-LocalDeleteBridgeTask
        Write-Host ''
        Read-Host '按 Enter 返回管理面板'
      }
      '5' {
        Invoke-CdpRowDiagnostics
        Write-Host ''
        Read-Host '按 Enter 返回管理面板'
      }
      '0' { return }
      default {
        Write-Host ''
        Write-Warn '无效选择，请输入 0-5。'
        Start-Sleep -Milliseconds 800
      }
    }
  }
}

# ── 卸载 ──────────────────────────────────────────────────
function Invoke-Uninstall {
  Write-Title '卸载中文补丁'
  Write-Host ''

  $s = Get-PatchStatus
  if (-not $s.HasArtifacts -and -not $s.Backup) {
    Write-Warn '未找到备份文件，无法自动恢复。'
    Write-Info "备份目录: $backupRoot"

    Write-Host ''
    $confirm = Read-Host '  是否仍要尝试删除中文资源文件？(y/N)'
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
      Write-Info '已取消。'
      return
    }

    # 手动删除 zh-CN 文件 + 尝试清除白名单中的 zh-CN
    Write-Info '正在关闭 Claude 进程...'
    Get-Process -Name claude -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $targets = @(
      (Join-Path $resDir 'zh-CN.json'),
      (Join-Path $resDir 'ion-dist\i18n\zh-CN.json'),
      (Join-Path $resDir 'ion-dist\i18n\statsig\zh-CN.json')
    )
    foreach ($t in $targets) {
      if (Test-Path $t) { Remove-Item $t -Force; Write-Info "  已删除: $t" }
    }

    # 尝试从白名单中移除 zh-CN
    $indexFiles = Get-ChildItem (Join-Path $resDir 'ion-dist\assets') -Recurse -File -Filter 'index-*.js' -ErrorAction SilentlyContinue
    foreach ($f in $indexFiles) {
      $content = [System.IO.File]::ReadAllText($f.FullName)
      if ($content.Contains(',"zh-CN"')) {
        $content = $content.Replace(',"zh-CN"', '')
        [System.IO.File]::WriteAllText($f.FullName, $content)
        Write-Info "  已从白名单移除 zh-CN: $($f.Name)"
      }
    }
  } else {
    Write-Info '正在关闭 Claude 进程...'
    Get-Process -Name claude -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    Write-Info '正在从备份恢复...'
    Write-Host ''
    & $python.Source "$scriptDir\restore_claude_zh_cn_windowsapps.py" --app-dir "$appDir"

    if ($LASTEXITCODE -ne 0) {
      Write-Host ''
      Write-Err '恢复失败。请检查上面的错误信息。'
      return
    }
  }

  # 移除 locale
  if (Test-Path $configPath) {
    try {
      $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
      if ($cfg.PSObject.Properties['locale']) {
        $cfg.PSObject.Properties.Remove('locale')
        $cfg | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
        Write-Info '已从配置中移除 locale'
      }
    } catch {
      Write-Warn "无法修改配置文件: $_"
    }
  }

  Write-Host ''
  Write-OK '卸载完成！'
  Write-Host ''
  Write-Info '运行时注入已随 Claude 关闭失效'
  Write-Host ''
  Write-Info '下一步：'
  Write-Info '  1. 打开 Claude Desktop'
  Write-Info '  2. 界面应该已经恢复英文'
}

# ── 主菜单 ────────────────────────────────────────────────
function Show-Menu {
  Clear-Host
  Write-Host ''
  Write-Host '  ╔══════════════════════════════════════════════╗' -ForegroundColor Cyan
  Write-Host '  ║   Claude Desktop 中文补丁 (zh-CN, Windows)  ║' -ForegroundColor Cyan
  Write-Host '  ╚══════════════════════════════════════════════╝' -ForegroundColor Cyan

  $s = Show-Status

  Write-Host ''
  Write-Host '  ─────────────────────────────────────────────' -ForegroundColor DarkGray

  if ($s.Installed) {
    Write-Host '  [1] 重新安装 / 更新中文补丁' -ForegroundColor White
    Write-Host '  [2] 卸载中文补丁（恢复英文）' -ForegroundColor White
  } else {
    Write-Host '  [1] 安装中文补丁' -ForegroundColor White
    Write-Host '  [2] 卸载中文补丁（恢复英文）' -ForegroundColor DarkGray
  }
  Write-Host '  [3] 手动指定 Claude app 目录' -ForegroundColor White
  Write-Host '  [4] 刷新状态' -ForegroundColor White
  Write-Host '  [5] 管理 / 诊断面板' -ForegroundColor White
  Write-Host '  [0] 退出' -ForegroundColor White
  Write-Host ''
}

# ── 主循环 ────────────────────────────────────────────────
while ($true) {
  Show-Menu
  $choice = Read-Host '  请选择'

  switch ($choice) {
    '1' {
      Invoke-Install
      Write-Host ''
      Read-Host '按 Enter 返回菜单'
    }
    '2' {
      $s = Get-PatchStatus
      if (-not $s.Installed -and -not $s.Backup) {
        Write-Host ''
        Write-Warn '当前未安装中文补丁，也没有备份，无需卸载。'
        Write-Host ''
        Read-Host '按 Enter 返回菜单'
      } else {
        Invoke-Uninstall
        Write-Host ''
        Read-Host '按 Enter 返回菜单'
      }
    }
    '3' {
      Write-Host ''
      $changed = Set-ClaudePackageManual
      Write-Host ''
      Read-Host '按 Enter 返回菜单'
    }
    '4' {
      # 刷新状态，直接回到菜单
    }
    '5' {
      Show-ManagementPanel
    }
    '0' {
      Write-Host ''
      Write-Info '再见！'
      Write-Host ''
      exit 0
    }
    default {
      Write-Host ''
      Write-Warn '无效选择，请输入 0-5。'
      Start-Sleep -Milliseconds 800
    }
  }
}
