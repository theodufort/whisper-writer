<#
.SYNOPSIS
  Builds a Vulkan-enabled llama-cpp-python wheel (llama.cpp for AMD / NVIDIA / Intel GPUs) into vendor\.

.DESCRIPTION
  Used by the optional transcript-cleanup LLM. PyPI only ships CPU-only Windows wheels, so the GPU build
  is compiled locally. scripts\setup.ps1 runs this for you; run it directly only to rebuild or upgrade.
  See docs\gpu-acceleration.md.

.PARAMETER Version   llama-cpp-python version to build (default 0.3.38).
.PARAMETER Work      Scratch folder. Keep it SHORT (default <system drive>\ww-build\llama).
#>
param(
    [string]$Version = "0.3.38",
    [string]$Work = ""
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"
Assert-Prerequisites

$Work = Get-WorkDir -Name "llama" -Override $Work
$src = Get-PyPiSource -Package "llama-cpp-python" -Version $Version -Work $Work

$vendor = Join-Path $script:RepoRoot "vendor"
New-Item -ItemType Directory -Force $vendor | Out-Null
Get-ChildItem $vendor -Filter "llama_cpp_python-*.whl" | Remove-Item

# GGML_NATIVE=off + explicit AVX2: the CPU parts must run on any modern PC, not only on the build machine.
$cmake = "-DGGML_VULKAN=on -DGGML_NATIVE=off -DGGML_AVX2=on -DGGML_FMA=on -DGGML_F16C=on " +
         "-DLLAMA_BUILD_EXAMPLES=off -DLLAMA_BUILD_TESTS=off -DLLAMA_BUILD_SERVER=off"
# SKBUILD_BUILD_DIR keeps scikit-build-core's build tree in the short work folder too.
Invoke-VulkanWheelBuild -Source $src -Work $Work -CmakeArgs $cmake -ExtraEnv @{ SKBUILD_BUILD_DIR = "$Work\b" }

Get-ChildItem $vendor -Filter "llama_cpp_python-*.whl" | ForEach-Object { Write-Host "Built: $($_.FullName)" -ForegroundColor Green }
