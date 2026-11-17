"""Real LANL authentication workflow. No synthetic replacement or invented IPs."""
from collections import deque
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from src.evaluate_model import metrics

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/lanl'
MODEL = ROOT/'models/lanl_isolation_forest.joblib'
FEATURES = ['hour_sin','hour_cos','failed_attempts','attempts_10min',
            'source_changed','new_source','new_destination']
RAW = ['event_id','time','user_id','source_host','destination_host','outcome']
CUTOFF = 2*86400


def validate(frame):
    missing = set(RAW)-set(frame)
    if missing: raise ValueError('Colonnes manquantes : '+', '.join(sorted(missing)))
    if frame.empty or len(frame)>1000000: raise ValueError('Entre 1 et 1 000 000 lignes attendues.')
    out = frame.copy()
    if out[RAW].isna().any().any(): raise ValueError('Champs obligatoires manquants.')
    if out.event_id.duplicated().any(): raise ValueError('event_id doit être unique.')
    out['time'] = pd.to_numeric(out.time,errors='raise')
    if not (np.isfinite(out.time)&(out.time>=0)&(out.time%1==0)).all():
        raise ValueError('time doit être un nombre entier positif de secondes relatives.')
    out['time'] = out.time.astype('int64')
    for col in ['event_id','user_id','source_host','destination_host']:
        out[col] = out[col].astype(str)
        if out[col].str.strip().eq('').any() or out[col].str.len().gt(128).any():
            raise ValueError(f'Champ {col} invalide.')
    if not out.user_id.str.fullmatch(r'U\d+@[^\s,]+').all():
        raise ValueError('Utilisateur LANL attendu, par exemple U748@DOM1.')
    for col in ['source_host','destination_host']:
        if not out[col].str.fullmatch(r'C\d+').all():
            raise ValueError('Machine anonymisée attendue, par exemple C17693 ; aucune IP inventée.')
    if not out.outcome.isin(['Success','Fail','Failure']).all():
        raise ValueError('outcome doit valoir Success, Fail ou Failure.')
    return out.sort_values('time',kind='stable').reset_index(drop=True)


def engineer(frame):
    out = validate(frame)
    states={}; pending=[]; previous_time=None; values=[]
    def update():
        for row,state in pending:
            failure=int(row.outcome!='Success')
            state['recent'].append((row.time,failure));state['failures']+=failure
            state['last']=row.source_host;state['sources'].add(row.source_host)
            state['destinations'].add(row.destination_host)
        pending.clear()
    for row in out.itertuples():
        if previous_time is not None and row.time!=previous_time: update()
        previous_time=row.time
        state=states.setdefault(row.user_id,dict(last=None,sources=set(),destinations=set(),recent=deque(),failures=0))
        q=state['recent']
        while q and q[0][0]<row.time-600:
            _,failure=q.popleft();state['failures']-=failure
        values.append((len(q),state['failures'],int(state['last'] is not None and state['last']!=row.source_host),
                       int(row.source_host not in state['sources']),int(row.destination_host not in state['destinations'])))
        pending.append((row,state))
    update()
    out[['attempts_10min','failed_attempts','source_changed','new_source','new_destination']]=values
    out['relative_day']=out.time//86400
    out['relative_hour']=(out.time%86400)//3600
    out['hour_sin']=np.sin(2*np.pi*out.relative_hour/24)
    out['hour_cos']=np.cos(2*np.pi*out.relative_hour/24)
    out['login_success']=(out.outcome=='Success').astype(int)
    out['relative_time']=[f'J+{t//86400} {t%86400//3600:02d}:{t%3600//60:02d}:{t%60:02d}' for t in out.time]
    return out


def matrix(frame):
    return frame[FEATURES].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan)


def train(frame,path=MODEL):
    pipe=Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
                   ('forest',IsolationForest(n_estimators=200,max_samples=256,contamination=.01,random_state=42,n_jobs=1))])
    pipe.fit(matrix(frame))
    bundle=dict(pipeline=pipe,features=FEATURES,contamination=.01,n_estimators=200,
                training_rows=len(frame),train_end=int(frame.time.max()),
                reference_scores=np.sort(-pipe.decision_function(matrix(frame))),dataset='LANL',
                scope='NTLM / Network / LogOn, source account U1..U1000, first 3 relative days')
    path.parent.mkdir(parents=True,exist_ok=True);joblib.dump(bundle,path)
    return bundle


