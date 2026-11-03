from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
MODEL = ROOT / 'models' / 'isolation_forest.joblib'
ARTIFACTS = ROOT / 'artifacts'
SEED = 42

def ensure_directories():
    for path in (DATA, MODEL.parent, ARTIFACTS):
        path.mkdir(parents=True, exist_ok=True)
