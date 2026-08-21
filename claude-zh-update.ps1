<#
  Claude Desktop 汉化补丁 - 更新后一键重装
  用法（管理员 PowerShell）:  .\claude-zh-update.ps1
  可选参数:
    -NoRestart   装完不自动启动 Claude
    -Force       即使版本没变也重装
#>
[CmdletBinding()]
param(
  [switch]$NoRestart,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'
# 脚本所在目录即补丁仓库根目录
$RepoDir     = $PSScriptRoot
if (-not $RepoDir) { $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Definition }
$BackupRoot  = Join-Path $env:LOCALAPPDATA 'claude-zh-update\backups'
$ClaudeRoot  = Join-Path $env:LOCALAPPDATA 'AnthropicClaude'
$StateFile   = Join-Path $env:LOCALAPPDATA 'claude-zh-update\last-version.txt'
$LogFile     = Join-Path $env:LOCALAPPDATA 'claude-zh-update\update.log'

function Say([string]$m, [string]$c = 'Gray') { Write-Host $m -ForegroundColor $c }
function Step([string]$m) { Write-Host ''; Write-Host "==> $m" -ForegroundColor Cyan }
function OK([string]$m)   { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn([string]$m) { Write-Host "[!] $m" -ForegroundColor Yellow }
function Fail([string]$m) { Write-Host "[X] $m" -ForegroundColor Red }
function Log([string]$m) {
  New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null
  Add-Content -LiteralPath $LogFile -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) -Encoding UTF8
}

Write-Host ''
Write-Host '  Claude Desktop 汉化 - 更新后重装  ' -ForegroundColor White -BackgroundColor DarkBlue
Log '=== run start ==='

# ---------- 0. 前置检查 ----------
Step '前置检查'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
      ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Fail '需要管理员权限。请右键 PowerShell -> 以管理员身份运行。'
  exit 1
}
OK '管理员权限'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python -or -not (& $python.Source --version 2>$null)) {
  $fallback = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
  if (Test-Path $fallback) { $python = Get-Command $fallback } else { $python = $null }
}
if (-not $python) { Fail ' 找不到可用的 Python。'; exit 1 }
OK ("Python: " + (& $python.Source --version 2>&1))

foreach ($req in @('patch_windowsapps_json_only.py', 'patch_chunks_zh_cn.py')) {
  if (-not (Test-Path (Join-Path $RepoDir $req))) {
    Fail "找不到 $req。请把本脚本放在补丁仓库根目录下运行。"
    exit 1
  }
}
OK "补丁仓库: $RepoDir"

# ---------- 1. 找当前版本 ----------
Step '定位 Claude 安装目录'

$appDirs = @(Get-ChildItem $ClaudeRoot -Directory -Filter 'app-*' -ErrorAction SilentlyContinue)
if ($appDirs.Count -eq 0) { Fail "在 $ClaudeRoot 下找不到 app-* 目录"; exit 1 }

# 按真实版本号排序，而不是字符串（1.34493.0 > 1.9.0）
$appDirs = $appDirs | Sort-Object -Property @{ Expression = {
  $v = $_.Name -replace '^app-', ''
  try { [version]$v } catch { [version]'0.0.0' }
} } -Descending

$appDir  = $appDirs[0].FullName
$version = $appDirs[0].Name -replace '^app-', ''
OK "当前版本: $version"
Say "     路径: $appDir" 'DarkGray'

# ---------- 2. 把旧版本移出 app* 匹配范围 ----------
# 补丁脚本枚举 app* 时不排序、取第一个匹配，多个目录会选错。
if ($appDirs.Count -gt 1) {
  Step '移开旧版本目录（规避补丁脚本选错目录的 bug）'
  foreach ($old in $appDirs[1..($appDirs.Count - 1)]) {
    $newName = 'old-' + ($old.Name -replace '^app-', '') + '.deleteme'
    $dest    = Join-Path $ClaudeRoot $newName
    if (Test-Path $dest) { Warn "$newName 已存在，跳过"; continue }
    Move-Item -LiteralPath $old.FullName -Destination $dest -Force
    OK "$($old.Name) -> $newName"
    Log "moved aside: $($old.Name)"
  }
}

