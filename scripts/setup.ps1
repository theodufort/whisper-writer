<#
.SYNOPSIS
  One-step install: builds the GPU wheels if needed, then installs everything with `uv sync`.

.DESCRIPTION
  Run this once after cloning (and again after pulling changes that touch dependencies).
    1. checks the build prerequisites (uv, Visual Studio C++ tools, Vulkan SDK),
    2. compiles the Vulkan versions of whisper.cpp and llama.cpp into .\vendor (first time only, ~10 min),
    3. runs `uv sync` to create .venv with Python and all dependencies.
  Afterwards start the app with:  uv run python src/main.py

.PARAMETER InstallPrerequisites
  Install any missing prerequisite with winget (asks Windows for permission where needed).
.PARAMETER Rebuild
  Rebuild the GPU wheels even if they already exist (e.g. after a Python upgrade).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -InstallPrerequisites
#>
param(
    [switch]$InstallPrerequisites,
    [switch]$Rebuild
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"
Set-Location $script:RepoRoot

if ($env:OS -ne "Windows_NT") {
    Write-Host "Not Windows: no custom GPU build is needed. Running plain 'uv sync'." -ForegroundColor Yellow
    uv sync
    exit $LASTEXITCODE
}

$vendor = Join-Path $script:RepoRoot "vendor"
$haveWhisper = [bool](Get-ChildItem $vendor -Filter "pywhispercpp-*.whl" -ErrorAction SilentlyContinue)
$haveLlama = [bool](Get-ChildItem $vendor -Filter "llama_cpp_python-*.whl" -ErrorAction SilentlyContinue)
$needBuild = $Rebuild -or -not ($haveWhisper -and $haveLlama)

if ($needBuild) {
    Assert-Prerequisites -Install:$InstallPrerequisites
    if ($Rebuild -or -not $haveWhisper) {
        Write-Host "`n[1/3] Building the GPU version of whisper.cpp (first time only) ..." -ForegroundColor Cyan
        & (Join-Path $PSScriptRoot "build_pywhispercpp_vulkan.ps1")
    }
    if ($Rebuild -or -not $haveLlama) {
        Write-Host "`n[2/3] Building the GPU version of llama.cpp (first time only) ..." -ForegroundColor Cyan
        & (Join-Path $PSScriptRoot "build_llama_cpp_vulkan.ps1")
    }
} else {
    Write-Host "GPU wheels already built in .\vendor (use -Rebuild to rebuild them)." -ForegroundColor Green
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Assert-Prerequisites -Install:$InstallPrerequisites }
}

Write-Host "`n[3/3] Installing Python and dependencies (uv sync) ..." -ForegroundColor Cyan
uv sync
if ($LASTEXITCODE -ne 0) { throw "uv sync failed." }

Write-Host "`nDone." -ForegroundColor Green
Write-Host "  Start the app:        uv run python src/main.py"
Write-Host "  Check the GPU:        uv run python scripts/check_gpu.py"
Write-Host "  Build the .exe:       powershell -ExecutionPolicy Bypass -File scripts\build.ps1"
Write-Host "The first dictation downloads the Whisper model (a few hundred MB); it is cached afterwards."
