"""Small hand-written fixtures test causality, not scientific performance."""
import joblib
import pandas as pd
import pytest
from src import lanl

def fixture():
    return pd.DataFrame([dict(event_id=str(i),time=t,user_id='U1@DOM1',
        source_host=s,destination_host='C2',outcome=o)
        for i,(t,s,o) in enumerate([(1,'C1','Fail'),(1,'C2','Success'),
                                   (601,'C1','Success'),(602,'C3','Fail')])])

def test_history_excludes_present_and_future():
    f=lanl.engineer(fixture())
    assert f.attempts_10min.tolist()==[0,0,2,1]
    assert f.failed_attempts.tolist()==[0,0,1,0]
    assert f.new_source.tolist()==[1,1,0,1]
    pd.testing.assert_frame_equal(f.iloc[:3],lanl.engineer(fixture().iloc[:3]))

def test_labels_not_features_and_reload(tmp_path):
    f=lanl.engineer(fixture()); f['redteam_label']=[0,1,0,1]
    path=tmp_path/'model.joblib'; bundle=lanl.train(f,path)
    assert set(lanl.matrix(f))==set(lanl.FEATURES)
    assert 'redteam_label' not in bundle['features']
    result=lanl.predict(f,joblib.load(path))
    assert set(result.prediction)<=set([0,1])
    assert result.anomaly_score.notna().all()
    event=fixture().iloc[-1].to_dict();event.update(user_id='U9999@DOM1',event_id='new')
    assessed=lanl.assess(event,f,bundle)
    assert assessed.history_events.iloc[0]==0
    assert assessed.new_source.iloc[0]==1

def test_upload_recalculates_context():
    f=fixture();f['attempts_10min']=999;f['redteam_label']=1
    out=lanl.read_upload(f.to_csv(index=False).encode())
    assert 'redteam_label' not in out
    assert out.attempts_10min.max()==2
    with pytest.raises(ValueError):lanl.read_upload(b'wrong\n1')
    f.loc[0,'source_host']=None
    with pytest.raises(ValueError):lanl.engineer(f)

@pytest.mark.parametrize('column,value',[('time',-1),('time',1.5),('source_host','192.0.2.1'),('outcome','unknown')])
def test_invalid_data(column,value):
    f=fixture().astype({'time':float});f.loc[0,column]=value
    with pytest.raises(ValueError):lanl.validate(f)

def test_real_prepared_dataset():
    if not (lanl.DATA/'login_logs.csv').exists():pytest.skip('Run real LANL import first')
    f=pd.read_csv(lanl.DATA/'login_logs.csv')
    train=pd.read_csv(lanl.DATA/'train_logs.csv');test=pd.read_csv(lanl.DATA/'test_logs.csv')
    assert train.time.max()<test.time.min()
    assert len(train)+len(test)==len(f)
    assert f.event_id.str.startswith('LANL-').all()
    assert not {'source_ip','device_type','timestamp'} & set(f)
    assert f.redteam_label.sum()>0