# ---------- 3. 版本比对 ----------
$lastVersion = if (Test-Path $StateFile) { (Get-Content $StateFile -Raw).Trim() } else { '' }
$zhInstalled = Test-Path (Join-Path $appDir 'resources\ion-dist\i18n\zh-CN.json')

if ($version -eq $lastVersion -and $zhInstalled -and -not $Force) {
  Step '无需操作'
  OK "版本 $version 的汉化补丁已在位。加 -Force 可强制重装。"
  Log "skip: already patched $version"
  exit 0
}

# ---------- 4. 备份官方状态 ----------
Step '备份官方状态'

$backupDir = Join-Path $BackupRoot ("app-{0}-official" -f $version)
if (Test-Path $backupDir) {
  OK "已有备份，跳过: $backupDir"
} elseif ($zhInstalled) {
  Warn '当前目录已被打过补丁，跳过备份（避免把改动过的状态存成"官方"备份）'
} else {
  New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
  Copy-Item -LiteralPath $appDir -Destination $backupDir -Recurse -Force
  $srcCount = @(Get-ChildItem $appDir -Recurse -File).Count
  $bakCount = @(Get-ChildItem $backupDir -Recurse -File).Count
  if ($srcCount -ne $bakCount) { Fail "备份文件数不一致 ($srcCount vs $bakCount)，中止"; exit 1 }
  OK "备份完成: $backupDir  ($bakCount 个文件)"
  Log "backup ok: $backupDir ($bakCount files)"
}

# ---------- 5. 优雅关闭 Claude ----------
Step '关闭 Claude'

$procs = @(Get-Process -Name claude -ErrorAction SilentlyContinue)
if ($procs.Count -eq 0) {
  OK 'Claude 未在运行'
} else {
  Say "  发现 $($procs.Count) 个进程，先请求正常退出..." 'DarkGray'
  foreach ($p in $procs) { try { $null = $p.CloseMainWindow() } catch {} }

  $deadline = (Get-Date).AddSeconds(10)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 400
    if (-not (Get-Process -Name claude -ErrorAction SilentlyContinue)) { break }
  }

  $left = @(Get-Process -Name claude -ErrorAction SilentlyContinue)
  if ($left.Count -gt 0) {
    Warn "$($left.Count) 个进程未响应，强制结束"
    $left | Stop-Process -Force -ErrorAction SilentlyContinue
  }
  OK 'Claude 已退出'
}

# 轮询确认文件句柄真的释放了 —— 不是死等固定秒数。
# 安装器写文件是原地覆盖、非原子的，撞上占用就会留下截断文件（上次白屏的成因）。
Say '  等待文件句柄释放...' 'DarkGray'
$probe    = Join-Path $appDir 'resources\ion-dist\i18n\en-US.json'
$released = $false
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
  try {
    $fs = [IO.File]::Open($probe, 'Open', 'ReadWrite', 'None')  # 独占打开
    $fs.Close(); $released = $true; break
  } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $released) {
  Fail '文件仍被占用，中止以避免写坏文件。请手动确认 Claude 完全退出（含托盘图标）后重试。'
  Log 'abort: file still locked'
  exit 1
}
OK '文件句柄已释放'

# ---------- 6. 打补丁 ----------
Step '安装汉化补丁'

Push-Location $RepoDir
try {
  & $python.Source 'patch_windowsapps_json_only.py' --app-dir $appDir
  if ($LASTEXITCODE -ne 0) { throw "JSON 资源 patch 失败 (exit $LASTEXITCODE)" }
  Write-Host ''
  & $python.Source 'patch_chunks_zh_cn.py' --app-dir $appDir
  if ($LASTEXITCODE -ne 0) { throw "chunk 补丁失败 (exit $LASTEXITCODE)" }
} catch {
  Fail $_.Exception.Message
  Log ("patch failed: " + $_.Exception.Message)
  if (Test-Path $backupDir) {
    Warn '正在从备份还原...'
    Copy-Item -LiteralPath (Join-Path $backupDir '*') -Destination $appDir -Recurse -Force
    OK '已还原到官方状态'
    Log 'rolled back'
  } else {
    Warn "没有可用备份，未还原。手动还原: $BackupRoot"
  }
  Pop-Location
  exit 1
} finally {
  if ((Get-Location).Path -eq $RepoDir) { Pop-Location }
}

