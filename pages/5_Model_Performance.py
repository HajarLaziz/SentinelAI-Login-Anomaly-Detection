import pandas as pd
import plotly.express as px
import streamlit as st
from src.ui import header,resources,chart,table,LABELS
from src.utils import DATA
from src.evaluate_model import evaluate,sensitivity
from src.predict import predict

header('Performance du modèle','Mesures calculées sur les 25 % d’événements les plus récents, jamais utilisés pour entraîner les arbres.')
_,bundle = resources()
test = pd.read_csv(DATA/'test_logs.csv')
results = evaluate(test,bundle)
score = results['Isolation Forest']
cols = st.columns(4)
for col,name in zip(cols,['precision','recall','f1','accuracy']):
    col.metric(LABELS[name],f'{score[name]:.3f}')
st.caption('L’accuracy seule peut masquer les erreurs sur une classe minoritaire. Les étiquettes du simulateur servent uniquement à cette évaluation.')
a,b = st.columns(2)
with a:
    chart(px.imshow(score['confusion_matrix'],x=['Prédit normal','Prédit suspect'],y=['Réel normal','Réel suspect'],text_auto=True,title='Matrice de confusion · test'),accent='indigo')
with b:
    comparison = pd.DataFrame(results).T[['precision','recall','f1','false_positive_rate']]
    chart(px.bar(comparison.reset_index().melt(id_vars='index'),x='variable',y='value',color='index',barmode='group',title='Modèle et règles — comparaison sur le test'),accent='turquoise')
table(pd.DataFrame(results).T.drop(columns='confusion_matrix').rename_axis('Modèle').reset_index(),'metrics')
scored = predict(test,bundle)
chart(px.histogram(scored,x='anomaly_score',color=scored.is_anomaly.map({0:'Normal réel',1:'Suspect réel'}),barmode='overlay',nbins=60,title='Distribution des scores par vérité terrain'),accent='rose')
st.caption(f'ROC-AUC : {score.get("roc_auc",float("nan")):.3f} · Average Precision : {score.get("average_precision",float("nan")):.3f}. AP résume la courbe précision-rappel ; ce n’est pas son intégrale trapézoïdale.')
st.caption(f'PR-AUC (intégrale trapézoïdale) : {score.get("pr_auc",float("nan")):.3f}. La différence avec AP vient de l’interpolation entre les seuils.')
with st.expander('Sensibilité au seuil et configuration'):
    experiment = pd.DataFrame(sensitivity(pd.read_csv(DATA/'train_logs.csv'),test,bundle))
    chart(px.line(experiment,x='contamination',y=['precision','recall','f1'],markers=True,title='Exploration descriptive — aucun choix final fondé sur le test'),accent='blue')
    st.json({k:bundle[k] for k in ['contamination','n_estimators','training_rows','train_end','features']})
st.warning('Prototype pédagogique : données synthétiques, erreurs possibles, dérive des comportements et démarrage sans historique. Une anomalie ne prouve pas une attaque. Aucune connexion n’est bloquée automatiquement.')
