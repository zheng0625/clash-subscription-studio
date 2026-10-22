param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
try { $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3 }
catch { Write-Host 'Clash Studio is not running on this port.'; exit 0 }
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $digest = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($PSScriptRoot.ToLowerInvariant()))
    $expectedInstance = ([BitConverter]::ToString($digest).Replace('-','').ToLowerInvariant()).Substring(0,16)
} finally { $sha.Dispose() }
if ($health.app -ne 'clash-studio' -or $health.instance -ne $expectedInstance) { throw 'This port does not belong to this Clash Studio workspace.' }
$studioPid = [int]$health.pid
$studioProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $studioPid"
if (-not $studioProcess -or $studioProcess.CommandLine -notlike '*run.py*') { throw 'The running process could not be verified.' }
Stop-Process -Id $studioPid
Write-Host 'Clash Studio stopped.'
