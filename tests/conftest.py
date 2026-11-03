import pytest
from src.generate_data import generate_raw
from src.preprocessing import engineer_history
from src.train_model import train

@pytest.fixture(scope='session')
def frame():
    return engineer_history(generate_raw(2000,50))

@pytest.fixture(scope='session')
def bundle(frame,tmp_path_factory):
    return train(frame.iloc[:1500],tmp_path_factory.mktemp('model')/'model.joblib',n_estimators=60)
