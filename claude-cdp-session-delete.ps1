param(
  [int]$Port = 9229,
  [string]$AppDir = '',
  [switch]$NoLaunch,
  [switch]$DiagnoseRows,
  [switch]$ScanPorts,
  [switch]$LocalDeleteBridge,
  [switch]$Background,
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

function Convert-ToProcessArgument {
  param([string]$Value)
  if ($null -eq $Value) { return '""' }
  if ($Value -match '[\s"]') {
    return '"' + ($Value -replace '"', '\"') + '"'
  }
  return $Value
}

if ($Background) {
  if (-not $LocalDeleteBridge) {
    Write-Error '-Background requires -LocalDeleteBridge.'
    exit 1
  }

  $scriptPath = $MyInvocation.MyCommand.Path
  $backgroundArgs = @(
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    (Convert-ToProcessArgument $scriptPath),
    '-Port',
    [string]$Port,
    '-TimeoutSeconds',
    [string]$TimeoutSeconds,
    '-LocalDeleteBridge'
  )

  if (-not [string]::IsNullOrWhiteSpace($AppDir)) {
    $backgroundArgs += @('-AppDir', (Convert-ToProcessArgument $AppDir))
  }
  if ($NoLaunch) {
    $backgroundArgs += '-NoLaunch'
  }
  if ($DiagnoseRows) {
    $backgroundArgs += '-DiagnoseRows'
  }
  if ($ScanPorts) {
    $backgroundArgs += '-ScanPorts'
  }

  $process = Start-Process -FilePath 'powershell' -ArgumentList ($backgroundArgs -join ' ') -WindowStyle Hidden -PassThru
  Write-Host "Local delete bridge started in background: pid=$($process.Id)"
  exit 0
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

if ($LocalDeleteBridge) {
  $argsList += '--local-delete-bridge'
}

& $python.Source @argsList
exit $LASTEXITCODE
