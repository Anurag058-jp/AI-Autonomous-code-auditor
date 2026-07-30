param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$outputRoot = Join-Path $projectRoot "outputs\windows"
$workRoot = Join-Path $projectRoot "work\pyinstaller"

if (-not (Test-Path $python)) {
    throw "Create the project virtual environment first: python -m venv .venv"
}

Push-Location $projectRoot
try {
    if (-not $SkipTests) {
        & $python -m pytest -q --basetemp work\pytest-packaging -p no:cacheprovider
        if ($LASTEXITCODE -ne 0) { throw "Tests failed; Windows bundles were not created." }
    }

    & $python -m PyInstaller --noconfirm --clean --windowed --name "AI-Code-Auditor" `
        --paths src --distpath $outputRoot --workpath $workRoot --specpath $workRoot `
        --collect-all streamlit --collect-all chromadb --collect-all tree_sitter_language_pack `
        --collect-all tree_sitter --add-data "$projectRoot\src\auditor\dashboard.py;auditor" `
        --hidden-import=auditor.dashboard --hidden-import=auditor.service `
        --hidden-import=watchdog.observers.winapi `
        src/auditor/desktop.py
    if ($LASTEXITCODE -ne 0) { throw "Desktop bundle build failed." }

    & $python -m PyInstaller --noconfirm --clean --console --name "audit" `
        --paths src --distpath $outputRoot --workpath $workRoot --specpath $workRoot `
        --collect-all chromadb --collect-all tree_sitter_language_pack --collect-all tree_sitter `
        --exclude-module streamlit --hidden-import=watchdog.observers.winapi `
        src/auditor/cli_entry.py
    if ($LASTEXITCODE -ne 0) { throw "CLI bundle build failed." }

    Write-Host "Bundles created in $outputRoot"
    Write-Host "Compile packaging\installer.iss with Inno Setup to create the installer."
}
finally {
    Pop-Location
}
