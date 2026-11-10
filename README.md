# Analyse des connexions

**Détection intelligente des connexions anormales par Intelligence Artificielle**

Mini-projet universitaire de cybersécurité : un simulateur de journaux, un modèle Isolation Forest et un tableau de bord Streamlit à cinq pages. Exécution locale sur CPU, sans API payante, base de données ni fournisseur d’authentification.

## Contexte et objectif

Les connexions inhabituelles peuvent justifier une vérification complémentaire : échecs répétés, activité nocturne, fréquence élevée, changement d’IP ou type de terminal inédit. Le système apprend sans étiquettes, puis compare ses alertes aux scénarios connus du simulateur. Une alerte n’est pas une preuve d’attaque.

## Fonctionnalités

- **Vue de sécurité** : indicateurs cohérents avec les filtres, activité, répartition des décisions et événements à vérifier.
- **Analyse des connexions** : distributions, corrélations, recherche littérale et export CSV.
- **Détection des anomalies** : évaluation manuelle avec historique causal, score et percentile relatif ; import de CSV fictifs validés.
- **Simulation** : événements normaux, suspects ou aléatoires ; contexte explicite et réinitialisation de session.
- **Performance** : matrice de confusion, précision, rappel, F1, accuracy, ROC-AUC, Average Precision, comparaison aux règles et sensibilité au seuil.

L’interface claire associe un fond blanc perlé, du vert d’eau, de la lavande et des accents ambre. La navigation avec icônes, les cartes de synthèse et les graphiques Plotly partagent la même identité visuelle. Aucun indicateur ne représente une mesure de trafic réel.

## Technologies

Python 3.11 (version testée), Pandas 2.3.3, NumPy 2.2.6, Scikit-learn 1.7.2, Streamlit 1.50.0, Plotly 6.3.1, Joblib 1.5.2 et pytest 8.4.2. Les versions directes sont fixées dans `requirements.txt`. Les outils du notebook sont également inclus. Python 3.12 est une cible compatible mais doit être vérifié dans son propre environnement.

## Interface

L’interface ne porte aucun nom de produit. Les textes courants utilisent une taille moyenne de 15–16 px et les intitulés décrivent directement les fonctions.

Refonte du 10 novembre 2026 : thème clair, navigation avec icônes, cartes aux accents pastel, graphique d’activité et anneau de répartition côte à côte, sections numérotées et formulaires sur fond blanc. Les cinq pages utilisent les mêmes composants visuels. La capture conservée dans `docs/screenshots/overview.jpg` est une archive de l’ancienne interface, pas une capture de cette refonte.

## Installation Windows / VS Code

