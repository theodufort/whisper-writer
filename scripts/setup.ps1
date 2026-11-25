<#
One-step setup: builds the GPU (Vulkan) pywhispercpp wheel if it is missing, then runs `uv sync`.
The wheel is not committed (vendor/*.whl is git-ignored); pyproject.toml points at it.

Usage:  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#>
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
if (-not (Get-ChildItem (Join-Path $repo "vendor") -Filter "pywhispercpp-*.whl" -ErrorAction SilentlyContinue)) {
    Write-Host "GPU wheel not found - building it (first time only, ~5-10 min)..."
    & (Join-Path $PSScriptRoot "build_pywhispercpp_vulkan.ps1")
}
Set-Location $repo
uv sync
