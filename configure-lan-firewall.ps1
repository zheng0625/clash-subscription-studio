param([switch]$Remove, [switch]$Elevated)
$ErrorActionPreference = 'Stop'
$networkFile = Join-Path $PSScriptRoot 'data\network.json'
if ($env:CLASH_STUDIO_DATA) { $networkFile = Join-Path $env:CLASH_STUDIO_DATA 'network.json' }
elseif (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'ClashStudio.exe')) { $networkFile = Join-Path $env:LOCALAPPDATA 'ClashStudio\network.json' }
if (-not (Test-Path -LiteralPath $networkFile)) { throw 'Enable LAN sharing in the app before configuring the firewall.' }
$settings = Get-Content -LiteralPath $networkFile -Raw -Encoding UTF8 | ConvertFrom-Json
$lanPort = [int]$settings.port
if ($lanPort -lt 1024 -or $lanPort -gt 65535) { throw 'Invalid LAN port in network settings.' }
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if ($Elevated) { throw 'Administrator privileges were not granted.' }
    $elevateArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'),'-Elevated')
    if ($Remove) { $elevateArgs += '-Remove' }
    $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $elevateArgs -Verb RunAs -WindowStyle Hidden -PassThru -Wait
    exit $process.ExitCode
}
$sha = [Security.Cryptography.SHA256]::Create()
try { $digest = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($PSScriptRoot.ToLowerInvariant())) }
finally { $sha.Dispose() }
$instanceKey = ([BitConverter]::ToString($digest).Replace('-','').ToLowerInvariant()).Substring(0,16)
$rulePrefix = "ClashStudio-LAN-$instanceKey-"
$existing = Get-NetFirewallRule -Name "$rulePrefix*" -ErrorAction SilentlyContinue
if ($existing) { $existing | Remove-NetFirewallRule }
if ($Remove) { Write-Host 'Clash Studio LAN firewall rules removed.'; exit 0 }
New-NetFirewallRule -Name "$rulePrefix$lanPort" -DisplayName "Clash Studio LAN subscription (TCP $lanPort)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $lanPort -RemoteAddress LocalSubnet -Profile Private -EdgeTraversalPolicy Block | Out-Null
Write-Host "LAN subscription TCP $lanPort allowed for Private networks / LocalSubnet only."
