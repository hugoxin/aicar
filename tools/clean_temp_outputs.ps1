$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$OutputDirs = @(
    Join-Path $WorkspaceRoot "aicar_sim\outputs",
    Join-Path $WorkspaceRoot "vehicle_type_lab\outputs\predictions",
    Join-Path $WorkspaceRoot "vehicle_type_lab\outputs\reports"
)

foreach ($Dir in $OutputDirs) {
    if (Test-Path $Dir) {
        Get-ChildItem -Path $Dir -File -Exclude ".gitkeep" | Remove-Item -Force
    }
}

Write-Host "Temporary scaffold outputs cleaned."

