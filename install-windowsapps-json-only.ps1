param(
  [string]$AppDir
)

$ErrorActionPreference = 'Stop'

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Write-Host 'This script requires administrator privileges.' -ForegroundColor Red
  Write-Host 'Right-click PowerShell -> Run as administrator.' -ForegroundColor Yellow
  Read-Host 'Press Enter to exit'
  exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Host 'Python 3 not found. Please install Python 3 first.' -ForegroundColor Red
  exit 1
}

Get-Process -Name claude -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host 'WindowsApps zh-CN patch (JSON + chunk labels + font customizer)'
Write-Host ''

Write-Host 'Step 1: JSON resources...'
if ($AppDir) {
  & $python.Source "$scriptDir\patch_windowsapps_json_only.py" --app-dir "$AppDir"
} else {
  & $python.Source "$scriptDir\patch_windowsapps_json_only.py"
}

if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host 'JSON patch failed. Check errors above.' -ForegroundColor Red
  Read-Host 'Press Enter to exit'
  exit 1
}

Write-Host ''
Write-Host 'Step 2: Chunk UI labels and font customizer...'
if ($AppDir) {
  & $python.Source "$scriptDir\patch_chunks_zh_cn.py" --app-dir "$AppDir"
} else {
  & $python.Source "$scriptDir\patch_chunks_zh_cn.py"
}

Write-Host ''
Write-Host 'Patch complete. Restart Claude Desktop to see Chinese UI.' -ForegroundColor Green
Write-Host 'Font customizer will appear in the existing Settings/Appearance area when available.' -ForegroundColor Green

Read-Host 'Press Enter to exit'
