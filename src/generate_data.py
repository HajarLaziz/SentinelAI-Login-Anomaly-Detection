"""Generate fictional raw events; history features are computed separately."""
import argparse
import numpy as np
import pandas as pd
from src.utils import DATA, SEED, ensure_directories

SCENARIOS = ['brute_force', 'night_login', 'unseen_ip', 'high_frequency', 'new_device', 'combined']

def generate_raw(n_events: int = 12000, n_users: int = 400, seed: int = SEED) -> pd.DataFrame:
    if n_events < 100 or not 1 <= n_users <= 65000:
        raise ValueError('Au moins 100 événements et 1 à 65000 utilisateurs requis.')
    rng = np.random.default_rng(seed)
    rows = []
    while len(rows) < n_events:
        user = int(rng.integers(n_users))
        attack = rng.random() < .065
        kind = str(rng.choice(SCENARIOS)) if attack else 'normal'
        day = int(rng.integers(60))
        hour = float(np.clip(rng.normal(10 + user % 6, 2.5), 0, 23.9))
        if kind in ('night_login', 'combined') or rng.random() < .025:
            hour = float(rng.uniform(0, 6))
        stamp = pd.Timestamp('2026-01-01') + pd.Timedelta(days=day, hours=hour)
        ip = f'10.{user // 254}.{user % 254}.10'
        if kind in ('unseen_ip', 'combined') or rng.random() < .04:
            ip = f'192.0.2.{rng.integers(1,255)}'
        device = str(rng.choice(['desktop', 'mobile', 'tablet'], p=[.78,.18,.04]))
        if kind in ('new_device', 'combined'):
            device = 'unknown'
        burst = int(rng.integers(5, 17)) if kind in ('brute_force', 'high_frequency', 'combined') else int(rng.choice([1,2,3], p=[.88,.09,.03]))
        for k in range(burst):
            success = int(rng.random() > (.82 if kind in ('brute_force','combined') else .07))
            rows.append(dict(user_id=f'USR-{user:04d}', timestamp=stamp + pd.Timedelta(seconds=k*25),
                             source_ip=ip, device_type=device, login_success=success,
                             anomaly_type=kind, is_anomaly=int(attack)))
            if len(rows) >= n_events:
                break
    frame = pd.DataFrame(rows).sort_values('timestamp', kind='stable').reset_index(drop=True)
    frame.insert(0, 'event_id', [f'EVT-{i:06d}' for i in range(len(frame))])
    return frame

def main(force=False):
    from src.preprocessing import engineer_history
    ensure_directories()
    if (DATA / 'login_logs.csv').exists() and not force:
        print('Données existantes conservées. Utilisez --force pour régénérer.')
        return
    frame = engineer_history(generate_raw())
    cut = int(len(frame)*.75)
    for name, subset in [('login_logs',frame),('train_logs',frame.iloc[:cut]),('test_logs',frame.iloc[cut:])]:
        subset.to_csv(DATA / f'{name}.csv', index=False)
    print(frame.shape, frame.is_anomaly.value_counts().to_dict())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true')
    main(parser.parse_args().force)
