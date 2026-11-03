# Résultats expérimentaux reproductibles

Exécution locale du 3 novembre 2026, Python 3.11, graine 42. Les chiffres ci-dessous proviennent de `artifacts/metrics.json` et des CSV générés. Relancer ce script après une nouvelle évaluation.

- Dataset : **12000 lignes × 15 colonnes**, 400 utilisateurs fictifs.
- Vérité terrain : 8915 normaux, 3085 suspects (25.71%).
- Train : 9000 événements, 2277 suspects (25.30%).
- Test : 3000 événements, 2192 normaux et 808 suspects.
- Découpage temporel 75/25 ; caractéristiques calculées sans observations futures.

| Modèle | Précision | Rappel | F1 | Accuracy | FP | FN | Taux FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isolation Forest | 0.6570 | 0.1683 | 0.2680 | 0.7523 | 71 | 672 | 3.2391% |
| Règles | 0.9978 | 0.5631 | 0.7199 | 0.8820 | 1 | 353 | 0.0456% |

Isolation Forest : ROC-AUC **0.8714**, PR-AUC trapézoïdale **0.6609**, Average Precision **0.6604**.

Matrice de confusion IA, lignes = réel et colonnes = prédit, ordre normal puis suspect :

```text
[2121, 71]
[672, 136]
```

## Interprétation

Le classement des scores est informatif (ROC-AUC), mais le seuil fixé à 8 % produit un rappel faible. La proportion réelle de scénarios suspects est nettement plus élevée. Les règles détectent mieux ces motifs synthétiques explicites. Le projet ne prétend donc pas démontrer une supériorité de l’IA. Modifier le seuil pour maximiser F1 sur ce test invaliderait son rôle d’évaluation indépendante. Une validation temporelle supplémentaire serait nécessaire.

## Vérifications exécutées

- 30 tests pytest réussis : génération, causalité, import, persistance, inférence et interactions des cinq pages.
- `pip check` : aucune dépendance incompatible signalée.
- Notebook : 11 cellules de code exécutées sans erreur dans le noyau local.
- Modèle sauvegardé puis rechargé ; prédictions identiques vérifiées.
- Serveur Streamlit local : endpoint de santé HTTP répondant `ok`.
- Vue de sécurité et graphiques de performance inspectés dans un navigateur, format portable 1366 × 900.
- GitHub : publication non effectuée, authentification propriétaire absente lors de la vérification.
- Licence : choix utilisateur en attente ; aucune licence ouverte imposée.

Les tests ne démontrent pas une efficacité opérationnelle sur des données réelles. Python 3.12 et tous les navigateurs possibles ne sont pas testés.
