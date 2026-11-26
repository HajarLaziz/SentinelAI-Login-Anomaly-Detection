"""Historical relationship rarity, fitted without attack annotations.

The reference day is frozen: neither validation nor test updates its counts.
Identifiers are lookup keys, never ordinal numeric predictors.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class ContextModel:
    def __init__(self, method='rarity'):
        self.method = method
        self.groups = [('user_id', 'source_host'),
                       ('user_id', 'destination_host'),
                       ('source_host', 'destination_host')]

    def fit(self, frame):
        self.counts = [frame.groupby(list(g)).size().to_dict() for g in self.groups]
        self.totals = [frame[g[0]].value_counts().to_dict() for g in self.groups]
        self.vocab = [frame[g[1]].nunique() + 1 for g in self.groups]
        if self.method == 'forest':
            self.forest = IsolationForest(n_estimators=300, max_samples=2048,
                                          random_state=42, n_jobs=1)
            self.forest.fit(self.transform(frame))
        return self

    def transform(self, frame):
        columns = {}
        for i, group in enumerate(self.groups):
            counts = np.array([self.counts[i].get(key, 0)
                               for key in frame[list(group)].itertuples(index=False, name=None)])
            totals = frame[group[0]].map(self.totals[i]).fillna(0).to_numpy()
            # Add-one smoothing gives finite values for unseen accounts/hosts.
            columns[f'rarity_{i}'] = -np.log((counts + 1) / (totals + self.vocab[i]))
        columns['failures'] = np.log1p(frame.failed_attempts.clip(lower=0))
        columns['attempts'] = np.log1p(frame.attempts_10min.clip(lower=0))
        columns['failure_now'] = frame.outcome.ne('Success').astype(int)
        return pd.DataFrame(columns, index=frame.index)

    def score(self, frame):
        features = self.transform(frame)
        if self.method == 'forest':
            return -self.forest.score_samples(features)
        return features[['rarity_0', 'rarity_1', 'rarity_2']].max(axis=1).to_numpy()

    def predict(self, frame):
        return (self.score(frame) > self.threshold).astype(int)

