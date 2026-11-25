<#
.SYNOPSIS
  Builds the standalone app (dist\whisper-writer\whisper-writer.exe), keeping your settings.

.DESCRIPTION
  Runs PyInstaller into a staging folder and then mirrors the result over dist\whisper-writer, replacing
  the exe and _internal\ but KEEPING the existing config.yaml and *.log there (PyInstaller alone wipes
  its output folder, config included). The GPU libraries are bundled, so the exe uses the GPU on any PC
  with a Vulkan-capable graphics driver; no Python or Visual C++ redistributable is needed there.

  Prerequisite: run scripts\setup.ps1 once (it installs the environment and builds the GPU wheels).
  Close the app first: a running exe cannot be replaced.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\build.ps1
#>
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$stage = Join-Path $repo "build\stage"
$target = Join-Path $repo "dist\whisper-writer"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found. Run scripts\setup.ps1 -InstallPrerequisites first."
}
if (-not (Test-Path (Join-Path $repo ".venv"))) {
    throw "No .venv yet. Run scripts\setup.ps1 first."
}

$running = Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath -like "$target\*" }
if ($running) { throw "whisper-writer is running from $target - exit it first (tray icon > Exit), then rebuild." }

Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
uv run pyinstaller whisper-writer.spec --noconfirm --distpath $stage --workpath (Join-Path $repo "build\work")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (see above). If it mentions Vulkan DLLs, run scripts\setup.ps1 first." }

# Mirror the new build over the target, but never delete/overwrite the user's config and logs.
robocopy (Join-Path $stage "whisper-writer") $target /MIR /XF config.yaml *.log /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Copy to $target failed (robocopy exit $LASTEXITCODE)." }

if (Test-Path (Join-Path $target "config.yaml")) { Write-Host "Kept existing config.yaml" }
else { Write-Host "No config.yaml in $target yet: it is created when you save settings in the app." }
Write-Host "Built: $target\whisper-writer.exe" -ForegroundColor Green
$global:LASTEXITCODE = 0
