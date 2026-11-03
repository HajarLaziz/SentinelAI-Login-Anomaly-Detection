import joblib
import numpy as np
import pandas as pd
from src.predict import predict,assess_event
from src.train_model import train
from src.evaluate_model import evaluate,metrics
from src.simulation import simulate

def test_persistence(frame,tmp_path):
    path=tmp_path/'model.joblib'
    original=train(frame.iloc[:1500],path,n_estimators=30)
    assert path.exists()
    pd.testing.assert_frame_equal(predict(frame.iloc[1500:],original),predict(frame.iloc[1500:],joblib.load(path)))

def test_predictions(frame,bundle):
    result=predict(frame,bundle)
    assert set(result.prediction)<={0,1}
    assert result.anomaly_score.notna().all()
    assert result.relative_percentile.between(0,100).all()
    assert ((result.anomaly_score>0)==(result.prediction==1)).all()
    broken=frame.head().copy()
    broken['failed_attempts']=np.nan
    assert predict(broken,bundle).anomaly_score.notna().all()

def test_manual_unseen_and_future_exclusion(frame,bundle):
    event=dict(event_id='NEW',user_id='unseen',timestamp='2025-01-01',source_ip='203.0.113.4',device_type='mobile',login_success=1)
    result=assess_event(event,frame,bundle).iloc[0]
    assert result.history_events==0 and result.new_ip==1 and result.attempts_10min==0

def test_scenarios(frame,bundle):
    normal,_=simulate(frame,1,'normal',bundle)
    suspect,_=simulate(frame,1,'suspect',bundle)
    assert normal.iloc[0].attempts_10min==0
    assert suspect.iloc[0].failed_attempts==9
    assert suspect.iloc[0].anomaly_score>normal.iloc[0].anomaly_score

def test_evaluation(frame,bundle):
    result=evaluate(frame.iloc[1500:],bundle)
    assert set(result)=={'Isolation Forest','Règles'}
    for values in result.values():
        assert 0<=values['f1']<=1
        assert sum(map(sum,values['confusion_matrix']))==500
    assert 'roc_auc' not in metrics([0,0],[0,1],[.1,.5])
