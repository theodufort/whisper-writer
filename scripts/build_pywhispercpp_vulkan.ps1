<#
.SYNOPSIS
  Builds a Vulkan-enabled pywhispercpp wheel (whisper.cpp for AMD / NVIDIA / Intel GPUs) into vendor\.

.DESCRIPTION
  PyPI only ships CPU-only Windows wheels, so the GPU build is compiled locally. scripts\setup.ps1 runs
  this for you; run it directly only to rebuild or upgrade. Needs the Visual Studio C++ tools and the
  Vulkan SDK (setup.ps1 -InstallPrerequisites installs them). See docs\gpu-acceleration.md.

.PARAMETER Version   pywhispercpp version to build (default 1.5.1).
.PARAMETER Work      Scratch folder. Keep it SHORT (default <system drive>\ww-build\whisper).
#>
param(
    [string]$Version = "1.5.1",
    [string]$Work = ""
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"
Assert-Prerequisites

$Work = Get-WorkDir -Name "whisper" -Override $Work
$src = Get-PyPiSource -Package "pywhispercpp" -Version $Version -Work $Work

# Patch: with the Ninja generator the DLLs land in bin\ instead of bin\Release\, which the packaging step expects.
$setup = Join-Path $src "setup.py"
$text = Get-Content $setup -Raw
$needle = "dll_folder = os.path.join(self.build_temp, '_pywhispercpp', 'bin', cfg)"
if (-not $text.Contains($needle)) { throw "pywhispercpp $Version has a different setup.py than expected; try -Version 1.5.1." }
$text = $text.Replace($needle, $needle + "`n        if not os.path.isdir(dll_folder):`n            dll_folder = os.path.join(self.build_temp, '_pywhispercpp', 'bin')")
Set-Content $setup $text -NoNewline

$vendor = Join-Path $script:RepoRoot "vendor"
New-Item -ItemType Directory -Force $vendor | Out-Null
Get-ChildItem $vendor -Filter "pywhispercpp-*.whl" | Remove-Item

Invoke-VulkanWheelBuild -Source $src -Work $Work -ExtraEnv @{ GGML_VULKAN = "1" }

Get-ChildItem $vendor -Filter "pywhispercpp-*.whl" | ForEach-Object { Write-Host "Built: $($_.FullName)" -ForegroundColor Green }
