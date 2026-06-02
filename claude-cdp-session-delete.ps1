param(
  [int]$Port = 9229,
  [string]$AppDir = '',
  [switch]$NoLaunch,
  [switch]$DiagnoseRows,
  [switch]$ScanPorts,
  [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Error 'Python 3 was not found.'
  exit 1
}

$launcher = Join-Path $scriptDir 'tools\cdp_session_delete_launcher.py'
$argsList = @(
  '-B',
  $launcher,
  '--port',
  [string]$Port,
  '--timeout',
  [string]$TimeoutSeconds
)

if (-not [string]::IsNullOrWhiteSpace($AppDir)) {
  $argsList += @('--app-dir', $AppDir)
}

if ($NoLaunch) {
  $argsList += '--no-launch'
}

if ($DiagnoseRows) {
  $argsList += '--diagnose-rows'
}

if ($ScanPorts) {
  $argsList += '--scan-ports'
}

& $python.Source @argsList
exit $LASTEXITCODE
