param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$entryPoint = Join-Path $repoRoot "src\local_tool_manager\main.py"
$distDirectory = Join-Path $repoRoot "dist"
$workDirectory = Join-Path $repoRoot "build\pyinstaller"
$specDirectory = Join-Path $repoRoot "build"

Push-Location $repoRoot
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name LocalToolManager `
        --paths (Join-Path $repoRoot "src") `
        --distpath $distDirectory `
        --workpath $workDirectory `
        --specpath $specDirectory `
        $entryPoint

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstallerのビルドに失敗しました。"
    }
} finally {
    Pop-Location
}

$executable = Join-Path $distDirectory "LocalToolManager.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "ビルド済みexeが見つかりません: $executable"
}

Write-Output "ビルド完了: $executable"
