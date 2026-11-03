"""Causal history: windows exclude the current event and include t-10 minutes."""
from collections import deque
from io import BytesIO
from ipaddress import ip_address
import numpy as np
import pandas as pd

RAW_COLUMNS = ['event_id','user_id','timestamp','source_ip','device_type','login_success']
FEATURES = ['hour_sin','hour_cos','failed_attempts','attempts_10min','ip_changed','new_ip','is_new_device']

def validate_raw(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(RAW_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError('Colonnes manquantes : ' + ', '.join(sorted(missing)))
    if frame.empty or len(frame) > 100000:
        raise ValueError('Le fichier doit contenir entre 1 et 100000 lignes.')
    out = frame.copy()
    if out[RAW_COLUMNS].isna().any().any():
        raise ValueError('Valeurs manquantes dans les champs obligatoires.')
    if out.event_id.duplicated().any():
        raise ValueError('Identifiants événement dupliqués.')
    out['timestamp'] = pd.to_datetime(out.timestamp, errors='raise', utc=True, format='mixed').dt.tz_convert(None)
    out['login_success'] = pd.to_numeric(out.login_success, errors='raise')
    if not out.login_success.isin([0,1]).all():
        raise ValueError('login_success doit valoir 0 ou 1.')
    for value in out.source_ip.unique():
        try:
            ip_address(str(value))
        except ValueError as exc:
            raise ValueError('Adresse IP invalide.') from exc
    for col in ['event_id','user_id','source_ip','device_type']:
        out[col] = out[col].astype(str)
        if out[col].str.strip().eq('').any() or out[col].str.len().gt(128).any():
            raise ValueError(f'Champ {col} vide ou trop long.')
    return out

def read_upload(content: bytes) -> pd.DataFrame:
    if len(content) > 10 * 1024 * 1024:
        raise ValueError('Limite de fichier : 10 Mo.')
    try:
        return engineer_history(pd.read_csv(BytesIO(content)))
    except (ValueError, TypeError, pd.errors.ParserError, UnicodeError) as exc:
        raise ValueError(f'CSV invalide : {exc}') from exc

def engineer_history(frame: pd.DataFrame) -> pd.DataFrame:
    out = validate_raw(frame).sort_values('timestamp', kind='stable').reset_index(drop=True)
    history = {}
    values = []
    # Equal timestamps are processed as a batch: none sees its simultaneous peers.
    for stamp, group in out.groupby('timestamp', sort=False):
        pending = []
        for row in group.itertuples():
            state = history.setdefault(row.user_id, dict(ip=None, ips=set(), devices=set(), recent=deque()))
            queue = state['recent']
            while queue and queue[0][0] < stamp - pd.Timedelta(minutes=10):
                queue.popleft()
            values.append((int(state['ip'] is not None and row.source_ip != state['ip']),
                           int(row.source_ip not in state['ips']), sum(1-s for _,s in queue),
                           len(queue), int(row.device_type not in state['devices'])))
            pending.append((row,state))
        for row,state in pending:
            state['ip'] = row.source_ip
            state['ips'].add(row.source_ip)
            state['devices'].add(row.device_type)
            state['recent'].append((stamp,row.login_success))
    out[['ip_changed','new_ip','failed_attempts','attempts_10min','is_new_device']] = values
    out['login_hour'] = out.timestamp.dt.hour
    out['day_of_week'] = out.timestamp.dt.dayofweek
    return out

def feature_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    hour = pd.to_numeric(frame['login_hour'], errors='coerce')
    if ((hour.dropna() < 0) | (hour.dropna() > 23)).any():
        raise ValueError('Heure hors intervalle 0–23.')
    result = pd.DataFrame({'hour_sin':np.sin(2*np.pi*hour/24), 'hour_cos':np.cos(2*np.pi*hour/24)}, index=frame.index)
    for col in FEATURES[2:]:
        result[col] = pd.to_numeric(frame[col], errors='coerce')
        if (result[col].dropna() < 0).any():
            raise ValueError('Les compteurs doivent être positifs.')
        if col in ('ip_changed','new_ip','is_new_device') and not result[col].dropna().isin([0,1]).all():
            raise ValueError('Les indicateurs doivent valoir 0 ou 1.')
    return result[FEATURES].replace([np.inf,-np.inf], np.nan)

def safe_csv(frame: pd.DataFrame) -> bytes:
    out = frame.copy()
    for col in out.select_dtypes(include=['object','string']):
        out[col] = out[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(('=','+','-','@','\t','\r')) else x)
    return out.to_csv(index=False).encode('utf-8-sig')
