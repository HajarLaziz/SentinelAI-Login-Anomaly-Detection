import joblib
import numpy as np
import pandas as pd
from src.preprocessing import feature_matrix, engineer_history, RAW_COLUMNS
from src.utils import MODEL

def load_model():
    if not MODEL.exists():
        raise FileNotFoundError('Modèle absent. Exécutez python -m src.train_model.')
    return joblib.load(MODEL)

def predict(frame, bundle=None):
    bundle = load_model() if bundle is None else bundle
    out = frame.copy()
    matrix = feature_matrix(frame)
    out['prediction'] = (bundle['pipeline'].predict(matrix) == -1).astype(int)
    out['anomaly_score'] = -bundle['pipeline'].decision_function(matrix)
    reference = bundle['reference_scores']
    out['relative_percentile'] = np.searchsorted(reference,out.anomaly_score,side='right') / len(reference)*100
    out['status'] = np.where(out.prediction==1, 'Suspect', 'Normal')
    out['severity'] = np.where(out.prediction==0,'Standard',np.where(out.relative_percentile>=99,'Élevée','À vérifier'))
    out['recommendation'] = np.where(out.prediction==1,'Vérification supplémentaire recommandée (MFA).','Surveillance habituelle.')
    return out

def assess_event(event: dict, history: pd.DataFrame, bundle=None):
    stamp = pd.to_datetime(event['timestamp'],utc=True).tz_convert(None)
    past = history.copy()
    past['timestamp'] = pd.to_datetime(past.timestamp,utc=True).dt.tz_convert(None)
    past = past[(past.timestamp < stamp) & (past.user_id == event['user_id'])]
    event = {**event,'timestamp':stamp}
    features = engineer_history(pd.concat([past[RAW_COLUMNS],pd.DataFrame([event])],ignore_index=True))
    current = features[features.event_id==event['event_id']]
    result = predict(current,bundle)
    result['history_events'] = len(past)
    return result

def contributing_factors(row):
    factors = []
    for condition,label in [(row.failed_attempts>=3,'Échecs récents répétés'),
                            (row.attempts_10min>=6,'Fréquence élevée'),
                            (row.login_hour<6,'Horaire nocturne'),
                            (row.new_ip==1,'IP absente de l’historique disponible'),
                            (row.is_new_device==1,'Type de terminal inédit dans cet historique')]:
        if condition:
            factors.append(label)
    return factors
