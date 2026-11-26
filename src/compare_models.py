"""Select on day 1 only, then report the frozen candidate on day 2.

Run: python -m src.compare_models
The existing deployed model is deliberately not overwritten.
"""
import json
import joblib
import numpy as np
import pandas as pd
from src.context_model import ContextModel
from src.evaluate_model import metrics
from src.lanl import DATA, ROOT


def main():
    frame = pd.read_csv(DATA / 'login_logs.csv')
    train = frame[frame.time < 86400]
    validation = frame[(frame.time >= 86400) & (frame.time < 172800)]
    trials = []
    models = {}
    # Predeclared search; test annotations are not accessed during selection.
    for method in ['rarity', 'forest']:
        model = ContextModel(method).fit(train)
        scores = model.score(validation)
        models[method] = model
        for quantile in [.99, .995, .999, .9995]:
            threshold = float(np.quantile(scores, quantile))
            prediction = (scores > threshold).astype(int)
            trials.append(dict(method=method, quantile=quantile, threshold=threshold,
                               alerts=int(prediction.sum()),
                               metrics=metrics(validation.redteam_label, prediction, scores)))
    best = max(trials, key=lambda row: (row['metrics']['f1'],
                                       row['metrics']['recall'], -row['alerts']))
    model = models[best['method']]
    model.threshold = best['threshold']
    model.train_end = int(train.time.max())
    model.reference_scores = np.sort(model.score(train) - model.threshold)
    test = frame[frame.time >= 172800]
    report = dict(protocol='Reference J+0; selection J+1; evaluation J+2. Frozen reference. Max 1% validation alerts.',
                  caveat='Annotations partielles; J+2 deja utilise pour le modele historique, pas un nouveau test externe.',
                  reference_rows=len(train), validation_rows=len(validation), test_rows=len(test),
                  validation_annotations=int(validation.redteam_label.sum()),
                  test_annotations=int(test.redteam_label.sum()), trials=trials, selected=best,
                  test=metrics(test.redteam_label, model.predict(test), model.score(test)))
    destination = ROOT / 'models/lanl_context_candidate.joblib'
    joblib.dump(model, destination)
    reloaded = joblib.load(destination)
    assert np.array_equal(model.predict(test), reloaded.predict(test))
    (ROOT / 'docs/model_comparison.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
