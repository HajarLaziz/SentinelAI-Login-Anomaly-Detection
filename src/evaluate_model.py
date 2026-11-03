import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, precision_score, recall_score, f1_score,
                             accuracy_score, roc_auc_score, average_precision_score)
from src.preprocessing import feature_matrix
from src.utils import DATA, MODEL, ARTIFACTS, ensure_directories

def baseline(frame):
    return ((frame.failed_attempts >= 3) | (frame.attempts_10min >= 6) |
            ((frame.new_ip == 1) & (frame.login_hour < 6))).astype(int).to_numpy()

def metrics(y, prediction, scores=None):
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0,1]).ravel()
    result = dict(precision=float(precision_score(y,prediction,zero_division=0)),
                  recall=float(recall_score(y,prediction,zero_division=0)),
                  f1=float(f1_score(y,prediction,zero_division=0)),
                  accuracy=float(accuracy_score(y,prediction)),
                  false_positives=int(fp), false_negatives=int(fn),
                  false_positive_rate=float(fp/(tn+fp)) if tn+fp else None,
                  confusion_matrix=[[int(tn),int(fp)],[int(fn),int(tp)]])
    if scores is not None and len(np.unique(y)) == 2:
        result.update(roc_auc=float(roc_auc_score(y,scores)),
                      average_precision=float(average_precision_score(y,scores)))
    return result

def evaluate(frame, bundle):
    matrix = feature_matrix(frame)
    pipeline = bundle['pipeline']
    return {'Isolation Forest':metrics(frame.is_anomaly, (pipeline.predict(matrix)==-1).astype(int),
                                      -pipeline.decision_function(matrix)),
            'Règles':metrics(frame.is_anomaly, baseline(frame))}

def sensitivity(train_frame, test_frame, bundle):
    # Change the offset only: contamination does not change the learned trees.
    pipe = bundle['pipeline']
    train_scores = pipe.score_samples(feature_matrix(train_frame))
    test_scores = pipe.score_samples(feature_matrix(test_frame))
    rows = []
    for c in [.03,.05,.08,.12,.18]:
        threshold = np.percentile(train_scores, 100*c)
        rows.append({'contamination':c, **metrics(test_frame.is_anomaly, (test_scores < threshold).astype(int))})
    return rows

def main():
    ensure_directories()
    bundle = joblib.load(MODEL)  # Trusted local file only; no uploaded models.
    test = pd.read_csv(DATA / 'test_logs.csv')
    result = evaluate(test,bundle)
    (ARTIFACTS/'metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame(sensitivity(pd.read_csv(DATA/'train_logs.csv'),test,bundle)).to_csv(ARTIFACTS/'sensitivity.csv',index=False)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__ == '__main__':
    main()
