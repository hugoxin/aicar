$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MainScript = Join-Path $ProjectRoot "src\vehicle_type_lab\main.py"
python $MainScript

