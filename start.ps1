$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Création de l’environnement impossible.' }
}
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation impossible.' }
& $python -m src.generate_data
if ($LASTEXITCODE -ne 0) { throw 'Génération impossible.' }
if (-not (Test-Path 'models/isolation_forest.joblib')) {
    & $python -m src.train_model
    if ($LASTEXITCODE -ne 0) { throw 'Entraînement impossible.' }
}
& $python -m src.evaluate_model
if ($LASTEXITCODE -ne 0) { throw 'Évaluation impossible.' }
& $python -m streamlit run app.py --server.address 127.0.0.1
