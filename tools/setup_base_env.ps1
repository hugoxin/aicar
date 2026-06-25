# Run manually when you are ready to install scaffold dependencies.

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

python -m pip install -r .\aicar_sim\requirements.txt
python -m pip install -r .\vehicle_type_lab\requirements.txt
