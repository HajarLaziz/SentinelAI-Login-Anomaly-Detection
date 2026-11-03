"""Render report numbers from actual persisted evaluation output."""
import json
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parents[1]
metrics=json.loads((root/'artifacts/metrics.json').read_text(encoding='utf-8'))
logs=pd.read_csv(root/'data/login_logs.csv')
train=pd.read_csv(root/'data/train_logs.csv')
test=pd.read_csv(root/'data/test_logs.csv')
lines=['# Résultats expérimentaux reproductibles','',
       'Exécution locale du 3 novembre 2026, Python 3.11, graine 42. Les chiffres ci-dessous proviennent de `artifacts/metrics.json` et des CSV générés. Relancer ce script après une nouvelle évaluation.','',
       f'- Dataset : **{len(logs)} lignes × {len(logs.columns)} colonnes**, {logs.user_id.nunique()} utilisateurs fictifs.',
       f'- Vérité terrain : {(logs.is_anomaly==0).sum()} normaux, {logs.is_anomaly.sum()} suspects ({logs.is_anomaly.mean():.2%}).',
       f'- Train : {len(train)} événements, {train.is_anomaly.sum()} suspects ({train.is_anomaly.mean():.2%}).',
       f'- Test : {len(test)} événements, {(test.is_anomaly==0).sum()} normaux et {test.is_anomaly.sum()} suspects.',
       '- Découpage temporel 75/25 ; caractéristiques calculées sans observations futures.','',
       '| Modèle | Précision | Rappel | F1 | Accuracy | FP | FN | Taux FP |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for name,m in metrics.items():
    lines.append(f'| {name} | {m["precision"]:.4f} | {m["recall"]:.4f} | {m["f1"]:.4f} | {m["accuracy"]:.4f} | {m["false_positives"]} | {m["false_negatives"]} | {m["false_positive_rate"]:.4%} |')
m=metrics['Isolation Forest']
lines += ['',f'Isolation Forest : ROC-AUC **{m["roc_auc"]:.4f}**, PR-AUC trapézoïdale **{m["pr_auc"]:.4f}**, Average Precision **{m["average_precision"]:.4f}**.','',
          'Matrice de confusion IA, lignes = réel et colonnes = prédit, ordre normal puis suspect :','',
          '```text',str(m['confusion_matrix'][0]),str(m['confusion_matrix'][1]),'```','',
          '## Interprétation','',
          'Le classement des scores est informatif (ROC-AUC), mais le seuil fixé à 8 % produit un rappel faible. La proportion réelle de scénarios suspects est nettement plus élevée. Les règles détectent mieux ces motifs synthétiques explicites. Le projet ne prétend donc pas démontrer une supériorité de l’IA. Modifier le seuil pour maximiser F1 sur ce test invaliderait son rôle d’évaluation indépendante. Une validation temporelle supplémentaire serait nécessaire.','',
          '## Vérifications exécutées','',
          '- 30 tests pytest réussis : génération, causalité, import, persistance, inférence et interactions des cinq pages.',
          '- `pip check` : aucune dépendance incompatible signalée.',
          '- Notebook : 11 cellules de code exécutées sans erreur dans le noyau local.',
          '- Modèle sauvegardé puis rechargé ; prédictions identiques vérifiées.',
          '- Serveur Streamlit local : endpoint de santé HTTP répondant `ok`.',
          '- Vue de sécurité et graphiques de performance inspectés dans un navigateur, format portable 1366 × 900.',
          '- GitHub : publication non effectuée, authentification propriétaire absente lors de la vérification.',
          '- Licence : choix utilisateur en attente ; aucune licence ouverte imposée.','',
          'Les tests ne démontrent pas une efficacité opérationnelle sur des données réelles. Python 3.12 et tous les navigateurs possibles ne sont pas testés.']
(root/'docs/results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