Ouvrir un terminal PowerShell **dans ce dossier** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.generate_data
.\.venv\Scripts\python.exe -m src.train_model
.\.venv\Scripts\python.exe -m src.evaluate_model
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Ouvrir [l’application locale](http://localhost:8501). Arrêter avec Ctrl+C. L’installation initiale télécharge les dépendances ; les données, l’entraînement et l’application ne font ensuite appel à aucun service externe.

Alternative automatisée : `powershell -ExecutionPolicy Bypass -File .\start.ps1`. Cette option ne vaut que pour ce processus. Si les scripts PowerShell sont interdits, utiliser directement les commandes `python.exe` ci-dessus, sans activation et sans modifier la politique de sécurité. Dans VS Code, sélectionner `.venv\Scripts\python.exe` comme interpréteur et noyau du notebook.

Les données et le modèle existants sont réutilisés au lancement. Pour une reconstruction volontaire :

```powershell
.\.venv\Scripts\python.exe -m src.generate_data --force
.\.venv\Scripts\python.exe -m src.train_model
.\.venv\Scripts\python.exe -m src.evaluate_model
```

**Après toute régénération des données, réentraîner et réévaluer le modèle.** Ne jamais remplacer le fichier Joblib par un modèle d’origine inconnue : sa désérialisation n’est pas sûre pour des fichiers non fiables.

## Données et variables

12 000 événements, 400 utilisateurs fictifs, 60 jours, graine 42. Les trois CSV sont créés dans `data/` : jeu complet, train de 9 000 lignes et test de 3 000 lignes. Les rafales augmentent la proportion finale d’événements suspects ; elle est calculée dans le rapport de résultats.

| Champ | Signification |
|---|---|
| event_id, user_id | Identifiants fictifs, exclus du modèle |
| timestamp, login_hour, day_of_week | Date UTC et composantes temporelles |
| source_ip | Adresse privée/documentaire, exclue du modèle |
| ip_changed, new_ip | Changement depuis la dernière IP et absence dans l’historique |
| failed_attempts, attempts_10min | Échecs et tentatives antérieurs sur [t−10 min, t[ |
| login_success | Résultat de la connexion courante |
| device_type, is_new_device | Type de terminal et nouveauté du type dans l’historique |
| anomaly_type, is_anomaly | Vérité terrain du simulateur, réservée à l’analyse/évaluation |

Les événements simultanés ne se voient pas mutuellement. Les utilisateurs inconnus démarrent sans historique : « nouveau » signifie inconnu dans le contexte disponible. L’IP n’est jamais transformée en nombre ordinal.

## Algorithme et évaluation

Le pipeline médiane + Isolation Forest reçoit sept caractéristiques numériques : heure sin/cos, compteurs récents, changement et nouveauté IP, nouveauté du type de terminal. Il apprend sur tout l’historique d’entraînement majoritairement normal, sans utiliser les labels. Paramètres : 200 arbres, sous-échantillon 256, contamination 8 %, graine 42.

`predict()` retourne +1 pour un inlier et −1 pour un outlier. Le système affiche 0 et 1. Le score présenté vaut `−decision_function` : un score strictement positif dépasse le seuil d’anomalie. Le percentile situe ce score dans le train ; **ce n’est pas une probabilité d’attaque**. Voir la [documentation officielle de l’algorithme](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html).

L’évaluation utilise les 25 % d’événements les plus récents. Les règles de référence déclenchent pour ≥3 échecs, ≥6 tentatives ou IP nouvelle avant 6 h. Les résultats réellement calculés sont dans [docs/results.md](docs/results.md) et la page Performance. Les JSON et CSV de calcul se trouvent dans `artifacts/`. Les variations de contamination sont descriptives et ne servent pas à optimiser sur le test.

## Architecture

```text
app.py                       Navigation Streamlit
requirements.txt             Dépendances directes fixées
start.ps1                    Installation et démarrage Windows
.streamlit/config.toml        Thème et télémétrie désactivée
src/
  generate_data.py            Génération reproductible
  preprocessing.py            Historique causal, validation, variables
  train_model.py              Entraînement et persistance
  evaluate_model.py           Mesures et baseline
  predict.py                 Inférence et évaluation contextuelle
  simulation.py              Scénarios interactifs
  ui.py, utils.py             Composants communs et chemins
pages/                       Les cinq pages du dashboard
assets/style.css             Styles cohérents
data/                        CSV générés localement, non versionnés
models/                      Joblib local de confiance, non versionné
artifacts/                   Résultats d’exécution, non versionnés
tests/                       Tests unitaires et interactions Streamlit
notebooks/                   Notebook explicatif exécutable
scripts/                     Construction et vérification du notebook
docs/                        Méthodologie, rapport, résultats, soutenance
```

## CSV et sécurité

Importer uniquement des données fictives. Limites : 10 Mo et 100 000 lignes. Champs bruts requis : event_id, user_id, timestamp, source_ip, device_type, login_success. Les doublons, champs absents, dates/IP invalides et résultats non binaires sont rejetés. Les caractéristiques sont recalculées depuis le fichier importé, sans fusion implicite avec les utilisateurs locaux. L’import n’est pas sauvegardé et ne réentraîne pas le modèle. Les exports neutralisent les cellules textuelles pouvant être interprétées comme formules par un tableur.

Aucun mot de passe, jeton, donnée personnelle ou journal réel n’est nécessaire. Aucun modèle téléversé n’est accepté. Les environnements, outils téléchargés, secrets, CSV et modèles sont ignorés par Git.

## Notebook et documentation

- [Notebook en français](notebooks/anomaly_detection_explained.ipynb) : exploration, modèle, graphiques et comparaison.
- [Méthodologie](docs/methodology.md) : fenêtres, conventions et intuition mathématique.
- [Rapport](docs/report.md) : mini-projet rédigé et résultats vérifiables.
- [Guide de soutenance](docs/presentation_guide.md) : parcours de 9 minutes et questions probables.
- [Validation](docs/results.md) : valeurs et vérifications réellement exécutées.

Exécuter toutes les cellules sans ouvrir Jupyter : `.\.venv\Scripts\python.exe scripts/verify_notebook.py`.
Le notebook exécuté est enregistré dans `artifacts/`. Pour mettre à jour le résumé chiffré après l’évaluation : `.\.venv\Scripts\python.exe scripts/write_results.py`.

## Limites et améliorations

Les données synthétiques ne représentent pas toute la diversité du terrain. Les règles peuvent mieux détecter les scénarios qui ont servi à concevoir le simulateur. Le modèle laisse passer certaines anomalies et peut signaler des événements légitimes. Il ne reconnaît pas les appareils physiques, n’apprend pas un profil individuel complet et ne gère pas automatiquement la dérive. Aucun mécanisme MFA réel ni blocage n’est implémenté.

Améliorations possibles : validation chronologique supplémentaire, profils par utilisateur, meilleure simulation des réseaux partagés, données représentatives autorisées et étude du coût des erreurs. Cette application est un prototype universitaire, pas un dispositif de sécurité opérationnel.

## GitHub et licence

Dépôt public : [HajarLaziz/SentinelAI-Login-Anomaly-Detection](https://github.com/HajarLaziz/SentinelAI-Login-Anomaly-Detection). Les jalons de développement sont conservés dans des commits distincts. La licence reste à choisir explicitement ; aucune autorisation open source n’est présumée avant ce choix.

Voir le [guide de publication et de vérification](docs/github.md) pour les prochaines contributions.
