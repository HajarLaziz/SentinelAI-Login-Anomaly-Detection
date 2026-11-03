import numpy as np
import pandas as pd
import pytest
from src.preprocessing import engineer_history,feature_matrix,FEATURES,read_upload,safe_csv

def tiny():
    return pd.DataFrame(dict(event_id=['a','b','c','d'],user_id=['u']*4,
        timestamp=['2026-01-01 10:00','2026-01-01 10:05','2026-01-01 10:10','2026-01-01 10:11'],
        source_ip=['192.0.2.1','192.0.2.1','192.0.2.2','192.0.2.1'],
        device_type=['desktop','desktop','mobile','desktop'],login_success=[0,0,1,1]))

def test_causal_windows():
    result=engineer_history(tiny())
    assert result.attempts_10min.tolist()==[0,1,2,2]
    assert result.failed_attempts.tolist()==[0,1,2,1]
    assert result.new_ip.tolist()==[1,0,1,0]
    assert result.ip_changed.tolist()==[0,0,1,1]
    assert result.is_new_device.tolist()==[1,0,1,0]
    pd.testing.assert_frame_equal(result.iloc[:2],engineer_history(tiny().iloc[:2]))

def test_simultaneous_and_unseen():
    raw=tiny()
    raw.loc[1,'timestamp']=raw.loc[0,'timestamp']
    raw.loc[3,'user_id']='unseen'
    out=engineer_history(raw)
    assert out.attempts_10min.tolist()==[0,0,2,0]
    assert out.iloc[3].new_ip==1

def test_target_leakage(frame):
    altered=frame.copy()
    altered['is_anomaly']=1-frame.is_anomaly
    altered['anomaly_type']='arbitrary'
    altered['user_id']='anything'
    pd.testing.assert_frame_equal(feature_matrix(frame),feature_matrix(altered))
    assert list(feature_matrix(frame))==FEATURES

def test_cyclical_and_missing(frame):
    test=frame.head(2).copy()
    test['login_hour']=[0,6]
    test.loc[0,'failed_attempts']=np.nan
    matrix=feature_matrix(test)
    assert np.allclose(matrix.hour_sin,[0,1])
    assert np.allclose(matrix.hour_cos,[1,0],atol=1e-10)
    assert pd.isna(matrix.iloc[0].failed_attempts)

@pytest.mark.parametrize('case',['missing','duplicate','ip','timestamp','success','blank'])
def test_upload_rejects_invalid(case):
    raw=tiny()
    if case=='missing': raw=raw.drop(columns='user_id')
    if case=='duplicate': raw.loc[1,'event_id']='a'
    if case=='ip': raw.loc[0,'source_ip']='not-an-ip'
    if case=='timestamp': raw.loc[0,'timestamp']='invalid'
    if case=='success': raw.loc[0,'login_success']=7
    if case=='blank': raw.loc[0,'user_id']=' '
    with pytest.raises(ValueError): read_upload(raw.to_csv(index=False).encode())

def test_upload_valid_and_size():
    assert len(read_upload(tiny().to_csv(index=False).encode()))==4
    with pytest.raises(ValueError): read_upload(b'x'*(10*1024*1024+1))
    with pytest.raises(ValueError): read_upload(b'')

def test_csv_formula_escaped():
    assert "'=1+1" in safe_csv(pd.DataFrame({'x':['=1+1']})).decode('utf-8-sig')
