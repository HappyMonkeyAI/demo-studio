<#
.SYNOPSIS
  demo-studio local setup for Windows (Python venv, package, Playwright, ffmpeg).
.PARAMETER Yes
  Accept install prompts without asking.
.PARAMETER SkipFfmpeg
  Do not install ffmpeg if missing.
.PARAMETER SkipPlaywright
  Skip Playwright Chromium browser download.
#>
[CmdletBinding()]
param(
    [Alias('y')]
    [switch]$Yes,
    [switch]$SkipFfmpeg,
    [switch]$SkipPlaywright
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

function Write-Ok([string]$Message) { Write-Host "  [ok]   $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "  [warn] $Message" -ForegroundColor Yellow }
function Write-Fail([string]$Message) { Write-Host "  [fail] $Message" -ForegroundColor Red }
function Write-Info([string]$Message) { Write-Host "  [..]   $Message" -ForegroundColor Gray }

function Test-Interactive {
    try {
        return [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
    } catch {
        return $false
    }
}

function Confirm-Install([string]$Prompt) {
    if ($Yes) { return $true }
    if (-not (Test-Interactive)) { return $false }
    $reply = Read-Host "  Install? $Prompt [y/N]"
    return ($reply -match '^[Yy]$')
}

function Get-PythonVersionString([string]$Exe) {
    try {
        $out = & $Exe -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        return ($out | Select-Object -First 1).ToString().Trim()
    } catch {
        return $null
    }
}

function Test-PythonOk([string]$Exe) {
    $ver = Get-PythonVersionString $Exe
    if (-not $ver) { return $false }
    $parts = $ver.Split('.')
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    return ($major -gt 3) -or ($major -eq 3 -and $minor -ge 11)
}

function Find-Python {
    foreach ($name in @('python3.13', 'python3.12', 'python3.11', 'python3', 'python', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $exe = $cmd.Source
        if ($name -eq 'py') {
            # Prefer the launcher's 3.12/3.11 if available
            foreach ($arg in @('-3.13', '-3.12', '-3.11', '-3')) {
                try {
                    $probe = & $exe $arg -c 'import sys; print(sys.executable)' 2>$null
                    if ($LASTEXITCODE -eq 0 -and $probe) {
                        $candidate = ($probe | Select-Object -First 1).ToString().Trim()
                        if (Test-PythonOk $candidate) { return $candidate }
                    }
                } catch { }
            }
            continue
        }
        if (Test-PythonOk $exe) { return $exe }
    }
    return $null
}

function Install-PythonOffer {
    Write-Fail 'Python >= 3.11 not found on PATH'
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget -and (Confirm-Install 'winget install Python.Python.3.12')) {
        & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        return
    }
    Write-Warn 'Install Python 3.11+ from https://www.python.org/downloads/ (tick "Add to PATH"), then re-run.'
}

function Install-FfmpegOffer {
    Write-Fail 'ffmpeg not on PATH (needed for mux / package)'
    if ($SkipFfmpeg) {
        Write-Warn 'Skipping ffmpeg (-SkipFfmpeg)'
        return
    }
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget -and (Confirm-Install 'winget install Gyan.FFmpeg')) {
        & winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
        return
    }
    $choco = Get-Command choco -ErrorAction SilentlyContinue
    if ($choco -and (Confirm-Install 'choco install ffmpeg')) {
        & choco install ffmpeg -y
        return
    }
    Write-Warn 'Install ffmpeg manually: https://ffmpeg.org/download.html (or winget install Gyan.FFmpeg)'
}

function Invoke-Native([string]$FilePath, [string[]]$ArgumentList) {
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($ArgumentList -join ' ')"
    }
}

Write-Host '=== demo-studio install ===' -ForegroundColor Cyan
Write-Host "Root: $Root"
Write-Host ''

Write-Host '1) Python'
$Python = Find-Python
if (-not $Python) {
    Install-PythonOffer
    $Python = Find-Python
    if (-not $Python) {
        Write-Fail 'Still no Python >= 3.11'
        exit 1
    }
}
Write-Ok "$Python $(Get-PythonVersionString $Python)"

Write-Host ''
Write-Host '2) Virtualenv (.venv)'
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $VenvPython) {
    Write-Ok '.venv already present'
} else {
    Write-Info 'Creating .venv'
    Invoke-Native $Python @('-m', 'venv', '.venv')
    Write-Ok 'Created .venv'
}
Write-Ok "Using $VenvPython ($(Get-PythonVersionString $VenvPython))"

Write-Host ''
Write-Host '3) Package (editable + capture extras)'
Write-Info 'pip install -e ".[dev,capture]"'
Invoke-Native $VenvPython @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-Native $VenvPython @('-m', 'pip', 'install', '-e', '.[dev,capture]')
Write-Ok 'demo-studio installed in venv'

Write-Host ''
Write-Host '4) Playwright Chromium'
if ($SkipPlaywright) {
    Write-Warn 'Skipping Playwright Chromium (-SkipPlaywright)'
} elseif (Confirm-Install 'playwright install chromium (required for --engine playwright)') {
    Invoke-Native $VenvPython @('-m', 'playwright', 'install', 'chromium')
    Write-Ok 'Chromium ready'
} else {
    Write-Warn 'Skipped — run later: .\.venv\Scripts\python.exe -m playwright install chromium'
}

Write-Host ''
Write-Host '5) ffmpeg'
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    $ver = (& ffmpeg -version 2>&1 | Select-Object -First 1)
    Write-Ok $ver
} else {
    Install-FfmpegOffer
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpeg) {
        $ver = (& ffmpeg -version 2>&1 | Select-Object -First 1)
        Write-Ok $ver
    } else {
        Write-Warn 'ffmpeg still missing — open a new shell after install, or add it to PATH'
    }
}

Write-Host ''
Write-Host '6) TTS sidecars (optional; not auto-installed)'
Write-Info 'Pocket TTS  → POCKET_TTS_URL  (default http://127.0.0.1:8000)'
Write-Info 'Piper TTS   → PIPER_TTS_URL   (default http://127.0.0.1:8010) + DEMO_TTS_PROVIDER=piper'
Write-Warn 'Start a TTS sidecar separately before narrate.'

Write-Host ''
Write-Host '7) Doctor'
$DemoStudio = Join-Path $Root '.venv\Scripts\demo-studio.exe'
try {
    if (Test-Path -LiteralPath $DemoStudio) {
        & $DemoStudio doctor
    } else {
        & $VenvPython -m demo_studio.cli doctor
    }
} catch {
    Write-Warn "doctor reported issues: $_"
}

Write-Host ''
Write-Host '=== Done ===' -ForegroundColor Cyan
Write-Host 'Activate:  .\.venv\Scripts\Activate.ps1'
Write-Host 'Smoke:     demo-studio doctor'
Write-Host 'Capture:   $env:DEMO_BASE_URL="https://alongfor.happymonkey.ai"'
Write-Host '           demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright'
