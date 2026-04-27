<#
.SYNOPSIS
  Claude Desktop 中文补丁 - 安装 / 卸载 / 状态检查
.DESCRIPTION
  交互式菜单，自动检测 Claude 安装路径，执行对应操作。
  需要以管理员身份运行（因为要写 WindowsApps 目录）。
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

function Find-ClaudePackage {
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
  return $null
}

$pkg = Find-ClaudePackage
if (-not $pkg) {
  Write-Host ''
  Write-Err '未找到已安装的 Claude Desktop (WindowsApps)。'
  Write-Info '请确认已从 Microsoft Store 安装 Claude Desktop。'
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
  $indexFiles = Get-ChildItem (Join-Path $resDir 'ion-dist\assets\v1') -Filter 'index-*.js' -ErrorAction SilentlyContinue
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

  return @{
    ZhFiles    = $hasZhFiles
    Whitelist  = $hasWhitelist
    Locale     = $hasLocale
    Backup     = $hasBackup
    Installed  = $hasZhFiles -and $hasWhitelist
  }
}

# ── 显示状态 ──────────────────────────────────────────────
function Show-Status {
  $s = Get-PatchStatus

  Write-Title '当前状态'
  Write-Info  "Claude 包: $pkgName"
  Write-Info  "安装路径:  $appDir"
  Write-Host ''

  if ($s.ZhFiles)   { Write-OK   '中文资源文件已写入' }   else { Write-Info '中文资源文件未写入' }
  if ($s.Whitelist)  { Write-OK   '语言白名单已包含 zh-CN' } else { Write-Info '语言白名单未包含 zh-CN' }
  if ($s.Locale)     { Write-OK   'locale 已设为 zh-CN' }   else { Write-Info 'locale 未设置' }
  if ($s.Backup)     { Write-OK   '备份存在' }             else { Write-Info '无备份' }

  Write-Host ''
  if ($s.Installed) {
    Write-OK '中文补丁状态: 已安装'
  } else {
    Write-Info '中文补丁状态: 未安装'
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
  Write-Info '正在执行 chunk 界面标签和字体自定义 patch...'
  Write-Host ''
  & $python.Source "$scriptDir\patch_chunks_zh_cn.py" --app-dir "$appDir"

  Write-Host ''
  Write-OK '安装完成！'
  Write-Host ''
  Write-Info '下一步：'
  Write-Info '  1. 打开 Claude Desktop'
  Write-Info '  2. 界面应该已经是中文'
  Write-Info '  3. 可在设置 / 外观区域使用中文字体设置'
  Write-Info ''
  Write-Warn '注意: 部分第三方推理配置页面文案来自 JS chunk，已尽量汉化，仍可能有少量英文残留'
  Write-Warn '注意: Claude 更新版本后需要重新运行此脚本'
}

# ── 卸载 ──────────────────────────────────────────────────
function Invoke-Uninstall {
  Write-Title '卸载中文补丁'
  Write-Host ''

  $s = Get-PatchStatus
  if (-not $s.Backup) {
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
    $indexFiles = Get-ChildItem (Join-Path $resDir 'ion-dist\assets\v1') -Filter 'index-*.js' -ErrorAction SilentlyContinue
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
  Write-Host '  [3] 刷新状态' -ForegroundColor White
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
      # 刷新状态，直接回到菜单
    }
    '0' {
      Write-Host ''
      Write-Info '再见！'
      Write-Host ''
      exit 0
    }
    default {
      Write-Host ''
      Write-Warn '无效选择，请输入 0-3。'
      Start-Sleep -Milliseconds 800
    }
  }
}
