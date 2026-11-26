import joblib
import numpy as np
import pandas as pd
import pytest
from src.context_model import ContextModel
from src import lanl


def fixture():
    return lanl.engineer(pd.DataFrame([
        dict(event_id=str(i), time=i+1, user_id='U1@DOM1', source_host='C1',
             destination_host='C2', outcome='Success') for i in range(20)]))


def test_relationship_rarity_and_unseen_account():
    frame=fixture()
    model=ContextModel().fit(frame)
    unseen=frame.tail(1).copy()
    unseen['destination_host']='C99'
    assert model.score(unseen)[0]>model.score(frame)[0]
    unseen['user_id']='U999@DOM1'
    assert np.isfinite(model.score(unseen)).all()


def test_labels_do_not_change_reference():
    frame=fixture()
    first=ContextModel().fit(frame.assign(redteam_label=0))
    second=ContextModel().fit(frame.assign(redteam_label=1))
    np.testing.assert_array_equal(first.score(frame),second.score(frame))


def test_context_persistence_and_causal_guard(tmp_path):
    frame=fixture()
    model=ContextModel().fit(frame)
    model.threshold=2.;model.train_end=20
    model.reference_scores=np.sort(model.score(frame)-model.threshold)
    path=tmp_path/'model.joblib'
    joblib.dump(model,path)
    loaded=joblib.load(path)
    bundle=dict(context_model=loaded,reference_scores=loaded.reference_scores)
    with pytest.raises(ValueError,match='postérieur'):
        lanl.predict(frame,bundle)
    future=frame.tail(1).assign(time=21)
    prediction=lanl.predict(future,bundle)
    assert prediction.prediction.isin([0,1]).all()
    np.testing.assert_array_equal(loaded.score(future),model.score(future))
