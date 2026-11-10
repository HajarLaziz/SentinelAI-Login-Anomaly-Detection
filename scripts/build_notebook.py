"""Create the teaching notebook with standard JSON, no generated outputs."""
import json
from pathlib import Path

cells=[]
def markdown(text):
    cells.append(dict(cell_type='markdown',metadata={},source=text.splitlines(keepends=True)))
def code(text):
    cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=text.splitlines(keepends=True)))

markdown('''# Détection intelligente des connexions anormales par IA
## 1. Introduction
Clair est un prototype pédagogique local. Toutes les connexions sont fictives.
## 2. Objectifs
Construire un historique causal, apprendre une représentation du comportement ordinaire,
mesurer les erreurs et comparer Isolation Forest à des règles explicites.''')
markdown('## 3. Bibliothèques\nLe notebook réutilise exactement les fonctions de l’application.')
code('''from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import plotly.express as px
from src.utils import DATA, ARTIFACTS
from src.generate_data import main as generate
from src.preprocessing import engineer_history, feature_matrix
from src.train_model import train
from src.predict import predict
from src.evaluate_model import evaluate, sensitivity''')
markdown('## 4. Chargement\nGraine 42, 12 000 événements, 400 identifiants fictifs ; génération seulement si nécessaire.')
code("generate()\nlogs = pd.read_csv(DATA / 'login_logs.csv', parse_dates=['timestamp'])\nlogs.head()")
markdown('## 5. Exploration\nLes étiquettes décrivent les scénarios du simulateur, pas les décisions du modèle.')
code("display(logs.shape, logs.is_anomaly.value_counts(), logs.anomaly_type.value_counts())\npx.histogram(logs, x='login_hour', color='is_anomaly').show()")
markdown('## 6. Nettoyage\nLes champs bruts obligatoires invalides sont rejetés ; les valeurs numériques manquantes des caractéristiques sont imputées par une médiane apprise sur le train uniquement.')
code("display(logs.isna().sum(), logs.event_id.duplicated().sum())\nclean = engineer_history(logs)\nassert len(clean) == len(logs)")
markdown('## 7. Extraction des variables\nHeure cyclique : sin(2πh/24), cos(2πh/24). Compteurs sur [t−10 min, t[, donc sans événement actuel. Nouveauté par utilisateur selon le passé disponible. Aucun identifiant, IP brute ou label n’est fourni au modèle.')
code("X = feature_matrix(clean)\ndisplay(X.head(), X.columns.tolist())\nassert 'is_anomaly' not in X.columns")
markdown('## 8. Découpage chronologique\n75 % pour apprendre, 25 % pour évaluer. Le contexte antérieur du train est conservé pour les premières connexions du test : cette information est disponible dans un système réel.')
code("train_logs = pd.read_csv(DATA / 'train_logs.csv', parse_dates=['timestamp'])\ntest_logs = pd.read_csv(DATA / 'test_logs.csv', parse_dates=['timestamp'])\nassert train_logs.timestamp.max() <= test_logs.timestamp.min()\ndisplay(len(train_logs), len(test_logs))")
markdown('## 9. Apprentissage Isolation Forest\n200 arbres, sous-échantillons de 256, contamination fixée à 8 %. L’entraînement utilise tout le train, majoritairement normal, sans sélectionner les lignes avec leurs labels. Les points isolés rapidement sont plus atypiques.')
code("bundle = train(train_logs, ARTIFACTS / 'notebook_model.joblib')")
markdown('## 10. Prédiction\nScikit-learn renvoie −1 pour un outlier et +1 pour un inlier. Le dashboard les convertit en 1 et 0. Un score −decision_function positif indique un événement suspect ; ce score n’est pas une probabilité.')
code("scored = predict(test_logs, bundle)\nscored[['event_id', 'prediction', 'anomaly_score', 'relative_percentile']].head()")
markdown('## 11. Évaluation\nPrécision = VP/(VP+FP), rappel = VP/(VP+FN), F1 = moyenne harmonique. L’accuracy nécessite de tenir compte du déséquilibre. ROC-AUC et Average Precision utilisent le score continu.')
code("results = evaluate(test_logs, bundle)\ndisplay(pd.DataFrame(results).T.drop(columns='confusion_matrix'))")
markdown('## 12. Graphiques\nMatrice : lignes = réalité, colonnes = prédiction ; ordre normal puis suspect.')
code("px.imshow(results['Isolation Forest']['confusion_matrix'], text_auto=True, x=['Normal prédit','Suspect prédit'], y=['Normal réel','Suspect réel']).show()\npx.histogram(scored, x='anomaly_score', color='is_anomaly', barmode='overlay').show()")
markdown('## 13. Comparaison aux règles\nLes règles utilisent au moins trois échecs, six tentatives ou une IP nouvelle avant 6 h. La sensibilité au seuil est descriptive ; le jeu de test ne doit pas servir à sélectionner un modèle final.')
code("comparison = pd.DataFrame(results).T[['precision','recall','f1']]\npx.bar(comparison, barmode='group').show()\ndisplay(pd.DataFrame(sensitivity(train_logs, test_logs, bundle)).drop(columns='confusion_matrix'))")
markdown('''## 14. Conclusion
Les performances sont celles réellement affichées ci-dessus. Un résultat anormal appelle une
vérification, pas un blocage automatique. Les données simulées ne représentent pas tout le trafic réel.
La nouveauté au démarrage, la dérive temporelle, les faux positifs et les faux négatifs limitent ce prototype.
Une extension rigoureuse réserverait une validation temporelle distincte pour régler les paramètres.

Référence : [documentation officielle IsolationForest](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html).''')
notebook=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}},nbformat=4,nbformat_minor=5)
for i,cell in enumerate(cells): cell['id']=f'cell-{i:02d}'
path=Path(__file__).resolve().parents[1]/'notebooks'/'anomaly_detection_explained.ipynb'
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf-8')
