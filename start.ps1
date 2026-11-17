$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Création de l’environnement impossible.' }
}
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation impossible.' }
if (-not (Test-Path 'data/lanl/auth_selected.csv')) {
    & $python -m src.import_lanl
    if ($LASTEXITCODE -ne 0) { throw 'Import LANL impossible.' }
}
if (-not (Test-Path 'models/lanl_isolation_forest.joblib') -or -not (Test-Path 'data/lanl/login_logs.csv')) {
    & $python -m src.lanl
    if ($LASTEXITCODE -ne 0) { throw 'Preparation impossible.' }
}
& $python -m streamlit run app.py --server.address 127.0.0.1
