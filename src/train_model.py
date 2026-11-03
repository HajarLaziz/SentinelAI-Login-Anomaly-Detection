"""Unsupervised training on all historical rows, never filtered by labels."""
import argparse
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from src.preprocessing import feature_matrix, FEATURES
from src.utils import DATA, MODEL, SEED, ensure_directories

def train(frame: pd.DataFrame, path=MODEL, contamination=.08, n_estimators=200):
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
        ('forest', IsolationForest(n_estimators=n_estimators, contamination=contamination,
                                   max_samples=256, random_state=SEED, n_jobs=1))])
    matrix = feature_matrix(frame)
    pipeline.fit(matrix)
    bundle = dict(pipeline=pipeline, features=FEATURES, contamination=contamination,
                  n_estimators=n_estimators, training_rows=len(frame),
                  train_end=str(pd.to_datetime(frame.timestamp).max()),
                  reference_scores=np.sort(-pipeline.decision_function(matrix)))
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return bundle

def main():
    from src.generate_data import main as generate
    ensure_directories()
    generate()
    bundle = train(pd.read_csv(DATA / 'train_logs.csv'))
    print(f'Modèle enregistré : {MODEL}; {bundle["training_rows"]} événements historiques.')

if __name__ == '__main__':
    main()
