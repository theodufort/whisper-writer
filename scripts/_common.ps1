# Shared helpers for the build scripts in this folder. Dot-source it:  . "$PSScriptRoot\_common.ps1"
# Nothing here is specific to one machine: tools are discovered, never hard-coded.

$script:RepoRoot = Split-Path $PSScriptRoot -Parent

function Get-PythonVersion {
    # The wheels must match the project's Python. Use the major.minor from .python-version.
    $file = Join-Path $script:RepoRoot ".python-version"
    if (Test-Path $file) {
        $m = [regex]::Match((Get-Content $file -Raw), "^\s*(\d+\.\d+)")
        if ($m.Success) { return $m.Groups[1].Value }
    }
    return "3.13"
}

function Find-VulkanSdk {
    # Returns the Vulkan SDK folder (the one containing Bin\glslc.exe), or $null.
    $candidates = @(
        $env:VULKAN_SDK,
        [Environment]::GetEnvironmentVariable("VULKAN_SDK", "User"),
        [Environment]::GetEnvironmentVariable("VULKAN_SDK", "Machine"),
        (Join-Path $env:USERPROFILE "scoop\apps\vulkan\current")
    )
    $default = Join-Path $env:SystemDrive "VulkanSDK"   # where the official installer puts it
    if (Test-Path $default) {
        $candidates += Get-ChildItem $default -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | ForEach-Object FullName
    }
    $glslc = Get-Command glslc -ErrorAction SilentlyContinue
    if ($glslc) { $candidates += (Split-Path (Split-Path $glslc.Source -Parent) -Parent) }
    foreach ($c in $candidates) {
        if ($c -and (Test-Path (Join-Path $c "Bin\glslc.exe"))) { return $c }
    }
    return $null
}

function Find-VcVars {
    # Returns the path of vcvars64.bat from any Visual Studio / Build Tools with the C++ workload, or $null.
    foreach ($pf in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
        if (-not $pf) { continue }
        $vswhere = Join-Path $pf "Microsoft Visual Studio\Installer\vswhere.exe"
        if (-not (Test-Path $vswhere)) { continue }
        $root = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath
        if ($root) {
            $vcvars = Join-Path $root "VC\Auxiliary\Build\vcvars64.bat"
            if (Test-Path $vcvars) { return $vcvars }
        }
    }
    return $null
}

function Get-MissingPrerequisites {
    # Everything needed to COMPILE the GPU wheels. Each item: Name, Why, Command (how to install it).
    $missing = @()
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        $missing += [pscustomobject]@{ Name = "uv"; Why = "installs Python and the dependencies"
            Command = "winget install --id astral-sh.uv -e" }
    }
    if (-not (Find-VcVars)) {
        $missing += [pscustomobject]@{ Name = "Visual Studio C++ build tools"; Why = "compiles whisper.cpp / llama.cpp"
            Command = 'winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"' }
    }
    if (-not (Find-VulkanSdk)) {
        $missing += [pscustomobject]@{ Name = "Vulkan SDK"; Why = "provides glslc, the GPU shader compiler"
            Command = "winget install --id KhronosGroup.VulkanSDK -e" }
    }
    return $missing
}

function Assert-Prerequisites {
    param([switch]$Install)
    $missing = @(Get-MissingPrerequisites)
    if ($missing.Count -eq 0) { return }
    if ($Install) {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            throw "winget is not available; install the missing tools manually (see below).`n" +
                  (($missing | ForEach-Object { "  - $($_.Name): $($_.Command)" }) -join "`n")
        }
        foreach ($m in $missing) {
            Write-Host "Installing $($m.Name) ..." -ForegroundColor Cyan
            Invoke-Expression $m.Command
        }
        $missing = @(Get-MissingPrerequisites)   # re-detect (no shell restart needed)
        if ($missing.Count -eq 0) { return }
    }
    $lines = $missing | ForEach-Object { "  - $($_.Name) ($($_.Why)):`n      $($_.Command)" }
    throw "Missing prerequisites:`n$($lines -join "`n")`n`nInstall them (or re-run with -InstallPrerequisites), then run this script again."
}

function Get-WorkDir {
    # The Vulkan shader sub-build creates paths close to Windows' 260-character limit, so the build
    # must happen in a SHORT folder. Default: <system drive>\ww-build\<name> (for example C:\ww-build\whisper).
    param([string]$Name, [string]$Override)
    if ($Override) { return $Override }
    return (Join-Path (Join-Path $env:SystemDrive "ww-build") $Name)
}

function Get-PyPiSource {
    # Downloads an sdist from PyPI, verifies its SHA-256 and unpacks it to <Work>\src. Returns that path.
    param([string]$Package, [string]$Version, [string]$Work)
    $meta = Invoke-RestMethod "https://pypi.org/pypi/$Package/$Version/json"
    $sdist = $meta.urls | Where-Object packagetype -eq "sdist" | Select-Object -First 1
    if (-not $sdist) { throw "PyPI has no source distribution for $Package $Version." }
    Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $Work | Out-Null
    $archive = Join-Path $Work $sdist.filename
    Write-Host "Downloading $($sdist.filename) ..."
    Invoke-WebRequest $sdist.url -OutFile $archive
    if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLower() -ne $sdist.digests.sha256) {
        throw "SHA-256 mismatch for $($sdist.filename); refusing to build it."
    }
    # Windows' own tar.exe: a "tar" from Git Bash would read "C:" as a remote host.
    & (Join-Path $env:SystemRoot "System32\tar.exe") -xzf $archive -C $Work
    $unpacked = Get-ChildItem $Work -Directory | Select-Object -First 1
    Rename-Item $unpacked.FullName "src"
    return (Join-Path $Work "src")
}

function Invoke-VulkanWheelBuild {
    # Builds a wheel from an unpacked source folder with Vulkan enabled, using the Ninja generator and
    # the Visual Studio compiler. Output goes to <repo>\vendor.
    param([string]$Source, [string]$Work, [string]$CmakeArgs = "", [hashtable]$ExtraEnv = @{})
    $vulkan = Find-VulkanSdk
    $vcvars = Find-VcVars
    $vendor = Join-Path $script:RepoRoot "vendor"
    New-Item -ItemType Directory -Force $vendor, (Join-Path $Work "t"), (Join-Path $Work "c") | Out-Null
    $extra = ($ExtraEnv.GetEnumerator() | ForEach-Object { "&& set `"$($_.Key)=$($_.Value)`"" }) -join ""
    # NB: cmd expands %PATH% for the whole line up front, so PATH must be set BEFORE vcvars runs (vcvars
    # then puts the MSVC compiler first; otherwise CMake can pick up a MinGW gcc found on PATH).
    $cmd = "set TEMP=$Work\t&& set TMP=$Work\t&& set UV_CACHE_DIR=$Work\c" +
           "&& set VK_SDK_PATH=$vulkan&& set VULKAN_SDK=$vulkan&& set CMAKE_GENERATOR=Ninja" +
           "&& set `"CMAKE_ARGS=$CmakeArgs`" $extra" +
           "&& set PATH=$vulkan\Bin;%PATH%&& call `"$vcvars`" >nul" +
           "&& uv build --wheel --python $(Get-PythonVersion) --out-dir `"$vendor`" `"$Source`""
    cmd /c $cmd
    if ($LASTEXITCODE -ne 0) { throw "Building the wheel failed (see the output above)." }
    Remove-Item (Join-Path $vendor ".gitignore") -ErrorAction SilentlyContinue  # `uv build` adds one that would hide the wheel
}