# ---------- 7. 装后校验 ----------
Step '校验安装结果'

$ionDist = Join-Path $appDir 'resources\ion-dist'
$issues  = @()

$zhJson = Join-Path $ionDist 'i18n\zh-CN.json'
if (Test-Path $zhJson) {
  try {
    $null = Get-Content $zhJson -Raw -Encoding UTF8 | ConvertFrom-Json
    OK ("中文资源已写入 ({0:N0} KB)" -f ((Get-Item $zhJson).Length / 1KB))
  } catch { $issues += 'zh-CN.json 不是合法 JSON' }
} else { $issues += '缺少 zh-CN.json' }

$assets = Join-Path $ionDist 'assets'
$wlHit  = @(Get-ChildItem $assets -Recurse -File -Filter '*.js' -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -lt 2MB } |
            Where-Object { (Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue) -match '"en-US","zh-CN"' })
if ($wlHit.Count -gt 0) { OK "语言白名单已含 zh-CN ($($wlHit[0].Name))" }
else { $issues += '语言白名单未包含 zh-CN' }

$zeroJs = @(Get-ChildItem $ionDist -Recurse -File -Filter '*.js' -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -eq 0 })
if ($zeroJs.Count -eq 0) { OK '无零字节 JS 文件' }
else {
  $issues += "发现 $($zeroJs.Count) 个零字节 JS（文件损坏，白屏风险）"
  $zeroJs | Select-Object -First 5 | ForEach-Object { Say ("      " + $_.Name) 'Red' }
}

foreach ($cfg in @((Join-Path $env:APPDATA 'Claude\config.json'),
                   (Join-Path $env:APPDATA 'Claude-3p\config.json'))) {
  if (Test-Path $cfg) {
    $raw = Get-Content $cfg -Raw
    if ($raw -match '"locale"\s*:\s*"zh-CN"') { OK "locale=zh-CN  ($(Split-Path $cfg -Parent | Split-Path -Leaf))" }
    else { Warn "locale 不是 zh-CN: $cfg" }
  }
}

if ($issues.Count -gt 0) {
  Write-Host ''
  Fail '校验未通过:'
  $issues | ForEach-Object { Say "      - $_" 'Red' }
  Log ("verify failed: " + ($issues -join '; '))
  if (Test-Path $backupDir) {
    Write-Host ''
    Warn '正在从备份还原...'
    Copy-Item -LiteralPath (Join-Path $backupDir '*') -Destination $appDir -Recurse -Force
    OK '已还原到官方状态。汉化未生效，但 Claude 可正常使用。'
    Log 'rolled back after verify failure'
  }
  exit 1
}

# ---------- 8. 记录版本 ----------
New-Item -ItemType Directory -Path (Split-Path $StateFile) -Force | Out-Null
Set-Content -LiteralPath $StateFile -Value $version -Encoding UTF8
Log "success: $version"

# ---------- 9. 重启 Claude ----------
Write-Host ''
OK "汉化补丁已安装到 $version"

if (-not $NoRestart) {
  Step '启动 Claude'
  $exe = Join-Path $ClaudeRoot 'claude.exe'
  if (-not (Test-Path $exe)) { $exe = Join-Path $appDir 'claude.exe' }
  if (Test-Path $exe) { Start-Process $exe; OK '已启动' }
  else { Warn '找不到 claude.exe，请手动启动' }
}

Write-Host ''
Say "日志: $LogFile" 'DarkGray'
Write-Host ''
