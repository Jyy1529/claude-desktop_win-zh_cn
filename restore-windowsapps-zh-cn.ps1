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

Write-Host 'Restore WindowsApps zh-CN patch backup'
Write-Host ''

& $python.Source "$scriptDir\restore_claude_zh_cn_windowsapps.py"

if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host 'Restore failed. Check errors above.' -ForegroundColor Red
} else {
  Write-Host ''
  Write-Host 'Restore complete. Restart Claude Desktop to see English UI.' -ForegroundColor Green
}

Read-Host 'Press Enter to exit'
