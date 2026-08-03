param(
    [string]$ExecutablePath,
    [string]$ShortcutPath
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ExecutablePath) {
    $ExecutablePath = Join-Path $repoRoot "dist\LocalToolManager.exe"
}
if (-not $ShortcutPath) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $desktop "Local Tool Manager.lnk"
}

$resolvedExecutable = (Resolve-Path -LiteralPath $ExecutablePath).Path
$shortcutDirectory = Split-Path -Parent $ShortcutPath
if (-not (Test-Path -LiteralPath $shortcutDirectory -PathType Container)) {
    throw "ショートカットの保存先が見つかりません: $shortcutDirectory"
}

$shell = New-Object -ComObject WScript.Shell
try {
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $resolvedExecutable
    $shortcut.WorkingDirectory = Split-Path -Parent $resolvedExecutable
    $shortcut.IconLocation = "$resolvedExecutable,0"
    $shortcut.Description = "Local Tool Managerを起動"
    $shortcut.Save()
} finally {
    if ($shortcut) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut)
    }
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell)
}

Write-Output "ショートカット作成完了: $ShortcutPath"