def predict(frame,bundle):
    out=frame.copy();X=matrix(frame);pipe=bundle['pipeline']
    out['prediction']=(pipe.predict(X)==-1).astype(int)
    out['anomaly_score']=-pipe.decision_function(X)
    out['relative_percentile']=np.searchsorted(bundle['reference_scores'],out.anomaly_score,side='right')/len(bundle['reference_scores'])*100
    out['status']=np.where(out.prediction==1,'À vérifier','Habituel')
    out['recommendation']=np.where(out.prediction==1,'Vérification complémentaire recommandée.','Aucun dépassement du seuil ; absence d’attaque non garantie.')
    return out


def assess(event,history,bundle):
    event=validate(pd.DataFrame([event])).iloc[0].to_dict()
    past=history[(history.user_id==event['user_id'])&(history.time<event['time'])]
    if event['event_id'] in set(past.event_id): raise ValueError('Identifiant déjà présent dans le contexte.')
    result=predict(engineer(pd.concat([past[RAW],pd.DataFrame([event])],ignore_index=True)).tail(1),bundle)
    result['history_events']=len(past)
    return result


def read_upload(blob):
    if len(blob)>10*1024*1024: raise ValueError('Limite : 10 Mo.')
    try:
        frame=pd.read_csv(BytesIO(blob))
        if len(frame)>100000: raise ValueError('Limite import : 100 000 lignes.')
        # Discard alleged labels and supplied features. They are not trusted.
        return engineer(frame[RAW] if set(RAW)<=set(frame) else frame)
    except (ValueError,TypeError,UnicodeError,pd.errors.ParserError) as exc:
        raise ValueError(f'CSV invalide : {exc}') from exc


def baseline(frame):
    return ((frame.failed_attempts>=3)|(frame.attempts_10min>=6)|
            ((frame.new_source==1)&(frame.new_destination==1)&(frame.attempts_10min>=3))).astype(int)


def evaluate(frame,bundle):
    scored=predict(frame,bundle)
    result={'Isolation Forest':metrics(frame.redteam_label,scored.prediction,scored.anomaly_score),
            'Règles':metrics(frame.redteam_label,baseline(frame))}
    return result


def prepare():
    path=DATA/'auth_selected.csv'
    if not path.exists(): raise FileNotFoundError('Exécutez python -m src.import_lanl pour télécharger les journaux réels.')
    parts=[]
    for part in pd.read_csv(path,chunksize=100000):
        parts.append(part[(part.auth_type=='NTLM')&(part.logon_type=='Network')])
    frame=engineer(pd.concat(parts,ignore_index=True))
    train_frame=frame[frame.time<CUTOFF];test=frame[frame.time>=CUTOFF]
    if train_frame.empty or test.empty: raise ValueError('Découpage temporel vide.')
    for name,value in [('login_logs',frame),('train_logs',train_frame),('test_logs',test)]:
        value.to_csv(DATA/f'{name}.csv',index=False)
    bundle=train(train_frame)
    results=evaluate(test,bundle)
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    manifest.update(scope=bundle['scope'],rows=len(frame),users=frame.user_id.nunique(),
                    train_rows=len(train_frame),test_rows=len(test),train_redteam=int(train_frame.redteam_label.sum()),
                    test_redteam=int(test.redteam_label.sum()),redteam=int(frame.redteam_label.sum()),
                    failures=int((frame.outcome!='Success').sum()),features=FEATURES,
                    first_second=int(frame.time.min()),last_second=int(frame.time.max()),
                    prepared_sha256=hashlib.sha256((DATA/'login_logs.csv').read_bytes()).hexdigest())
    (DATA/'prepared_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'metrics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(manifest=manifest,metrics=results),ensure_ascii=True,indent=2))


if __name__=='__main__': prepare()
