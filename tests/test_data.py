import pandas as pd
import pytest
from src.generate_data import generate_raw, SCENARIOS
from src.preprocessing import RAW_COLUMNS, engineer_history

def test_generation_reproducible():
    pd.testing.assert_frame_equal(generate_raw(500,20),generate_raw(500,20))

def test_schema_ranges(frame):
    expected = set(RAW_COLUMNS+['login_hour','day_of_week','ip_changed','new_ip','failed_attempts','attempts_10min','is_new_device','anomaly_type','is_anomaly'])
    assert expected <= set(frame)
    assert len(frame)==2000 and frame.user_id.nunique()==50
    assert frame.timestamp.is_monotonic_increasing
    assert frame.event_id.is_unique and not frame.isna().any().any()
    assert frame.login_hour.between(0,23).all()
    assert frame.day_of_week.between(0,6).all()
    assert (frame.failed_attempts<=frame.attempts_10min).all()
    assert set(frame.is_anomaly)=={0,1}
    assert set(SCENARIOS)<=set(frame.anomaly_type)

def test_invalid_generator():
    with pytest.raises(ValueError):
        generate_raw(0)
