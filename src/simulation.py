"""One click produces a finite synthetic scenario and its causal context."""
import numpy as np
import pandas as pd
from src.predict import assess_event
from src.preprocessing import RAW_COLUMNS

def simulate(history, sequence, mode, bundle):
    rng = np.random.default_rng(4200+sequence)
    suspicious = mode == 'suspect' or (mode == 'random' and rng.random()<.5)
    user = f'USR-{int(rng.integers(400)):04d}'
    stamp = pd.to_datetime(history.timestamp).max().normalize()+pd.Timedelta(days=1,hours=2 if suspicious else 14)
    known = history[history.user_id==user].sort_values('timestamp')
    ip = f'198.51.100.{int(rng.integers(1,255))}' if suspicious or known.empty else known.iloc[-1].source_ip
    device = 'unknown' if suspicious else 'desktop'
    prefix = f'SIM-{sequence}'
    context = []
    if suspicious:
        for i in range(9):
            context.append(dict(event_id=f'{prefix}-CTX-{i}',user_id=user,timestamp=stamp-pd.Timedelta(seconds=(9-i)*30),source_ip=ip,device_type=device,login_success=0))
    event = dict(event_id=prefix,user_id=user,timestamp=stamp,source_ip=ip,device_type=device,login_success=1)
    extra = pd.DataFrame(context,columns=RAW_COLUMNS)
    result = assess_event(event,pd.concat([history[RAW_COLUMNS],extra],ignore_index=True),bundle)
    result['scenario'] = 'Suspect simulé' if suspicious else 'Normal simulé'
    return result,pd.concat([extra,pd.DataFrame([event])],ignore_index=True)
