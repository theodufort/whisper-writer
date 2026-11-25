<#
Builds a Vulkan-enabled pywhispercpp wheel (AMD / Intel / NVIDIA GPUs) into vendor\.

PyPI only ships CPU wheels, so the project pins to the wheel built here
(see [tool.uv.sources] in pyproject.toml). Re-run this only to upgrade pywhispercpp
or the Python version.

Prerequisites (one-time):
  - Visual Studio 2022 with the C++ workload
  - Vulkan SDK (provides glslc):  scoop install vulkan
  - uv

Usage:  powershell -ExecutionPolicy Bypass -File scripts\build_pywhispercpp_vulkan.ps1
#>
param(
    [string]$Version = "1.5.1",
    # Keep this path SHORT: the Vulkan shader sub-build exceeds Windows' 260-char path limit otherwise.
    [string]$Work = "C:\w"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$vendor = Join-Path $repo "vendor"

# --- locate prerequisites -------------------------------------------------
$vulkan = $env:VULKAN_SDK
if (-not $vulkan) { $vulkan = [Environment]::GetEnvironmentVariable("VULKAN_SDK", "User") }
if (-not $vulkan) { $vulkan = [Environment]::GetEnvironmentVariable("VULKAN_SDK", "Machine") }
if (-not $vulkan -or -not (Test-Path "$vulkan\Bin\glslc.exe")) {
    throw "Vulkan SDK not found (VULKAN_SDK\Bin\glslc.exe). Install it: scoop install vulkan"
}
$vsRoot = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsRoot) { throw "Visual Studio C++ build tools not found." }
$vcvars = Join-Path $vsRoot "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv not found." }

# --- fetch + verify sdist from PyPI ----------------------------------------
$meta = Invoke-RestMethod "https://pypi.org/pypi/pywhispercpp/$Version/json"
$sdist = $meta.urls | Where-Object packagetype -eq "sdist" | Select-Object -First 1
if (-not $sdist) { throw "No sdist for pywhispercpp $Version" }

Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$Work\t", "$Work\c" | Out-Null
$archive = Join-Path $Work $sdist.filename
Invoke-WebRequest $sdist.url -OutFile $archive
$hash = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLower()
if ($hash -ne $sdist.digests.sha256) { throw "SHA256 mismatch for $($sdist.filename)" }
tar -xzf $archive -C $Work
$src = Join-Path $Work "p"
Rename-Item (Join-Path $Work "pywhispercpp-$Version") $src

# --- patch: Ninja puts DLLs in bin\, MSBuild in bin\Release\ ---------------
$setup = Join-Path $src "setup.py"
$text = Get-Content $setup -Raw
$needle = "dll_folder = os.path.join(self.build_temp, '_pywhispercpp', 'bin', cfg)"
if (-not $text.Contains($needle)) { throw "setup.py layout changed; update this script's patch." }
$text = $text.Replace($needle, $needle + "`n        if not os.path.isdir(dll_folder):`n            dll_folder = os.path.join(self.build_temp, '_pywhispercpp', 'bin')")
Set-Content $setup $text -NoNewline

# --- build the wheel (Ninja avoids MSBuild's path-length failures) ----------
New-Item -ItemType Directory -Force $vendor | Out-Null
Get-ChildItem $vendor -Filter "pywhispercpp-*.whl" | Remove-Item
# NB: cmd expands %PATH% for the whole line up front, so PATH must be set BEFORE vcvars runs
# (vcvars then prepends the MSVC toolchain; otherwise CMake may pick a MinGW gcc).
$cmd = "set TEMP=$Work\t&& set TMP=$Work\t&& set UV_CACHE_DIR=$Work\c" +
       "&& set VK_SDK_PATH=$vulkan&& set VULKAN_SDK=$vulkan&& set GGML_VULKAN=1&& set CMAKE_GENERATOR=Ninja" +
       "&& set PATH=$vulkan\Bin;%PATH%&& call `"$vcvars`" >nul" +
       "&& uv build --wheel --python 3.13 --out-dir `"$vendor`" `"$src`""
cmd /c $cmd
if ($LASTEXITCODE -ne 0) { throw "Wheel build failed." }

Get-ChildItem $vendor -Filter "pywhispercpp-*.whl" | ForEach-Object { "Built: $($_.FullName)" }
Write-Host "Now point [tool.uv.sources] in pyproject.toml at that wheel and run: uv sync"
