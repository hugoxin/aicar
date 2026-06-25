$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MainScript = Join-Path $ProjectRoot "src\aicar_sim\main.py"
python $MainScript

