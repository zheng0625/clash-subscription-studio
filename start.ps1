param([int]$Port = 8765, [switch]$Rebuild, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Checked {
    param([string]$Program, [string[]]$ProgramArgs)
    & $Program @ProgramArgs
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Program (exit $LASTEXITCODE)" }
}

$runtimeRoot = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies'
$bundledPython = Join-Path $runtimeRoot 'python\python.exe'
$bundledNodeDir = Join-Path $runtimeRoot 'node\bin'
if (Test-Path -LiteralPath $bundledNodeDir) { $env:PATH = "$bundledNodeDir;$env:PATH" }
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host 'Preparing local Python environment...'
    if (Test-Path -LiteralPath $bundledPython) {
        Invoke-Checked $bundledPython @('-m','venv','.venv')
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Checked 'py' @('-3','-m','venv','.venv')
    } else {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand -or $pythonCommand.Source -like '*WindowsApps*') { throw 'Python 3.11+ is required. Install Python and run this file again.' }
        Invoke-Checked $pythonCommand.Source @('-m','venv','.venv')
    }
}
$requirementsHash = (Get-FileHash -LiteralPath 'requirements.txt' -Algorithm SHA256).Hash
$stampPath = Join-Path $PSScriptRoot '.venv\studio-requirements.sha256'
if (-not (Test-Path -LiteralPath $stampPath) -or (Get-Content -LiteralPath $stampPath -Raw).Trim() -ne $requirementsHash) {
    Write-Host 'Installing project dependencies...'
    Invoke-Checked $venvPython @('-m','pip','install','-r','requirements.txt')
    Set-Content -LiteralPath $stampPath -Value $requirementsHash -Encoding ASCII
}
if ($Rebuild -or -not (Test-Path -LiteralPath 'frontend\dist\index.html')) {
    Write-Host 'Building local interface...'
    $bundledPnpm = Join-Path $runtimeRoot 'bin\fallback\pnpm.cmd'
    if (Test-Path -LiteralPath $bundledPnpm) { $packageManager = $bundledPnpm }
    elseif (Get-Command pnpm -ErrorAction SilentlyContinue) { $packageManager = (Get-Command pnpm).Source }
    elseif (Get-Command npm -ErrorAction SilentlyContinue) { $packageManager = (Get-Command npm).Source }
    else { throw 'Node.js 20.19+ and npm/pnpm are required to build the interface.' }
    Push-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
    try {
        Invoke-Checked $packageManager @('install')
        Invoke-Checked $packageManager @('run','build')
    } finally { Pop-Location }
}
$runArgs = @('run.py','--port',"$Port")
if ($NoBrowser) { $runArgs += '--no-browser' }
Invoke-Checked $venvPython $runArgs
