<#
.SYNOPSIS
  One-shot validate → capture → narrate → package for a demo pack.
.EXAMPLE
  .\scripts\run-demo.ps1 alongfor
  .\scripts\run-demo.ps1 mrpg-realms -Provider piper
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Pack,

    [string]$BaseUrl,
    [ValidateSet('pocket', 'piper')]
    [string]$Provider = $(if ($env:DEMO_TTS_PROVIDER) { $env:DEMO_TTS_PROVIDER } else { 'pocket' }),
    [ValidateSet('playwright', 'chrome', 'auto')]
    [string]$Engine = 'playwright',
    [string]$Title,
    [string]$Subtitle,
    [string]$RunDir
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Root

$VenvActivate = Join-Path $Root '.venv\Scripts\Activate.ps1'
if (Test-Path -LiteralPath $VenvActivate) {
    . $VenvActivate
}

if (-not (Get-Command demo-studio -ErrorAction SilentlyContinue)) {
    throw 'demo-studio not on PATH. Run .\install.ps1 and activate .venv'
}

$Beats = $null
$PackName = $Pack

switch -Regex ($Pack) {
    '^(alongfor)$' {
        $Beats = 'demos/alongfor/demo.beats.json'
        if (-not $BaseUrl) { $BaseUrl = if ($env:DEMO_BASE_URL) { $env:DEMO_BASE_URL } else { 'https://alongfor.happymonkey.ai' } }
        if (-not $Title) { $Title = 'AlongFor' }
        if (-not $Subtitle) { $Subtitle = 'event companion' }
    }
    '^(mrpg-realms|realms)$' {
        $PackName = 'mrpg-realms'
        $Beats = 'demos/mrpg-realms/demo.beats.json'
        if (-not $BaseUrl) { $BaseUrl = if ($env:DEMO_BASE_URL) { $env:DEMO_BASE_URL } else { 'https://realms.happymonkey.ai' } }
        if (-not $Title) { $Title = 'MRPG Realms' }
        if (-not $Subtitle) { $Subtitle = 'voxel multiplayer · wiki' }
    }
    '^(astro-cms)$' {
        $Beats = 'demos/astro-cms/demo.beats.json'
        if (-not $BaseUrl) { $BaseUrl = $env:DEMO_BASE_URL }
        if (-not $BaseUrl) { throw 'astro-cms needs -BaseUrl or DEMO_BASE_URL (throwaway EmDash only)' }
        if (-not $Title) { $Title = 'Astro CMS' }
        if (-not $Subtitle) { $Subtitle = 'throwaway EmDash walkthrough' }
    }
    '^(example-static)$' {
        $Beats = 'demos/example-static/demo.beats.json'
        if (-not $BaseUrl) { $BaseUrl = $env:DEMO_BASE_URL }
        if (-not $BaseUrl) { throw 'example-static needs -BaseUrl or DEMO_BASE_URL' }
        if (-not $Title) { $Title = 'Example' }
        if (-not $Subtitle) { $Subtitle = 'static fixture' }
    }
    default {
        if (Test-Path -LiteralPath $Pack) {
            $Beats = $Pack
            $PackName = Split-Path -Leaf (Split-Path -Parent $Pack)
            if (-not $BaseUrl) { $BaseUrl = $env:DEMO_BASE_URL }
            if (-not $BaseUrl) { throw 'set DEMO_BASE_URL or pass -BaseUrl' }
        } elseif (Test-Path -LiteralPath "demos/$Pack/demo.beats.json") {
            $Beats = "demos/$Pack/demo.beats.json"
            if (-not $BaseUrl) { $BaseUrl = $env:DEMO_BASE_URL }
            if (-not $BaseUrl) { throw "set DEMO_BASE_URL or pass -BaseUrl for pack '$Pack'" }
        } else {
            throw "unknown pack or beats file: $Pack"
        }
    }
}

$env:DEMO_BASE_URL = $BaseUrl
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
if (-not $RunDir) { $RunDir = "outputs/${PackName}-${Stamp}" }

Write-Host '=== demo-studio run-demo ===' -ForegroundColor Cyan
Write-Host "beats:    $Beats"
Write-Host "base_url: $env:DEMO_BASE_URL"
Write-Host "provider: $Provider"
Write-Host "engine:   $Engine"
Write-Host "run_dir:  $RunDir"
Write-Host ''

demo-studio validate $Beats
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
demo-studio capture $Beats --run-dir $RunDir --engine $Engine
demo-studio narrate $Beats $RunDir --provider $Provider

$pkgArgs = @($RunDir)
if ($Title) { $pkgArgs += @('--title-card', $Title) }
if ($Subtitle) { $pkgArgs += @('--subtitle', $Subtitle) }
demo-studio package @pkgArgs

Write-Host ''
Write-Host '=== Done ===' -ForegroundColor Cyan
Write-Host "Review:  $RunDir/review.html"
Write-Host "Video:   $RunDir/demo.mp4"
